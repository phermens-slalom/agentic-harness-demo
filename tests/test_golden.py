import unittest

from harness.golden import GoldenWorkflow
from harness.policy import RiskPolicy, load_review_checklist


class GoldenTests(unittest.TestCase):
    def setUp(self):
        self.g = GoldenWorkflow.load()

    def test_workflow_and_raci_consistent(self):
        self.assertEqual(self.g.validate(), [])

    def test_policy_approvers_are_raci_roles(self):
        p = RiskPolicy.load()
        used = set(p.base_approvers) | {a for r in p.rules for a in r.get("approvers", [])}
        self.assertLessEqual(used, set(self.g.roles))

    def test_validate_catches_missing_step(self):
        self.g.stages = [s for s in self.g.stages if 13 not in s.steps]
        self.assertTrue(any("13" in x for x in self.g.validate()))

    def test_review_checklist_loads(self):
        self.assertTrue(load_review_checklist())


if __name__ == "__main__":
    unittest.main()
