"""Deterministic checks for PR diffs that weaken the harness's own evidence."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

_SKIP = re.compile(r"\b(?:skip|skipif|xfail)\b|pytest\.mark\.skip|unittest\.skip|@Disabled|t\.Skip\s*\(")
_ASSERT = re.compile(r"^\s*assert\b")
_TEST_DEF = re.compile(r"^\s*(?:async\s+)?def\s+test_[A-Za-z0-9_]*\s*\(")
_NUMBER = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?")
_PYTEST_CONFIG = re.compile(r"^\s*\[(?:tool\.pytest(?:\.ini_options)?|tool:pytest)\]\s*$")


def _file_path(header: str) -> str | None:
    if not header.startswith(("+++ ", "--- ")):
        return None
    raw = header[4:].split("\t", 1)[0]
    if raw == "/dev/null":
        return None
    return raw[2:] if len(raw) > 2 and raw[1] == "/" else raw


def _is_test_file(path: str) -> bool:
    name = PurePosixPath(path).name.lower()
    return "/tests/" in f"/{path.lower()}/" or name.startswith("test_") or name.endswith("_test.py")


def _diff_files(diff: str) -> set[str]:
    files: set[str] = set()
    for line in diff.splitlines():
        if line.startswith(("+++ ", "--- ")):
            path = _file_path(line)
            if path:
                files.add(path.replace("\\", "/"))
        elif line.startswith("diff --git "):
            parts = line.split()
            if len(parts) == 4:
                for raw in parts[2:]:
                    if raw.startswith(("a/", "b/")):
                        files.add(raw[2:].replace("\\", "/"))
    return files


def _check_deleted_tests(diff: str, findings: list[str]) -> None:
    current: str | None = None
    deleted_files: set[str] = set()
    removed_defs: list[str] = []
    for line in diff.splitlines():
        if line.startswith("--- "):
            current = _file_path(line)
        elif line.startswith("+++ "):
            if _file_path(line) is None and current and _is_test_file(current):
                deleted_files.add(current)
            current = _file_path(line)
        elif current and line.startswith("-") and not line.startswith("--- ") and _TEST_DEF.match(line[1:]):
            removed_defs.append(line[1:].strip())
    if deleted_files:
        findings.append("deleted test file(s): " + ", ".join(sorted(deleted_files)))
    if removed_defs:
        findings.append("deleted test function(s): " + ", ".join(removed_defs))


def _check_added_skips(diff: str, findings: list[str]) -> None:
    skips = [
        line[1:].strip()
        for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++") and _SKIP.search(line[1:])
    ]
    if skips:
        findings.append("added test skip/xfail marker(s): " + "; ".join(skips))


def _check_removed_asserts(diff: str, findings: list[str]) -> None:
    current: str | None = None
    removed = added = 0
    for line in diff.splitlines():
        if line.startswith(("+++ ", "--- ")):
            current = _file_path(line)
        elif current and _is_test_file(current):
            if line.startswith("-") and not line.startswith("--- ") and _ASSERT.match(line[1:]):
                removed += 1
            elif line.startswith("+") and not line.startswith("+++ ") and _ASSERT.match(line[1:]):
                added += 1
    if removed > added:
        findings.append(f"net removal of {removed - added} assert line(s) from test files")


def _check_control_files(diff: str, findings: list[str]) -> None:
    files = _diff_files(diff)
    baselines = sorted(p for p in files if p.startswith("evals/baseline/"))
    if baselines:
        findings.append("edited eval baseline file(s): " + ", ".join(baselines))
    changed_lines = [line[1:] for line in diff.splitlines() if line.startswith(("+", "-"))]
    has_pytest_section = any(
        _PYTEST_CONFIG.match(line[1:] if line.startswith(("+", "-", " ")) else line)
        for line in diff.splitlines()
    )
    for path in sorted(files):
        lowered = path.lower()
        if lowered.endswith(("conftest.py", "pytest.ini")):
            findings.append(f"edited test configuration: {path}")
        elif lowered.endswith(("pyproject.toml", "setup.cfg")) and (
            any("pytest" in line.lower() for line in changed_lines) or has_pytest_section
        ):
            findings.append(f"edited pytest configuration: {path}")


def _check_lowered_thresholds(diff: str, findings: list[str]) -> None:
    current: str | None = None
    removed: list[str] = []
    added: list[str] = []
    threshold_paths: set[str] = set()

    def compare() -> None:
        if not current or not current.startswith("evals/thresholds"):
            return
        for old, new in zip(removed, added):
            old_numbers = _NUMBER.findall(old)
            new_numbers = _NUMBER.findall(new)
            for before, after in zip(old_numbers, new_numbers):
                if float(after) < float(before):
                    threshold_paths.add(current)
                    break

    for line in diff.splitlines():
        if line.startswith(("--- ", "+++ ")):
            compare()
            current = _file_path(line)
            removed, added = [], []
        elif line.startswith("-") and not line.startswith("--- "):
            removed.append(line[1:])
        elif line.startswith("+") and not line.startswith("+++ "):
            added.append(line[1:])
    compare()
    if threshold_paths:
        findings.append("lowered numeric eval threshold(s): " + ", ".join(sorted(threshold_paths)))


def find_tampering(diff: str) -> list[str]:
    """Return deterministic findings; an empty diff has no findings."""
    if not diff:
        return []
    findings: list[str] = []
    _check_deleted_tests(diff, findings)
    _check_added_skips(diff, findings)
    _check_removed_asserts(diff, findings)
    _check_control_files(diff, findings)
    _check_lowered_thresholds(diff, findings)
    return findings
