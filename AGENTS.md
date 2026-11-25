# Repository guide

## Commands

- Install/sync: `uv sync --extra dev`
- Lint: `uv run ruff check .`
- Type-check: `uv run ty check`
- Tests: `uv run pytest -q`
- Offline policy/evaluation scenarios: `uv run python evals/run_evals.py --out .m0-eval-report.json`
- End-to-end bootstrap (Windows PowerShell): `$env:PYTHONIOENCODING = "utf-8"; uv run python scripts/e2e.py`

## Layout

- `app/harness/`: workflow, adapters, deterministic policy and bootstrap CLI.
- `policy/`: risk tiers, routing, RACI, residency, and input-guard configuration.
- `evals/`: golden/adversarial tasks and the offline runner.
- `agent-template/`: generated agent repository.
- `deployment/terraform/`: cloud platform provisioning notes and platform contracts.
- `docs/ROADMAP.md`: backlog, decisions, acceptance criteria, and work log.

## Invariants

- Use Australian English spelling in repository prose, comments and project-owned identifiers. Preserve externally defined names and wire formats.
- The merge gate is deterministic and never calls an LLM. Use Google ADK only; do not add another agent framework.
- Never weaken a gate, approval, threshold, baseline, or golden task to make a test pass.
- Changes under `policy/` or `app/harness/nodes/` require a new or updated adversarial/golden eval.
- Prompts and skills are behaviour-changing inputs: preserve approved provenance and revisions, review changes, and add behaviour evals. Prompts are not authorisation; enforce tool permissions and side-effect checks in code/platform IAM.
- Do not place secrets, credentials, full issue bodies, or sensitive tool payloads in source, traces, or audit records. Use the GitHub App and Workload Identity Federation, never personal tokens.
- Every change is a reviewed PR; do not assume console-only changes. Keep residency and egress restrictions intact.
- If a `TODO(<owner>)` blocks a decision, do not invent the owner's answer. Record the dependency and ask the appropriate role or owner.
- Update directly related docs and run the commands above. Keep generated agents' instructions in `agent-template/AGENTS.md`, not here.
