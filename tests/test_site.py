"""Guards for the static project site in site/ (see docs/tech/SITE.md).

The site makes claims about the repo, so these tests keep it honest: every local link and
anchor resolves, every link into the repo points at a file that exists, and nothing is loaded
from a third-party host (no tracking, no CDN scripts).
"""

from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
REPO_LINK = re.compile(r"^https://github\.com/[^/]+/[^/]+/(?:blob|tree)/main/(.+)$")


class _Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.hrefs: list[str] = []
        self.srcs: list[str] = []
        self.use_refs: list[str] = []
        self.imgs_without_alt: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: v or "" for k, v in attrs}
        if "id" in a:
            self.ids.add(a["id"])
        if tag in ("a", "link") and "href" in a:
            self.hrefs.append(a["href"])
        if tag in ("img", "script") and "src" in a:
            self.srcs.append(a["src"])
        if tag == "use" and "href" in a:
            self.use_refs.append(a["href"])
        if tag == "img" and "alt" not in a:
            self.imgs_without_alt.append(a.get("src", "?"))


def _parse() -> _Collector:
    c = _Collector()
    c.feed((SITE / "index.html").read_text(encoding="utf-8"))
    return c


class SiteTests(unittest.TestCase):
    def test_local_assets_exist(self) -> None:
        c = _parse()
        for ref in [*c.srcs, *[h for h in c.hrefs if not h.startswith(("#", "http"))]]:
            if ref.startswith(("http", "#")):
                continue
            self.assertTrue((SITE / ref).is_file(), f"missing local asset: {ref}")

    def test_css_references_exist(self) -> None:
        css = (SITE / "assets/css/styles.css").read_text(encoding="utf-8")
        for ref in re.findall(r'url\("([^"]+)"\)', css):
            self.assertTrue((SITE / "assets/css" / ref).resolve().is_file(), f"missing CSS asset: {ref}")

    def test_in_page_anchors_resolve(self) -> None:
        c = _parse()
        for h in c.hrefs + c.use_refs:
            if h.startswith("#") and len(h) > 1:
                self.assertIn(h[1:], c.ids, f"anchor {h} has no matching id")

    def test_links_into_repo_point_at_real_paths(self) -> None:
        for h in _parse().hrefs:
            m = REPO_LINK.match(h)
            if m:
                self.assertTrue(
                    (ROOT / m.group(1)).exists(), f"site links to a path that does not exist: {m.group(1)}"
                )

    def test_no_third_party_loads(self) -> None:
        c = _parse()
        for s in c.srcs:
            self.assertFalse(s.startswith(("http://", "https://", "//")), f"external load: {s}")
        for h in c.hrefs:
            if h.endswith((".css", ".js")):
                self.assertFalse(h.startswith(("http", "//")), f"external stylesheet or script: {h}")
        css = (SITE / "assets/css/styles.css").read_text(encoding="utf-8")
        self.assertNotIn("@import", css)

    def test_images_have_alt_text(self) -> None:
        self.assertEqual(_parse().imgs_without_alt, [])

    def test_pages_workflow_is_pinned_and_least_privilege(self) -> None:
        wf = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
        for line in wf.splitlines():
            if "uses:" in line:
                self.assertRegex(line, r"@[0-9a-f]{40}\b", f"action not pinned to a full SHA: {line.strip()}")
        self.assertIn("permissions: {}", wf)


if __name__ == "__main__":
    unittest.main()
