"""issue_to_merge workflow: the Build and Verify stages of the golden workflow.

Stages 1-4 and 7-8 (frame, register, provision, connect, release, operate) are
human-gated or handled by the bootstrap CLI; see policy/golden_workflow.yaml. Each trace
event carries the stage id of the node that produced it.

    issue -> triage/route -> plan (+HITL if tier 2+) -> build loop (sandbox, capped)
          -> reviewer agent -> deterministic merge gate -> auto-merge | human approval
    any node -> escalate

Written as a plain async orchestrator over ports so it is testable offline and
auditable line by line. Each method below maps 1:1 onto an ADK 2.0 Workflow node;
see docs/ADK_PORT.md for the port, which you do once you've verified the 2.x
Workflow API in `adk web` against the version you pin.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

from .golden import GoldenWorkflow
from .models import AdapterError, Decision, Issue, TaskOutcome, TraceEvent
from .nodes import merge_gate
from .nodes.input_guard import InputGuard
from .nodes.repo_context import build_repo_context
from .policy import RiskPolicy, Routing
from .ports import Builder, GitHubPort, HumanGate, Planner, Reviewer, Triager
from .residency import ResidencyError


class IssueToMerge:
    def __init__(
        self,
        *,
        triager: Triager,
        planner: Planner,
        builder: Builder,
        reviewer: Reviewer,
        human: HumanGate,
        policy: RiskPolicy | None = None,
        routing: Routing | None = None,
        golden: GoldenWorkflow | None = None,
        guard: InputGuard | None = None,
        egress_hosts: Sequence[str] = (),
        repo: GitHubPort | None = None,
    ):
        self.triager, self.planner, self.builder = triager, planner, builder
        self.reviewer, self.human = reviewer, human
        # Hosts the agent spec declares. TODO(AI governance team): read them from the repo's spec once the
        # GitHub client can read repo files (R2/R6); until then every non-allowlisted host is undeclared.
        self.egress_hosts = tuple(egress_hosts)
        # Read-only repo access for planner/reviewer context. None = no repo context (offline default).
        self.repo = repo
        self.guard = guard  # None = no input scanning (default; opt in via InputGuard.load)
        self.policy = policy or RiskPolicy.load()
        self.routing = routing or Routing.load()
        self.golden = golden or GoldenWorkflow.load()

    async def run(self, issue: Issue) -> TaskOutcome:
        out = TaskOutcome(issue=issue, decision=Decision.IGNORED)

        def trace(node: str, **detail):
            out.trace.append(TraceEvent(node, detail, self.golden.stage_for_node(node)))

        # 1. Route (deterministic first: no agent:* label -> harness ignores it)
        if self.routing.workflow_for(issue.labels) != "issue_to_merge":
            out.reason = "no matching agent:* route label"
            trace("route", result="ignored")
            return out

        # 1b. Input guard (deterministic): untrusted issue text is scanned before any LLM reads it
        if blocked := await self._scan("issue", f"{issue.title}\n\n{issue.body}", trace):
            return await self._escalate(out, trace, blocked)

        # 1c. Config checks that must be visible in the trace (no content, only names)
        planner_model = getattr(self.planner, "model_id", None)
        if planner_model and planner_model == getattr(self.reviewer, "model_id", None):
            trace("config", warning="reviewer model matches planner model", model=planner_model)
        for role, agent in (("planner", self.planner), ("reviewer", self.reviewer)):
            skills = getattr(agent, "provenance", None)
            if skills:
                trace("behaviour_artefacts", role=role, skills=[x.as_trace() for x in skills])

        # 2. Triage (LLM)
        try:
            triage = await self.triager.triage(issue)
        except (AdapterError, ResidencyError) as e:
            return await self._escalate(out, trace, f"triage failed: {e}")
        trace("triage", summary=triage.summary, size=triage.estimated_size)
        if triage.estimated_size == "l":
            return await self._escalate(out, trace, "triage sized task as large; needs splitting")

        # 3. Plan (LLM) + spec gate (HITL)
        context, blocked = await self._repo_context(issue, triage.files, "planner", trace)
        if blocked:
            return await self._escalate(out, trace, blocked)
        try:
            plan = await self.planner.plan(issue, triage, context)
        except (AdapterError, ResidencyError) as e:
            return await self._escalate(out, trace, f"planning failed: {e}")
        plan_tier = self.policy.tier_for_change(plan.files, 0)
        policy_requires_approval = self.policy.plan_approval == "always" or (
            self.policy.plan_approval == "tier_at_least_2" and plan_tier >= 2
        )
        requires_approval = policy_requires_approval or plan.needs_human_approval
        trace(
            "plan",
            steps=len(plan.steps),
            files=plan.files,
            predicted_tier=plan_tier,
            needs_approval=requires_approval,
            approval_rule=self.policy.plan_approval if policy_requires_approval else "llm_additional",
        )
        if requires_approval and not await self.human.approve_plan(issue, plan):
            return await self._escalate(out, trace, "human rejected plan")

        # 4. Build loop (sandbox), capped by iterations and token budget
        feedback, build = None, None
        review_context: str | None = None
        for i in range(1, self.routing.max_build_iterations + 1):
            out.build_iterations = i
            build = await self.builder.build(issue, plan, feedback)
            out.tokens_used += build.tokens_used
            out.pr_number = build.pr_number
            trace("build", iteration=i, passed=build.passed, lines=build.lines_changed)
            # PR comments are attacker-influenceable and the builder reads them: scan before anything else.
            if build.comments and (
                blocked := await self._scan("pr_comment", "\n\n".join(build.comments), trace)
            ):
                return await self._escalate(out, trace, blocked)
            if out.tokens_used > self.routing.max_tokens_per_task:
                return await self._escalate(out, trace, "token budget exceeded")
            if not build.passed:
                feedback = f"CI failed: {build.ci_summary or ', '.join(build.failing_checks)}"
                if blocked := await self._scan("build_feedback", feedback, trace):
                    return await self._escalate(out, trace, blocked)
                continue

            # 5. Review (LLM, different identity from builder)
            if review_context is None:
                review_context, blocked = await self._repo_context(issue, plan.files, "reviewer", trace)
                if blocked:
                    return await self._escalate(out, trace, blocked)
            try:
                review = await self.reviewer.review(issue, plan, build, review_context)
            except (AdapterError, ResidencyError) as e:
                return await self._escalate(out, trace, f"review failed: {e}")
            trace("review", approved=review.approved, findings=len(review.blocking_findings))
            if not review.approved and i < self.routing.max_build_iterations:
                feedback = "Review findings:\n" + "\n".join(review.blocking_findings)
                # The reviewer's findings can quote attacker-influenced diff text and go to the builder.
                if blocked := await self._scan("review_feedback", feedback, trace):
                    return await self._escalate(out, trace, blocked)
                continue

            # 6. Merge gate (deterministic)
            gate = merge_gate.decide(self.policy, build, review, egress_hosts=self.egress_hosts)
            out.decision, out.tier, out.reason = gate.decision, gate.tier, gate.reason
            out.required_approvers = gate.required_approvers
            trace(
                "merge_gate",
                decision=gate.decision.value,
                tier=gate.tier,
                reason=gate.reason,
                approvers=gate.required_approvers,
                new_capabilities=gate.new_capabilities,
            )
            if gate.decision is Decision.ESCALATED:
                return await self._escalate(out, trace, gate.reason)
            if gate.decision is Decision.HUMAN_APPROVAL:
                await self.human.notify(issue, f"PR #{build.pr_number} ready for review: {gate.reason}")
            return out

        reason = f"build loop hit cap of {self.routing.max_build_iterations}"
        if build:
            missing_checks = self.policy.missing_checks(build.checks)
            if missing_checks:
                reason += "; required checks not reported: " + ", ".join(missing_checks)
        return await self._escalate(out, trace, reason)

    async def _repo_context(
        self, issue: Issue, named_files: list[str], role: str, trace
    ) -> tuple[str, str | None]:
        """Read-only repo context for `role`, scanned by the input guard. Returns (text, block_reason)."""
        if self.repo is None:
            return "", None
        ctx = await build_repo_context(self.repo, issue.repo, self.routing.repo_context, named_files)
        # Names and sizes only: never file content in the trace.
        trace("repo_context", role=role, files=ctx.included, skipped=len(ctx.skipped), bytes=ctx.size)
        if blocked := await self._scan("repo_context", ctx.text, trace):
            return "", blocked
        return ctx.text, None

    async def _scan(self, surface: str, text: str, trace) -> str | None:
        """Scan untrusted text with the input guard; return the block reason, or None to carry on.

        The scanner may call a network service (Model Armor), so it runs in a worker thread rather
        than on the event loop. The trace records the surface and rule ids, never the text.
        """
        if not self.guard:
            return None
        g = await asyncio.to_thread(self.guard.check, surface, text)
        if not g.ok or g.shadow_hit:
            trace(
                "input_guard", surface=surface, blocked=not g.ok, shadow=g.shadow_hit, rules=list(g.rule_ids)
            )
        return None if g.ok else g.reason

    async def _escalate(self, out: TaskOutcome, trace, reason: str) -> TaskOutcome:
        out.decision, out.reason = Decision.ESCALATED, reason
        trace("escalate", reason=reason)
        await self.human.notify(out.issue, f"Escalated: {reason}")
        return out
