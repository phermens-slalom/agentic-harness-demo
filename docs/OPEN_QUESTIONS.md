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
| Q6 | Can we get access to existing reference agent template and the existing bootstrap layer? | W2 | Unassigned |
| Q7 | What are the pinned skills repository skill names for the planner and reviewer? | R6 | AI governance team |
| Q8 | What are the business-owned eval, coverage and quality thresholds for each agent? | E3 | Product Owner (to be named) |
| Q9 | Do work items come from GitHub Issues, or from Jira or Jira Align? | R4 (may need an `IssueSource` port) | Unassigned |
| Q10 | What are the criteria for moving to a later phase? (Draft in O3.) | O3 | Unassigned |
| Q11 | Is GitHub Advanced Security licensed (secret scanning, push protection, CodeQL, dependency review)? | S1 | AI governance team |
| Q12 | What is the actual infrastructure repository and file layout? `workload-infrastructure` and `platform.tf` are illustrative only. | W1 | platform team |
| Q13 | Who may raise an `AgentRequest`, and who sponsors it before the intake agent creates a branch? | I1, I7 | Unassigned |
| Q14 | Who owns and reviews the connector library, which connectors come first, and how do Jira and other internal APIs reach agents (approved connector gateway)? | I2 | AI governance team and platform team |
| Q15 | Which second model family, if any, is approved for cross-model review under Australian residency? | I5 | security team |
| Q16 | Should agents built only from approved connectors stay tier 3, or may they use a lighter approval route? | M9 | security team, AI governance team |

## Blockers

| Blocked item | Reason | Needs |
|---|---|---|
| **R2** Real GitHub client | GitHub's Copilot issue-assignment API needs a user-to-server token. The harness rule allows installation tokens only. | A security team decision. Do not switch auth models quietly. |
| R1, R3, R4, R5, R7, O1, W5 | Depend on R2, directly or through R3 | R2 |
| **W2** Template from existing reference agent template | No access yet | Q6 |
| **E1** Live eval replay | No pilot repos or history yet | Pilot repos |
| D1 (a possible blocker for Copilot as default builder) | Copilot residency in Australia is unconfirmed | Q3, GitHub's answer |

## TODOs in the code and policy

Each `TODO(owner)` means "ask the appropriate role or owner; do not invent the answer".

| Where | TODO | Owner |
|---|---|---|
| `policy/risk_tiers.yaml` | Sign off the full control-file boundary | security team |
| `policy/risk_tiers.yaml` | Confirm which files are "privileged YAML" | security team |
| `policy/capabilities.yaml` | Agree the starting allowlists (hosts, regions, models, stores, dependencies) and the package mirror | security team |
| `policy/routing.yaml` | Confirm the repo-context caps and the deny list | AI governance team |
| `policy/routing.yaml`, `policy/skills.lock.yaml` | Name the real skills, their source and the approved revision | AI governance team (Q7) |
| `app/harness/workflow.py` | Read the spec's `egress_hosts` at run time once the GitHub client can read repo files | AI governance team |
| `app/harness/adapters/copilot_builder.py` | Confirm the exact `custom_agent` identifier the API expects | verify when R2 is built |
| `app/harness/adapters/adk_agents.py` | Give the reviewer the diff | R7 |
| `deployment/terraform/README.md` | Confirm the landing-zone claim mapping, repository identity, service-account name and minimum Vertex role for WIF | platform team |
| `agent-template/.github/workflows/copilot-setup-steps.yml` | Install from an approved package source and pin `google-agents-cli` | security team |
| `agent-template/.github/workflows/agent-checks.yml` | Wire `evals_no_regression` through WIF and `agents-cli eval run` | verify |
| `.github/workflows/ci.yml`, template workflow | Enable GHAS for private repos and set `GHAS_ENABLED=true` | AI governance team |
| `agent-template/evals/thresholds.yaml` | Agree the pass marks | The business owner of each agent |

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
| Any plan for a workflow-engine integration beyond keeping a port ready | [Glossary](GLOSSARY.md) |
| The repo licence, code of conduct and a security contact | [Index](README.md), [Contributing](CONTRIBUTING.md), [Security](SECURITY.md) |
| How to run the ADK adapters live | [Getting started](GETTING_STARTED.md) |
| Whether the booking-refusal eval passes live | [Examples](EXAMPLES.md) |
| Release and tagging practice (S5 is planned) | [Changelog](CHANGELOG.md) |
