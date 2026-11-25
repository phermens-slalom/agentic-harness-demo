# Decisions

The fifteen design decisions from the [Roadmap](ROADMAP.md), in plain English.
A decision marked **Proposed** is built behind a setting or a port so it is cheap to reverse when the appropriate owner rules.
**Built** means the behaviour is in the code. It does not mean the owner has signed off.

| ID | Decision | Why | Status | Owner | Built? |
|---|---|---|---|---|---|
| D-01 | **Fail closed on missing evidence.** No checks, an unknown check state or a missing required check means escalate. Never auto-merge. | Unknown is not green. | Accepted | | Yes (G1) |
| D-02 | **Files that control the gate are tier 3 and never auto-merge.** Policy, CI workflows, CODEOWNERS, rulesets, eval thresholds and baselines, skills and prompts, agent steering files, tool and agent definitions. `ai_governance` and `security` approve. | An agent must not edit the rules that judge it. | Proposed | `security` | Yes (G2) |
| D-03 | **GitHub enforces the gate. The harness only decides.** The decision is posted as a required check (`harness/merge-gate`). CODEOWNERS is generated from `risk_tiers.yaml`. | One source of truth that GitHub enforces even if the harness is down. | Accepted | | No (R1, blocked by R2) |
| D-04 | **Plan approval is by rule.** Always required in phases 1 and 2. From phase 3 it is required when the predicted tier is 2 or more. The AI's "sensitive" flag can only add an approval. | An injected issue must not switch off the human checkpoint. | Accepted | | Yes (G4) |
| D-05 | **Run the harness as an ADK 2.0 Workflow on Cloud Run** in `australia-southeast2`, saving sessions in Cloud SQL for Postgres. | Approvals that survive a restart. A webhook needs plain HTTP. | Proposed | `platform_team` | No (R3) |
| D-06 | **Take events in through a queue.** A receiver checks the webhook signature, removes duplicates, and queues work in Cloud Tasks. Workers are safe to repeat per issue. | A repeated webhook must not start a second Copilot job. | Proposed | `platform_team` (ingress route) | No (R4) |
| D-07 | **Record traces and an audit log.** OpenTelemetry traces to Cloud Trace. Every gate decision as an insert-only row in BigQuery. | Reviewers need to explain why something happened, without keeping secrets. | Proposed | `ai_governance` | No (O1) |
| D-08 | **Use existing security tools first.** Gitleaks, GitHub secret scanning, CodeQL, dependency review and zizmor. Keep only harness-specific rules in `agentic-bootstrap check`. | Do not build what already exists. | Accepted | | Partly (S1). Secret scanning waits on licensing (Q11). |
| D-09 | **Model Armor is a proposed primary input scanner, with Sunglasses as a local tripwire.** Both sit behind the `InputScanner` port. | Pattern matchers miss novel phrasing; adoption of a semantic scanner remains a proposal. | Proposed | `security` | Sunglasses only; the semantic scanner remains planned (S2). |
| D-10 | **Copilot stays the default builder, but residency is a gate on it.** If Copilot cannot confirm Australian processing, a Cloud Run sandbox builder becomes the fallback for classified repos. | Copilot's in-region processing was US and EU only as of April 2026. | Proposed (possible blocker) | `security` | No (D1). The sandbox is a stub. |
| D-11 | **Move to a later phase on evidence.** Run the gate in shadow mode at the next phase and raise it only once agreed thresholds are met. | Today the criteria for raising the phase remain unresolved. | Proposed | Unassigned | No (O3) |
| D-12 | **Base the template on an existing reference agent template** (pinned by git ref) with a project-specific layer on top, and let generated repos upgrade in place. | Matches prior requirements. Respects teams already on the current version. | Proposed | Unassigned | No (W2, blocked) |
| D-13 | **An `AgentRequest` issue starts an intake agent that builds the agent.** It asks the requester plain-language questions on the issue, adds the agent to the division's agent repo, writes its code and evals, and opens a PR. It only raises PRs. It never approves or merges, and every PR goes through the merge gate. | People who own a business problem should not need to write Python and evals to get an agent. | Proposed | `ai_governance` | No (I1 to I7) |
| D-14 | **Generated agents reach other systems only through a curated connector library.** Anything the library cannot do is handed to a person. | The AI must not invent integrations. A fixed library keeps review bounded. | Proposed | `ai_governance`, `security` | No (I2) |
| D-15 | **A different model family reviews the generated agent**, where residency allows. Its opinion is advisory. The gate and `agentic-bootstrap check` decide. | One model grading its own work shares its blind spots. | Proposed | `security` | No (I5) |

## How decisions are made

- A decision is a short record: what, why, status, owner. New ones are added to the roadmap table.
- If a decision needs an accountable role and it has not been assigned, the code is built behind a setting and the
  question goes to [Open questions](OPEN_QUESTIONS.md). Nobody guesses the owner's answer.
- If you change a decision, edit the roadmap first. The roadmap is the spec.

Some historical individual owners have been generalised. Their roles remain unresolved where no team was recorded; see [Open questions](OPEN_QUESTIONS.md).
