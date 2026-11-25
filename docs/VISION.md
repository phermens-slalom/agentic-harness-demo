# Vision

A short summary of what this repo is for, what is in each folder, and where it is heading.
New words are explained in the [Glossary](GLOSSARY.md).

## The idea in one paragraph

Teams use this harness to build AI agents for deployment on a cloud platform.
This repo is the **harness**: the rules, checks and approvals that let an AI coding agent do the build
work safely. Humans stay accountable. The harness decides, with plain code and no AI, whether a change can
merge and who must approve it.

## The problem it solves

| Without the harness | With the harness |
|---|---|
| Each team invents its own path to production. | One standard path: the **golden workflow** (eight stages). |
| An AI builder could change its own tests, rules or permissions. | Files that control the gate are always high risk and need people. |
| Missing evidence can look like a pass. | Missing evidence is a stop (**fail closed**). |
| Approvers are chosen by hand. | The gate works out who must approve from the files changed. |
| Data might leave Australia. | Only Australian regions are allowed. |

## The overall picture

```
 teams using this harness                    THIS REPO (the harness)                        GitHub and Google Cloud
 ---------                    -----------------------                        -----------------------

 write a spec  ───────►  1. BOOTSTRAP  (agentic-bootstrap)
 (spec.yaml)                new   → makes an agent repo from agent-template/
                            check → harness policy checks
                            plan  → lists the ordered cloud-project PRs
                                         │
                                         ▼
 raise a GitHub  ─────►  2. ISSUE-TO-MERGE LOOP  (workflow)
 issue                      route → guard → triage → plan (+ human) ─►  Copilot builds a PR
                            ◄── CI feedback ◄── required checks ◄────   (GitHub Actions)
                            review (review checklist)
                                         │
                                         ▼
                         3. MERGE GATE  (plain code, no AI)
                            tier + checks + tamper + new capabilities
                                         │
              ┌───────────────┬──────────┴──────────┬───────────────┐
              ▼               ▼                     ▼               ▼
         auto_merge    human_approval        reject_to_planning   escalated
        (tier 1 only,   (named roles                (too big)     (a person
         phase 3-4)      must approve)                             looks)

 All of it is steered by  policy/  (YAML files, reviewed by people)
 and tested by            evals/   (golden tasks the harness must get right)
```

The eight stages of the golden workflow are:

```
frame ▸ register ▸ provision ▸ connect ▸ build ▸ verify ▸ release ▸ operate
                                           └──────┬──────┘
                                       the part the harness automates today
```

The harness covers **build** and **verify** in code. The bootstrap helps with the early stages
(it makes the repo and lists the cloud PRs). The other stages are still manual.

## What each top-level folder holds

| Folder or file | Holds | Why it exists |
|---|---|---|
| `app/harness/` | The Python code: workflow, merge gate, detectors, adapters, bootstrap CLI | Runs the issue-to-merge loop and the bootstrap |
| `policy/` | YAML rules: stages, roles, risk tiers, routing, regions, checklist, guard, allowlists, skills lock | The rules live as data so people can review them |
| `evals/` | Golden tasks and the runner | Proves the harness still behaves correctly when anything changes |
| `agent-template/` | The starting repo for a new agent | Every agent starts with the same safe setup |
| `tests/` | Unit and property tests | Checks the code and the policy files |
| `deployment/terraform/` | Notes on how the harness is hosted | Cloud setup follows the same reviewed-PR rule |
| `sandbox/` | A stub for an optional container builder | A possible fallback, not the default |
| `skills/` | A note on where skills come from | Skills are pinned and reviewed |
| `scripts/` | The end-to-end script and wrappers | A quick check that everything works together |
| `docs/` | These documents and the roadmap | Explains the repo and tracks the work |
| `site/` | A static project site (HTML, CSS, SVG) | A visual overview, published to GitHub Pages ([Site](SITE.md)) |
| `.github/` | The harness's own CI | Lint, type check, tests, evals and security scans on every PR |
| `AGENTS.md`, `CLAUDE.md` | Rules for coding agents working on this repo | `CLAUDE.md` just imports `AGENTS.md` |
| `spec.yaml.example` | Example input for the bootstrap | Shows the fields a team fills in |
| `pyproject.toml`, `uv.lock`, `Makefile` | Packaging, locked versions, shortcuts | |

## How this lines up with the direction

These rules come from [`AGENTS.md`](../AGENTS.md) and the README's ground rules. Each folder serves them.

| Rule | Where it shows up |
|---|---|
| The merge gate never calls an LLM | `app/harness/nodes/merge_gate.py` |
| Google ADK is the only agent framework | The adapters, the template, and a check that rejects other frameworks |
| Never weaken a gate, threshold or golden task to pass a test | `evals/` and `AGENTS.md` |
| Policy and node changes need an eval | `policy/` and `evals/golden_tasks/` |
| Prompts and skills change behaviour, so pin and review them | `policy/skills.lock.yaml`, the harness-controls rule |
| No secrets in code or traces; GitHub App and WIF, no personal tokens | `deployment/terraform/README.md`, CI, trace design |
| Every change is a reviewed PR | The roadmap and the CI |
| Stay in Australian regions | `policy/residency.yaml`, `app/harness/residency.py` |

## Where things stand

The roadmap ([`ROADMAP.md`](ROADMAP.md)) is the source of truth. In short:

- **Working and tested:** the policy files and their checks, the merge gate, the tamper and
  new-capability detectors, the input guard, the issue-to-merge workflow with fakes, the ADK adapters
  with fakes, the bootstrap `new` and `check`, the template, the dry-run evals and the CI.
- **Phase:** the policy ships at **phase 1**: a person reviews every agent PR. Moving to a later phase
  needs agreed criteria. The roadmap has a draft (O3, not built yet); owner assignment remains unresolved (Q10).
- **Plan only:** bootstrap `plan` lists the cloud-project PRs. It does not write the Terraform.
- **Blocked:** the real GitHub client (R2). GitHub's Copilot assignment API needs a kind of token that the
  "no personal tokens, installation token only" rule does not cover. The security team must decide.
  Several later items wait on it.
- **Not built:** live evals, real traces and audit log, durable workflow and webhook ingress, Model Armor,
  the optional sandbox, and the later golden-workflow stages.

## What this repo is not

- Not the agents themselves. Those live in the repos it generates.
- Not a replacement for people. Humans approve; the harness only decides what needs approval.
- Not a second agent framework. ADK only.
- Not a deployment tool. Deployment is gated and needs explicit human approval.

## Where to go next

- Words you do not know: [Glossary](GLOSSARY.md)
- How it is built: [Architecture](ARCHITECTURE.md)
- How it could be used: [Examples](EXAMPLES.md)
- Why choices were made: [Decisions](DECISIONS.md)
- What is still unknown: [Open questions](OPEN_QUESTIONS.md)
