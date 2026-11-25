"""Hunk-aware unified-diff parsing, standard library only.

Hunk line counts decide where a hunk ends, so an added line that merely looks like a file header
(for example `+++ b/x`, written as `++++ b/x`) cannot change which file later lines belong to.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_HUNK = re.compile(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@")


@dataclass
class FileDiff:
    path: str
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


def _path(header: str) -> str | None:
    raw = header[4:].split("\t", 1)[0].strip()
    if raw == "/dev/null":
        return None
    if len(raw) > 2 and raw[:2] in ("a/", "b/"):
        raw = raw[2:]
    return raw.replace("\\", "/")


def parse_diff(diff: str) -> list[FileDiff]:
    """Return one entry per file that still exists after the change, with its added/removed lines."""
    files: list[FileDiff] = []
    current: FileDiff | None = None
    old_left = new_left = 0
    for line in diff.splitlines():
        if old_left > 0 or new_left > 0:
            tag = line[:1]
            if tag == "\\":  # "\ No newline at end of file"
                continue
            if tag == "+":
                new_left -= 1
                if current:
                    current.added.append(line[1:])
            elif tag == "-":
                old_left -= 1
                if current:
                    current.removed.append(line[1:])
            else:
                old_left -= 1
                new_left -= 1
            continue
        hunk = _HUNK.match(line)
        if hunk:
            old_left = int(hunk[1]) if hunk[1] is not None else 1
            new_left = int(hunk[2]) if hunk[2] is not None else 1
        elif line.startswith("+++ "):
            path = _path(line)
            current = FileDiff(path) if path else None
            if current:
                files.append(current)
        elif line.startswith("--- "):
            current = None
        elif current and line.startswith("+"):  # tolerate hand-written hunks with short counts
            current.added.append(line[1:])
        elif current and line.startswith("-"):
            current.removed.append(line[1:])
    return files
