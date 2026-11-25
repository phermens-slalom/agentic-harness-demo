"""Default Builder: the GitHub Copilot coding agent, driven through the GitHub App.

First loop: assign the issue to Copilot with the plan + AGENTS.md pointer as instructions.
Later loops: comment CI/review feedback on the PR; Copilot pushes to the same branch.
Either way we then wait for the PR's required checks and report what they said.

Needs a concrete GitHubPort (GitHub App installation token, issues/pull_requests/contents
read-write, checks read). VERIFY the assignment API against GitHub Enterprise's current
Copilot coding agent docs when implementing it. Copilot is billed per premium request,
not tokens, so `tokens_used` is 0 and the iteration cap in routing.yaml is the budget.
"""

from __future__ import annotations

from ..models import BuildResult, Issue, Plan
from ..ports import GitHubPort

# Profile shipped in the template at .github/agents/agent-builder.agent.md. GitHub names an agent by
# its file name without the .md/.agent.md suffix unless `name` is set; the REST docs only say
# `custom_agent` is "a custom agent to use for the task".
# TODO(verify): confirm the exact identifier the API expects when the real GitHubPort is built (R2).
DEFAULT_CUSTOM_AGENT = "agent-builder"


class CopilotBuilder:
    def __init__(self, github: GitHubPort, custom_agent: str | None = DEFAULT_CUSTOM_AGENT):
        self.github = github
        self.custom_agent = custom_agent
        self._pr: dict[tuple[str, int], int] = {}

    async def build(self, issue: Issue, plan: Plan, feedback: str | None) -> BuildResult:
        key = (issue.repo, issue.number)
        if key not in self._pr:
            self._pr[key] = await self.github.assign_to_copilot(
                issue.repo, issue.number, self._instructions(plan), self.custom_agent
            )
        elif feedback:
            await self.github.comment(issue.repo, self._pr[key], f"@copilot {feedback}")
        snap = await self.github.wait_for_checks(issue.repo, self._pr[key])
        failing = sorted(n for n, ok in snap.checks.items() if not ok)
        return BuildResult(
            pr_number=snap.pr_number,
            changed_files=snap.changed_files,
            lines_changed=snap.lines_changed,
            ci_green=bool(snap.checks) and not failing,
            checks=snap.checks,
            previous_paths=snap.previous_paths,
            diff=snap.diff,
            ci_summary=snap.summary or ("failing: " + ", ".join(failing) if failing else ""),
        )

    @staticmethod
    def _instructions(plan: Plan) -> str:
        steps = "\n".join(f"- {s}" for s in plan.steps)
        done = "\n".join(f"- {c}" for c in plan.acceptance_criteria)
        return f"Follow AGENTS.md.\n\nPlan:\n{steps}\n\nAcceptance criteria:\n{done}"
