import unittest

from harness.nodes.tamper_check import find_tampering


class TamperCheckTests(unittest.TestCase):
    def test_deleted_test_file_is_detected(self):
        diff = "--- a/tests/test_auth.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-def test_auth(): pass\n"
        self.assertTrue(any("deleted test file" in f for f in find_tampering(diff)))

    def test_deleted_test_function_is_detected_without_flagging_renames(self):
        diff = (
            "--- a/tests/test_auth.py\n+++ b/tests/test_auth.py\n"
            "@@ -1,2 +1 @@\n def helper(): pass\n-def test_auth(): assert True\n"
        )
        self.assertTrue(any("deleted test function" in f for f in find_tampering(diff)))
        benign = "--- a/tests/test_old.py\n+++ b/tests/test_new.py\n@@ -1 +1 @@\n-a = 1\n+b = 1\n"
        self.assertFalse(any("deleted test file" in f for f in find_tampering(benign)))

    def test_added_skip_marker_is_detected(self):
        diff = "--- a/tests/test_auth.py\n+++ b/tests/test_auth.py\n@@ -1 +1,2 @@\n def test_auth():\n+    pytest.skip('later')\n"
        self.assertTrue(any("skip/xfail" in f for f in find_tampering(diff)))

    def test_net_assert_removal_is_detected(self):
        diff = "--- a/tests/test_auth.py\n+++ b/tests/test_auth.py\n@@ -1,2 +1 @@\n-    assert user.is_valid\n     assert user.is_active\n"
        self.assertTrue(any("net removal" in f for f in find_tampering(diff)))

    def test_eval_baseline_edit_is_detected(self):
        diff = "--- a/evals/baseline/results.json\n+++ b/evals/baseline/results.json\n@@ -1 +1 @@\n-{}\n+{}\n"
        self.assertTrue(any("baseline" in f for f in find_tampering(diff)))

    def test_lowered_threshold_is_detected_but_raise_is_allowed(self):
        lower = (
            "--- a/evals/thresholds.yaml\n+++ b/evals/thresholds.yaml\n"
            "@@ -1 +1 @@\n-fail_under: 90\n+fail_under: 80\n"
        )
        higher = lower.replace("80", "95")
        self.assertTrue(any("lowered numeric" in f for f in find_tampering(lower)))
        self.assertFalse(any("lowered numeric" in f for f in find_tampering(higher)))

    def test_pytest_configuration_edit_is_detected(self):
        diff = "--- a/pyproject.toml\n+++ b/pyproject.toml\n@@ -1,2 +1,2 @@\n-[tool.pytest.ini_options]\n+[tool.pytest.ini_options]\n+addopts = '--disable-warnings'\n"
        self.assertTrue(any("pytest configuration" in f for f in find_tampering(diff)))

    def test_benign_test_edit_is_allowed(self):
        diff = (
            "--- a/tests/test_auth.py\n+++ b/tests/test_auth.py\n"
            "@@ -1 +1 @@\n-    assert user.is_active\n+    assert user.is_active is True\n"
        )
        self.assertEqual(find_tampering(diff), [])


if __name__ == "__main__":
    unittest.main()
