# Architecture

A technical breakdown of the repo in three levels, in the style of the C4 model:

- **Level 1 (C1), System context:** the harness, the people and the outside systems it touches.
- **Level 2 (C2), Containers:** the main parts, one per top-level folder.
- **Level 3 (C3), Components:** what is inside each part.

There is no Level 4 (single files and functions). Read the code for that.

Each part is marked with its state:

| Mark | Meaning |
|---|---|
| **Working** | Built and tested. May use fakes in place of real systems. |
| **Stub** | A placeholder that does nothing real yet. |
| **Planned** | In the [roadmap](ROADMAP.md) only. Not in the code. |

New words are in the [Glossary](GLOSSARY.md). The big picture is in the [Vision](VISION.md).

---

## Technology at a glance

| Area | What is used |
|---|---|
| Language | Python. `requires-python >=3.11,<3.14`. Local default 3.13 (`.python-version`). CI tests 3.11, 3.12 and 3.13. |
| Packaging | `setuptools` (build), `uv` (installs and lock file), console script `agentic-bootstrap` |
| Runtime packages | `pyyaml>=6.0`, `pydantic>=2.12,<3` |
| Optional packages | `google-adk>=2.12,<3` (extra `adk`), `sunglasses==0.6.20` (extra `guard`) |
| Dev packages | `pytest`, `hypothesis`, `ruff`, `ty`, `codespell`, plus `sunglasses` |
| Agent framework | Google ADK only |
| Models | Gemini through Vertex AI (AI Studio only for local use) |
| Builder | GitHub Copilot coding agent (default) |
| CI | GitHub Actions: lint, type check, tests, dry-run evals, Gitleaks, CodeQL, dependency review, zizmor |
| Infrastructure | Terraform; `workload-infrastructure` and `platform.tf` are illustrative, unconfirmed names |
| Config format | YAML files in `policy/`, checked by Pydantic models |

Language features the code relies on:

| Feature | Used for |
|---|---|
| `dataclass` (some `frozen=True`) | Plain data types (`Issue`, `Plan`, `BuildResult`, `GateResult` and others) |
| `typing.Protocol` | Ports. Real parts and fakes fit a port without sharing a base class. |
| `async` / `await`, `asyncio` | The workflow and the LLM and GitHub calls |
| `from __future__ import annotations` | Type hints in every module |
| `enum.Enum` | The gate's `Decision` values |
| Pydantic v2 (`strict=True`, `extra="forbid"`) | Rejects unknown or mistyped keys in every policy file |
| `re`, `fnmatch.fnmatchcase`, `hashlib`, `pathlib` | Diff scanning, case-insensitive path rules, skill fingerprints |
| `functools.lru_cache` | Loads the default capability policy once |
| `unittest.TestCase` run by `pytest`; `hypothesis` | Unit and property tests |

---

## C1: System context

Who and what the harness deals with.

```ascii
                         ┌─────────────────────────┐
 Application team ─────► │                         │ ─────► GitHub (issues, PRs, checks,
   (raise issues,        │ AGENTIC HARNESS DEMO    │        Copilot coding agent)
    approve PRs)         │                         │ ─────► Google Cloud
 `ai_governance` ──────► │ Decides whether a       │        Vertex AI / Gemini models
 `security`,             │ change can merge and    │        (regions in policy)
 `platform_team`,        │ who must approve        │ ─────► Generated agent repos
 `product_owner`,        │                         │        (from agent-template/)
 `architecture`          └─────────────────────────┘
                                  ▲       │
             policy files (YAML)  │       └────► Illustrative cloud-project plan
             reviewed by people ──┘              (`workload-infrastructure`, `platform.tf`)
```

| Actor or system | What it does with the harness | State |
|---|---|---|
| `app_team` (application team) | Fills in the spec, raises issues with an `agent:*` label, approves PRs | Working (as people) |
| `ai_governance` (AI governance team) | Approves agent PRs. Owns the template and the checklist. | Working (as people) |
| `security`, `platform_team`, `product_owner`, `architecture` | Approve the PRs that touch their files. The gate names them. | Working (as people) |
| GitHub | Holds the repos, runs CI, hosts the Copilot builder | **Planned** for the real client. Only a fake exists. The real client is blocked (R2). |
| Google Cloud / Vertex AI | Runs Gemini for triage, planning and review | Working with fakes. Not run live yet. |
| Generated agent repos | The output of bootstrap `new` | Working |
| `workload-infrastructure` repository | Illustrative name for a possible cloud-project repository; actual layout is unconfirmed | Plan only (`agentic-bootstrap plan`) |

The harness has no database, no web server and no queue today. It is a library and a command-line tool.

---

## C2: Containers (one per top-level folder)

```ascii
 ┌──────────────────────────────────────────────────────────────────────────┐
 │                                THE REPO                                  │
 │                                                                          │
 │   policy/  ◄────────────── read by ───────────────┐                      │
 │   YAML rules                                      │                      │
 │        ▲                                          │                      │
 │        │ checked by                               │                      │
 │   ┌────┴─────────────────────────────────┐   ┌────┴─────────┐            │
 │   │ app/harness/                         │   │ evals/       │            │
 │   │  workflow ─► nodes ─► adapters       │◄──│ golden tasks │            │
 │   │  bootstrap CLI                       │   │ + runner     │            │
 │   └───────┬───────────────┬──────────────┘   └──────────────┘            │
 │           │ renders       │ tested by                                    │
 │           ▼               ▼                                              │
 │   agent-template/       tests/          scripts/   .github/   sandbox/   │
 │   (becomes each        unit and        e2e run    harness    optional    │
 │    agent repo)         property        script     CI         builder     │
 │                                                                          │
 │   docs/   deployment/terraform/   skills/   (notes and guidance)         │
 └──────────────────────────────────────────────────────────────────────────┘
```

| Container | Is | Technology | State |
|---|---|---|---|
| `app/harness/` | The Python package with all the logic | Python, Pydantic, PyYAML, optional ADK and Sunglasses | Working |
| `policy/` | The rules, as data | YAML | Working. Several `TODO`s need owners. |
| `evals/` | Golden tasks and the runner | Python, YAML | Dry-run working. Live mode is a stub. |
| `agent-template/` | The starting repo for one agent | Python, ADK, `agents-cli`, YAML, GitHub Actions | Working as a starter |
| `tests/` | Tests for the harness | `pytest`, `unittest`, `hypothesis` | Working |
| `scripts/` | End-to-end script (`e2e.py`) with shell and PowerShell wrappers | Python standard library | Working |
| `.github/workflows/ci.yml` | The harness's own CI | GitHub Actions | Working |
| `deployment/terraform/` | A README on how the harness should be hosted | Markdown | Notes only. No Terraform files. |
| `sandbox/` | An optional builder container and runner | Docker (`node:22-slim`), shell | **Stub** |
| `skills/` | A note on skills | Markdown | Notes only |
| `docs/` | Documentation and the roadmap | Markdown | Working |
| `site/` | The static project site, published to GitHub Pages by `.github/workflows/pages.yml` | HTML, CSS, SVG, a little JavaScript | Working |

How they connect:

- `app/harness/` **reads** `policy/` on start. Every policy file is checked against a strict schema.
- `app/harness/` **renders** `agent-template/` when you run `agentic-bootstrap new`.
- `evals/` **runs** the workflow and the gate on saved tasks and scores the outcomes.
- `.github/workflows/ci.yml` **runs** lint, type check, tests and the dry-run evals on every PR.
- `tests/` and `evals/` both guard `policy/` and `app/harness/nodes/`. A change there needs an eval.

---

## C3: Components

### Inside `app/harness/`

```ascii
 ┌───────────────────────────────── app/harness/ ─────────────────────────────────────┐
 │                                                                                    │
 │  models.py   plain data types          ports.py   the slots (Protocols)            │
 │                                                                                    │
 │  workflow.py  IssueToMerge ────────────────────────────────────────────┐           │
 │     │                                                                  │           │
 │     ├─ nodes/          (no LLM, plain code)                            │           │
 │     │    input_guard.py      scan untrusted text                       │           │
 │     │    repo_context.py     read-only, capped repo context            │           │
 │     │    merge_gate.py ─┬─ tamper_check.py   (+ diff_parse.py)         │           │
 │     │                   └─ capability_check.py (+ diff_parse.py)       │           │
 │     │                                                                  │           │
 │     └─ adapters/       (real parts that fit the ports)                 │           │
 │          adk_agents.py        triage, plan, review (Gemini via ADK)    │           │
 │          copilot_builder.py   builder over GitHubPort                  │           │
 │          sunglasses_scanner.py, model_armor_scanner.py                 │           │
 │          composite_scanner.py   scanners behind InputScanner           │           │
 │          sandbox_builder.py   optional builder (stub)                  │           │
 │          fakes.py             scripted stand-ins for tests             │           │
 │                                                                        │           │
 │  policy.py  policy_validation.py  golden.py  residency.py  skills.py ◄─┘           │
 │     (load, validate and apply the YAML policy)                                     │
 │                                                                                    │
 │  bootstrap/   cli.py  spec.py  template.py  terraform_plan.py  security_harness.py |
 └────────────────────────────────────────────────────────────────────────────────────┘
```

#### Core

| Component | Does | State |
|---|---|---|
| `models.py` | Plain data types: `Issue`, `TriageResult`, `Plan`, `BuildResult`, `PRSnapshot`, `ReviewResult`, `ScanVerdict`, `TaskOutcome`, `TraceEvent`, the `Decision` enum and the `AdapterError` family | Working |
| `ports.py` | The interfaces: `Triager`, `Planner`, `Builder`, `Reviewer`, `HumanGate`, `InputScanner`, `GitHubPort` (assign to Copilot, comment, wait for checks, read a file, list files) | Working |
| `workflow.py` | `IssueToMerge`: runs the loop and records a trace. Escalates on any adapter or residency error. | Working with fakes |

#### The loop, step by step

```ascii
 issue ─► 1 route ─► 1b input guard ─► 1c config checks ─► 2 triage
        (no agent:* label = ignored)   (issue text)         (model, skill notes in the trace)
                                                                   │
   ┌───────────────────────────────────────────────────────────────┘
   ▼
 3 repo context (guarded) ─► plan ─► plan approval (people, by rule)
                                            │
   ┌────────────────────────────────────────┘
   ▼
 4 build loop (up to 4 rounds)
      builder ─► PR ─► checks
        ├─ checks failed ─► guard the feedback ─► build again
        └─ checks passed
                    │
   ┌────────────────┘
   ▼ 
 5 review (repo context, review checklist)
        ├─ not approved and rounds left ─► build again
        └─► 6 MERGE GATE ─► decision ─► human notified if needed
```

The loop stops at **4 build rounds** and **400,000 tokens** (from `policy/routing.yaml`). Hitting either escalates.

#### Nodes (plain code, never an LLM)

| Component | Does | State |
|---|---|---|
| `nodes/merge_gate.py` | Applies the rules in order (below) and returns a decision, a tier, a reason and the approvers | Working |
| `nodes/tamper_check.py` | Finds signs of weakened tests or evals in the diff: deleted tests, added skips, fewer asserts, edited baselines, lowered thresholds, edited test config | Working |
| `nodes/capability_check.py` | Finds newly added models, hosts, regions, data stores, dependencies and tool or protocol links in the added lines. Adds approvers. | Working |
| `nodes/diff_parse.py` | Reads a unified diff safely by hunk counts | Working |
| `nodes/input_guard.py` | Scans untrusted text before an LLM sees it: issue, CI feedback, review findings, PR comments and repo context. Modes: `shadow` and `enforce`. Fails closed. | Working |
| `nodes/repo_context.py` | Builds capped, read-only context: `AGENTS.md`, file tree and named files. Refuses unsafe or denied paths. | Working |

The merge gate applies these rules in this order:

```text
 1. too many lines (over 400)             ─► reject_to_planning
 2. a required check failed or is missing ─► escalated
 3. CI not green                          ─► escalated
 4. tampering found in the diff           ─► escalated
 5. reviewer is the builder (lockout)     ─► escalated
 6. reviewer did not approve              ─► human_approval
 7. tier allows auto-merge, and no new capability found ─► auto_merge
 8. otherwise                             ─► human_approval (names the approvers)
```

New capabilities add approvers to the result and never turn a decision into a block.

#### Adapters (real parts behind the ports)

| Component | Does | State |
|---|---|---|
| `adapters/adk_agents.py` | The triager, planner and reviewer on ADK. Output is a Pydantic model through `output_schema`. One retry on a bad reply, then escalate. One reused runner per role. Registers `ModelArmorPlugin` on its ADK app. | Working with fakes. Not run against live Vertex or Model Armor. |
| `adapters/copilot_builder.py` | Assigns the issue to Copilot, sends feedback as comments, waits for checks. Passes the `agent-builder` custom agent. | Logic working. The real GitHub client does not exist (R2 is blocked). |
| `adapters/sunglasses_scanner.py` | The Sunglasses scanner behind `InputScanner`. Imported lazily. | Working |
| `adapters/model_armor_scanner.py` | The Model Armor scanner behind `InputScanner`. Regional endpoint, template from config. Needs the `armor` extra. | Working with a fixture. Not run live. |
| `adapters/composite_scanner.py` | Runs several scanners. Blocked if any blocks. A scanner that errors counts as a block. | Working |
| `adapters/sandbox_builder.py` | A builder that would run a Cloud Run Job | **Stub** (raises `NotImplementedError`) |
| `adapters/fakes.py` | Scripted stand-ins, including a fake GitHub | Working |

#### Policy loading and checks

| Component | Does | State |
|---|---|---|
| `policy.py` | `RiskPolicy` (tiers, approvers, checks, phases), `CapabilityPolicy`, `RepoContextLimits`, `Routing`, the review checklist. Case-insensitive path matching. | Working |
| `policy_validation.py` | Strict Pydantic schemas for every file in `policy/`, plus cross-file checks (roles exist, checks exist as template jobs, regions fit residency, skills are pinned) | Working |
| `golden.py` | Loads the golden workflow and RACI. Checks that all 13 steps are covered and each row has one accountable owner. | Working |
| `residency.py` | Allows only listed locations. Checks the model backend and fails closed. | Working |
| `skills.py` | Loads a skill only if routing names it and the lock pins its fingerprint | Working. The lock is empty. |

#### Bootstrap CLI (`bootstrap/`)

```ascii
 spec.yaml ─► spec.py (validate) ─┬─► new   ─► template.py ─► a new agent repo
                                  ├─► check ─► security_harness.py ─► findings (exit 1)
                                  └─► plan  ─► terraform_plan.py ─► three ordered PRs (JSON)
```

| Component | Does | State |
|---|---|---|
| `cli.py` | The `agentic-bootstrap` command with `new`, `check` and `plan` | Working |
| `spec.py` | Reads and checks the spec: slug names, allowed location, exact egress hosts | Working |
| `template.py` | Copies `agent-template/`, fills in the names, and writes the Copilot firewall list from the egress hosts | Working |
| `security_harness.py` | harness-specific checks: required files, no other agent framework, no global location. Copied into each agent repo. | Working |
| `terraform_plan.py` | Lists the three ordered PRs for `workload-infrastructure` repository with their approvers | Plan only. Folder layout is an assumption (Q12). |

### Inside `policy/`

| File | Holds |
|---|---|
| `golden_workflow.yaml` | The eight stages, which of the 13 steps each covers, who raises and approves |
| `raci.yaml` | The six roles and who does what |
| `risk_tiers.yaml` | The phase, the plan-approval rule, the path rules and their tiers, required checks, size limits |
| `routing.yaml` | Label to workflow, build and token limits, repo-context caps and deny list, skills per role |
| `residency.yaml` | Allowed locations and known gaps |
| `review_checklist.yaml` | The nine items the reviewer applies |
| `input_guard.yaml` | On or off, mode, and which text is scanned |
| `capabilities.yaml` | Allowlists and approver roles for the new-capability detectors |
| `skills.lock.yaml` | The pinned skill version and fingerprints (empty) |

### Inside `evals/`

```ascii
 evals/golden_tasks/*.yaml ─► run_evals.py ─► builds the workflow with fakes
                                           ─► runs each task
                                           ─► scores it ─► JSON report + pass/fail
```

| Component | Does | State |
|---|---|---|
| `golden_tasks/example_tasks.yaml` | Ordinary cases | Working |
| `golden_tasks/adversarial_tasks.yaml` | Attack and look-alike cases. `expected` is always the safe outcome. | Working |
| `run_evals.py` | Runs tasks and scores them. Mode `dry-run` works; mode `live` exits with a stub message. | Dry-run working |

The run passes only if these hold: decision, tier and approver accuracy at least 0.9; injection detection 1.0
(when present); guard false positives 0.0; adversarial auto-merges 0. An open known gap is reported but not scored.

### Inside `agent-template/` (becomes a generated agent)

```ascii
 agent repo
 ├─ agent/         agent.py (ADK root agent) · prompts.py · tools.py · config.py
 │                 telemetry.py (redacted tool diagnostics) · data/ · skills/ (one pinned skill)
 │                 harness_bootstrap.py (the harness policy check, so CI can run it)
 ├─ tests/         unit tests (no cloud needed) · eval/ (two starter eval cases)
 ├─ evals/         golden_set.yaml · thresholds.yaml · baseline/ · holdout/ (README only)
 ├─ docs/          mission-brief.md · runbook.md · copilot-agent-environment.md
 ├─ .github/       CODEOWNERS · copilot-instructions.md · PR template
 │                 agents/agent-builder.agent.md
 │                 workflows/ agent-checks.yml · copilot-setup-steps.yml
 ├─ AGENTS.md      rules for the coding agent
 └─ pyproject.toml · agents-cli-manifest.yaml (target: agent_runtime)
```

| Component | Does | State |
|---|---|---|
| `agent/agent.py` | The ADK root agent with two read-only example tools | Working (example content) |
| `agent/tools.py` | `get_service_history` and `estimate_repair` on sample data. No write tools. | Working (placeholder data) |
| `agent/telemetry.py` | Wraps each tool to log its name, outcome and timing. No prompts or arguments. | Working |
| `agent/skills/garage-summary/` | One example skill, pinned by fingerprint. Guidance only. | Working |
| `.github/workflows/agent-checks.yml` | Preflight scans before dependent jobs; jobs include `lint`, `tests`, `coverage`, `quality`, `evals_no_regression`, `secret_scan`, `codeql`, `dependency_review`, `zizmor`. Only `evals_no_regression` can get cloud identity. | Coverage enforces 80%; `evals_no_regression` is a **stub** that fails until wired (E3). Workflow protection is needed to prevent PRs bypassing preflight. |
| `.github/workflows/copilot-setup-steps.yml` | Prepares Copilot's environment with pinned actions | Working |
| `evals/` | Example cases, starter pass marks, baseline | 80% starter marks; baseline requires AI Governance approval |

### Harness CI (`.github/workflows/ci.yml`)

| Job | Does |
|---|---|
| `test-and-eval` (Python 3.11, 3.12, 3.13) | `ruff check`, `ty check`, `pytest`, dry-run evals, uploads the report |
| `secret_scan` | Gitleaks v8.30.1 over the PR commits |
| `codeql`, `dependency_review` | Run on public repos or when `GHAS_ENABLED=true` |
| `zizmor` | Checks the workflow files |

---

## Data and trust

```text
 untrusted:  issue text · CI output · repo files · model output (file names, plans)
 checked by: input guard · path checks · size caps · schema parsing · the gate
 trusted:    policy files (changed only by reviewed PRs) · the gate code
```

- The gate never reads a model's opinion as proof. It uses paths, diffs and check results.
- Traces and logs hold names, counts and sizes. They never hold file content, secrets or full issue bodies.
- Model calls go to Vertex AI in an allowed Australian region. AI Studio keys are for local use only.

## Planned, not built

These appear in the roadmap and in comments, but not as working code.

| Item | Roadmap code |
|---|---|
| Real GitHub client on a GitHub App | R2 (blocked) |
| Gate published as a required check; generated CODEOWNERS and ruleset | R1 |
| Durable ADK 2.0 workflow with saved sessions | R3 |
| Webhook receiver and queue | R4 |
| Kill switch and budgets | R5 |
| Reviewer sees the diff | R7 |
| Traces to Cloud Trace and an audit log in BigQuery | O1 |
| Live evals, holdout runner, real `evals_no_regression` | E1, E3 |
| Template based on existing reference agent template | W2 (blocked) |
| Where the harness runs (Cloud Run, Cloud SQL) | D-05, still a proposal |
