# Vision

A short summary of what this repo is for, what is in each folder, and where it is heading.
New words are explained in the [Glossary](GLOSSARY.md).

## The idea in one paragraph

This repo is the **harness** and the **delivery process** for a **multi-agent system**: a full software system
with a complex multi-agent core, built and run on a cloud platform, not a place for small experimental agents.
The **harness** is the software controls: the rules, checks and approvals that let an AI coding agent do the build
work safely. The **delivery process** guides different people, including product managers, from idea to
production in lanes (prototype, verify, then harden), each with exit requirements the harness enforces.
Humans stay accountable. The harness decides, with plain code and no AI, whether a change can merge and who must
approve it. See [Delivery process](DELIVERY.md) and [Personas](PERSONAS.md).

**Maturity.** This design comes from theory, documentation and experience. It has **not** yet been tested on
real work or deployed. Today the code runs against fakes. The security team members and the escalation process
are unknown (Q19). The lanes are a proposal that still needs an owner (Q20).

## The problem it solves

| Without the harness | With the harness |
|---|---|
| Each team invents its own path to production. | One standard path: the **golden workflow** (eight stages). |
| An AI builder could change its own tests, rules or permissions. | Files that control the gate are always high risk and need people. |
| Missing evidence can look like a pass. | Missing evidence is a stop (**fail closed**). |
| Approvers are chosen by hand. | The gate works out who must approve from the files changed. |
| Data might leave Australia. | Only Australian regions are allowed. |

## The overall picture

Two layers. The delivery process is what a person moves through. The harness is what checks each step. The
delivery process is a proposal; the harness is built, with fakes.

```ascii
 DELIVERY PROCESS (proposed, see DELIVERY.md), run by an external process orchestrator (proposed, D-17)

   idea ─► PROTOTYPE ─► VERIFY ─► HARDEN ─► OPERATE
           demo-ready   MVP-ready

   people come in by orchestrator, issue form or CLI:
   product manager, application engineer, AI governance, security, platform, architecture
                  │
                  │  asks the harness: "does this lane's exit pass?"  "what tier, who approves?"
                  ▼
 HARNESS (this repo: the controls, which stay as they are)
 ---------------------------------------------------------------------------------------------------
 teams using this harness                    THIS REPO                                  GitHub and Google Cloud
 ------------------------                    ---------                                  -----------------------

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

The target is a system of several agents that work together, not one small agent. Today `agent-template/`
generates a single starter agent. A multi-agent template variant is planned (DP4 in the [Roadmap](ROADMAP.md)).

The eight stages of the golden workflow, the lane each belongs to, and what the harness automates today:

| Stage | Lane | What the harness automates today |
|---|---|---|
| frame | Prototype | Request form and offline draft parser (I1). No intake agent yet. |
| register | Harden | Nothing. Identity and support records are manual. |
| provision | Harden | `plan` lists the ordered cloud-project PRs. It writes no Terraform. |
| connect | Harden | The spec holds exact egress hosts. The tfvars PR is not built. |
| build | Prototype (sandbox) and Verify | Template and builder, against fakes. |
| verify | Verify | Required checks, review checklist and merge gate, against fakes. |
| release | Harden | Nothing. The review pack is planned (W3). |
| operate | Operate | Nothing. Monitoring is planned. |

The harness covers **build** and **verify** in code. The bootstrap helps with the early stages
(it makes the repo and lists the cloud PRs). The other stages are still manual.

## Platform scope

This is a full software system, so the offering is wider than one agent's code. It has to account for:

| Area | What it covers | Where it stands |
|---|---|---|
| Google services | Agent Development Kit (ADK), Vertex AI models and Model Armor in allowed Australian regions, Cloud Run, Cloud SQL, Cloud Tasks, Cloud Trace and BigQuery as the planned runtime, trace and audit services | ADK adapters and Model Armor are built (Model Armor against a fixture only). The hosted runtime is proposed (D-05 to D-07) |
| Integrations | A curated connector library so agents reach other systems only through reviewed connectors (D-14, I2), and an optional agent-to-agent protocol for a multi-agent core. How agents are invoked at runtime is open (Q22). | Not built (I2, DP4, DP11) |
| Orchestration | An external process orchestrator that holds each idea-to-production journey as a long-running case, routes human tasks and is the UI for non-engineers. The harness supplies deterministic evidence and decisions; GitHub enforces merges. | Proposed (D-17). Not built. Q21 is open. |
| Identity | A GitHub App and Workload Identity Federation for the harness, plus an identity and registry entry for each agent | Harness identity: R2 is blocked. Agent identity integration: not built (DP5, W4) |
| Adjacent technologies | The configuration database and support records, infrastructure as code, observability, secret and dependency scanning | Partly planned (W1, W4, O1). Scanning is built (S1) |

Product names stay generic in this repo. Whether other adjacent technologies are in scope is for the owner to say
(Q20).

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
| `site/` | A static project site (HTML, CSS, SVG) | A visual overview, published to GitHub Pages ([Site](tech/SITE.md)) |
| `.github/` | The harness's own CI, the Pages deploy and the `AgentRequest` issue form | Lint, format, spelling, type check, tests, evals and security scans on every PR |
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
  with fakes, the bootstrap `new` and `check`, the template, the `AgentRequest` form and offline parser (the hosted
  access lookup is I7), the dry-run evals and the CI.
- **Phase:** the policy ships at **phase 1**: a person reviews every agent PR. Moving to a later phase
  needs agreed criteria. The roadmap has a draft (O3, not built yet); owner assignment remains unresolved (Q10).
- **Plan only:** bootstrap `plan` lists the cloud-project PRs. It does not write the Terraform.
- **Blocked:** the real GitHub client (R2). GitHub's Copilot assignment API needs a kind of token that the
  "no personal tokens, installation token only" rule does not cover. The security team must decide.
  Several later items wait on it.
- **Not built:** live evals, real traces and audit log, durable workflow and webhook ingress,
  the optional sandbox, and the later golden-workflow stages. Model Armor is wired in but has not been run live.

## What this repo is not

- Not the agents themselves. Those live in the repos it generates.
- Not a replacement for people. Humans approve; the harness only decides what needs approval.
- Not a second agent framework. ADK only.
- Not a deployment tool. Deployment is gated and needs explicit human approval.

## Where to go next

- Words you do not know: [Glossary](GLOSSARY.md)
- How a person takes an idea to production: [Delivery process](DELIVERY.md) and [Personas](PERSONAS.md)
- How it is built: [Architecture](ARCHITECTURE.md)
- How it could be used: [Examples](EXAMPLES.md)
- Why choices were made: [Decisions](DECISIONS.md)
- What is still unknown: [Open questions](OPEN_QUESTIONS.md)
