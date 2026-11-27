# Open questions

What is blocked, unknown or waiting on an owner. Nothing here has been guessed.

Sections: [Open questions](#open-questions) · [Blockers](#blockers) · [TODOs in the code and policy](#todos-in-the-code-and-policy) ·
[Unconfirmed items in these docs](#unconfirmed-items-in-these-docs)

## Open questions

From the [Roadmap](ROADMAP.md). "Suggested owner" shows a generic role where one is recorded; it is not a confirmed assignment.

| # | Question | Blocks | Suggested owner |
|---|---|---|---|
| Q1 | Which files count as "privileged YAML"? | G2, R1 | security team |
| Q2 | What are the real GitHub team names for application, AI governance, platform, security, product and architecture roles? | R1, S5 | AI governance team |
| Q3 | Is the Copilot coding agent acceptable for each data classification, given residency? | D1 | security team |
| Q4 | Who approves workflow runs on Copilot PRs, and should "skip approval" be switched on? | R2 | security team |
| Q5 | Where is the harness hosted (Cloud Run and Cloud SQL in Melbourne?), and what is the webhook route? | R3, R4 | platform team |
| Q7 | What are the pinned skills repository skill names for the planner and reviewer? | R6 | AI governance team |
| Q9 | Do work items come from GitHub Issues, or from Jira or Jira Align? | R4 (may need an `IssueSource` port) | Unassigned |
| Q10 | What are the criteria for moving to a later phase? (Draft in O3.) | O3 | Unassigned |
| Q11 | Is GitHub Advanced Security licensed (secret scanning, push protection, CodeQL, dependency review)? | S1 | AI governance team |
| Q12 | What is the actual infrastructure repository and file layout? `workload-infrastructure` and `platform.tf` are illustrative only. | W1 | platform team |
| Q14 | Who owns and reviews the connector library, which connectors come first, and how do Jira and other internal APIs reach agents (approved connector gateway)? | I2 | AI governance team and platform team |
| Q15 | Which second model family, if any, is approved for cross-model review under Australian residency? | I5 | security team |
| Q16 | Should agents built only from approved connectors stay tier 3, or may they use a lighter approval route? | M9 | security team, AI governance team |
| Q17 | Who sponsors an `AgentRequest` before spending budget or creating a branch, and how is sponsorship verified? | I7 | Unassigned |
| Q18 | Which approved evaluation project, regions and WIF identity should be used, and how can holdouts remain hidden from PR-authored code? | E3 | security team and platform team |
| Q19 | Who are the security-team reviewers, and what is the escalation process? | Tier-3 approvals and the D-02 sign-off | Unassigned |
| Q20 | Do the delivery lanes and the D-16 RACI proposal stand, and who owns the delivery process? | DP2, DP3, DP8, DP9, DP10, D-16 | Unassigned |
| Q21 | For long human waits, does the harness keep its own durable runtime (D-05, R3, W5), or hand them to the external process orchestrator and keep only the short issue-to-merge loop? | R3, W5, DP10 | Unassigned |
| Q22 | How are generated agents invoked at runtime (API, A2A, or as steps in orchestrated business processes), and what invocation contract must the template expose? | DP4, DP11 | Unassigned |
| Q23 | Who owns the standards register, and which security, control, engineering-excellence and AI-engineering standards apply? AI governance and security are the likely contributors. | DP2 | Unassigned |

Resolved: Q6's access contact is the AI governance team, though access is still needed. Q13's requester
eligibility is any person with repository access; the separate sponsorship decision is tracked as Q17.
Q8's starter thresholds are 80% coverage and eval pass mark; AI Governance approves the baseline.
The user accepts the risk of PR code accessing credentials on GitHub Actions, subject to minimising
credentials and deterministic pre-execution scanning. This does not resolve holdout isolation or
approve a project, region or identity.

## Blockers

| Blocked item | Reason | Needs |
|---|---|---|
| **R2** Real GitHub client | GitHub's Copilot issue-assignment API needs a user-to-server token. The harness rule allows installation tokens only. | A security team decision. Do not switch auth models quietly. |
| **I7** Hosted trigger | Needs the real GitHub client (R2), the durable runtime (R3, R4), the hosting route (Q5) and a sponsorship rule for requests (Q17). The offline request parser (I1) is done. | R2, platform team, Q17 owner unassigned |
| R1, R3, R4, R5, R7, O1, W5 | Depend on R2, directly or through R3 | R2 |
| **W2** Template from existing reference agent template | No access yet | AI governance team |
| **E1** Live eval replay | No pilot repos or history yet | Pilot repos |
| **E3** Live and holdout evals | No accepted baseline, approved evaluation setup or reviewed holdout isolation | AI Governance baseline approval; Q18 |
| D1 (a possible blocker for Copilot as default builder) | Copilot residency in Australia is unconfirmed | Q3, GitHub's answer |

## TODOs in the code and policy

Each `TODO(owner)` means "ask the appropriate role or owner; do not invent the answer".

| Where | TODO | Owner |
|---|---|---|
| `policy/risk_tiers.yaml` | Sign off the full control-file boundary | security team |
| `policy/risk_tiers.yaml` | Confirm which files are "privileged YAML" | security team |
| `policy/capabilities.yaml` | Agree the starting allowlists (hosts, regions, models, stores, dependencies) and the package mirror | security team |
| `policy/input_guard.yaml` | Confirm Model Armor templates are required outside local use, and what they screen | security team |
| `docs/tech/INPUT_GUARD.md` | Confirm the Private Service Connect route for the Model Armor regional endpoint | platform team |
| `evals/fixtures/model_armor.json` | Replace the authored fixture with responses recorded from an approved non-production template | AI governance team |
| `policy/routing.yaml` | Confirm the repo-context caps and the deny list | AI governance team |
| `policy/routing.yaml`, `policy/skills.lock.yaml` | Name the real skills, their source and the approved revision | AI governance team (Q7) |
| `app/harness/workflow.py` | Read the spec's `egress_hosts` at run time once the GitHub client can read repo files | AI governance team |
| `app/harness/adapters/copilot_builder.py` | Confirm the exact `custom_agent` identifier the API expects | verify when R2 is built |
| `app/harness/adapters/adk_agents.py` | Give the reviewer the diff | R7 |
| `deployment/terraform/README.md` | Confirm the landing-zone claim mapping, repository identity, service-account name and minimum Vertex role for WIF | platform team |
| `agent-template/.github/workflows/copilot-setup-steps.yml` | Install from an approved package source and pin `google-agents-cli` | security team |
| `agent-template/.github/workflows/agent-checks.yml` | Wire `evals_no_regression` through WIF and `agents-cli eval run` | verify |
| `.github/workflows/ci.yml`, template workflow | Enable GHAS for private repos and set `GHAS_ENABLED=true` | AI governance team |

## Unconfirmed items in these docs

These are things the repo does not say. They are marked **TODO: UNCONFIRMED** in the docs.

| Item | Where it shows up |
|---|---|
| Scope of the cloud platform and responsibilities of the review teams | [Glossary](GLOSSARY.md) |
| Specific owner assignments where no team was recorded | [Decisions](DECISIONS.md), [Roadmap](ROADMAP.md) |
| Whether the `security` role maps to the security team | [Glossary](GLOSSARY.md) |
| What the Opportunity Canvas contains | [Glossary](GLOSSARY.md) |
| The list of classification values | [Glossary](GLOSSARY.md) |
| Whether an existing reference template is available | [Glossary](GLOSSARY.md) |
| Whether the external process orchestrator proposal (D-17) is adopted, and where long human waits live (Q21) | [Glossary](GLOSSARY.md), [Decisions](DECISIONS.md) |
| The repo licence, code of conduct and a security contact | [Index](README.md), [Contributing](CONTRIBUTING.md), [Security](SECURITY.md) |
| How to run the ADK adapters live | [Getting started](GETTING_STARTED.md) |
| Whether the booking-refusal eval passes live | [Examples](EXAMPLES.md) |
| Release and tagging practice (S5 is planned) | [Changelog](CHANGELOG.md) |
| Regional availability of memory services, beyond the known gaps in `policy/residency.yaml` | [Security](SECURITY.md) |
