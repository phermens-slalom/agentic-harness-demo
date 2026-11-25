"""Stage 3 (plan only): the three ordered PRs that provision an agent's project in
workload-infrastructure, with the approvers each needs. Generating the HCL is the later part
of this stage; Terraform construction is still manual today.

ASSUMPTION: the folder layout under workload-infrastructure is `<division>/<agent>/...`.
This is an illustrative repository name and layout; confirm both before relying on the plan.
The example policy requires AI governance approval for every file; other approvers come from
policy/risk_tiers.yaml.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..policy import RiskPolicy
from .spec import AgentSpec

REPO = "workload-infrastructure"


@dataclass
class PRPlan:
    order: int
    title: str
    repo: str
    files: list[str]
    approvers: list[str]


def plan_prs(spec: AgentSpec, policy: RiskPolicy | None = None) -> list[PRPlan]:
    policy = policy or RiskPolicy.load()
    base = f"{spec.division}/{spec.name}"
    egress = [f"{base}/egress.tfvars"] if spec.egress_hosts else []
    steps = [
        ("Workload", [f"{base}/workload.tf"]),
        ("Environments", [f"{base}/env.tf"]),
        (
            "Project and agent platform (pin the platform module version)",
            [f"{base}/project.tf", f"{base}/platform.tf", *egress],
        ),
    ]
    return [
        PRPlan(i, title, REPO, files, policy.approvers_for_change(files, base=["ai_governance"]))
        for i, (title, files) in enumerate(steps, 1)
    ]
