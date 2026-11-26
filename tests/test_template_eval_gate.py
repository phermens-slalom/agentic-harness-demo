import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "agent-template" / ".github" / "workflows" / "eval_gate.py"
spec = importlib.util.spec_from_file_location("template_eval_gate", PATH)
assert spec is not None and spec.loader is not None
gate = importlib.util.module_from_spec(spec)
original_bytecode_setting = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    spec.loader.exec_module(gate)
finally:
    sys.dont_write_bytecode = original_bytecode_setting


@pytest.fixture
def evidence(tmp_path):
    dataset = tmp_path / "dataset.json"
    config = tmp_path / "config.yaml"
    thresholds = tmp_path / "thresholds.yaml"
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    manifest = tmp_path / "manifest.json"
    dataset.write_text(json.dumps({"eval_cases": [{"eval_case_id": "one"}, {"eval_case_id": "two"}]}))
    config.write_text(
        "metrics_to_run: [final_response_quality]\n"
        "custom_metrics:\n"
        "  - name: final_response_quality\n"
        "    metric_spec_parameters: {rubric_group_key: starter_behaviour}\n"
        "thresholds: {final_response_quality: 0.8}\n"
    )
    thresholds.write_text("outcome_quality: 0.8\nmax_regression: 0.0\n")

    def result(scores):
        return {
            "summary_metrics": [
                {
                    "metric_name": "final_response_quality_v1",
                    "num_cases_total": 2,
                    "num_cases_valid": 2,
                    "num_cases_error": 0,
                    "mean_score": sum(scores) / len(scores),
                }
            ],
            "eval_case_results": [
                {
                    "eval_case_index": i,
                    "response_candidate_results": [
                        {
                            "metric_results": {
                                "final_response_quality_v1": {"score": score, "error_message": None}
                            }
                        }
                    ],
                }
                for i, score in enumerate(scores)
            ],
        }

    baseline.write_text(json.dumps(result([0.8, 1.0])))
    candidate.write_text(json.dumps(result([0.8, 1.0])))
    manifest.write_text(
        json.dumps(
            {
                f"{name}_sha256": hashlib.sha256(path.read_bytes()).hexdigest()
                for name, path in (("dataset", dataset), ("config", config), ("results", baseline))
            }
        )
    )
    return baseline, candidate, manifest, dataset, config, thresholds, result


def test_valid_results_pass(evidence):
    gate.check(*evidence[:-1])


@pytest.mark.parametrize("scores", [[0.7, 1.0], [0.7, 0.8]])
def test_regression_or_below_pass_mark_fails(evidence, scores):
    evidence[1].write_text(json.dumps(evidence[-1](scores)))
    with pytest.raises(ValueError, match="regression"):
        gate.check(*evidence[:-1])


def test_changed_dataset_or_baseline_fails(evidence):
    evidence[3].write_text('{"eval_cases": []}')
    with pytest.raises(ValueError, match="manifest"):
        gate.check(*evidence[:-1])


def test_duplicate_threshold_fails(evidence):
    with evidence[5].open("a") as stream:
        stream.write("outcome_quality: 0.9\n")
    with pytest.raises(ValueError, match="duplicate YAML"):
        gate.check(*evidence[:-1])


@pytest.mark.parametrize("mutation", ["missing", "error", "inconsistent", "duplicate"])
def test_incomplete_or_invalid_candidate_fails(evidence, mutation):
    result = evidence[-1]([0.8, 1.0])
    if mutation == "missing":
        result["eval_case_results"].pop()
    elif mutation == "error":
        result["eval_case_results"][0]["response_candidate_results"][0]["metric_results"][
            "final_response_quality_v1"
        ]["error_message"] = "failed"
    elif mutation == "inconsistent":
        result["summary_metrics"][0]["mean_score"] = 1.0
    else:
        result["eval_case_results"][1]["eval_case_index"] = 0
    evidence[1].write_text(json.dumps(result))
    with pytest.raises(ValueError):
        gate.check(*evidence[:-1])


def test_placeholder_baseline_fails(evidence):
    evidence[0].write_text('{"outcome_quality": null}')
    manifest = json.loads(evidence[2].read_text())
    manifest["results_sha256"] = hashlib.sha256(evidence[0].read_bytes()).hexdigest()
    evidence[2].write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="missing evaluation results"):
        gate.check(*evidence[:-1])


def test_custom_function_is_not_accepted(evidence):
    config = evidence[4].read_text()
    evidence[4].write_text(
        config.replace(
            "    metric_spec_parameters:",
            "    custom_function: arbitrary.module.function\n    metric_spec_parameters:",
        )
    )
    manifest = json.loads(evidence[2].read_text())
    manifest["config_sha256"] = hashlib.sha256(evidence[4].read_bytes()).hexdigest()
    evidence[2].write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="custom metric"):
        gate.check(*evidence[:-1])
