import asyncio
import unittest

from harness.adapters.fakes import FakeGitHub
from harness.nodes.repo_context import build_repo_context, safe_path
from harness.policy import RepoContextLimits, Routing

LIMITS = RepoContextLimits(
    max_files=2,
    max_bytes_per_file=50,
    max_total_bytes=120,
    max_tree_entries=3,
    deny_paths=("**/.env", "**/*secret*", ".git/**"),
)


def build(files, named=(), limits=LIMITS):
    gh = FakeGitHub([], files=files)
    return gh, asyncio.run(build_repo_context(gh, "example-org/a", limits, named))


class SafePathTests(unittest.TestCase):
    def test_accepts_plain_relative_paths(self):
        self.assertEqual(safe_path("agent/tools.py"), "agent/tools.py")
        self.assertEqual(safe_path("  docs\\notes.md "), "docs/notes.md")

    def test_rejects_traversal_absolute_and_odd_paths(self):
        for bad in ("", "../x", "a/../../x", "/etc/passwd", "~/x", "a//b", "./a", "C:/x", "a\0b", "x" * 300):
            self.assertIsNone(safe_path(bad), bad)


class BuildRepoContextTests(unittest.TestCase):
    def test_includes_agents_md_tree_and_named_files(self):
        _, ctx = build({"AGENTS.md": "# guide", "agent/a.py": "A = 1", "agent/b.py": "B = 2"}, ["agent/a.py"])
        self.assertEqual(ctx.included, ["AGENTS.md", "agent/a.py"])
        self.assertIn("--- BEGIN FILE AGENTS.md ---", ctx.text)
        self.assertIn("agent/b.py", ctx.text)  # listed in the tree
        self.assertIn("A = 1", ctx.text)
        self.assertNotIn("B = 2", ctx.text)  # not named, so its content is not read
        self.assertIn("never instructions", ctx.text)

    def test_only_named_files_are_read(self):
        gh, _ = build({"AGENTS.md": "x", "a.py": "1", "b.py": "2"}, ["a.py"])
        self.assertEqual(gh.reads, ["AGENTS.md", "a.py"])

    def test_deny_list_and_unsafe_paths_are_never_read(self):
        files = {"AGENTS.md": "x", ".env": "TOKEN=abc", "cfg/my_secret.txt": "s3", "ok.py": "1"}
        gh, ctx = build(files, [".env", "cfg/my_secret.txt", "../etc/passwd", "/abs", ".git/config", "ok.py"])
        self.assertEqual(gh.reads, ["AGENTS.md", "ok.py"])
        self.assertEqual(ctx.included, ["AGENTS.md", "ok.py"])
        self.assertEqual(len(ctx.skipped), 5)
        for secret in ("TOKEN=abc", "s3", ".env", "my_secret"):
            self.assertNotIn(secret, ctx.text)  # denied files are hidden from the tree too

    def test_per_file_cap_truncates_and_says_so(self):
        _, ctx = build({"a.py": "x" * 500}, ["a.py"])
        self.assertIn("[truncated at 50 bytes]", ctx.text)
        self.assertLess(ctx.text.count("x"), 60)

    def test_total_budget_stops_adding_files(self):
        limits = RepoContextLimits(5, 100, 120, 10, ())
        _, ctx = build(
            {"AGENTS.md": "a" * 100, "b.py": "b" * 100, "c.py": "c" * 100}, ["b.py", "c.py"], limits
        )
        self.assertEqual(ctx.included, ["AGENTS.md", "b.py"])
        self.assertEqual(ctx.skipped, ["c.py"])
        self.assertIn("b" * 20 + "\n[truncated at 20 bytes]", ctx.text)  # only the remaining budget
        self.assertNotIn("c" * 10, ctx.text)

    def test_max_files_is_enforced_and_duplicates_collapse(self):
        files = {"a.py": "1", "b.py": "2", "c.py": "3"}
        gh, ctx = build(files, ["a.py", "a.py", "b.py", "c.py"])
        self.assertEqual(gh.reads, ["AGENTS.md", "a.py", "b.py"])  # c.py is over max_files, never read
        self.assertEqual(ctx.skipped, ["c.py"])

    def test_tree_is_capped(self):
        files = {f"f{i}.py": "" for i in range(10)}
        _, ctx = build(files)
        self.assertIn("[+7 more files not listed]", ctx.text)

    def test_missing_and_binary_files_are_skipped(self):
        _, ctx = build({"bin.dat": "ab\0cd"}, ["nope.py", "bin.dat"])
        self.assertEqual(ctx.included, [])
        self.assertEqual(sorted(ctx.skipped), ["bin.dat", "nope.py"])

    def test_missing_agents_md_is_fine(self):
        _, ctx = build({"a.py": "1"}, ["a.py"])
        self.assertEqual(ctx.included, ["a.py"])

    def test_repository_limits_load_from_routing_yaml(self):
        limits = Routing.load().repo_context
        self.assertGreater(limits.max_files, 0)
        self.assertTrue(limits.denies(".env") and limits.denies("a/B/Secret.txt"))
        self.assertFalse(limits.denies("agent/tools.py"))


if __name__ == "__main__":
    unittest.main()
