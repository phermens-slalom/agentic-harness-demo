"""Deterministic new-capability detectors over the *added* lines of a PR diff.

Each detector is a small named function. A hit only adds approvers (Security, and AI governance team for
undeclared hosts and tool/protocol integrations); it never auto-approves a change and never blocks
one by itself. Allowlists and approver roles live in policy/capabilities.yaml.

What this does not do: it cannot see capabilities added outside the diff (for example a transitive
dependency that only changes a lock file), and a pattern match is review routing, not authorisation.
Tool access is enforced in code and platform IAM; protocol metadata (MCP, A2A) never grants access.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath

from ..policy import CapabilityPolicy
from .diff_parse import FileDiff, parse_diff

_COMMENT = re.compile(r"^\s*(?:#|//|/\*|\*|<!--)")


@dataclass(frozen=True)
class CapabilityFinding:
    kind: str  # model | host | region | data_store | dependency | tool_protocol
    detail: str  # a name only (never the full source line)
    path: str
    approvers: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.kind} {self.detail} ({self.path})"


def _normalise_package(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.lower())


# ---- line detectors: one added line in, the capability names it introduces out ----------------

_MODEL = re.compile(
    r"\b(?:gemini|gemma|imagen|veo|claude)-[a-z0-9][a-z0-9.\-]*[a-z0-9]"
    r"|\btext-embedding-[a-z0-9.\-]*[a-z0-9]|\btextembedding-gecko[a-z0-9.@\-]*",
    re.IGNORECASE,
)
_URL_HOST = re.compile(
    r"\b(?:https?|wss?|grpcs?|ftp)://(?:[^/\s@\"'<>]+@)?([a-z0-9](?:[a-z0-9.\-]*[a-z0-9])?)", re.IGNORECASE
)
_GOOGLEAPIS_HOST = re.compile(r"\b((?:[a-z0-9\-]+\.)+googleapis\.com)\b", re.IGNORECASE)
_REGION = re.compile(r"\b(?:us|europe|asia|australia|northamerica|southamerica|me|africa)-[a-z]+[0-9]+\b")
_GLOBAL_LOCATION = re.compile(
    r"""(?:\b(?:location|region)s?\w*\s*[=:]\s*["']global["']|/locations/global\b)"""
)
_DATA_STORES: dict[str, re.Pattern[str]] = {
    "bigquery": re.compile(
        r"\bbigquery\.Client\b|from\s+google\.cloud\s+import[^#]*\bbigquery\b|google\.cloud\.bigquery"
        r"|\bBigQuery\w*(?:Toolset|Plugin)\b"
    ),
    "firestore": re.compile(
        r"\bfirestore\.(?:Async)?Client\b|from\s+google\.cloud\s+import[^#]*\bfirestore\b"
        r"|google\.cloud\.firestore|\bFirestore\w*Service\b"
    ),
    "spanner": re.compile(
        r"\bspanner\.Client\b|from\s+google\.cloud\s+import[^#]*\bspanner\b|google\.cloud\.spanner"
        r"|\bSpanner\w*Toolset\b"
    ),
    "gcs": re.compile(
        r"\bstorage\.Client\b|from\s+google\.cloud\s+import[^#]*\bstorage\b|google\.cloud\.storage|\bgs://"
    ),
    "memory_bank": re.compile(r"MemoryBank|memory[_-]bank", re.IGNORECASE),
}
_PROTOCOLS: dict[str, re.Pattern[str]] = {
    "mcp": re.compile(
        r"\b(?:MCPToolset|McpToolset|StreamableHTTPConnectionParams|SseConnectionParams"
        r"|StdioConnectionParams|StdioServerParameters)\b|\bmcp[-_]?servers?\b|\b(?:from|import)\s+mcp\b",
        re.IGNORECASE,
    ),
    "a2a": re.compile(
        r"\b(?:RemoteA2aAgent|A2aAgent|AgentCard)\b|\ba2a[-_]sdk\b|\bagent[-_]card\b"
        r"|\.well-known/agent(?:-card)?(?:\.json)?|\b(?:from|import)\s+a2a\b",
        re.IGNORECASE,
    ),
    "delegation": re.compile(r"\bsub_agents\s*=|\bAgentTool\s*\(|\btransfer_to_agent\b"),
    "toolset": re.compile(
        r"\b(?:FunctionTool|LongRunningFunctionTool|OpenAPIToolset|APIHubToolset"
        r"|ApplicationIntegrationToolset|ComputerUseToolset)\b"
    ),
}
_TOOL_DEF = re.compile(r"^(?:async\s+)?def\s+([A-Za-z][A-Za-z0-9_]*)\s*\(")


def detect_models(line: str) -> list[str]:
    return sorted({m.lower() for m in _MODEL.findall(line)})


def detect_hosts(line: str) -> list[str]:
    hosts = {h.lower() for h in _URL_HOST.findall(line) if "." in h or h.lower() == "localhost"}
    hosts |= {h.lower() for h in _GOOGLEAPIS_HOST.findall(line)}
    return sorted(hosts)


def detect_regions(line: str) -> list[str]:
    found = set(_REGION.findall(line))
    if _GLOBAL_LOCATION.search(line):
        found.add("global")
    return sorted(found)


def detect_data_stores(line: str) -> list[str]:
    return sorted(name for name, pattern in _DATA_STORES.items() if pattern.search(line))


def detect_protocols(line: str) -> list[str]:
    return sorted(name for name, pattern in _PROTOCOLS.items() if pattern.search(line))


def detect_new_tool_functions(path: str, line: str) -> list[str]:
    """A new public top-level function in a `tools.py` or `tools/` module is a new agent tool."""
    p = PurePosixPath(path.lower())
    if p.name != "tools.py" and "tools" not in p.parts[:-1]:
        return []
    m = _TOOL_DEF.match(line)
    return [m[1]] if m else []


# ---- dependency detector: needs the whole file's added and removed lines ----------------------

_PYTHON_MANIFESTS = {"pyproject.toml"}
_REQ_NAME = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")
_PYPROJECT_DEP = re.compile(
    r"""^\s*["']([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*(?:[<>=!~;@(][^"']*)?["']\s*,?\s*(?:#.*)?$"""
)
_PACKAGE_JSON_DEP = re.compile(
    r"""^\s*"(@?[A-Za-z0-9][\w./@-]*)"\s*:\s*"(?:[\^~<>=*]|\d|latest|npm:|git|https?:|file:|github:)[^"]*"\s*,?\s*$"""
)
_GO_MOD_DEP = re.compile(r"^\s*(?:require\s+)?([a-z0-9.\-]+\.[a-z]{2,}/\S+)\s+v\d")


def _dependency_names(path: str, lines: Iterable[str]) -> set[str]:
    name = PurePosixPath(path.lower()).name
    out: set[str] = set()
    for line in lines:
        if not line.strip() or _COMMENT.match(line):
            continue
        if name.startswith("requirements") and name.endswith(".txt"):
            m = None if line.lstrip().startswith("-") else _REQ_NAME.match(line.strip())
        elif name == "pyproject.toml":
            m = _PYPROJECT_DEP.match(line)
        elif name == "package.json":
            m = _PACKAGE_JSON_DEP.match(line)
            if m and m[1] == "version":
                m = None
        elif name == "go.mod":
            m = _GO_MOD_DEP.match(line)
        else:
            return out
        if m:
            out.add(
                _normalise_package(m[1])
                if name in _PYTHON_MANIFESTS or name.startswith("requirements")
                else m[1].lower()
            )
    return out


def detect_new_dependencies(file: FileDiff) -> list[str]:
    """Names added to a manifest and not also removed from it (a version bump is not a new dependency)."""
    return sorted(_dependency_names(file.path, file.added) - _dependency_names(file.path, file.removed))


# ---- orchestration -----------------------------------------------------------------------------


def _scan_line(
    file: FileDiff, line: str, policy: CapabilityPolicy, egress: frozenset[str]
) -> Iterator[CapabilityFinding]:
    approvers = policy.approvers
    for model in detect_models(line):
        if model not in policy.allowed_models:
            yield CapabilityFinding("model", model, file.path, approvers["model"])
    for host in detect_hosts(line):
        if host in policy.allowed_hosts:
            continue
        # Declaring a host in the spec registers it; it does not grant access, so Security still reviews.
        roles = approvers["host"] if host in egress else approvers["undeclared_host"]
        yield CapabilityFinding("host", host, file.path, roles)
    for region in detect_regions(line):
        if region not in policy.allowed_regions:
            yield CapabilityFinding("region", region, file.path, approvers["region"])
    for store in detect_data_stores(line):
        if store not in policy.allowed_data_stores:
            yield CapabilityFinding("data_store", store, file.path, approvers["data_store"])
    for protocol in detect_protocols(line):
        yield CapabilityFinding("tool_protocol", protocol, file.path, approvers["tool_protocol"])
    for tool in detect_new_tool_functions(file.path, line):
        yield CapabilityFinding("tool_protocol", f"tool {tool}", file.path, approvers["tool_protocol"])


def find_new_capabilities(
    diff: str, policy: CapabilityPolicy, egress_hosts: Sequence[str] = ()
) -> list[CapabilityFinding]:
    """Return deduplicated findings for capabilities added by `diff`; an empty diff has none."""
    if not diff:
        return []
    egress = frozenset(h.lower() for h in egress_hosts)
    seen: dict[tuple[str, str, str], CapabilityFinding] = {}
    for file in parse_diff(diff):
        if policy.ignores(file.path):
            continue
        found: list[CapabilityFinding] = []
        for line in file.added:
            if line.strip() and not _COMMENT.match(line):
                found.extend(_scan_line(file, line, policy, egress))
        found.extend(
            CapabilityFinding("dependency", dep, file.path, policy.approvers["dependency"])
            for dep in detect_new_dependencies(file)
            if dep not in policy.allowed_dependencies
        )
        for finding in found:
            seen.setdefault((finding.kind, finding.detail, finding.path), finding)
    return list(seen.values())


def approvers_from(findings: Iterable[CapabilityFinding]) -> list[str]:
    out: list[str] = []
    for finding in findings:
        for role in finding.approvers:
            if role not in out:
                out.append(role)
    return out


def summarise(findings: Sequence[CapabilityFinding], limit: int = 5) -> str:
    shown = "; ".join(str(f) for f in findings[:limit])
    return shown + (f"; +{len(findings) - limit} more" if len(findings) > limit else "")
