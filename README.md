# Agentic Harness Demo

The golden workflow for taking an agent live on a cloud platform, as code: policy and role assignments as adaptable data,
a deterministic merge gate, an issue-to-merge loop for the Build and Verify stages, a staged
bootstrap CLI, and evals that gate changes to the harness itself.
Humans stay accountable; `policy/raci.yaml` is an illustrative, adaptable starting point for roles and responsibilities. See `docs/ALIGNMENT_V4.md`
for what changed from the first skeleton and what is still open.

```ascii
frame ▸ register ▸ provision ▸ connect ▸ build ▸ verify ▸ release ▸ operate     (policy/golden_workflow.yaml)
                                          └─ issue ▸ route ▸ triage ▸ plan(+HITL) ▸ Copilot build loop
                                             ▸ review checklist ▸ merge gate ▸ required approvers
```

## Documentation

Start at the [documentation index](docs/README.md): [Vision](docs/VISION.md), [Architecture](docs/ARCHITECTURE.md),
[Examples](docs/EXAMPLES.md), [Glossary](docs/GLOSSARY.md), [Getting started](docs/GETTING_STARTED.md),
[Contributing](docs/CONTRIBUTING.md), [Security](docs/SECURITY.md), [Decisions](docs/DECISIONS.md),
[Open questions](docs/OPEN_QUESTIONS.md), [FAQ](docs/FAQ.md) and [Changelog](docs/CHANGELOG.md).
A visual overview lives in [`site/`](site/) and deploys to GitHub Pages; see [Project site](docs/SITE.md).

## Layout

| Path | What it is | Status |
| --- | --- | --- |
| `policy/` | `golden_workflow`, `raci`, `risk_tiers` (phases, approvers, required checks), `routing`, `residency`, `review_checklist`, `capabilities` (allowlists for new-capability detectors) | Working; confirm TODOs |
| `app/harness/golden.py` | Loads and validates stages and RACI (13 steps covered, one A per row) | Working, tested |
| `app/harness/workflow.py` | Build/Verify graph; trace events carry the stage id | Working, tested |
| `app/harness/nodes/merge_gate.py` | Deterministic; phase-flagged auto-merge, path-derived approvers, required checks | Working, tested |
| `app/harness/nodes/capability_check.py` | Deterministic detectors for new models, hosts, regions, data stores, dependencies and tool/protocol integrations; they add approvers, never approve or block | Working, tested |
| `app/harness/adapters/model_armor_scanner.py`, `composite_scanner.py` | Model Armor (primary) and Sunglasses scanners behind the input guard; blocked if either blocks | Tested with a fixture; not run live |
| `app/harness/residency.py` | Fails closed on `global` or non-Australian locations | Working, tested |
| `app/harness/bootstrap/` | `agentic-bootstrap new / check / plan` (template, security harness, Terraform PR plan) | Stages 1-2 working, 3 plan only |
| `app/harness/adapters/copilot_builder.py` | Default builder over a `GitHubPort` | Logic tested; GitHub client to write |
| `app/harness/adapters/adk_agents.py` | ADK + Gemini triage/plan/review: Pydantic `output_schema`, one retry then escalate, reused runner, residency fail-closed | Tested with fakes; live run needs Vertex |
| `app/harness/nodes/repo_context.py`, `app/harness/skills.py` | Read-only, capped, guard-scanned repo context; skills only from a pinned revision (`policy/skills.lock.yaml`) | Working, tested |
| `app/harness/adapters/sandbox_builder.py`, `sandbox/` | Optional Cloud Run Job builder | Stub, non-default |
| `agent-template/` | Source for stage 1 and what each agent repo receives | Starter |
| `evals/` | Golden tasks, runner, metrics (decision, tier, approver accuracy) | Dry-run working |
| `site/` | Static project site for GitHub Pages (no build step); published by `.github/workflows/pages.yml` | Working |

## Prerequisites

Required for the harness and for generated agent repos (their `lint`, `evals_no_regression` checks and `AGENTS.md` commands call `agents-cli`):

| Tool | Why | Install |
| --- | --- | --- |
| Python 3.11+ | harness and agents | python.org |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | runs/installs `agents-cli` | Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| Node.js | needed by `agents-cli` setup | nodejs.org |
| [`agents-cli`](https://github.com/google/agents-cli) (`google-agents-cli` on PyPI) | lint, evals, scaffold, deploy | `uvx --python 3.13 google-agents-cli setup` |

`uvx` runs the CLI without putting `agents-cli` on your PATH. To get the bare `agents-cli` command used throughout this repo, open a new terminal after `setup` and run `agents-cli --version`; if it is still not found, run `uv tool install --python 3.13 google-agents-cli` (check with `agents-cli info`). **Python pin:** the harness and generated agents ship a `.python-version` (3.13) and `requires-python <3.14`, so `uv sync` / `agents-cli install` use 3.13 instead of the newest installed Python.

**Windows note:** pin Python to 3.13 as above (3.12 also works). With a very new Python (e.g. 3.15) uv may have no prebuilt PyYAML wheel, tries to compile it, and fails with "Microsoft Visual C++ 14.0 or greater is required".

Local runs and evals can use an AI Studio key; deployment and cloud features need Google Cloud auth (`agents-cli login`).

## Run it

1. Copy `spec.yaml.example` to `spec.yaml` first: `cp spec.yaml.example spec.yaml`
2. Edit the fields: name, division, owner, sponsor, classification, description, and optionally location (default `australia-southeast2`), environments, egress_hosts (exact hostnames).
3. Then run the scripts below:

```bash
pip install -e ".[dev]"
pytest                                   # policy, gate, workflow, golden, bootstrap, builder
python evals/run_evals.py                # dry-run evals + metrics
agentic-bootstrap plan spec.yaml             # illustrative workload-infrastructure plan
agentic-bootstrap new spec.yaml ./my-agent   # render agent repo from agent-template/
agentic-bootstrap check ./my-agent           # harness policy checks (exit 1 on findings)
```

`agentic-bootstrap check` validates harness-specific framework, residency, and required-file rules; it does not
detect secrets. CI runs Gitleaks for secret detection. CodeQL and pull-request dependency review run
on public repositories or when `GHAS_ENABLED=true` is set after enabling GitHub Code Security.
Dependency review also requires the dependency graph to be enabled. Gitleaks CLI
v8.30.1 is installed from its official release using a verified SHA-256 digest; GitHub secret scanning and push protection remain an open licensing question (GHAS, Q11).

> NOTE: The generated agent has its own environment. Run `deactivate` (or open a new terminal) after `agentic-bootstrap`, then `cd my-agent` for the `agents-cli` commands. Staying in the harness venv causes uv's harmless "`VIRTUAL_ENV` does not match the project environment path" warning.

## Next steps

The full backlog, decisions and per-task Claude Code prompts live in [`docs/ROADMAP.md`](docs/ROADMAP.md).
The list below is the short version.

1. Walk `policy/` with the security and platform teams; resolve the `TODO`s (privileged YAML paths, role-to-team mappings).
2. Resolve the R2 auth blocker with security team: GitHub's Copilot issue-assignment API currently requires a GitHub App user-to-server token, not the installation token required by this harness. Then implement the `GitHubPort`; see [`docs/ROADMAP.md`](docs/ROADMAP.md#r2-real-githubport-on-the-github-app-copilot-aware).
3. Install `.[adk]`, set `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_LOCATION=australia-southeast2`, `HARNESS_MODEL_DEFAULT`, `HARNESS_SKILLS_DIR` (pinned skills repository); exercise the adapters in `adk web`.
4. Wire `agents-cli eval run` / `eval compare` into `agent-template/.github/workflows/agent-checks.yml`; replace golden tasks with closed PRs from representative repositories.
5. Stage 3: generate HCL from designs against the cloud platform module. Port to an ADK 2.0 Workflow (`docs/ADK_PORT.md`).

## Ground rules

- The merge gate never calls an LLM.
- Every prompt, model, skill or policy change goes through `evals/` before merge.
- Every change is a PR; no console changes. No personal tokens: GitHub App + Workload Identity Federation only.
- Google ADK is the only agent framework.
