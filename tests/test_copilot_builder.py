import asyncio
import unittest

from harness.adapters.copilot_builder import CopilotBuilder
from harness.adapters.fakes import FakeGitHub
from harness.models import Issue, Plan, PRSnapshot

ISSUE = Issue(repo="example-org/a", number=1, title="t", body="b", labels=["agent:bugfix"])
PLAN = Plan(steps=["fix"], acceptance_criteria=["tests pass"])


def snap(ok):
    return PRSnapshot(
        pr_number=5, changed_files=["a.py"], lines_changed=5, checks={"tests": ok, "lint": True}
    )


class CopilotBuilderTests(unittest.TestCase):
    def test_assign_then_feedback_comment(self):
        gh = FakeGitHub([snap(False), snap(True)])
        b = CopilotBuilder(gh)
        r1 = asyncio.run(b.build(ISSUE, PLAN, None))
        self.assertFalse(r1.passed)
        self.assertEqual(r1.failing_checks, ["tests"])
        r2 = asyncio.run(b.build(ISSUE, PLAN, "CI failed: tests"))
        self.assertTrue(r2.passed)
        self.assertEqual(len(gh.assigned), 1)
        self.assertEqual(gh.comments, ["@copilot CI failed: tests"])
        self.assertIn("AGENTS.md", gh.assigned[0])

    def test_assignment_passes_the_custom_agent(self):
        gh = FakeGitHub([snap(True)])
        asyncio.run(CopilotBuilder(gh).build(ISSUE, PLAN, None))
        self.assertEqual(gh.custom_agents, ["agent-builder"])
        gh = FakeGitHub([snap(True)])
        asyncio.run(CopilotBuilder(gh, custom_agent=None).build(ISSUE, PLAN, None))
        self.assertEqual(gh.custom_agents, [None])

    def test_empty_check_snapshot_is_not_ci_green(self):
        unknown = PRSnapshot(pr_number=5, changed_files=["a.py"], lines_changed=5, checks={})
        result = asyncio.run(CopilotBuilder(FakeGitHub([unknown])).build(ISSUE, PLAN, None))
        self.assertFalse(result.ci_green)
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
