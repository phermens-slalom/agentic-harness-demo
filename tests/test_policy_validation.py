import shutil
import tempfile
import unittest
from pathlib import Path

from harness.policy_validation import RiskTiers, load_policy_file, validate_policy_directory

ROOT = Path(__file__).resolve().parents[1]


class PolicyValidationTests(unittest.TestCase):
    def test_repository_policies_and_cross_references_are_valid(self):
        validate_policy_directory()

    def test_strict_schema_rejects_bad_fixture(self):
        path = ROOT / "tests" / "fixtures" / "policy_bad" / "risk_tiers.yaml"
        with self.assertRaisesRegex(ValueError, "teir"):
            load_policy_file(path, RiskTiers)

    def test_cross_file_role_reference_must_exist(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / "policy", root / "policy")
            shutil.copytree(ROOT / "agent-template", root / "agent-template")
            risk = root / "policy" / "risk_tiers.yaml"
            risk.write_text(
                risk.read_text().replace(
                    "base_approvers: [app_team, ai_governance]", "base_approvers: [unknown_role]"
                )
            )
            with self.assertRaisesRegex(ValueError, "unknown RACI role"):
                validate_policy_directory(root / "policy")

    def test_required_check_must_exist_as_a_template_job(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / "policy", root / "policy")
            shutil.copytree(ROOT / "agent-template", root / "agent-template")
            risk = root / "policy" / "risk_tiers.yaml"
            risk.write_text(risk.read_text().replace("secret_scan]", "not_a_job]"))
            with self.assertRaisesRegex(ValueError, "required checks missing"):
                validate_policy_directory(root / "policy")

    def test_capability_approver_must_be_a_raci_role(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / "policy", root / "policy")
            shutil.copytree(ROOT / "agent-template", root / "agent-template")
            caps = root / "policy" / "capabilities.yaml"
            caps.write_text(caps.read_text().replace("  model: [security]", "  model: [nobody]"))
            with self.assertRaisesRegex(ValueError, "unknown RACI role"):
                validate_policy_directory(root / "policy")

    def test_capability_regions_must_be_allowed_by_residency(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / "policy", root / "policy")
            shutil.copytree(ROOT / "agent-template", root / "agent-template")
            caps = root / "policy" / "capabilities.yaml"
            caps.write_text(caps.read_text().replace("allowed_regions: [", "allowed_regions: [us-central1, "))
            with self.assertRaisesRegex(ValueError, "not in residency"):
                validate_policy_directory(root / "policy")

    def test_capability_schema_rejects_unknown_keys_and_stores(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / "policy", root / "policy")
            shutil.copytree(ROOT / "agent-template", root / "agent-template")
            caps = root / "policy" / "capabilities.yaml"
            original = caps.read_text()
            caps.write_text(original + "allowed_hots: []\n")
            with self.assertRaisesRegex(ValueError, "allowed_hots"):
                validate_policy_directory(root / "policy")
            caps.write_text(original.replace("allowed_data_stores: []", "allowed_data_stores: [redis]"))
            with self.assertRaisesRegex(ValueError, "allowed_data_stores"):
                validate_policy_directory(root / "policy")

    def test_routed_skills_must_be_pinned_in_the_lock(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / "policy", root / "policy")
            shutil.copytree(ROOT / "agent-template", root / "agent-template")
            routing = root / "policy" / "routing.yaml"
            routing.write_text(routing.read_text().replace("  planner: []", "  planner: [style]"))
            with self.assertRaisesRegex(ValueError, "not pinned in skills.lock.yaml"):
                validate_policy_directory(root / "policy")

    def test_a_pinned_skill_needs_a_full_commit_revision_and_real_digest(self):
        pinned = (
            "source: https://example.com/hub\nrevision: {rev}\nskills:\n  style:\n"
            "    sha256: {sha}\n    capabilities: [instructions]\n    owner: ai_governance\n"
        )
        cases = (
            ("latest", "a" * 64, "40-character"),
            ("a" * 40, "xyz", "64 hex"),
        )
        for rev, sha, message in cases:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                shutil.copytree(ROOT / "policy", root / "policy")
                shutil.copytree(ROOT / "agent-template", root / "agent-template")
                (root / "policy" / "skills.lock.yaml").write_text(pinned.format(rev=rev, sha=sha))
                with self.assertRaisesRegex(ValueError, message):
                    validate_policy_directory(root / "policy")

    def test_repo_context_limits_are_required_and_strict(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / "policy", root / "policy")
            shutil.copytree(ROOT / "agent-template", root / "agent-template")
            routing = root / "policy" / "routing.yaml"
            routing.write_text(routing.read_text().replace("max_files: 5", "max_files: 5\n  max_filez: 9"))
            with self.assertRaisesRegex(ValueError, "max_filez"):
                validate_policy_directory(root / "policy")

    def test_every_surface_the_workflow_scans_must_be_in_the_guard_policy(self):
        for surface in ("review_feedback", "pr_comment", "repo_context", "issue", "build_feedback"):
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                shutil.copytree(ROOT / "policy", root / "policy")
                shutil.copytree(ROOT / "agent-template", root / "agent-template")
                guard = root / "policy" / "input_guard.yaml"
                kept = [ln for ln in guard.read_text().splitlines() if not ln.startswith(f"  {surface}:")]
                guard.write_text("\n".join(kept) + "\n")
                with self.assertRaisesRegex(ValueError, f"would not be scanned.*{surface}"):
                    validate_policy_directory(root / "policy")

    def test_the_model_armor_policy_is_required_and_strict(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / "policy", root / "policy")
            shutil.copytree(ROOT / "agent-template", root / "agent-template")
            guard = root / "policy" / "input_guard.yaml"
            original = guard.read_text()
            guard.write_text(
                original.replace("require_outside_local: true", "require_outside_local: yes-please")
            )
            with self.assertRaisesRegex(ValueError, "require_outside_local"):
                validate_policy_directory(root / "policy")
            guard.write_text(original.replace("model_armor:\n  require_outside_local: true\n", ""))
            with self.assertRaisesRegex(ValueError, "model_armor"):
                validate_policy_directory(root / "policy")

    def test_route_target_must_be_a_known_workflow(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(ROOT / "policy", root / "policy")
            shutil.copytree(ROOT / "agent-template", root / "agent-template")
            routing = root / "policy" / "routing.yaml"
            routing.write_text(routing.read_text().replace("issue_to_merge", "unknown_flow"))
            with self.assertRaisesRegex(ValueError, "unknown workflow"):
                validate_policy_directory(root / "policy")


if __name__ == "__main__":
    unittest.main()
