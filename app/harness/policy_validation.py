"""Strict schemas and cross-file checks for the repository's policy YAML."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, StrictBool, StrictInt, StrictStr, ValidationError

POLICY_DIR = Path(__file__).resolve().parents[2] / "policy"
TEMPLATE_WORKFLOW = (
    Path(__file__).resolve().parents[2] / "agent-template" / ".github" / "workflows" / "agent-checks.yml"
)
KNOWN_WORKFLOWS = {"issue_to_merge"}
RACI_VALUES = {"", "R", "A", "C", "I", "R/A", "approves"}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Phase(StrictModel):
    plan_approval: Literal["always", "tier_at_least_2"]
    auto_merge_tiers: list[StrictInt]


class RiskRule(StrictModel):
    name: StrictStr
    tier: StrictInt
    paths: list[StrictStr]
    approvers: list[StrictStr] = []


class Limits(StrictModel):
    max_lines_for_tier_1: StrictInt
    max_lines_any_tier: StrictInt


class RiskTiers(StrictModel):
    default_tier: StrictInt
    phase: StrictInt
    phases: dict[int, Phase]
    base_approvers: list[StrictStr]
    required_checks: list[StrictStr]
    rules: list[RiskRule]
    limits: Limits


class RaciActivity(StrictModel):
    name: StrictStr
    app_team: StrictStr
    ai_governance: StrictStr
    platform_team: StrictStr
    security: StrictStr
    product_owner: StrictStr
    architecture: StrictStr


class Raci(StrictModel):
    roles: list[StrictStr]
    activities: list[RaciActivity]


class WorkflowStage(StrictModel):
    id: StrictStr
    title: StrictStr
    steps: list[StrictInt]
    kind: Literal[
        "deterministic",
        "non_deterministic",
        "mixed",
        "deterministic_checks_on_non_deterministic_output",
    ]
    raises: StrictStr
    approves: list[StrictStr]
    gates: list[Literal["person", "check"]]
    nodes: list[StrictStr]
    harness: StrictStr


class GoldenWorkflow(StrictModel):
    stages: list[WorkflowStage]


class Budgets(StrictModel):
    max_build_iterations: StrictInt
    max_tokens_per_task: StrictInt


class RepoContext(StrictModel):
    max_files: StrictInt
    max_bytes_per_file: StrictInt
    max_total_bytes: StrictInt
    max_tree_entries: StrictInt
    deny_paths: list[StrictStr]


class Routing(StrictModel):
    routes: dict[StrictStr, StrictStr]
    budgets: Budgets
    repo_context: RepoContext
    skills: dict[StrictStr, list[StrictStr]]


class LockedSkill(StrictModel):
    sha256: StrictStr
    capabilities: list[Literal["instructions"]]
    owner: StrictStr


class SkillsLock(StrictModel):
    source: StrictStr
    revision: StrictStr
    skills: dict[StrictStr, LockedSkill]


class Residency(StrictModel):
    allowed_locations: list[StrictStr]
    known_gaps: list[StrictStr]


class InputGuard(StrictModel):
    enabled: StrictBool
    mode: Literal["shadow", "enforce"]
    fail_closed: StrictBool
    surfaces: dict[StrictStr, StrictStr]


class CapabilityApprovers(StrictModel):
    model: list[StrictStr]
    host: list[StrictStr]
    undeclared_host: list[StrictStr]
    region: list[StrictStr]
    data_store: list[StrictStr]
    dependency: list[StrictStr]
    tool_protocol: list[StrictStr]


class Capabilities(StrictModel):
    ignore_paths: list[StrictStr]
    allowed_models: list[StrictStr]
    allowed_hosts: list[StrictStr]
    allowed_regions: list[StrictStr]
    allowed_data_stores: list[Literal["bigquery", "firestore", "spanner", "gcs", "memory_bank"]]
    allowed_dependencies: list[StrictStr]
    approvers: CapabilityApprovers


class ReviewChecklist(StrictModel):
    items: list[StrictStr]


SCHEMAS: dict[str, type[BaseModel]] = {
    "risk_tiers.yaml": RiskTiers,
    "raci.yaml": Raci,
    "golden_workflow.yaml": GoldenWorkflow,
    "routing.yaml": Routing,
    "residency.yaml": Residency,
    "input_guard.yaml": InputGuard,
    "review_checklist.yaml": ReviewChecklist,
    "capabilities.yaml": Capabilities,
    "skills.lock.yaml": SkillsLock,
}


def load_policy_file(path: Path, schema: type[BaseModel]) -> dict:
    """Load one YAML policy file and validate its shape, rejecting unknown keys."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path}: expected a YAML mapping")
    try:
        return schema.model_validate(data).model_dump()
    except ValidationError as exc:
        raise ValueError(f"{path}: invalid policy: {exc}") from exc


def _read(directory: Path, filename: str) -> dict:
    return load_policy_file(directory / filename, SCHEMAS[filename])


def validate_policy_directory(directory: Path | None = None) -> None:
    """Validate all policy files and the role, check, and route references between them."""
    policy_dir = directory or POLICY_DIR
    files = {name: _read(policy_dir, name) for name in SCHEMAS}
    roles = set(files["raci.yaml"]["roles"])
    used_roles = set(files["risk_tiers.yaml"]["base_approvers"])
    for rule in files["risk_tiers.yaml"]["rules"]:
        used_roles.update(rule["approvers"])
    used_roles.update(r for roles_ in files["capabilities.yaml"]["approvers"].values() for r in roles_)
    for stage in files["golden_workflow.yaml"]["stages"]:
        used_roles.add(stage["raises"])
        used_roles.update(stage["approves"])
    unknown_roles = sorted(used_roles - roles)
    if unknown_roles:
        raise ValueError(f"policy references unknown RACI role(s): {', '.join(unknown_roles)}")

    check_workflow = TEMPLATE_WORKFLOW
    if directory is not None:
        check_workflow = directory.parent / "agent-template" / ".github" / "workflows" / "agent-checks.yml"
    jobs_data = yaml.safe_load(check_workflow.read_text(encoding="utf-8"))
    job_names = set((jobs_data or {}).get("jobs", {}))
    missing_jobs = sorted(set(files["risk_tiers.yaml"]["required_checks"]) - job_names)
    if missing_jobs:
        raise ValueError(f"required checks missing from agent-checks.yml jobs: {', '.join(missing_jobs)}")

    outside_residency = sorted(
        set(files["capabilities.yaml"]["allowed_regions"]) - set(files["residency.yaml"]["allowed_locations"])
    )
    if outside_residency:
        raise ValueError(
            "capabilities.yaml allowed_regions not in residency.yaml allowed_locations: "
            + ", ".join(outside_residency)
        )

    lock = files["skills.lock.yaml"]
    named = {n for names in files["routing.yaml"]["skills"].values() for n in names}
    unpinned = sorted(named - set(lock["skills"]))
    if unpinned:
        raise ValueError(f"routing.yaml skills not pinned in skills.lock.yaml: {', '.join(unpinned)}")
    if lock["skills"] and not re.fullmatch(r"[0-9a-f]{40}", lock["revision"]):
        raise ValueError(
            "skills.lock.yaml revision must be a full 40-character commit SHA, not a floating ref"
        )
    for skill_name, skill in lock["skills"].items():
        if not re.fullmatch(r"[0-9a-f]{64}", skill["sha256"]):
            raise ValueError(f"skills.lock.yaml {skill_name}: sha256 must be 64 hex characters")
        if skill["owner"] not in roles:
            raise ValueError(f"policy references unknown RACI role(s): {skill['owner']}")

    route_targets = set(files["routing.yaml"]["routes"].values())
    unknown_targets = sorted(route_targets - KNOWN_WORKFLOWS)
    if unknown_targets:
        raise ValueError(f"routing references unknown workflow(s): {', '.join(unknown_targets)}")

    for row in files["raci.yaml"]["activities"]:
        accountable = [v for k, v in row.items() if k != "name" and v in ("A", "R/A")]
        if len(accountable) != 1:
            raise ValueError(f"RACI row {row['name']!r}: needs exactly one A, has {len(accountable)}")
        invalid = sorted({v for k, v in row.items() if k != "name" and v not in RACI_VALUES})
        if invalid:
            raise ValueError(f"RACI row {row['name']!r}: invalid value(s) {invalid}")

    phase = files["risk_tiers.yaml"]["phase"]
    if phase not in files["risk_tiers.yaml"]["phases"]:
        raise ValueError(f"risk_tiers.yaml: active phase {phase} is not defined")
