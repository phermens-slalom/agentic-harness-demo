# Delivery process

How a person takes an idea to a running agent, and how that relates to the harness in this repo.

Status: **a proposal**. The harness (the controls) is built and tested against fakes. The delivery process
(the lanes below) is a design. It has not been tested on real work and nothing in the code knows what a lane
is. Where something is not built, this page says so and gives the roadmap ID. New words are in the
[Glossary](GLOSSARY.md).

## Two layers

| | Harness | Delivery process |
|---|---|---|
| What it is | The software controls: merge gate, risk tiers, input guard, evals, detectors, residency, secret handling | The path a person follows from idea to production, in **lanes**, each with **exit requirements** |
| Who uses it | Nobody "uses" it. It runs on every change and decides. | Personas: product manager, application engineer, AI governance, security, platform and architecture ([Personas](PERSONAS.md)) |
| Entry point | Pull requests and the `agentic-bootstrap` CLI | Proposed: an external process orchestrator for non-engineers. The issue form and the CLI remain. See [Who runs the process](#who-runs-the-process). |
| Changes by | Reviewed PRs to `policy/` and `app/harness/` | Reviewed PRs to this page, then to policy once the owner agrees (D-16, Q20) |
| Status | Built, with fakes. Real GitHub client blocked (R2). | Design only |

The harness stays as it is. The delivery process sits on top and says *when* a piece of work may move on. The
harness is what *enforces* each exit, where an enforcing control exists.

## The lanes

Two working lanes, then hardening, then running it. Each lane has exit requirements. Work moves on when they
are met, not when time has passed.

```ascii
 idea
  │
  ▼
 PROTOTYPE ──exit──► VERIFY ──exit──► HARDEN ──exit──► OPERATE
 frame, build        build, verify    register, provision,   operate
 (sandbox)                            connect, release
 "demo-ready"        "MVP-ready"      security sign-off,
                     golden data set  runbooks, egress,
                     and evals pass   production approval

 Deterministic controls (input guard, merge gate, residency, secret handling) apply in every lane.
```

| Lane | Golden stages (`policy/golden_workflow.yaml`) | What agents do | Exit requirements |
|---|---|---|---|
| **Prototype** | frame, build (sandbox) | The intake agent (I3) asks questions and fills the Mission Brief. The builder generates from the template and runs against fake or synthetic connectors. | Mission Brief done; hypotheses written as eval criteria; golden data set drafted; demo runs in the sandbox (**demo-ready**) |
| **Verify** | build, verify | The builder iterates. The adversarial reviewer (D-15, E2) and the evals judge. | Golden data set and evals pass with no regression; coverage and quality met; review checklist clean; agents meet their success criteria in the intended non-production environment (**MVP-ready**) |
| **Harden** | register, provision, connect, release | Bootstrap `plan` PRs, identity, integrations, security review, release pack (W3) | Security sign-off; runbooks; egress approved; production approval |
| **Operate** | operate | Monitoring and the learning loop | None. Operating continues. |

Notes on the mapping:

- **Build appears in two lanes.** In Prototype it generates a first version in a sandbox against fake or
  synthetic data. In Verify the same builder iterates until the criteria are met.
- **Lead-time work can start early.** The `register` stage in `policy/golden_workflow.yaml` says to start identity
  alongside step 1 because it takes time. Lanes order the *exits*, not every activity. Naming the security
  reviewers (Q19) is another long lead-time item.
- **Every stage's existing approvers stay as they are** in `policy/golden_workflow.yaml` and
  `policy/risk_tiers.yaml`. This page does not change them.

### Demo-ready and MVP-ready

These are two different bars. Formal security work belongs at MVP, so **MVP-ready is what starts Harden**.

| | Demo-ready (the Prototype exit) | MVP-ready (the Verify exit) |
|---|---|---|
| Runs where | In the sandbox | In the intended non-production environment, not only locally |
| Data | Synthetic only | Synthetic or approved non-production data. Real or classified data, or a real system, needs security approval first. |
| Evidence | A recorded demo. The agent works through the main cases of the drafted golden data set, and the hypotheses are visible. | Golden data set and evals pass with no regression; coverage and quality met; review checklist clean; agents meet their success criteria |
| It is not | Secure, reviewed or connected to real systems | Production-ready. Security sign-off, runbooks, egress and production approval are still ahead in Harden. |

### What applies in every lane

The deterministic controls apply in **every** lane. A lane changes who must approve and what evidence is needed
to move on. It never switches a control off.

- **Input guard.** Untrusted text is scanned before any model reads it (S2).
- **Merge gate.** Plain code, no LLM, fails closed. Every change that reaches an agent repo is a PR and goes
  through it. A prototype that never opens a PR never meets the gate, so anything leaving the sandbox must
  leave as a PR.
- **Residency.** Allowed Australian regions only (`policy/residency.yaml`).
- **Secret handling.** No secrets, full issue bodies or sensitive tool payloads in source, traces or audit
  records. The GitHub App and Workload Identity Federation, never personal tokens. `secret_scan` is a required
  check.
- **Tier 3 files.** Policy, workflows, skills, prompts, agent steering files, Terraform, IAM config, production
  config and sensitive domains are tier 3 in any lane.

Today these controls run against fakes, because the real GitHub client is blocked (R2).

## Who runs the process

Three parts, each with one job. This is a proposal (D-17, owner unassigned, Built: No).

| Part | Job |
|---|---|
| **An external process orchestrator** | The intended home for the delivery process. It holds each idea-to-production journey as a long-running case (the **delivery-process record**), routes human tasks with SLAs, waits on reviews, and is the UI for non-engineers. It coordinates agents. It does not author them. |
| **The harness** | The deterministic evidence-and-decision engine the orchestrator calls, for questions like "does this lane's exit pass?" and "what tier is this PR, and who approves?". It never calls an LLM. |
| **GitHub** | Enforces merges (D-03). Not built yet: the gate's decision is not yet published as a required check (R1, blocked by R2). |

Rules that keep the three apart:

- **An orchestrator approval never replaces the merge gate or a GitHub review.** It must map to the same team
  identities, and reviewer lockout (R7) still applies.
- **Agents built through the harness stay ADK only.** The orchestrator coordinates them but does not replace
  the framework.
- **The orchestrator is not named in this repo.** It is a category: an external process orchestrator for
  long-lived processes that mix agents, APIs and people.

### How a person comes in

- The orchestrator is the proposed primary entry point for non-engineers.
- The `AgentRequest` issue form and the `agentic-bootstrap` CLI remain.
- `agentic-bootstrap lane status|next` (DP3) is an engineer convenience. It reads the same lane-exit contract
  (DP10) as the orchestrator.
- **Ownership of the delivery process stays open (Q20).** So does whether long human waits live in the
  orchestrator or in the harness's own durable runtime (Q21).

## Exit requirements and what enforces them

**Status rule.** **Built** means the check or rule exists and is tested. It is **not yet enforced on real PRs**
until the gate's decision is published as a required check (D-03, R1, blocked by R2). The gate runs against
fakes today. **Partly built** and **Not built** are as described in each row. The roadmap ID is the work that
would finish it.

"Enforced today" cites an existing check, gate rule, checklist item or eval.

### Prototype

| Exit requirement | Enforced today by | Status |
|---|---|---|
| Mission Brief done | The template ships `docs/mission-brief.md` starting with `PLACEHOLDER`. The request parser (I1) drafts a brief and lists missing fields offline. Nothing checks that a finished brief is complete. | **Not built**: I3 (intake agent), W3 (pack fails on `PLACEHOLDER`), DP2 |
| Hypotheses written as eval criteria, and visible in the demo | The brief has a "hypotheses to test" field, as guidance only. Nothing checks it. | **Not built**: I3, I5 (adversarial case proposals), DP2 |
| Golden data set drafted | The template ships a small starter dataset and a planning set (`evals/golden_set.yaml`) (E3, first slice). Nothing checks that an agent's set goes beyond the starter. | **Partly built**. The check is **Not built**: DP2, DP10 |
| Demo runs in the sandbox on synthetic data through the main cases of the drafted set. A recorded demo is the evidence. | None. The sandbox builder is a stub (D1), the connector library does not exist (I2) and nothing records a demo. | **Not built**: D1, I2, DP2 |

### Verify

| Exit requirement | Enforced today by | Status |
|---|---|---|
| Golden data set and evals pass with no regression | `evals_no_regression` is in `required_checks`, and the gate escalates when a required check is missing (G1). The template job is hard-coded `exit 1`, so **today the check always fails and no agent can meet this exit until E3 wires it.** That is fail-closed by design, not a gap in the gate. `eval_gate.py` is a complete fail-closed comparator that no job calls yet. Holdout cases and live evals do not exist yet. | **Partly built**: E3 (doing), E1; Q18 blocks the evaluation setup |
| Coverage and quality met | `coverage` (80% starter mark) and `quality` are required checks in the template and in `policy/risk_tiers.yaml` (E3, first slice). AI governance approves the baseline. | **Built** (see the status rule) |
| Review checklist clean | `policy/review_checklist.yaml`, applied by the reviewer role. The gate does not auto-merge when the reviewer does not approve. An AI governance reviewer approves against the checklist. The reviewer sees file names only, not the diff. | **Partly built**: R7 |
| Adversarial review done | One reviewer role exists. A second, different model family (D-15) and a measure of how well the reviewer catches seeded defects (E2) do not. | **Not built**: I5, E2 |
| Agents meet their success criteria running in the intended non-production environment, not only locally | None. No environment is chosen or provisioned for agents, and live evals do not exist. | **Not built**: E3, W1 (provision), Q12 |

### Harden

| Exit requirement | Enforced today by | Status |
|---|---|---|
| Security sign-off | Path-driven: `security` must approve control files with `ai_governance`, IAM config, sensitive domains and agent steering files (tier 3 rules in `policy/risk_tiers.yaml`). The security team members and escalation process are unknown (Q19). A lane-level sign-off for an MVP is not a gate rule. | **Partly built**. Lane sign-off **Not built**: DP2, DP10. People: Q19 |
| Runbooks | Review checklist item: runbook and alert changes included when behaviour or dependencies change. The template runbook is a placeholder. | **Partly built**. Placeholder check **Not built**: W3 |
| Egress approved | (1) `app/harness/nodes/capability_check.py` adds approvers for new hosts it finds in diffs. It is regex-based and only adds approvers. (2) `app/harness/workflow.py` has a `TODO(AI governance team)` to read the spec's declared `egress_hosts` at run time (R2, R6). Until then every non-allowlisted host is treated as undeclared. (3) Network-level egress (the `connect` stage tfvars PR) is not built (W1). | **Partly built**: R2, R6, W1 |
| Production approval | `production-deploy` is tier 3 and needs `product_owner` and `architecture`. Never auto-merged. Deployment itself is manual. | **Built** for matching paths (see the status rule). Release stage automation: W3 |

Register, provision and connect also happen in this lane. `agentic-bootstrap plan` lists the PRs but writes no
Terraform (W1 is not built). Identity integration is **Not built** (DP5, W4).

## A proposal: formal security review moves to Harden

Today `policy/raci.yaml` has the security team as responsible and accountable for "Security Architecture or
design review of every change", and the `frame` stage lists `security` as an approver. The feedback is that
formal security work should happen once an MVP is ready, not before.

That is a **proposal** and it would change policy. This PR does not change any tier, approver or threshold. If
the owner agrees, a follow-up PR would change `policy/` and needs an eval (DP8, blocked on Q20). Until then
today's policy stands.

Tier 3 rules, the input guard, residency and secret handling in every lane are good but not enough on their own.
The proposal therefore comes with these **compensating controls**:

1. **Synthetic data by default in Prototype and Verify.** Approved non-production data is allowed in Verify.
   Real or classified data, or a real system, needs security approval first, whatever the lane.
2. **New-capability findings keep their approvers in every lane.** New hosts, models, data stores,
   dependencies and tool protocols (S3) still add their approvers.
3. **Security is informed when work enters Prototype**, so it can flag classification or residency concerns
   early. Informed, not approving.
4. **Escalation.** Anything the gate escalates still goes to security in any lane, once Q19 names the people.

## A proposed lane-aware RACI (D-16)

**Proposed. Owner unassigned. Built: No.** See [Decisions](DECISIONS.md). The aim is application-team autonomy in
the early lanes, with central-team review kept where it is needed.

Legend as in `policy/raci.yaml`: R does it, A accountable, C consulted, I informed, "approves" is a gating
approval.

| Lane or change | app_team | ai_governance | platform_team | security | product_owner | architecture |
|---|---|---|---|---|---|---|
| Prototype | R/A | C | C | I (informed on entry) | C | C |
| Verify | R/A | C | C | C | C | C |
| Harden, release | R | approves | approves | approves | approves | approves |
| Any tier-3 change, in any lane | R | approves per `risk_tiers.yaml` | approves per rule | approves per rule | approves per rule | approves per rule |
| Operate | As today (`policy/raci.yaml`) | | | | | |

For Harden and release, the accountable role for each activity stays as it is in `policy/raci.yaml` (for
example, `product_owner` is accountable for production approval). Only the early lanes change.

**What it would relax.** `base_approvers` is `[app_team, ai_governance]` on every agent PR today, and the
`verify` stage lists `ai_governance` as an approver. In Prototype and Verify, `ai_governance` would move from
approving to consulted. Policy also says phase 1 means a person reviews every agent PR, and raising a phase is
evidence-based (D-11, O3). This proposal overlaps with that.

**Before any policy change (preconditions):**

1. The owner signs off. Nobody owns the delivery process yet (Q20).
2. An eval proves the relaxed approvals cannot reach tier 3 files or new capabilities. `policy/` changes need
   a new or updated adversarial or golden eval.
3. **The lane source is trusted.** The gate must read the lane from a source that the builder cannot edit and
   that no LLM node can set. A label is **not** a valid lane source: `policy/routing.yaml` lets the triage node
   apply labels. A file in the agent repo is not valid either. The lane comes from a record held **outside
   the agent repo**: the delivery-process record (see [Who runs the process](#who-runs-the-process)).
   Changing it is a human-approved, tier-3-equivalent action. Otherwise an agent could mark its own PR
   "prototype" and lower its own approvals.
4. The security team members and escalation process are known (Q19).
5. The compensating controls above are in place.

`policy/raci.yaml` and `policy/risk_tiers.yaml` are unchanged.

## Reliability

Reliability is built into the system in three places. This table says what exists and what is planned.

| Part | Built | Planned |
|---|---|---|
| **Checks in CI/CD** | Harness CI: `ruff`, `ty`, `codespell`, tests (with docs and site checks), dry-run evals, secret scan, `zizmor`. Template: `preflight`, `lint`, `tests`, `coverage` (80% starter), `quality`, `secret_scan`. The gate fails closed when a required check is missing. | Wire `evals_no_regression` to real evals and the baseline comparator; a holdout job the coding agent cannot read; live eval replay (E3, E1). Q18 blocks the evaluation setup. |
| **Developer-agent skills** | Skills load only from a pinned, fingerprinted version (`policy/skills.lock.yaml`), and skill files are tier 3. The template has an `AGENTS.md` steering file. The skills lock is empty until skill names, source and provenance are agreed (Q7). | A **spec-gap skill** (DP6): one skill with two users. The intake agent (I3) uses it to ask the requester. The builder uses it to stop and comment on the issue instead of guessing. It produces a structured "missing information" comment and a stop that the workflow routes to a person. It never writes guessed values into the spec, evals or thresholds. |
| **Adversarial reviewer** | A reviewer role applies the review checklist, and reviewer lockout stops a builder approving its own work. It is advisory. The gate decides. | The reviewer sees the diff (R7). A different model family reviews generated agents (D-15, I5). Measure it with seeded defects (E2, DP7 asks to raise its priority). |

Prompts and skills are not authorisation. Permissions and side-effect checks stay in code and platform IAM.

## Standards

The system should carry security, control and software-practice standards, including engineering-excellence
and AI-engineering standards. **This repo does not name which standards apply.** The tables below are the
traceability structure: standard, the control that enforces it, and status. The standards themselves are for the
owner to supply. Nothing here invents one. Who owns the standards register, and which standards apply, is
Q23. AI governance and security are the likely contributors; the owner is unassigned.
Planned structure as data: `policy/standards.yaml` (DP2, linked to Q23).

Controls listed as "candidates" exist today but have **not** been mapped to a standard.

### Security

| Standard | Control that enforces it | Status |
|---|---|---|
| TODO(owner): organisational security standard. **TODO: UNCONFIRMED** | Candidates: input guard, secret scan, residency, tier 3 approvals | Not mapped |
| OWASP, *Top 10 for Agentic Applications 2026* (cited in the roadmap references) | Candidates: tamper check, new-capability detectors, input guard | Cited as a reference. Adoption as a standard: **TODO: UNCONFIRMED** |

### Controls

| Standard | Control that enforces it | Status |
|---|---|---|
| TODO(owner): control and assurance framework. **TODO: UNCONFIRMED** | Candidates: merge gate, risk tiers, RACI, audit log (O1, not built) | Not mapped |
| NIST, *AI Risk Management Framework: Generative AI Profile* (cited in the roadmap references) | Not mapped | Cited as a reference. Adoption: **TODO: UNCONFIRMED** |

### Engineering excellence

| Standard | Control that enforces it | Status |
|---|---|---|
| TODO(owner): software engineering practice standard. **TODO: UNCONFIRMED** | Candidates: `coverage` and `quality` required checks, reviewed PRs, `ruff`, `ty` | Not mapped |

### AI engineering

| Standard | Control that enforces it | Status |
|---|---|---|
| TODO(owner): AI engineering practice standard. **TODO: UNCONFIRMED** | Candidates: evals and golden data sets, review checklist, pinned skills and prompts | Not mapped |

## Not decided

- **Q19:** who the security-team reviewers are, and the escalation process. It blocks tier-3 approvals and the
  D-02 sign-off.
- **Q20:** whether the lanes and the D-16 RACI proposal stand, and who owns the delivery process.
- **Q21:** for long human waits, whether the harness keeps its own durable runtime (D-05, R3, W5) or hands them to
  the orchestrator and keeps only the short issue-to-merge loop.
- **Q22:** how generated agents are invoked at runtime (API, A2A, or as steps in orchestrated business
  processes), and what invocation contract the template must expose.
- **Q23:** who owns the standards register, and which standards apply.

All are in [Open questions](OPEN_QUESTIONS.md). The backlog is in the [Roadmap](ROADMAP.md) (M10 to M12).

## Readiness

The design comes from theory, documentation and experience. It has **not** been tested on real work or
deployed. M12 in the roadmap proposes a pilot on real work, with draft success criteria that still need owner
agreement.
