"""Interfaces the workflow depends on. Real implementations live in adapters/
(ADK + Gemini, Cloud Run sandbox, GitHub App); fakes are used for tests/evals.
Keeping the workflow behind these ports lets you swap the coding agent
(GitHub Copilot by default; Cloud Run sandbox optional) or the model without touching
orchestration."""

from __future__ import annotations

from typing import Protocol

from .models import BuildResult, Issue, Plan, PRSnapshot, ReviewResult, ScanVerdict, TriageResult


class Triager(Protocol):
    async def triage(self, issue: Issue) -> TriageResult: ...


class Planner(Protocol):
    """`context` is size-capped, input-guard-scanned repo context (AGENTS.md, file tree, named files)."""

    async def plan(self, issue: Issue, triage: TriageResult, context: str = "") -> Plan: ...


class GitHubPort(Protocol):
    """The slice of GitHub (via the GitHub App, never a personal token) the builder needs."""

    async def assign_to_copilot(
        self, repo: str, issue_number: int, instructions: str, custom_agent: str | None = None
    ) -> int:
        """Hand the issue to the Copilot coding agent; return the PR number it opens.

        `custom_agent` names a repo custom agent profile (`.github/agents/<name>.agent.md`)."""

    async def comment(self, repo: str, pr_number: int, body: str) -> None:
        """Comment on the PR (Copilot picks up review feedback from comments)."""

    async def wait_for_checks(self, repo: str, pr_number: int) -> PRSnapshot:
        """Block until the PR's required checks finish; return files, size and results."""

    async def read_file(self, repo: str, path: str, ref: str | None = None) -> str | None:
        """Read one file from the default branch (or `ref`); None if it does not exist.
        Read-only: the GitHub App needs contents:read for this and nothing more."""

    async def list_files(self, repo: str, ref: str | None = None) -> list[str]:
        """Repo-relative file paths on the default branch (or `ref`)."""


class Builder(Protocol):
    """Runs the coding agent; ends with a PR whose checks have finished.
    `feedback` carries CI failures or review findings from the last loop."""

    async def build(self, issue: Issue, plan: Plan, feedback: str | None) -> BuildResult: ...


class Reviewer(Protocol):
    async def review(
        self, issue: Issue, plan: Plan, build: BuildResult, context: str = ""
    ) -> ReviewResult: ...


class HumanGate(Protocol):
    """HITL breakpoint. In production this pauses the workflow until a human acts."""

    async def approve_plan(self, issue: Issue, plan: Plan) -> bool: ...
    async def notify(self, issue: Issue, message: str) -> None: ...


class InputScanner(Protocol):
    """Deterministic scan of untrusted text before an LLM reads it (defence in depth: it narrows what
    reaches the model; it never replaces the merge gate or human approval). May raise on failure."""

    def scan(self, text: str, channel: str) -> ScanVerdict: ...
