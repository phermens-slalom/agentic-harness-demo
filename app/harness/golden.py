"""The golden workflow and RACI as data (policy/golden_workflow.yaml, policy/raci.yaml).

Code reads these instead of hard-coding stages, so the workflow documentation, the harness
trace and the approver rules cannot drift apart: `validate()` is run in tests and CI.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .policy_validation import GoldenWorkflow as GoldenWorkflowSchema
from .policy_validation import Raci as RaciSchema
from .policy_validation import load_policy_file

POLICY_DIR = Path(__file__).resolve().parents[2] / "policy"
ONBOARDING_STEPS = range(1, 14)  # the example 13-step onboarding journey


@dataclass(frozen=True)
class Stage:
    id: str
    title: str
    steps: tuple[int, ...]
    kind: str
    raises: str
    approves: tuple[str, ...]
    gates: tuple[str, ...]
    nodes: tuple[str, ...]
    harness: str


@dataclass
class GoldenWorkflow:
    stages: list[Stage]
    roles: list[str]
    raci: list[dict]

    @classmethod
    def load(cls, policy_dir: Path | None = None) -> GoldenWorkflow:
        d = policy_dir or POLICY_DIR
        wf = load_policy_file(d / "golden_workflow.yaml", GoldenWorkflowSchema)
        raci = load_policy_file(d / "raci.yaml", RaciSchema)
        stages = [
            Stage(
                id=s["id"],
                title=s["title"],
                steps=tuple(s["steps"]),
                kind=s["kind"],
                raises=s["raises"],
                approves=tuple(s["approves"]),
                gates=tuple(s["gates"]),
                nodes=tuple(s["nodes"]),
                harness=s["harness"],
            )
            for s in wf["stages"]
        ]
        return cls(stages=stages, roles=raci["roles"], raci=raci["activities"])

    def stage_for_node(self, node: str) -> str | None:
        return next((s.id for s in self.stages if node in s.nodes), None)

    def validate(self) -> list[str]:
        """Return a list of problems; empty means consistent."""
        problems: list[str] = []
        covered = sorted({n for s in self.stages for n in s.steps})
        missing = [n for n in ONBOARDING_STEPS if n not in covered]
        if missing:
            problems.append(f"onboarding steps not covered by any stage: {missing}")
        for s in self.stages:
            for r in (s.raises, *s.approves):
                if r not in self.roles:
                    problems.append(f"stage {s.id}: unknown role {r!r}")
        for row in self.raci:
            cells = [row.get(r, "") for r in self.roles]
            accountable = [c for c in cells if c in ("A", "R/A")]
            if len(accountable) != 1:
                problems.append(f"RACI row {row['name']!r}: needs exactly one A, has {len(accountable)}")
        return problems
