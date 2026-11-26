"""Guards for the static project site in site/ (see docs/tech/SITE.md).

The site makes claims about the repo, so these tests keep it honest: every local link and
anchor resolves, every link into the repo points at a file that exists, and nothing is loaded
from a third-party host (no tracking, no CDN scripts).
"""

from __future__ import annotations

import html
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

import yaml

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


PAGES = sorted(SITE.glob("*.html"))


def _parse(page: Path | None = None) -> _Collector:
    c = _Collector()
    c.feed((page or SITE / "index.html").read_text(encoding="utf-8"))
    return c


def _all() -> dict[Path, _Collector]:
    return {p: _parse(p) for p in PAGES}


class SiteTests(unittest.TestCase):
    def test_site_has_the_expected_pages(self) -> None:
        self.assertEqual([p.name for p in PAGES], ["glossary.html", "index.html", "roadmap.html"])

    def test_local_assets_exist(self) -> None:
        for page, c in _all().items():
            for ref in [*c.srcs, *[h for h in c.hrefs if not h.startswith(("#", "http"))]]:
                if ref.startswith(("http", "#")):
                    continue
                target = ref.split("#", 1)[0]
                self.assertTrue((SITE / target).is_file(), f"{page.name}: missing local asset: {ref}")

    def test_cross_page_anchors_resolve(self) -> None:
        pages = _all()
        for page, c in pages.items():
            for h in c.hrefs:
                if h.startswith(("http", "#")) or "#" not in h:
                    continue
                name, anchor = h.split("#", 1)
                if anchor:
                    self.assertIn(anchor, pages[SITE / name].ids, f"{page.name}: {h} has no matching id")

    def test_css_references_exist(self) -> None:
        css = (SITE / "assets/css/styles.css").read_text(encoding="utf-8")
        for ref in re.findall(r'url\("([^"]+)"\)', css):
            self.assertTrue((SITE / "assets/css" / ref).resolve().is_file(), f"missing CSS asset: {ref}")

    def test_in_page_anchors_resolve(self) -> None:
        for page, c in _all().items():
            for h in c.hrefs + c.use_refs:
                if h.startswith("#") and len(h) > 1:
                    self.assertIn(h[1:], c.ids, f"{page.name}: anchor {h} has no matching id")

    def test_links_into_repo_point_at_real_paths(self) -> None:
        for page, c in _all().items():
            for h in c.hrefs:
                m = REPO_LINK.match(h)
                if m:
                    self.assertTrue(
                        (ROOT / m.group(1)).exists(),
                        f"{page.name} links to a path that does not exist: {m.group(1)}",
                    )

    def test_no_third_party_loads(self) -> None:
        for page, c in _all().items():
            for s in c.srcs:
                self.assertFalse(
                    s.startswith(("http://", "https://", "//")), f"{page.name}: external load: {s}"
                )
            for h in c.hrefs:
                if h.endswith((".css", ".js")):
                    self.assertFalse(h.startswith(("http", "//")), f"{page.name}: external script: {h}")
        css = (SITE / "assets/css/styles.css").read_text(encoding="utf-8")
        self.assertNotIn("@import", css)

    def test_images_have_alt_text(self) -> None:
        for page, c in _all().items():
            self.assertEqual(c.imgs_without_alt, [], page.name)

    def test_every_page_has_the_same_primary_nav(self) -> None:
        navs = []
        for page in PAGES:
            m = re.search(r'<nav class="nav-links".*?</nav>', page.read_text(encoding="utf-8"), re.DOTALL)
            self.assertTrue(m, page.name)
            labels = re.findall(r">([^<]+)</a>", m.group(0)) if m else []
            navs.append(labels)
        self.assertTrue(all(n == navs[0] for n in navs), navs)
        for label in ("Roadmap", "Glossary"):
            self.assertIn(label, navs[0])

    def test_no_unconfirmed_markers_on_the_site(self) -> None:
        for page in PAGES:
            self.assertNotIn("unconfirmed", page.read_text(encoding="utf-8").lower(), page.name)
        self.assertNotIn("unconfirmed", (SITE / "assets/js/main.js").read_text(encoding="utf-8").lower())

    def test_glossary_page_covers_every_docs_term(self) -> None:
        """site/glossary.html mirrors docs/GLOSSARY.md. A term added to the docs must reach the site."""
        text = html.unescape(re.sub(r"<[^>]+>", "", (SITE / "glossary.html").read_text(encoding="utf-8")))
        terms = []
        for line in (ROOT / "docs/GLOSSARY.md").read_text(encoding="utf-8").splitlines():
            if line.startswith("| ") and not line.startswith(("| ---", "| |", "|---")):
                first = line.split("|")[1].strip().replace("**", "").replace("`", "")
                if first and first not in {"Term", "Role ID", "Outcome", "Code", "TODO: UNCONFIRMED"}:
                    terms.append(first)
        self.assertGreater(len(terms), 100)
        missing = [t for t in terms if t not in text]
        self.assertEqual(missing, [], "terms in docs/GLOSSARY.md missing from site/glossary.html")

    def test_roadmap_page_lists_every_milestone(self) -> None:
        page = (SITE / "roadmap.html").read_text(encoding="utf-8")
        roadmap = (ROOT / "docs/ROADMAP.md").read_text(encoding="utf-8")
        codes = re.findall(r"^\| \*\*(M\d+)\*\* \|", roadmap, re.MULTILINE)
        self.assertEqual(len(codes), 10)
        for code in codes:
            self.assertIn(f'id="{code.lower()}"', page, f"roadmap page has no card for {code}")

    def test_headline_figures_match_the_repo(self) -> None:
        index = (SITE / "index.html").read_text(encoding="utf-8")
        tasks = 0
        gaps = 0
        for f in (ROOT / "evals/golden_tasks").glob("*.yaml"):
            for t in yaml.safe_load(f.read_text(encoding="utf-8")):
                if t.get("known_gap"):
                    gaps += 1
                else:
                    tasks += 1
        self.assertIn(f"{tasks} scored golden tasks", index)
        self.assertIn(f"{gaps} known gaps open", index)
        checks = yaml.safe_load((ROOT / "policy/risk_tiers.yaml").read_text(encoding="utf-8"))[
            "required_checks"
        ]
        self.assertIn(f"<b>{len(checks)}</b><span>required checks", index)
        self.assertIn("Run the six checks", index)  # AGENTS.md lists six commands

    def test_pages_workflow_is_pinned_and_least_privilege(self) -> None:
        wf = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
        for line in wf.splitlines():
            if "uses:" in line:
                self.assertRegex(line, r"@[0-9a-f]{40}\b", f"action not pinned to a full SHA: {line.strip()}")
        self.assertIn("permissions: {}", wf)


if __name__ == "__main__":
    unittest.main()
