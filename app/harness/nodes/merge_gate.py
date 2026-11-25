"""Deterministic merge gate. No LLM in here, by design.

Phase 1 policy: nothing auto-merges; the gate's job is to say which approvals a PR
needs (derived from changed paths) and to block on failing checks.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from functools import lru_cache

from ..models import BuildResult, Decision, ReviewResult
from ..policy import CapabilityPolicy, RiskPolicy
from .capability_check import approvers_from, find_new_capabilities, summarise
from .tamper_check import find_tampering


@dataclass(frozen=True)
class GateResult:
    decision: Decision
    tier: int
    reason: str
    required_approvers: list[str] = field(default_factory=list)
    new_capabilities: list[str] = field(default_factory=list)


@lru_cache(maxsize=1)
def _default_capabilities() -> CapabilityPolicy:
    return CapabilityPolicy.load()


def decide(
    policy: RiskPolicy,
    build: BuildResult,
    review: ReviewResult,
    builder_id: str = "builder-agent",
    capabilities: CapabilityPolicy | None = None,
    egress_hosts: Sequence[str] = (),
) -> GateResult:
    tier = policy.tier_for_change(build.changed_files, build.lines_changed, build.previous_paths)
    approvers = policy.approvers_for_change(build.changed_files, previous_paths=build.previous_paths)
    # New capabilities only ever add approvers and a reason. They never lift a decision toward
    # AUTO_MERGE and never block on their own: the only decision they change is AUTO_MERGE, which
    # becomes HUMAN_APPROVAL because the extra approvers must actually approve.
    found = find_new_capabilities(build.diff, capabilities or _default_capabilities(), egress_hosts)
    approvers = [*approvers, *(a for a in approvers_from(found) if a not in approvers)]
    capability_note = ("; new capabilities: " + summarise(found)) if found else ""

    def result(decision: Decision, reason: str) -> GateResult:
        return GateResult(decision, tier, reason + capability_note, approvers, [str(f) for f in found])

    if policy.too_large(build.lines_changed):
        return result(
            Decision.REJECT_TO_PLANNING,
            f"{build.lines_changed} lines exceeds limit {policy.max_lines_any_tier}; split the task",
        )
    failing = build.failing_checks
    missing = policy.missing_checks(build.checks)
    check_reasons = []
    if failing:
        check_reasons.append("required checks failing: " + ", ".join(failing))
    if missing:
        check_reasons.append("required checks not reported: " + ", ".join(missing))
    if check_reasons:
        return result(Decision.ESCALATED, "; ".join(check_reasons))
    if not build.ci_green:
        return result(Decision.ESCALATED, "CI not green at merge gate")
    tampering = find_tampering(build.diff)
    if tampering:
        return result(Decision.ESCALATED, "test/eval tampering detected: " + "; ".join(tampering))
    if review.reviewer_id == builder_id:
        return result(Decision.ESCALATED, "reviewer lockout: builder cannot approve its own PR")
    if not review.approved:
        return result(Decision.HUMAN_APPROVAL, "reviewer agent did not approve")
    if tier in policy.auto_merge_tiers and not found:
        return result(
            Decision.AUTO_MERGE, f"phase {policy.phase}, tier {tier}, checks green, reviewer approved"
        )
    return result(
        Decision.HUMAN_APPROVAL,
        f"phase {policy.phase}, tier {tier}: approvals needed from {', '.join(approvers)}",
    )
