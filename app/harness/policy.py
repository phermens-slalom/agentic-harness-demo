"""Deterministic risk tiering. This is the code your risk team audits: keep it boring."""

from __future__ import annotations

import re
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path

from .policy_validation import Capabilities as CapabilitiesSchema
from .policy_validation import ReviewChecklist as ReviewChecklistSchema
from .policy_validation import RiskTiers as RiskTiersSchema
from .policy_validation import Routing as RoutingSchema
from .policy_validation import load_policy_file

POLICY_DIR = Path(__file__).resolve().parents[2] / "policy"


def _matches(path: str, pattern: str) -> bool:
    path = path.replace("\\", "/").lower()
    pattern = pattern.replace("\\", "/").lower()
    # fnmatchcase is platform-independent; also match root paths for **/ patterns.
    return fnmatchcase(path, pattern) or (pattern.startswith("**/") and fnmatchcase(path, pattern[3:]))


@dataclass
class RiskPolicy:
    default_tier: int
    rules: list[dict]
    max_lines_for_tier_1: int
    max_lines_any_tier: int
    phase: int
    plan_approval: str
    auto_merge_tiers: set[int]
    base_approvers: list[str]
    required_checks: list[str]

    @classmethod
    def load(cls, path: Path | None = None, phase: int | None = None) -> RiskPolicy:
        data = load_policy_file(path or POLICY_DIR / "risk_tiers.yaml", RiskTiersSchema)
        phase = phase if phase is not None else data["phase"]
        if phase not in data["phases"]:
            raise ValueError(f"unknown phase {phase}; defined: {sorted(data['phases'])}")
        return cls(
            default_tier=data["default_tier"],
            rules=data["rules"],
            max_lines_for_tier_1=data["limits"]["max_lines_for_tier_1"],
            max_lines_any_tier=data["limits"]["max_lines_any_tier"],
            phase=phase,
            plan_approval=data["phases"][phase]["plan_approval"],
            auto_merge_tiers=set(data["phases"][phase]["auto_merge_tiers"]),
            base_approvers=list(data["base_approvers"]),
            required_checks=list(data["required_checks"]),
        )

    def rule_for_file(self, path: str) -> dict | None:
        for rule in self.rules:
            if any(_matches(path, p) for p in rule["paths"]):
                return rule
        return None

    def tier_for_file(self, path: str) -> int:
        rule = self.rule_for_file(path)
        return rule["tier"] if rule else self.default_tier

    def approvers_for_change(
        self,
        changed_files: list[str],
        base: list[str] | None = None,
        previous_paths: list[str] | None = None,
    ) -> list[str]:
        """Base approvers plus those named by the first matching rule of each file."""
        out = list(base if base is not None else self.base_approvers)
        for f in [*(previous_paths or []), *changed_files]:
            rule = self.rule_for_file(f)
            for a in (rule or {}).get("approvers", []):
                if a not in out:
                    out.append(a)
        return out

    def missing_checks(self, reported: dict[str, bool]) -> list[str]:
        """Required checks absent from the report; false results are reported as failures."""
        return [c for c in self.required_checks if c not in reported]

    def tier_for_change(
        self, changed_files: list[str], lines_changed: int, previous_paths: list[str] | None = None
    ) -> int:
        paths = [*(previous_paths or []), *changed_files]
        if not paths:
            return self.default_tier
        tier = max(self.tier_for_file(f) for f in paths)
        if tier == 1 and lines_changed > self.max_lines_for_tier_1:
            tier = 2
        return tier

    def too_large(self, lines_changed: int) -> bool:
        return lines_changed > self.max_lines_any_tier


@dataclass(frozen=True)
class CapabilityPolicy:
    """Allowlists and approvers for the new-capability detectors (policy/capabilities.yaml)."""

    ignore_paths: tuple[str, ...]
    allowed_models: frozenset[str]
    allowed_hosts: frozenset[str]
    allowed_regions: frozenset[str]
    allowed_data_stores: frozenset[str]
    allowed_dependencies: frozenset[str]
    approvers: dict[str, tuple[str, ...]]

    @classmethod
    def load(cls, path: Path | None = None) -> CapabilityPolicy:
        data = load_policy_file(path or POLICY_DIR / "capabilities.yaml", CapabilitiesSchema)
        return cls(
            ignore_paths=tuple(data["ignore_paths"]),
            allowed_models=frozenset(m.lower() for m in data["allowed_models"]),
            allowed_hosts=frozenset(h.lower() for h in data["allowed_hosts"]),
            allowed_regions=frozenset(r.lower() for r in data["allowed_regions"]),
            allowed_data_stores=frozenset(data["allowed_data_stores"]),
            # Python names compare with -/_/. equivalent; Go and npm names compare exactly (lowercase).
            allowed_dependencies=frozenset(
                form
                for d in data["allowed_dependencies"]
                for form in (d.lower(), re.sub(r"[-_.]+", "-", d.lower()))
            ),
            approvers={k: tuple(v) for k, v in data["approvers"].items()},
        )

    def ignores(self, path: str) -> bool:
        return any(_matches(path, p) for p in self.ignore_paths)


@dataclass(frozen=True)
class RepoContextLimits:
    max_files: int
    max_bytes_per_file: int
    max_total_bytes: int
    max_tree_entries: int
    deny_paths: tuple[str, ...]

    def denies(self, path: str) -> bool:
        return any(_matches(path, p) for p in self.deny_paths)


@dataclass
class Routing:
    routes: dict[str, str]
    max_build_iterations: int
    max_tokens_per_task: int
    skills: dict[str, list[str]]
    repo_context: RepoContextLimits

    @classmethod
    def load(cls, path: Path | None = None) -> Routing:
        data = load_policy_file(path or POLICY_DIR / "routing.yaml", RoutingSchema)
        return cls(
            routes=data["routes"],
            max_build_iterations=data["budgets"]["max_build_iterations"],
            max_tokens_per_task=data["budgets"]["max_tokens_per_task"],
            skills=data.get("skills", {}),
            repo_context=RepoContextLimits(
                max_files=data["repo_context"]["max_files"],
                max_bytes_per_file=data["repo_context"]["max_bytes_per_file"],
                max_total_bytes=data["repo_context"]["max_total_bytes"],
                max_tree_entries=data["repo_context"]["max_tree_entries"],
                deny_paths=tuple(data["repo_context"]["deny_paths"]),
            ),
        )

    def workflow_for(self, labels: list[str]) -> str | None:
        for label in labels:
            if label in self.routes:
                return self.routes[label]
        return None


def load_review_checklist(path: Path | None = None) -> list[str]:
    data = load_policy_file(path or POLICY_DIR / "review_checklist.yaml", ReviewChecklistSchema)
    return data["items"]
