# Glossary

Plain-English meanings for the words, acronyms, teams and codes used in this repo.

How to read this page:

- **Plain English** lines say what a thing means in everyday words.
- **TODO: UNCONFIRMED** means the repo does not say, and we have not guessed.
- Where a word has two meanings in this repo, both are listed.

Sections: [Acronyms](#acronyms) · [Teams and roles](#teams-and-roles) ·
[Core ideas](#core-ideas) · [The gate and its outcomes](#the-gate-and-its-outcomes) ·
[Safety words](#safety-words) · [Parts of the code](#parts-of-the-code) ·
[Google and GitHub products](#google-and-github-products) · [Roadmap codes](#roadmap-codes)

---

## Acronyms

| Term | Means | Plain English |
|---|---|---|
| **A2A** | Agent2Agent protocol | A standard way for one AI agent to talk to another. Not used by the harness. The roadmap says to wait until it is really needed. |
| **ADK** | Google Agent Development Kit | The one agent framework allowed in this repo. It is the toolkit that builds the AI agents. |
| **AGENTS.md** | A file name | A short instruction sheet for a coding agent. It lists the commands, rules and boundaries for a repo. |
| **ASCII** | Plain text characters | Diagrams drawn with keyboard characters. |
| **CI** (1) | Continuous integration | Automatic checks that run on every pull request. |
| **CI** (2) | Configuration item | A record in the CMDB. The "AI Agent" CI is the record for one agent. |
| **CMDB** | Configuration management database | A register of systems and their configuration items. Each agent gets an "AI Agent" record. |
| **CODEOWNERS** | A GitHub file | A list that says which people or teams must review changes to which files. |
| **AI governance team** | A generic role name | Reviews agent work against the review checklist. |
| **cloud platform** | A generic platform term | The cloud services used by this project; specific services and constraints are described where relevant. |
| **GHAS** | GitHub Advanced Security | A GitHub package with additional security scanning. Licensing and availability remain open questions (Q11). |
| **GHE.com** | GitHub Enterprise Cloud with data residency | GitHub's enterprise hosting where data stays in a chosen region. |
| **HCL** | HashiCorp Configuration Language | The language Terraform files are written in. |
| **HITL** | Human in the loop | A person must approve before the work goes on. |
| **IAM** | Identity and Access Management | Who or what is allowed to do what in a cloud system. |
| **LLM** | Large language model | The AI model (here, Gemini) that reads and writes text. |
| **MCP** | Model Context Protocol | A standard way to plug tools into an AI agent. Optional here. If used, it needs review. |
| **OIDC** | OpenID Connect | How a GitHub job proves who it is to Google Cloud, without a stored password. |
| **PR** | Pull request | A proposed change to the code that others review before it is merged. |
| **RACI** | Responsible, Accountable, Consulted, Informed | An adaptable policy format for recording who does, owns, advises and is informed. The example configuration is [`policy/raci.yaml`](../policy/raci.yaml). |
| **REST** | Representational State Transfer | A common way for programs to talk over the web. |
| **SHA** | Secure hash (git commit ID / file fingerprint) | A long code that identifies one exact version of something. "Pin to a SHA" means "use this exact version, never a moving one". |
| **WIF** | Workload Identity Federation | A way for GitHub jobs to get short-lived Google Cloud access without keys or passwords. |
| **YAML** | A text format | The format used for the policy files in `policy/`. |

---

## Teams and roles

These are the six role IDs in [`policy/raci.yaml`](../policy/raci.yaml). They are the words the gate
uses when it names who must approve.

| Role ID | Team | What the repo says they do |
|---|---|---|
| `app_team` | Application team | Builds and owns one agent. Raises the work. Always an approver on agent PRs. |
| `ai_governance` | AI governance team | Owns the golden workflow, the template and the review checklist. Always an approver on agent PRs. |
| `platform_team` | platform team | Reviews Terraform (`*.tf`) changes. The illustrative `workload-infrastructure` repository and `platform.tf` filename do not assert an actual repository layout. |
| `security` | security team | Approves changes to the files that steer or control agents, IAM files and sensitive areas. |
| `product_owner` | Product Owner | Approves production deployment. |
| `architecture` | Architecture | Reviews before production. |

Other team words you will see:

| Term | Plain English |
|---|---|
| **security team** | Named in the roadmap as the owner of several security decisions. TODO: UNCONFIRMED whether this is the same group as the `security` role. |
| **Agent teams / app teams** | The teams that build agents using this harness. |
| **platform team ingress route** | The network path for GitHub events to reach the harness. Not yet agreed. |

---

## Core ideas

| Term | Plain English |
|---|---|
| **Harness** | This repo. It wraps AI agents in rules, checks and approvals so that they can build software safely. |
| **Agent** | An AI program that can use tools and make choices. The harness has agents that plan and review. The generated agent repos hold the agents that the app teams build. |
| **Generated agent / agent repo** | A new repo the harness creates from `agent-template/` for one agent. |
| **Golden workflow** | The harness's standard path for taking an agent live. It has eight stages: frame, register, provision, connect, build, verify, release, operate. Defined in [`policy/golden_workflow.yaml`](../policy/golden_workflow.yaml). |
| **Stage** | One step of the golden workflow. |
| **Onboarding steps (13)** | The 13 example steps in the adaptable RACI configuration. The eight stages group them. |
| **Issue-to-merge loop** | The part of the harness that turns a GitHub issue into a merged change. It covers the Build and Verify stages only. |
| **Build stage / Verify stage** | Build: an agent writes the change. Verify: checks and a review decide if it can merge. |
| **Mission Brief** | A short document that states what an agent is for, who uses it, what data it uses and which hosts it calls. Its test ideas become eval criteria. |
| **Opportunity Canvas** | Drafted in the Frame stage. TODO: UNCONFIRMED what it contains. |
| **Runbook** | A how-to-operate guide for one agent: what it does, how to spot faults, how to roll back. |
| **Spec (`spec.yaml`)** | A small file with the facts the bootstrap needs: name, division, owner, sponsor, classification, description, and optional location, environments and egress hosts. |
| **Division** | The business area that owns an agent. |
| **Classification** | A label for how sensitive an agent is. TODO: UNCONFIRMED the list of values; the example uses `internal`. |
| **Sponsor** | The business person who backs an agent. |
| **Egress host** | A website or service that an agent is allowed to call out to. The spec lists exact host names only. |
| **Registry entry** | A record for each allowed egress host in the Agent Registry. |
| **Landing zone** | The ready-made cloud setup that new projects are placed in. Referred to for WIF and for provisioning. |
| **Provision** | Create the cloud project and its settings for an agent. |
| **Residency (data residency)** | Keeping data and AI processing inside allowed places. Here: Australian regions only. |
| **Allowed regions** | `australia-southeast1` (Sydney) and `australia-southeast2` (Melbourne), listed in [`policy/residency.yaml`](../policy/residency.yaml). |
| **Global endpoint** | A cloud address with no fixed location. Never allowed. |
| **Phase** | How much the gate trusts itself. Phase 1: a person reviews every agent PR. Phases 3 and 4: the lowest-risk changes may merge by themselves. The file ships at phase 1. |
| **Tier** | How risky a change is. Tier 1 is low (tests and docs). Tier 2 is the default. Tier 3 is high (controls, Terraform, IAM, production, sensitive areas, agent instructions). |
| **Required checks** | Six automatic checks every agent PR must pass: `lint`, `tests`, `coverage`, `quality`, `evals_no_regression`, `secret_scan`. |
| **Lint** | An automatic style and error check on code. |
| **Evals** | Tests of how an AI behaves (not just whether code runs). |
| **Golden task** | A saved example case used to test the harness. It says what the right outcome is. |
| **Delivery process** | The path a person follows from idea to production, in lanes, with exit requirements. It sits on top of the harness. Proposed; see [`DELIVERY.md`](DELIVERY.md). |
| **Lane** | A phase of the delivery process: prototype, verify, harden or operate. Each has exit requirements. A lane never switches off a deterministic control. |
| **Exit requirement** | What must be true before work leaves a lane. Each one is enforced by an existing control, or marked Not built with its roadmap ID. |
| **Golden data set** | In a generated agent: the cases that verification judges the agent against (the same idea as the golden set, used as a lane exit). Not the harness's own golden tasks. |
| **Demo-ready** | The Prototype exit: the agent runs in the sandbox against synthetic data, works through the main cases of the drafted golden data set, and the hypotheses are visible. A recorded demo is the evidence. Not secure, reviewed or connected to real systems. |
| **MVP** | A minimum viable product. In the delivery process, **MVP-ready** is the Verify exit: golden data set and evals pass with no regression, coverage and quality are met, the review checklist is clean, and the agents meet their success criteria in the intended non-production environment. MVP-ready is what starts Harden, where formal security work happens (proposed). |
| **Persona** | A kind of person who works with the harness and delivery process, described by role: product manager, application engineer, AI governance, security or platform. See [`PERSONAS.md`](PERSONAS.md). |
| **Golden set** | In a generated agent: example cases for the agent's own behaviour. |
| **Baseline** | The last accepted eval results. A new PR may not do worse than it. |
| **Threshold** | A pass mark for an eval. The business owner sets it, not the builders. |
| **Holdout** | Secret test cases the coding agent never sees. Described in the template; the runner is still to be built (E3). |
| **AgentRequest** | A GitHub issue, raised with the issue form, that asks for a new agent. The harness turns it into an untrusted draft (a Mission Brief, a review-only spec and a list of missing fields). A draft grants nothing. |
| **Intake agent** | Planned (M9). An agent that would interview the requester on the issue and open a PR for the agent they need. It only raises PRs and never approves or merges. |
| **Connector library** | Planned (I2). A fixed, reviewed set of ways for generated agents to reach other systems. Anything outside it goes to a person. |
| **Preflight** | The first job in a generated repo's checks. It inspects a candidate checkout without running it, using trusted code from the base revision. A tripwire, not a sandbox. |
| **Coverage / Quality** | Two required checks in generated repos. Coverage enforces a minimum share of agent code run by tests (80% to start). Quality runs the style, complexity and type checks. |
| **Dry-run eval** | An eval that uses scripted fakes. It is free and fast. |
| **Live eval** | An eval that calls real models. It costs money and needs approved cloud access. Not built yet. |
| **Trace** | A step-by-step log of what the harness did on one task. |
| **Escalate** | Stop and hand the task to a person. |
| **Plan approval** | A person approves the plan before the builder starts. |
| **Skill** | A text file of guidance that changes how an agent behaves. It does not give the agent any new powers. |
| **pinned skills repository** | The configured source of approved skills. The harness does not copy skills in; it reads a pinned checkout. |
| **Skills lock** | [`policy/skills.lock.yaml`](../policy/skills.lock.yaml): the exact approved version and fingerprint of each skill. Empty today. |
| **Pinning** | Locking to one exact version so nothing changes without a reviewed PR. |
| **TODO(owner)** | A marker for a decision that needs an accountable role or owner. Do not guess; keep it unresolved until assigned. |
| **TODO: UNCONFIRMED** | A marker used in these docs for facts that the repo does not confirm. |

---

## The gate and its outcomes

The **merge gate** ([`merge_gate.py`](../app/harness/nodes/merge_gate.py)) is plain code. It never calls an LLM.

| Outcome | Plain English |
|---|---|
| `auto_merge` | The change may merge without a person. Only for tier 1, only at phase 3 or 4, and only if nothing new was detected. |
| `human_approval` | A named set of people must approve before it merges. |
| `reject_to_planning` | The change is too big (over 400 lines). Split it and plan again. |
| `escalated` | Something is wrong or unknown (failed or missing check, tampering, a blocked input). A person must look. |
| `ignored` | The issue has no `agent:*` label, so the harness does nothing. |

| Term | Plain English |
|---|---|
| **Fail closed** | When unsure, stop. Missing evidence counts as a failure, never as a pass. |
| **Reviewer lockout** | The agent that built a change cannot approve it. |
| **Harness controls** | Files that control the gate or agent behaviour (workflows, CODEOWNERS, policy, skills, prompts, eval thresholds). Always tier 3, never auto-merged. |
| **Privileged YAML** | Config files that grant access. TODO: UNCONFIRMED which files count (Q1). |
| **Tamper check** | Looks at a change for signs the agent weakened its own tests or evals (deleted tests, added skips, lowered thresholds). |
| **Capability check** | Looks at a change for newly added models, hosts, regions, data stores, dependencies or tool and protocol links. It adds approvers. It never approves or blocks by itself. |
| **Approvers** | The roles that must sign off. The gate works them out from the changed file paths. |

---

## Safety words

| Term | Plain English |
|---|---|
| **Input guard** | A scan of untrusted text before an LLM reads it. Ships in `shadow` mode. |
| **Shadow mode** | Record what would have been blocked, but let the task continue. Used while we learn about false alarms. |
| **Enforce mode** | A match, crash or incomplete scan stops the task. |
| **Prompt injection** | Text that tries to give an AI new orders (for example "ignore previous instructions"). |
| **Sunglasses** | The pattern-matching scanner used by the input guard. A cheap tripwire, not a full defence. |
| **Model Armor** | A Google Cloud service that screens prompts and replies for prompt injection and other risks. The main scanner (S2). Wired in and tested with a fixture. Not run against the live service yet. |
| **Composite scanner** | Runs Model Armor and Sunglasses on the same text. Blocked if either blocks. A scanner that errors counts as a block. |
| **ModelArmorPlugin** | The part of ADK that screens a model's input and replies with Model Armor. Registered on the harness's own ADK app. |
| **Template (Model Armor)** | A saved set of Model Armor settings in one cloud region. Not the same as `agent-template/`. |
| **Adversarial task** | A golden task that tries bad behaviour to prove the harness catches it. |
| **Known gap** | A documented miss. It is reported as open and must be removed once it is fixed. |
| **Reward hacking** | An agent passing its checks by cheating (for example by editing the tests) rather than by doing the work. |
| **Gitleaks** | A tool that finds secrets (keys, passwords) in code. Used in CI. |
| **zizmor** | A tool that checks GitHub workflow files for security mistakes. |
| **CodeQL / dependency review** | GitHub code-scanning and dependency checks. They run on public repos or when `GHAS_ENABLED=true`. |
| **Secret** | A password, key or token. Never kept in code, traces or audit records. |
| **GitHub App** | The way the harness acts on GitHub. No personal access tokens. |
| **Least privilege** | Give only the access that is needed and no more. |

---

## Parts of the code

| Term | Plain English |
|---|---|
| **Port** | A named slot in the code (such as `GitHubPort`) that real or fake parts plug into. Lets the workflow stay the same when parts change. |
| **Adapter** | A real part that plugs into a port (for example the ADK agents or the Copilot builder). |
| **Fake** | A scripted stand-in used in tests and dry-run evals. No network. |
| **Builder** | The part that writes the code change. Default: GitHub Copilot. |
| **Triager / Planner / Reviewer** | The three LLM roles: size the issue, write the plan, review the result. |
| **Repo context** | AGENTS.md, the file tree and a few named files, read-only, size-capped and scanned, given to the planner and reviewer. |
| **Bootstrap** | The `agentic-bootstrap` command with three stages: `new` (make an agent repo), `check` (harness policy checks), `plan` (the ordered PRs for a cloud project). |
| **Template (`agent-template/`)** | The starting repo that `new` copies for each agent. |
| **Sandbox** | An optional, not-yet-built way to run a build in a Cloud Run Job. Not the default. |
| **e2e script** | `scripts/e2e.py`: runs the harness end to end, then cleans up. |
| **`agents-cli`** | Google's command-line tool for agent projects (lint, evals, scaffold, deploy). |
| **`uv`** | A Python tool for installs and environments. |
| **Pydantic** | A Python library that checks data has the right shape. |
| **Hypothesis** | A Python library that tests rules across many generated inputs (property tests). |
| **ty / ruff / codespell** | Type checker, style checker and spell checker. |

---

## Google and GitHub products

| Term | Plain English |
|---|---|
| **Gemini** | Google's AI models, used for triage, planning and review. |
| **Vertex AI** | Google Cloud's service for running models in a chosen region. |
| **AI Studio key** | A simple API key for Gemini. Allowed for local development only (`HARNESS_ENV=local`). |
| **Agent Runtime** | Where deployed agents run on the chosen cloud platform. The deployment target in the template. |
| **Agent Gateway / Agent Registry** | Cloud platform services for controlling and recording which hosts an agent may call. |
| **memory service** | An optional service whose regional availability remains unconfirmed. |
| **Cloud Run** | Google Cloud's service for running containers. The roadmap proposes it to host the harness (not yet agreed). |
| **Cloud SQL / Cloud Tasks / Cloud Trace / BigQuery** | Google Cloud database, task queue, tracing and data warehouse. Proposed in the roadmap; none are built. |
| **Secret Manager** | Google Cloud's store for secrets. |
| **Terraform** | A tool that sets up cloud resources from text files. |
| **cloud platform module** | A Terraform module for cloud resources. |
| **`workload-infrastructure` repository** | An illustrative repository name only. The actual repository and layout remain unconfirmed (Q12). |
| **existing reference agent template** | A generic reference to a possible template source. Access and use remain unconfirmed (Q6). |
| **GitHub Copilot coding agent** | GitHub's AI that takes an issue and opens a PR. The default builder. |
| **`copilot-setup-steps.yml`** | A workflow file that prepares Copilot's work environment. |
| **Custom agent profile** | A file in `.github/agents/` that tells Copilot how to behave in this repo. |
| **Firewall allowlist (Copilot)** | A list of hosts Copilot may reach. Set in GitHub settings, not in a repo file. |
| **Ruleset / branch protection** | GitHub rules that block merges until checks pass. Planned (R1). |
| **Check run** | A single status line on a PR. |
| **External process orchestrator** | A proposed category of tool (D-17) that would run the delivery process as long-lived cases mixing agents, APIs and people, with human tasks, SLAs and an audit trail. The harness supplies evidence and decisions and GitHub enforces merges. W5 keeps a port ready. No product or adoption decision is recorded. See Q21. |
| **Antigravity / Gemini CLI** | Google coding-agent tools named as options for the optional sandbox. |

---

## Roadmap codes

The roadmap ([`ROADMAP.md`](ROADMAP.md)) numbers its work. Each code is stable.

| Code | Plain English |
|---|---|
| **D-01 … D-17** | Decisions. Short design choices with a reason and an owner. See [`DECISIONS.md`](DECISIONS.md). |
| **Q1 … Q23** | Open questions for this project. See [`OPEN_QUESTIONS.md`](OPEN_QUESTIONS.md). |
| **M0 … M12** | Milestones (groups of work). M0 makes the gate trustworthy; M8 gets a generated agent ready for the pilot; M9 lets a person request an agent and get a governed PR; M10 builds the delivery process, M11 the platform scope, and M12 pilots them on real work. |
| **H0 to H2** | Hygiene items: the repo guide (H0), CI and repo tidy-up (H1), and the generated-project preflight and acceptance test (H2). |
| **G1 … G7** | Gate items: fail closed, control files in tier 3, tamper detection, plan approval, path matching, least-privilege CI, policy validation. |
| **R1 … R7** | Runtime items: GitHub checks and CODEOWNERS, real GitHub client, durable workflow, ingress queue, controls, hardened ADK adapters, reviewer sees the diff. |
| **S1 … S5** | Security items: scanners, Model Armor, new-capability detectors, Copilot environment, supply chain. |
| **D1** | Builder residency (not the same as the `D-` decisions). |
| **O1 … O3** | Observability: traces and audit, metrics, shadow gate and phase promotion. |
| **E1 … E3** | Evals: live replay, reviewer defects, real template evals. |
| **W1 … W5** | Workflow coverage: workload PR checks, template from existing reference agent template, release pack, registration, GitHub-native human gate. |
| **A1 … A3** | Generated-agent items: authorisation boundary, telemetry, governed skill. |
| **DP1 … DP11** | Delivery-process items in M10 to M12: this documentation (DP1), lane and standards policy files, the `lane` CLI, a spec-gap skill, the E2 priority change, the D-16 policy change, the lane-exit contract, a multi-agent template variant, identity integration, the runtime invocation contract, and the pilot. Not the same as the `P0 / P1 / P2` priorities. |
| **I1 … I7** | Agent intake items: request form and parser, connector library, intake agent, authoring, cross-model review, tailoring through comments, hosted trigger. |
| **Status words** | `todo`, `doing`, `blocked`, `review`, `done`, `dropped`. |
| **P0 / P1 / P2** | Priority: before the agent discussion, before the pilot agent, after the pilot. |
| **S / M / L** (size) | Up to half a day, up to two days, more than two days. |
