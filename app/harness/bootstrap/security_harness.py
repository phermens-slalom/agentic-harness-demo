"""Harness-specific policy checks for generated agent repositories.

Secret detection is handled by Gitleaks in CI; this check validates framework,
residency, and required-file policy and never replaces human approval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}
FOREIGN_FRAMEWORKS = re.compile(
    r"^\s*(?:from|import)\s+(langchain\w*|langgraph|crewai|autogen\w*|openai)\b", re.MULTILINE
)
GLOBAL_LOCATION = re.compile(r"""(?i)\blocation\s*[:=]\s*['"]?global\b""")
REQUIRED_FILES = ["AGENTS.md", ".github/CODEOWNERS"]


@dataclass
class Finding:
    check: str
    path: str
    detail: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.findings

    def to_markdown(self) -> str:
        if self.ok:
            return "Harness policy checks: no findings.\n"
        rows = "\n".join(f"| {f.check} | `{f.path}` | {f.detail} |" for f in self.findings)
        return f"| Check | File | Detail |\n|---|---|---|\n{rows}\n"


def scan(repo: Path) -> Report:
    report = Report()
    for rel in REQUIRED_FILES:
        if not (repo / rel).exists():
            report.findings.append(Finding("required file", rel, "missing"))
    for p in sorted(repo.rglob("*")):
        if not p.is_file() or SKIP_DIRS & set(p.relative_to(repo).parts):
            continue
        try:
            text = p.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        rel = p.relative_to(repo).as_posix()
        if p.suffix == ".py":
            for m in FOREIGN_FRAMEWORKS.finditer(text):
                report.findings.append(Finding("framework", rel, f"{m.group(1)}: ADK is the only framework"))
        if GLOBAL_LOCATION.search(text):
            report.findings.append(
                Finding("residency", rel, "global location; use an allowed Australian region")
            )
    return report
