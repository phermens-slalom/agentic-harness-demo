# Getting started

How to install the harness, run its checks, and try the bootstrap. Commands come from the
[README](../README.md) and [`AGENTS.md`](../AGENTS.md).

## What you need

| Tool | Why | Notes |
|---|---|---|
| Python 3.11, 3.12 or 3.13 | Runs the harness | The repo pins 3.13 locally (`.python-version`). It needs `<3.14`. |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | Installs packages and runs `agents-cli` | |
| Node.js | Needed by `agents-cli` setup | |
| [`agents-cli`](https://github.com/google/agents-cli) | Used by generated agents for lint, evals and deploy | `uvx --python 3.13 google-agents-cli setup` |

You only need `agents-cli` for generated agent repos. The harness itself needs Python and `uv`.

Cloud access is **not** needed to run the harness tests or the dry-run evals. Local runs can use an
AI Studio key. Cloud features need Google Cloud sign-in (`agents-cli login`).

## Set up

```bash
uv sync --extra dev
```

This installs the harness and the dev tools (`pytest`, `hypothesis`, `ruff`, `ty`, `codespell`, `sunglasses`).

## Check that everything works

Run these four. They are the same checks CI runs.

```bash
uv run ruff check .
uv run ty check
uv run pytest -q
uv run python evals/run_evals.py --out .m0-eval-report.json
```

| Command | What it proves |
|---|---|
| `ruff check .` | Style and common errors |
| `ty check` | Type hints are consistent |
| `pytest -q` | The code and the policy files behave |
| `run_evals.py` | The gate and workflow give the right answer on the golden tasks |

For a full end-to-end run (harness, then a new agent, then the agent's checks, then cleanup):

```bash
python scripts/e2e.py          # or: make e2e
python scripts/e2e.py --keep   # leave the generated agent in .e2e-work/ to look at
```

On Windows PowerShell, set UTF-8 first: `$env:PYTHONIOENCODING = "utf-8"; uv run python scripts/e2e.py`.
Live evals (`--live-evals`) need approved cloud credentials and `the configured evaluation-region variable`. Skip them unless you have both.

## Try the bootstrap

1. Copy the example spec and edit it.

```bash
cp spec.yaml.example spec.yaml
```

2. Fill in `name`, `division`, `owner`, `sponsor`, `classification` and `description`. Optionally set
   `location` (default `australia-southeast2`), `environments` and `egress_hosts` (exact host names only).

3. Run the three stages.

```bash
agentic-bootstrap plan spec.yaml
agentic-bootstrap new spec.yaml ./my-agent
agentic-bootstrap check ./my-agent
```

| Stage | What you get |
|---|---|
| `plan` | The illustrative three-stage plan for `workload-infrastructure`, as JSON. It does not write any Terraform. |
| `new` | A new agent repo in `./my-agent`, built from `agent-template/` |
| `check` | A table of findings. Exit code 1 if there are any. |

`check` does not look for secrets. CI uses Gitleaks for that.

After `new`, run `deactivate` (or open a new terminal) before working inside the new repo. Otherwise `uv`
prints a harmless warning that `VIRTUAL_ENV` does not match the project.

Inside the new repo, the template README has the next steps:

```bash
agents-cli install && agents-cli lint && uv run pytest
```

## Settings you may meet

| Setting | Meaning |
|---|---|
| `HARNESS_ENV=local` | Allows an AI Studio key for development. Anything else needs Vertex AI. |
| `GOOGLE_GENAI_USE_VERTEXAI=TRUE` | Use Vertex AI for the models |
| `GOOGLE_CLOUD_LOCATION` | Must be an allowed Australian region. Never `global`. |
| `HARNESS_MODEL_DEFAULT` | The model name. Override per role with `HARNESS_MODEL_TRIAGE`, `_PLANNER`, `_REVIEWER`. |
| `HARNESS_SKILLS_DIR` | Folder with a pinned pinned skills repository checkout. Only needed once skills are configured. |
| `GHAS_ENABLED=true` | Turns on CodeQL and dependency review in CI for private repos. Set only once GitHub Code Security is enabled. |

The ADK adapters need the extra: `pip install -e ".[adk]"`. They have only been tested with fakes. TODO: UNCONFIRMED
how to run them live; it needs an approved Google Cloud project.

## Where things are

| You want to... | Look in |
|---|---|
| Change who approves what | `policy/risk_tiers.yaml` (needs an eval, see [Contributing](CONTRIBUTING.md)) |
| Add or change an allowed region | `policy/residency.yaml` |
| See the gate's rules | `app/harness/nodes/merge_gate.py` |
| Add a test case for the gate | `evals/golden_tasks/` |
| Change what new agents start with | `agent-template/` |

Next: [Architecture](ARCHITECTURE.md), [Contributing](CONTRIBUTING.md), [FAQ](FAQ.md).
