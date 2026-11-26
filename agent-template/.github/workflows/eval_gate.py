"""Fail-closed comparison of agents-cli evaluation results with an approved baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import yaml
from yaml.resolver import BaseResolver


class UniqueLoader(yaml.SafeLoader):
    pass


def _mapping(loader: UniqueLoader, node: yaml.MappingNode, deep: bool = False) -> dict:
    result = {}
    for key, value in loader.construct_pairs(node, deep=deep):
        if key in result:
            raise ValueError("duplicate YAML key")
        result[key] = value
    return result


UniqueLoader.add_constructor(BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def _read_yaml(path: Path) -> object:
    loader = UniqueLoader(path.read_text(encoding="utf-8"))
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()


def _read_json(path: Path) -> dict:
    def unique_pairs(pairs: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise ValueError("non-finite JSON number")

    data = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs, parse_constant=reject_constant
    )
    if not isinstance(data, dict):
        raise TypeError("expected a JSON object")
    return data


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _summary_scores(summaries: list, expected_count: int) -> dict[str, float]:
    scores = {}
    for metric in summaries:
        if not isinstance(metric, dict):
            raise TypeError("invalid metric summary")
        name = metric.get("metric_name")
        if not isinstance(name, str) or not name or name in scores:
            raise ValueError("missing or duplicate metric")
        if (
            type(metric.get("num_cases_total")) is not int
            or type(metric.get("num_cases_valid")) is not int
            or type(metric.get("num_cases_error")) is not int
            or metric.get("num_cases_total") != expected_count
            or metric.get("num_cases_valid") != expected_count
            or metric.get("num_cases_error") != 0
        ):
            raise ValueError("incomplete or errored metric")
        score = _number(metric.get("mean_score"), "mean score")
        if not 0 <= score <= 1:
            raise ValueError("metric score is outside the 0-1 scale")
        scores[name] = score
    return scores


def _case_metrics(case: object, scores: dict[str, float]) -> dict[str, float]:
    if not isinstance(case, dict):
        raise TypeError("invalid case result")
    candidates = case.get("response_candidate_results")
    if not isinstance(candidates, list) or len(candidates) != 1 or not isinstance(candidates[0], dict):
        raise ValueError("expected one response per case")
    metrics = candidates[0].get("metric_results")
    if not isinstance(metrics, dict) or set(metrics) != set(scores):
        raise ValueError("missing or incompatible case metrics")
    result = {}
    for name, metric in metrics.items():
        if not isinstance(metric, dict) or metric.get("error_message") is not None:
            raise ValueError("errored case metric")
        value = _number(metric.get("score"), "case score")
        if not 0 <= value <= 1:
            raise ValueError("case score is outside the 0-1 scale")
        result[name] = value
    return result


def _scores(result: dict, expected_count: int) -> dict[str, float]:
    summaries = result.get("summary_metrics")
    cases = result.get("eval_case_results")
    if not isinstance(summaries, list) or not summaries or not isinstance(cases, list):
        raise ValueError("missing evaluation results")
    if len(cases) != expected_count:
        raise ValueError("incomplete evaluation cases")
    scores = _summary_scores(summaries, expected_count)
    seen = set()
    case_scores: dict[str, list[float]] = {name: [] for name in scores}
    for position, case in enumerate(cases):
        if not isinstance(case, dict):
            raise TypeError("invalid case result")
        index = case.get("eval_case_index")
        index = position if index is None else index
        if type(index) is not int or index not in range(expected_count) or index in seen:
            raise ValueError("missing or duplicate case index")
        seen.add(index)
        for name, value in _case_metrics(case, scores).items():
            case_scores[name].append(value)
    if any(
        not math.isclose(sum(values) / len(values), scores[name], abs_tol=1e-6)
        for name, values in case_scores.items()
    ):
        raise ValueError("metric summary does not match case scores")
    return scores


def _settings(config: Path, thresholds: Path) -> tuple[float, float]:
    settings = _read_yaml(config)
    limits = _read_yaml(thresholds)
    if not isinstance(settings, dict) or not isinstance(limits, dict):
        raise TypeError("invalid eval configuration")
    metric_names = settings.get("metrics_to_run")
    if metric_names != ["final_response_quality"]:
        raise ValueError("unsupported eval metric selection")
    custom_metrics = settings.get("custom_metrics")
    if (
        not isinstance(custom_metrics, list)
        or len(custom_metrics) != 1
        or not isinstance(custom_metrics[0], dict)
        or set(custom_metrics[0]) != {"name", "metric_spec_parameters"}
        or custom_metrics[0]["name"] != "final_response_quality"
        or not isinstance(custom_metrics[0]["metric_spec_parameters"], dict)
        or set(custom_metrics[0]["metric_spec_parameters"]) != {"rubric_group_key"}
        or not isinstance(custom_metrics[0]["metric_spec_parameters"]["rubric_group_key"], str)
        or not custom_metrics[0]["metric_spec_parameters"]["rubric_group_key"]
    ):
        raise ValueError("unsupported or executable custom metric")
    threshold = _number(limits.get("outcome_quality"), "outcome quality threshold")
    regression = _number(limits.get("max_regression"), "max regression")
    if not 0.8 <= threshold <= 1 or not 0 <= regression <= 1:
        raise ValueError("invalid outcome quality threshold or max regression")
    configured = settings.get("thresholds")
    if (
        not isinstance(configured, dict)
        or not threshold <= _number(configured.get("final_response_quality"), "eval threshold") <= 1
    ):
        raise ValueError("eval config does not enforce the required threshold")
    return threshold, regression


def check(
    baseline: Path, candidate: Path, manifest: Path, dataset: Path, config: Path, thresholds: Path
) -> None:
    manifest_data = _read_json(manifest)
    if (
        manifest_data.get("dataset_sha256") != _digest(dataset)
        or manifest_data.get("config_sha256") != _digest(config)
        or manifest_data.get("results_sha256") != _digest(baseline)
    ):
        raise ValueError("baseline, dataset or config does not match its manifest")
    dataset_data = _read_json(dataset)
    cases = dataset_data.get("eval_cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("dataset has no cases")
    ids = [case.get("eval_case_id") if isinstance(case, dict) else None for case in cases]
    if any(not isinstance(case_id, str) or not case_id for case_id in ids) or len(set(ids)) != len(ids):
        raise ValueError("dataset case IDs must be unique and non-empty")
    threshold, regression = _settings(config, thresholds)
    before = _scores(_read_json(baseline), len(cases))
    after = _scores(_read_json(candidate), len(cases))
    if set(before) != set(after) or len(before) != 1:
        raise ValueError("baseline and candidate metrics are incompatible")
    name = next(iter(before))
    if not re.fullmatch(r"final_response_quality(?:_v\d+)?", name):
        raise ValueError("result metric does not match the configured metric")
    if after[name] < threshold or before[name] - after[name] > regression + 1e-12:
        raise ValueError("evaluation threshold or baseline regression exceeded")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("baseline", "candidate", "manifest", "dataset", "config", "thresholds"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    try:
        check(args.baseline, args.candidate, args.manifest, args.dataset, args.config, args.thresholds)
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        print(f"Evaluation gate failed: {exc}", file=sys.stderr)
        return 1
    print("Evaluation gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
