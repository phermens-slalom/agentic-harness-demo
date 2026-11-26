# Security

What the harness does to stay safe, what it does not cover, and what is still open.
This page describes the repo as it is. It is not a promise about anything outside the repo.

Not yet reviewed by security team. TODO: UNCONFIRMED sign-off (see the `TODO(security)`
notes in `policy/`).

## Reporting a problem

TODO: UNCONFIRMED. The repo names no security contact or reporting process. Add one before this repo is shared
more widely.

## The main ideas

| Idea | Plain English |
|---|---|
| Plain code decides | The merge gate never calls an LLM. It follows rules. |
| Fail closed | Unknown or missing evidence is a stop, never a pass. |
| People for the risky parts | Files that control the gate or agent behaviour always need people. |
| Treat outside text as untrusted | Issue text, CI output, repo files and model output are checked before use. |
| No standing secrets | The GitHub App and Workload Identity Federation. No personal tokens. |
| Stay in Australia | Allowed regions only. No global endpoints. |

## Controls in place

| Threat | Control | Where |
|---|---|---|
| An agent changes the rules that judge it | Control files are tier 3. AI governance team and security team approve. Never auto-merged. | `policy/risk_tiers.yaml` (`harness-controls`) |
| An agent weakens tests to pass | Tamper check: deleted tests, added skips, fewer asserts, edited baselines, lowered thresholds, edited test config | `nodes/tamper_check.py` |
| A change adds a new model, host, region, store or dependency quietly | Capability check adds approvers and withdraws auto-merge | `nodes/capability_check.py`, `policy/capabilities.yaml` |
| Missing or false check results | The gate escalates when any required check is missing or failing | `nodes/merge_gate.py` |
| An agent approves its own work | Reviewer lockout | `nodes/merge_gate.py` |
| Prompt injection in issues, CI output, review findings, PR comments or repo files | Input guard: Model Armor and Sunglasses together, blocked if either blocks. Fails closed on any scanner error. Ships in `shadow` mode. | `nodes/input_guard.py`, `adapters/composite_scanner.py`, `policy/input_guard.yaml` |
| A model call is steered or leaks | `ModelArmorPlugin` on the harness's ADK app screens model input and replies. Outside local use both templates are required. | `adapters/adk_agents.py` |
| A model-chosen file name reads a secret | Repo context refuses absolute paths, `..` and a deny list. Caps the size. | `nodes/repo_context.py`, `policy/routing.yaml` |
| An LLM reply is malformed or hostile | Output is parsed against a schema. One retry, then escalate. | `adapters/adk_agents.py` |
| Data leaves Australia | Allowed regions only. Model backend must be Vertex AI outside local use. | `residency.py`, `policy/residency.yaml` |
| A changed skill alters behaviour | A skill loads only if pinned by version and file fingerprint | `skills.py`, `policy/skills.lock.yaml` |
| Path case or renames dodge a rule | Matching ignores case and slashes. Both old and new paths count. | `policy.py` |
| A typo in a policy file changes behaviour | Strict schemas reject unknown keys. Cross-file checks. | `policy_validation.py` |
| Workflow files leak access | Least-privilege permissions, actions pinned by SHA, `zizmor` | `.github/workflows/`, template workflows |
| Agent-written test code mints cloud credentials | Only the `evals_no_regression` job gets `id-token: write`, in a named environment | `agent-template/.github/workflows/agent-checks.yml` |
| Secrets in code | Gitleaks over the PR commits. Traces hold names and sizes, never content. | CI, workflow design |
| Another agent framework sneaks in | A policy check rejects imports of other frameworks | `bootstrap/security_harness.py` |

## Things the controls do not cover

Be clear about the limits.

| Limit | Detail |
|---|---|
| Sunglasses is a pattern matcher | A cheap tripwire. Two phrasings are known to get through it (an HTML-comment instruction and a terse exfiltration phrasing). Model Armor is meant to cover them, but that has not been tried against the live service. |
| Model Armor has not been run live | CI plays back a fixture authored from the API shape, not recorded responses. It proves the wiring, not detection quality. It is available in Melbourne only among the allowed regions, with three filters. |
| The guard ships in `shadow` mode | In shadow mode a match is recorded but does not stop the task. It must also be switched on by passing a guard to the workflow. |
| The capability check sees only the diff | It does not see lock-file-only dependency changes or things added outside the diff. |
| Pattern matches are review routing, not permission | Tool access must be enforced in code and platform IAM. |
| Copilot's firewall allowlist is set in GitHub settings | Not from a repo file, and it does not cover the setup steps. |
| Residency of GitHub Copilot is not confirmed for Australia | See D-10 and Q3. This could block Copilot as the default builder for classified repos. TODO: UNCONFIRMED. |
| The real GitHub client does not exist yet | R2 is blocked on an authentication decision. |
| The reviewer does not see the diff yet | It sees file names and repo context. R7 is planned. |
| No audit log or trace export yet | O1 is planned. Traces exist in memory per task only. |
| `evals_no_regression` in generated repos is a stub | It fails until wired up (E3). |
| Not all CodeQL and dependency review run | They need a public repo or `GHAS_ENABLED=true` (Q11). |

## Supply chain

- `sunglasses` is pinned to an exact version (`0.6.20`). The evaluation notes it is a young, single-maintainer
  package and that its source was skimmed, not audited. It needs a dependency review, an approved package source and
  hash-pinned installs before real use (S5 planned).
- The template's Copilot setup step installs `google-agents-cli` without a pin. TODO(security).
- Gitleaks is installed from its official release and checked by SHA-256.

## Open security decisions

These need security team. They are also in [Open questions](OPEN_QUESTIONS.md).

1. The full list of control files (D-02) and which YAML counts as privileged (Q1).
2. How to authenticate Copilot assignment without a personal token (R2).
3. Whether to let Copilot workflows skip approval (Q4).
4. Copilot residency for each data classification (Q3, D-10).
5. Model Armor as the main scanner, with Sunglasses as a tripwire beside it (D-09): built, but not signed off. Whether templates are required outside local use, and what they screen.
6. The starting allowlists in `policy/capabilities.yaml` and the caps in `policy/routing.yaml`.

See also: [Decisions](DECISIONS.md), [Input guard](tech/INPUT_GUARD.md).
