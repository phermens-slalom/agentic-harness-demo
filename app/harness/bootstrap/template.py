"""Stage 1: render a new agent repo from agent-template/ (the single source of the template)."""

from __future__ import annotations

from pathlib import Path

from . import security_harness
from .spec import AgentSpec

TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "agent-template"
# Python package hosts. GitHub's recommended firewall allowlist already includes them; they only
# matter if that allowlist is disabled. TODO(Security): replace with the internal package mirror.
PACKAGE_HOSTS = ("pypi.org", "files.pythonhosted.org")


def _bullets(hosts: list[str], none: str) -> str:
    # GitHub allows a bare domain *and all its subdomains*, but a URL only that scheme and host
    # (and path). Exact hosts are the policy, so render URLs, never bare domains.
    return "\n".join(f"- `https://{h}/`" for h in sorted(set(hosts))) or none


def render(spec: AgentSpec, dest: Path, template_dir: Path | None = None) -> list[Path]:
    problems = spec.validate()
    if problems:
        raise ValueError("invalid spec: " + "; ".join(problems))
    subs = {
        "__AGENT_NAME__": spec.name,
        "__DIVISION__": spec.division,
        "__OWNER__": spec.owner,
        "__DESCRIPTION__": spec.description,
        "__AGENT_ID__": spec.name.replace("-", "_"),
        "__EGRESS_ALLOWLIST__": _bullets(spec.egress_hosts, "- None: the spec declares no egress hosts."),
        "__PACKAGE_ALLOWLIST__": _bullets(list(PACKAGE_HOSTS), "- None."),
    }
    src_root = template_dir or TEMPLATE_DIR
    written = []
    for src in sorted(p for p in src_root.rglob("*") if p.is_file()):
        out = dest / src.relative_to(src_root)
        if out.exists():
            raise FileExistsError(f"refusing to overwrite {out}")
        text = src.read_text()
        for k, v in subs.items():
            text = text.replace(k, v)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
        written.append(out)
    scanner = dest / "agent" / "security_harness.py"
    if scanner.exists():
        raise FileExistsError(f"refusing to overwrite {scanner}")
    scanner.write_text(Path(security_harness.__file__).read_text())
    written.append(scanner)
    return written
