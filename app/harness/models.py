"""Plain data types passed between workflow nodes. No framework imports here."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Decision(str, Enum):
    AUTO_MERGE = "auto_merge"
    HUMAN_APPROVAL = "human_approval"
    REJECT_TO_PLANNING = "reject_to_planning"
    ESCALATED = "escalated"
    IGNORED = "ignored"


@dataclass
class Issue:
    repo: str
    number: int
    title: str
    body: str
    labels: list[str] = field(default_factory=list)


class AdapterError(RuntimeError):
    """An adapter could not do its job safely (bad config, unpinned skill, unusable model output).
    The workflow escalates on it. Messages must never contain model output or repo content."""


class AgentOutputError(AdapterError):
    """An LLM agent could not produce output matching its schema (after the one allowed retry).
    The workflow escalates; it never guesses at a partial result."""


@dataclass
class TriageResult:
    workflow: str | None  # from routing.yaml, None = not for the harness
    summary: str
    estimated_size: str  # "s" | "m" | "l"
    # Repo paths the issue names. Untrusted model output: the context builder validates them.
    files: list[str] = field(default_factory=list)


@dataclass
class Plan:
    steps: list[str]
    acceptance_criteria: list[str]
    files: list[str] = field(default_factory=list)
    needs_human_approval: bool = False


@dataclass
class BuildResult:
    pr_number: int | None
    changed_files: list[str]
    lines_changed: int
    ci_green: bool
    tokens_used: int = 0
    ci_summary: str = ""
    # Per required check (lint, tests, evals_no_regression, secret_scan). The merge gate
    # requires every configured check to be explicitly green; an empty report is unknown.
    checks: dict[str, bool] = field(default_factory=dict)
    previous_paths: list[str] = field(default_factory=list)
    diff: str = ""
    # PR comment text from the GitHub client. Attacker-influenceable and read by the builder
    # (Copilot reads PR comments), so the workflow scans it before anything else happens.
    comments: list[str] = field(default_factory=list)

    @property
    def failing_checks(self) -> list[str]:
        return sorted(name for name, ok in self.checks.items() if not ok)

    @property
    def passed(self) -> bool:
        return self.ci_green and not self.failing_checks


@dataclass
class PRSnapshot:
    """What a GitHub client reports about a PR once its checks have finished."""

    pr_number: int
    changed_files: list[str]
    lines_changed: int
    checks: dict[str, bool]
    summary: str = ""
    previous_paths: list[str] = field(default_factory=list)
    diff: str = ""
    comments: list[str] = field(default_factory=list)


@dataclass
class ReviewResult:
    approved: bool
    blocking_findings: list[str] = field(default_factory=list)
    reviewer_id: str = "reviewer-agent"


@dataclass
class ScanVerdict:
    """What an input scanner says about one piece of untrusted text. `complete=False` means part of
    the input was not read, which is never treated as clean."""

    blocked: bool
    complete: bool = True
    rule_ids: list[str] = field(default_factory=list)
    severity: str = "none"

    @property
    def clean(self) -> bool:
        return self.complete and not self.blocked


@dataclass
class TraceEvent:
    node: str
    detail: dict
    stage: str | None = None  # golden-workflow stage id, from policy/golden_workflow.yaml


@dataclass
class TaskOutcome:
    issue: Issue
    decision: Decision
    tier: int | None = None
    pr_number: int | None = None
    build_iterations: int = 0
    tokens_used: int = 0
    reason: str = ""
    required_approvers: list[str] = field(default_factory=list)
    trace: list[TraceEvent] = field(default_factory=list)
