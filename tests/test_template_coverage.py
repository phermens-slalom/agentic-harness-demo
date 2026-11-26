import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

PATH = Path(__file__).resolve().parents[1] / "agent-template" / ".github" / "workflows" / "coverage.py"
spec = importlib.util.spec_from_file_location("template_ci_checks", PATH)
assert spec is not None and spec.loader is not None
checks = importlib.util.module_from_spec(spec)
original_bytecode_setting = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    spec.loader.exec_module(checks)
finally:
    sys.dont_write_bytecode = original_bytecode_setting


@pytest.mark.parametrize("value", ["null", "true", "-1", "79.9", "101", ".nan", ".inf", '"80"'])
def test_missing_or_invalid_coverage_threshold_fails_closed(tmp_path, value):
    threshold_file = tmp_path / "thresholds.yaml"
    threshold_file.write_text(f"coverage: {value}\n", encoding="utf-8")
    with pytest.raises((TypeError, ValueError), match="coverage threshold"):
        checks.coverage_threshold(threshold_file)


def test_coverage_check_passes_owner_threshold_to_pytest(tmp_path, monkeypatch):
    (tmp_path / "evals").mkdir()
    (tmp_path / "evals" / "thresholds.yaml").write_text("coverage: 82.5\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    calls = []

    def run(command, *, check):
        calls.append(command)
        return type("Result", (), {"returncode": 1})()

    monkeypatch.setattr(checks.subprocess, "run", run)
    assert checks.main() == 1
    assert "--cov=agent" in calls[0]
    assert "--cov-fail-under=82.5" in calls[0]


def test_new_jobs_use_no_cloud_identity():
    workflow = yaml.safe_load((PATH.parent / "agent-checks.yml").read_text(encoding="utf-8"))
    for name in ("coverage", "quality"):
        assert workflow["jobs"][name]["permissions"] == {"contents": "read"}
