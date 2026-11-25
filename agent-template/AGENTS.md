# Agent guide for __AGENT_NAME__ (__DIVISION__)

Read by the coding agent (Copilot) on every task. Keep it short and accurate.

## Commands
- Install: `agents-cli install`
- Lint: `agents-cli lint`
- Test (local, no cloud credentials): `uv run pytest`
- Evals: follow [the eval guide](evals/README.md) for the approved live run; do not regress against the accepted baseline.

## Conventions
- Google ADK is the only agent framework. Do not add another.
- Keep PRs under ~150 changed lines; split otherwise.
- Every bug fix includes a regression test; behaviour changes include an eval case.
- Never edit: generated code, `evals/baseline/`.

## Boundaries
- Do not change `.github/` (workflows, CODEOWNERS), `*.tf`, `*.tfvars`, or IAM/access-management files unless the issue explicitly asks.
- Do not add egress hosts, models, regions or data stores; those need AI governance team and Security approval.
- Use only policy-approved regions; never a `global` endpoint.
- Never loosen Model Armor settings.
- Do not add dependencies without saying so in the PR description.

## Layout
- `agent/`: ADK agent. Tools in `tools.py` must be typed, documented and unit-tested.
- `evals/`: golden set and thresholds. Add a case for every behaviour change.
- `docs/`: update `runbook.md` when behaviour or dependencies change.
