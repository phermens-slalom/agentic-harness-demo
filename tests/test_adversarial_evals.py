"""The adversarial golden tasks must run green in pytest too, and must go red when the guard goes blind."""

import asyncio
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _runner():
    spec = importlib.util.spec_from_file_location("run_evals", ROOT / "evals" / "run_evals.py")
    if spec is None or spec.loader is None:
        raise ImportError("could not load eval runner")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(mod):
    out = Path(tempfile.mkdtemp()) / "report.json"
    rc = asyncio.run(mod.main("dry-run", ROOT / "evals" / "golden_tasks", out))
    return rc, json.loads(out.read_text())


class AdversarialEvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import sunglasses  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("sunglasses not installed (.[guard])")

    def test_shipped_tasks_pass_and_report_open_gaps(self):
        rc, report = _run(_runner())
        m = report["metrics"]
        self.assertEqual(rc, 0)
        self.assertEqual(m["injection_detection_rate"], 1.0)
        self.assertEqual(m["guard_false_positive_rate"], 0.0)
        self.assertEqual(m["adversarial_automerge"], 0)
        self.assertGreater(m["known_gaps_open"], 0)

    def test_blind_scanner_turns_the_run_red(self):
        from harness.adapters import sunglasses_scanner
        from harness.models import ScanVerdict

        original = sunglasses_scanner.SunglassesScanner.scan
        sunglasses_scanner.SunglassesScanner.scan = lambda self, text, channel: ScanVerdict(blocked=False)
        try:
            rc, report = _run(_runner())
        finally:
            sunglasses_scanner.SunglassesScanner.scan = original
        self.assertEqual(rc, 1)
        # Sunglasses-only tasks all go undetected. The composite tasks are still flagged by the Model
        # Armor fixture (that is the point of a second scanner), so the rate falls below 1.0, not to 0.
        self.assertLess(report["metrics"]["injection_detection_rate"], 1.0)
        self.assertGreater(report["metrics"]["adversarial_automerge"], 0)

    def test_blind_model_armor_turns_the_run_red(self):
        """The composite tasks must really depend on Model Armor: without it the two Sunglasses gaps reopen."""
        from harness.adapters import model_armor_scanner
        from harness.models import ScanVerdict

        original = model_armor_scanner.ModelArmorScanner.scan
        model_armor_scanner.ModelArmorScanner.scan = lambda self, text, channel: ScanVerdict(blocked=False)
        try:
            rc, report = _run(_runner())
        finally:
            model_armor_scanner.ModelArmorScanner.scan = original
        self.assertEqual(rc, 1)
        failed = {t["id"] for t in report["tasks"] if not t["known_gap"] and not t["ok"]}
        self.assertTrue({"adv-ma-html-comment-composite", "adv-ma-terse-exfil-composite"} <= failed)


if __name__ == "__main__":
    unittest.main()
