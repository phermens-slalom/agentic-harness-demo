"""Scripted fakes for unit tests and offline eval dry-runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

from ..models import BuildResult, Issue, Plan, PRSnapshot, ReviewResult, ScanVerdict, TriageResult


@dataclass
class FakeTriager:
    size: str = "s"
    files: list[str] = field(default_factory=list)

    async def triage(self, issue: Issue) -> TriageResult:
        return TriageResult(
            workflow="issue_to_merge", summary=issue.title, estimated_size=self.size, files=list(self.files)
        )


@dataclass
class FakePlanner:
    needs_approval: bool = False
    files: list[str] = field(default_factory=lambda: ["tests/test_round.py"])

    contexts: list[str] = field(default_factory=list)

    async def plan(self, issue: Issue, triage: TriageResult, context: str = "") -> Plan:
        self.contexts.append(context)
        return Plan(
            steps=["reproduce", "fix", "add regression test"],
            acceptance_criteria=["tests pass"],
            files=self.files,
            needs_human_approval=self.needs_approval,
        )


@dataclass
class ScriptedBuilder:
    """Returns the given BuildResults in order (last one repeats)."""

    results: list[BuildResult]
    calls: list[str | None] = field(default_factory=list)

    async def build(self, issue: Issue, plan: Plan, feedback: str | None) -> BuildResult:
        self.calls.append(feedback)
        return self.results[min(len(self.calls) - 1, len(self.results) - 1)]


@dataclass
class ScriptedReviewer:
    results: list[ReviewResult] = field(default_factory=lambda: [ReviewResult(approved=True)])
    n: int = 0
    contexts: list[str] = field(default_factory=list)

    async def review(self, issue: Issue, plan: Plan, build: BuildResult, context: str = "") -> ReviewResult:
        self.n += 1
        self.contexts.append(context)
        return self.results[min(self.n - 1, len(self.results) - 1)]


@dataclass
class RecordingHuman:
    approve: bool = True
    messages: list[str] = field(default_factory=list)
    plan_approvals: int = 0

    async def approve_plan(self, issue: Issue, plan: Plan) -> bool:
        self.plan_approvals += 1
        return self.approve

    async def notify(self, issue: Issue, message: str) -> None:
        self.messages.append(message)


@dataclass
class FakeGitHub:
    """Scripted GitHubPort: returns the given snapshots in order (last one repeats)."""

    snapshots: list[PRSnapshot]
    pr_number: int = 1
    assigned: list[str] = field(default_factory=list)
    custom_agents: list[str | None] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)
    waits: int = 0
    files: dict[str, str] = field(default_factory=dict)
    reads: list[str] = field(default_factory=list)

    async def read_file(self, repo: str, path: str, ref: str | None = None) -> str | None:
        self.reads.append(path)
        return self.files.get(path)

    async def list_files(self, repo: str, ref: str | None = None) -> list[str]:
        return sorted(self.files)

    async def assign_to_copilot(
        self, repo: str, issue_number: int, instructions: str, custom_agent: str | None = None
    ) -> int:
        self.assigned.append(instructions)
        self.custom_agents.append(custom_agent)
        return self.pr_number

    async def comment(self, repo: str, pr_number: int, body: str) -> None:
        self.comments.append(body)

    async def wait_for_checks(self, repo: str, pr_number: int) -> PRSnapshot:
        self.waits += 1
        return self.snapshots[min(self.waits - 1, len(self.snapshots) - 1)]


@dataclass
class FakeScanner:
    """Blocks any text containing one of `trigger` (case-insensitive); can simulate failure/incomplete."""

    trigger: tuple[str, ...] = ("ignore previous instructions",)
    incomplete: bool = False
    raises: bool = False
    seen: list[tuple[str, str]] = field(default_factory=list)

    def scan(self, text: str, channel: str) -> ScanVerdict:
        self.seen.append((channel, text))
        if self.raises:
            raise RuntimeError("scanner crashed")
        hit = any(t in text.lower() for t in self.trigger)
        return ScanVerdict(blocked=hit, complete=not self.incomplete, rule_ids=["FAKE-1"] if hit else [])


def _snake(name: str) -> str:
    return "".join("_" + c.lower() if c.isupper() else c for c in name)


_ENUM = {"MATCH_FOUND": 2, "NO_MATCH_FOUND": 1, "SUCCESS": 1, "PARTIAL": 2, "FAILURE": 3}
_ENUM_KEYS = {"matchState", "filterMatchState", "invocationResult"}


def _from_rest(value, key: str = ""):
    """A Model Armor REST JSON value as attribute-style objects, like the client library returns."""
    if isinstance(value, dict):
        if key in ("filterResults", "raiFilterTypeResults"):  # maps keyed by filter name stay dicts
            return {k: _from_rest(v) for k, v in value.items()}
        return SimpleNamespace(**{_snake(k): _from_rest(v, k) for k, v in value.items()})
    if key in _ENUM_KEYS and isinstance(value, str):
        return _ENUM[value]
    return value


class FixtureModelArmorClient:
    """Plays back a fixture file as Model Armor's `sanitize_user_prompt`. No network, no google libraries.

    `fixture` is {"default": <response>, "rules": [{"contains": text, "response": <response> | "raise": name}]}
    in the REST JSON shape. The first rule whose `contains` is in the prompt (case-insensitive) wins.
    """

    def __init__(self, fixture: dict):
        self.fixture = fixture
        self.requests: list[dict] = []

    def sanitize_user_prompt(self, request: dict, timeout: float | None = None):
        self.requests.append(request)
        text = request["user_prompt_data"]["text"].lower()
        for rule in self.fixture["rules"]:
            if rule["contains"].lower() in text:
                if "raise" in rule:
                    raise RuntimeError("fixture error")
                return _from_rest(rule["response"])
        return _from_rest(self.fixture["default"])
