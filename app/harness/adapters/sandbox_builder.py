"""OPTIONAL Builder: an ephemeral Cloud Run Job running a headless coding agent.

Not the default (see copilot_builder.py). Keep it only if a team cannot use Copilot or
needs a fully isolated build; not implemented. Shape of the implementation:
  1. Mint a short-lived GitHub App installation token scoped to the one repo.
  2. Launch the `sandbox/` image as a Cloud Run Job execution with env:
     ISSUE, PLAN, FEEDBACK, BRANCH, and the token via Secret Manager.
     No standing credentials; egress limited to exact hosts (GitHub, package mirrors,
     Gemini) via Agent Gateway/Registry; region from policy/residency.yaml.
  3. The job runs the coding agent headless (Gemini CLI under an approved Code Assist
     Enterprise licence, or Antigravity CLI), commits, pushes, opens/updates the PR.
  4. Poll the PR's check runs until complete; return BuildResult.
"""

from __future__ import annotations

from ..models import BuildResult, Issue, Plan


class CloudRunJobBuilder:
    def __init__(self, project: str, region: str, job_name: str = "harness-sandbox"):
        self.project, self.region, self.job_name = project, region, job_name

    async def build(self, issue: Issue, plan: Plan, feedback: str | None) -> BuildResult:
        raise NotImplementedError("optional adapter, not implemented: see module docstring")
