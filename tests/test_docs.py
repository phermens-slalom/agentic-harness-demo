"""Guards for the docs: every relative link and heading anchor in the Markdown files must resolve.

Moving or renaming a document, or editing a heading, can silently break links elsewhere. This runs in CI
with the rest of the tests, so a broken link fails the pull request.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\]\(([^)#\s]*)(#[^)\s]*)?\)")
SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:")
FENCE = re.compile(r"^\s*(```|~~~)")


def _markdown_files() -> list[Path]:
    return sorted([*ROOT.joinpath("docs").rglob("*.md"), ROOT / "README.md", ROOT / "AGENTS.md"])


def _slug(heading: str) -> str:
    """GitHub's heading anchor: lowercase, punctuation dropped, spaces become hyphens."""
    text = re.sub(r"[^\w\s-]", "", heading.strip().lower())
    return re.sub(r"\s+", "-", text)


def _anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and line.startswith("#"):
            anchors.add(_slug(line.lstrip("#")))
    return anchors


def _links(path: Path) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence:
            found.extend((m.group(1), m.group(2) or "") for m in LINK.finditer(line))
    return found


class DocLinkTests(unittest.TestCase):
    def test_there_are_docs_to_check(self) -> None:
        names = {p.name for p in _markdown_files()}
        self.assertTrue({"README.md", "AGENTS.md", "ROADMAP.md", "INPUT_GUARD.md"} <= names)

    def test_relative_links_and_anchors_resolve(self) -> None:
        problems: list[str] = []
        for doc in _markdown_files():
            for target, anchor in _links(doc):
                if SCHEME.match(target) or (not target and not anchor):
                    continue
                path = (doc.parent / target).resolve() if target else doc
                where = f"{doc.relative_to(ROOT)} -> {target}{anchor}"
                if not path.exists():
                    problems.append(f"{where}: file not found")
                elif anchor and path.suffix == ".md" and anchor[1:] not in _anchors(path):
                    problems.append(f"{where}: no such heading")
        self.assertEqual(problems, [], "\n".join(problems))

    def test_slug_matches_github_for_common_headings(self) -> None:
        self.assertEqual(_slug(" Unconfirmed items in these docs"), "unconfirmed-items-in-these-docs")
        self.assertEqual(_slug(" TODOs in the code and policy"), "todos-in-the-code-and-policy")
        self.assertEqual(_slug(" Run it (fast)"), "run-it-fast")


if __name__ == "__main__":
    unittest.main()
