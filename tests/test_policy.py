import unittest

from harness.policy import RiskPolicy, Routing


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.p = RiskPolicy.load()

    def test_sensitive_paths_are_tier_3(self):
        self.assertEqual(self.p.tier_for_file("services/payments/refund.py"), 3)
        self.assertEqual(self.p.tier_for_file("auth/login.py"), 3)  # matches at repo root
        self.assertEqual(self.p.tier_for_file(r"Services\Payments\Refund.py"), 3)
        self.assertEqual(self.p.tier_for_file(".GITHUB/WORKFLOWS/CI.YML"), 3)

    def test_tests_are_tier_1(self):
        self.assertEqual(self.p.tier_for_file("tests/test_quote.py"), 1)

    def test_deps_and_test_config_code_are_not_auto_mergeable(self):
        self.assertEqual(self.p.tier_for_file("svc/requirements.txt"), 2)
        self.assertEqual(self.p.tier_for_file("tests/conftest.py"), 2)  # must beat tests/**

    def test_agent_instruction_files_need_security(self):
        for f in ["AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md", "svc/AGENTS.md"]:
            self.assertEqual(self.p.tier_for_file(f), 3, f)
            self.assertIn("security", self.p.approvers_for_change([f]), f)
        self.assertEqual(self.p.tier_for_file("docs/readme.md"), 1)  # ordinary docs unchanged

    def test_harness_controls_are_tier_3_but_regular_tests_remain_tier_1(self):
        for path in [
            "policy/risk_tiers.yaml",
            "evals/thresholds.yaml",
            "evals/baseline/results.json",
            "skills/planner/SKILL.md",
            "agent/prompts.py",
            "agent/prompts/mission.md",
        ]:
            self.assertEqual(self.p.tier_for_file(path), 3, path)
            self.assertIn("security", self.p.approvers_for_change([path]), path)
        self.assertEqual(self.p.tier_for_file("tests/test_policy.py"), 1)
        self.assertEqual(self.p.tier_for_file("docs/readme.md"), 1)
        self.assertEqual(self.p.tier_for_file("docs/mission.md"), 1)

    def test_highest_tier_wins(self):
        self.assertEqual(self.p.tier_for_change(["tests/a.py", "svc/claims/x.py"], 20), 3)

    def test_renamed_paths_keep_old_path_tier_and_approver(self):
        self.assertEqual(
            self.p.tier_for_change(["src/refund.py"], 20, previous_paths=["payments/refund.py"]), 3
        )
        self.assertIn(
            "security",
            self.p.approvers_for_change(["src/refund.py"], previous_paths=["payments/refund.py"]),
        )

    def test_large_tier_1_bumped(self):
        self.assertEqual(self.p.tier_for_change(["docs/readme.md"], 500), 2)

    def test_approvers_derived_from_paths(self):
        self.assertEqual(self.p.approvers_for_change(["svc/a.py"]), ["app_team", "ai_governance"])
        got = self.p.approvers_for_change(["x/platform.tf", "svc/prod/c.py", "iam/b.yaml"])
        self.assertEqual(
            got, ["app_team", "ai_governance", "platform_team", "product_owner", "architecture", "security"]
        )

    def test_phase_controls_auto_merge(self):
        self.assertEqual(RiskPolicy.load().auto_merge_tiers, set())
        self.assertEqual(RiskPolicy.load(phase=3).auto_merge_tiers, {1})
        self.assertEqual(RiskPolicy.load(phase=1).plan_approval, "always")
        self.assertEqual(RiskPolicy.load(phase=3).plan_approval, "tier_at_least_2")
        with self.assertRaises(ValueError):
            RiskPolicy.load(phase=9)

    def test_missing_checks_includes_empty_report_and_non_green_values(self):
        required = self.p.required_checks
        self.assertEqual(self.p.missing_checks({}), required)
        self.assertEqual(self.p.missing_checks({required[0]: True}), required[1:])
        self.assertNotIn(required[0], self.p.missing_checks({required[0]: False}))

    def test_routing(self):
        r = Routing.load()
        self.assertEqual(r.workflow_for(["bug", "agent:bugfix"]), "issue_to_merge")
        self.assertIsNone(r.workflow_for(["bug"]))


if __name__ == "__main__":
    unittest.main()
