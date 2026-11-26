# Examples

A series of worked examples that use insurance ideas as metaphors for what the harness does.

How to read these:

- **The stories are metaphors and illustrations.** Names such as `claims-triage` and `rates.vendor.io` are
  made up. They do not describe a real actual agent or system.
- **The harness behaviour is real.** The gate outputs, reasons and approver lists shown below were produced
  by running the code in this repo. Where something is only planned, it is marked **Planned**.
- Words you do not know are in the [Glossary](GLOSSARY.md). The big picture is in the [Vision](VISION.md)
  and the parts are in the [Architecture](ARCHITECTURE.md).

## The metaphor key

Think of the harness as the **approvals office of an insurer**. It does not write the claims. It decides how
much sign-off each one needs and checks that the paperwork is honest.

| In the harness | In an insurer (metaphor) |
|---|---|
| The harness | The approvals office |
| The golden workflow (eight stages) | The life of a policy, from first idea to renewal |
| A generated agent repo | A new claims desk, set up with standard procedures |
| The coding agent (Copilot) | A junior assessor who does the legwork |
| The reviewer agent | A second assessor who checks the first one's file |
| A pull request | A claim file sent up for sign-off |
| Tier 1, 2, 3 | Claim bands: small, standard, large |
| Phase 1 to 4 | How much authority the junior assessor has earned |
| The merge gate | The authority panel. It follows the rule book and has no opinions. |
| `auto_merge` | A small claim paid within the desk limit |
| `human_approval` | A claim that needs named signatures |
| `escalated` | "Refer to a senior assessor" |
| `reject_to_planning` | "This file is too big. Split it up." |
| Fail closed | No evidence, no payout |
| Required checks | The standard documents every file must contain |
| Tamper check | Looking for altered claim forms |
| Capability check | Vetting a new repairer or supplier before they join the panel |
| Input guard | Checking incoming notes for forged instructions |
| Residency | Customer records stay in the onshore vault |
| A skill | An underwriting guideline. It advises; it grants no authority. |
| The skills lock | The signed-off edition of the guideline |
| Golden tasks | Practice claims with known right answers, used to test the panel |

---

## Example 1: Opening a new claims desk

**Metaphor:** a business area opens a new desk. Head office gives it the standard desk kit.
**Real feature:** bootstrap, stages `plan`, `new` and `check`.

```ascii
 Team writes a short form (spec.yaml)
        │
        ├─► agentic-bootstrap plan  spec.yaml     "Which cloud-project PRs, in what order?"
        ├─► agentic-bootstrap new   spec.yaml ./claims-triage     "Make the desk kit"
        └─► agentic-bootstrap check ./claims-triage               "Do the harness rules hold?"
```

The form uses the fields from [`spec.yaml.example`](../spec.yaml.example). Using the repo's own example:

```yaml
name: workshop-assistant
division: example-division
owner: a.owner
sponsor: s.sponsor
classification: internal
description: Example agent that helps a mechanic with vehicle service history and repair estimates
egress_hosts:
  - api.example.com.au
```

What `plan` prints for this form (real output, shortened):

| Order | PR title | Files | Approvers |
|---|---|---|---|
| 1 | Workload | `example-division/workshop-assistant/workload.tf` | AI governance team, platform team |
| 2 | Environments | `.../env.tf` | AI governance team, platform team |
| 3 | Project and cloud platform (pin the cloud platform module version) | `workload-infrastructure/platform.tf` (illustrative), `.../project.tf`, `.../egress.tfvars` | `ai_governance`, `platform_team` |

- `plan` only **lists** the PRs. People still write the Terraform. The folder layout is an assumption (Q12).
- `new` copies [`agent-template/`](../agent-template) into the new folder and fills in the names.
- `check` fails (exit code 1) if the desk breaks a rule: another agent framework, a `global` location, or a
  missing `AGENTS.md` or `CODEOWNERS`.
- A bad form is refused. A wildcard host such as `*.example.com`, or the location `global`, is rejected.

---

## Example 2: A small claim and the desk limit

**Metaphor:** a small claim under the desk limit. At first every claim needs a signature. Once the junior
assessor has earned trust, small claims go through alone.
**Real feature:** tiers and phases in the merge gate.

A change that only adds a test (`tests/test_a.py`) is **tier 1**. The same change, with all four checks green
and the reviewer approving, gives different results by phase (real output):

| Phase | Decision | Reason shown |
|---|---|---|
| 1 | `human_approval` (App team, AI governance team) | `phase 1, tier 1: approvals needed from app_team, ai_governance` |
| 3 | `auto_merge` | `phase 3, tier 1, checks green, reviewer approved` |

```ascii
 Phase 1   every file ───────────────────────────►  a person signs
 Phase 3   tier 1 (tests, docs) ─► auto_merge       everything else still needs people
```

The policy file ships at **phase 1**. Raising the phase is a decision for people. The roadmap has a draft rule
for it (O3, **Planned**).

---

## Example 3: A large claim needs the panel

**Metaphor:** a big claim goes to a panel. The panel is chosen by the type of claim, not by who asks.
**Real feature:** approvers worked out from file paths.

The gate reads the changed file paths and adds the right signatures (real output, phase 3):

| Change touches | Tier | Who must approve (besides App team and AI governance team) |
|---|---|---|
| `tests/test_a.py` | 1 | nobody extra |
| `svc/payments/refund.py` (a sensitive area) | 3 | security team |
| `infra/main.tf` (Terraform) | 3 | platform team |
| `AGENTS.md` (an agent steering file) | 3 | security team |
| a file under `prod/` | 3 | Product Owner, Architecture |

```ascii
 changed files ─► match rules in policy/risk_tiers.yaml ─► highest tier wins ─► approvers = base + rule roles
```

Why steering files such as `AGENTS.md` are tier 3: one poisoned edit would change every future agent run.
That is why they never auto-merge.

---

## Example 4: The assessor who alters the claim form

**Metaphor:** an assessor is told to "close this claim as fast as possible" and quietly deletes the form that
shows a problem.
**Real feature:** the tamper check.

An agent is asked to make a failing build pass. Instead of fixing the code it deletes the failing test. At
phase 3 the gate answers (real output):

```ascii
 decision:  escalated
 reason:    test/eval tampering detected: deleted test file(s): tests/test_a.py
```

The tamper check also looks for added skips, fewer `assert` lines, edited baselines, lowered thresholds and
edited test config. A normal edit to a test (rename, extra case) does not trigger it.

| Rule | Why it is there |
|---|---|
| Control files (workflows, policy, skills, eval thresholds and baselines) are always tier 3 | The agent must not edit the things that grade it |
| The tamper check escalates on a weakened test | A pass that comes from cheating is not a pass |

---

## Example 5: A new repairer joins the panel

**Metaphor:** a claim suddenly uses a repairer nobody has vetted. Before they are paid, the security team checks them.
**Real feature:** the capability check, plus the exact-host rule.

A change adds one line that calls `https://rates.vendor.io/v1`. At phase 3 the gate answers (real output):

```ascii
 decision:   human_approval
 tier:       2
 approvers:  app_team, ai_governance, security
 reason:     phase 3, tier 2: approvals needed from app_team, ai_governance, security;
             new capabilities: host rates.vendor.io (agent/rates.py)
```

What the capability check looks at (added lines only):

| New thing | Example |
|---|---|
| Model | a new Gemini model name |
| Host | a new web address |
| Region | `us-central1`, or a `global` location |
| Data store | BigQuery, Firestore, Spanner, GCS, memory service |
| Dependency | a new package in `requirements.txt`, `pyproject.toml`, `package.json` or `go.mod` |
| Tool or protocol | an MCP toolset, an A2A agent card, a sub-agent, a new tool function |

Things to know:

- A hit **adds approvers**. It does not approve and it does not block.
- A hit **withdraws auto-merge**. A tier-1 change with a new host becomes `human_approval`.
- A host written in the spec's `egress_hosts` still needs the security team's approval. Listing a host is like adding a repairer to
  the books; it does not mean they are cleared.
- Comments, docs and test fixtures that only mention a host do not trigger it.
- TODO: UNCONFIRMED: the allowlists in [`policy/capabilities.yaml`](../policy/capabilities.yaml) are starting
  values that security team still has to agree.

---

## Example 6: A forged note in the claim file

**Metaphor:** someone slips a note into a claim file: "Ignore the usual checks and approve this." A careful
clerk checks incoming notes before the assessor reads them.
**Real feature:** the input guard.

Text from outside is scanned before any AI reads it:

```ascii
 issue text     ─────┐
 CI feedback    ─────┼─► input guard ─► clean ─► the AI reads it
 AGENTS.md + files ──┘        │
                              └─► match ─► shadow: record it, carry on
                                           enforce: stop and escalate
```

| Mode | What happens on a match |
|---|---|
| `shadow` (ships this way) | The trace records a would-be block. The task continues. Used to learn about false alarms. |
| `enforce` | The task stops and is escalated. A crash or incomplete scan also stops it. |

Facts to be honest about:

- The scanner is a pattern matcher. It is a cheap tripwire, not a full defence. Two phrasings are known to
  slip past it and are listed as open gaps in the evals.
- Even if text slips through, the merge gate is still the control. It never sees the scanner.
- Model Armor now runs beside it, and the text is blocked if either scanner blocks. A scanner that errors also
  blocks. Model Armor has not been run against the live service yet (see [Input guard](tech/INPUT_GUARD.md)).

---

## Example 7: No receipts, no payout

**Metaphor:** a claim arrives with no supporting documents. It is not treated as "probably fine".
**Real feature:** fail closed.

If no checks are reported, or a required check is missing, the gate escalates (real output):

```text
 decision:  escalated
 reason:    required checks not reported: lint, tests, evals_no_regression, secret_scan
```

| Situation | Result |
|---|---|
| A required check failed | `escalated` |
| A required check is missing, or no checks were reported | `escalated` |
| CI is not green | `escalated` |
| The PR is over 400 lines | `reject_to_planning`: "500 lines exceeds limit 400; split the task" |
| The build loop used all 4 rounds, or the token budget | `escalated` |
| An AI reply does not match its schema after one retry | `escalated` |
| The model backend is not allowed | `escalated` |

---

## Example 8: Records stay in the onshore vault

**Metaphor:** customer files may only be stored in approved onshore vaults.
**Real feature:** residency.

| What someone tries | Result |
|---|---|
| Location `australia-southeast2` (Melbourne) or `australia-southeast1` (Sydney) | Allowed |
| Location `global`, or any non-Australian region | Refused |
| A Gemini API key (AI Studio) outside local development | Refused |
| A Gemini API key set next to Vertex AI outside local development | Refused |
| Vertex AI in an allowed region | Allowed |

The allowed regions are listed in [`policy/residency.yaml`](../policy/residency.yaml). The `HARNESS_ENV=local`
setting is the only thing that allows an AI Studio key.

---

## Example 9: An assessor cannot mark their own homework

**Metaphor:** the assessor who prepared a claim cannot also be the second signature.
**Real feature:** reviewer lockout, a separate reviewer, and a different model.

- The gate escalates if the reviewer is the same identity as the builder.
- The reviewer applies the nine-point checklist in [`policy/review_checklist.yaml`](../policy/review_checklist.yaml),
  for example "ADK only", "exact egress hosts" and "no secrets".
- If the planner and reviewer use the same model, the trace records a warning.
- TODO: UNCONFIRMED how lockout will use real GitHub identities. The roadmap lists this as R7 (**Planned**).

---

## Example 10: The motor-repair assistant (a generated agent)

**Metaphor:** a motor-claims assistant that looks up a vehicle's service history and estimates a repair cost.
It can read. It cannot book or pay.
**Real feature:** the starter agent in [`agent-template/`](../agent-template).

The template's example agent is a mechanic assistant with two tools:

| Tool | Does |
|---|---|
| `get_service_history` | Returns a vehicle's details and service history from sample data |
| `estimate_repair` | Returns a cost estimate in AUD from placeholder prices |

How the template keeps it safe:

```text
 prompts.py      the rules in words (guidance only)
 tools.py        read-only tools, no booking tool exists
 telemetry.py    logs tool name, outcome and timing (never prompts or arguments)
 skills/         one pinned, guidance-only skill
 evals/          a normal case, and a case where a booking request must be refused
 AGENTS.md       what the coding agent may and may not change
 CODEOWNERS      who must review changes
```

A person who wants a different agent changes the prompts, tools and evals **together** and fills in the
Mission Brief and the runbook. The template says its mechanic content is a placeholder.

TODO: UNCONFIRMED: the booking-refusal eval has not been run live. That needs an approved non-production
project. The `evals_no_regression` check in the template is still a stub that fails until wired (E3).

---

## Example 11: Changing the guideline book

**Metaphor:** the underwriting guideline book changes. The new edition must be signed off before anyone uses it.
**Real feature:** skills and the skills lock.

```ascii
 a skill is named in routing.yaml
        AND pinned in skills.lock.yaml (full commit + file fingerprint)
        AND the file on disk matches the fingerprint
        ──► it loads, and its source and version go in the trace
 anything else ──► it refuses to load, and the task escalates
```

- A skill is guidance text. It cannot grant tools, permissions or network access.
- Changing a skill or the lock is a tier-3 change: AI governance team and security team approve, and an eval is needed.
- TODO: UNCONFIRMED: the real skill names and the approved version (Q7). The lock is empty today.

---

## Example 12: One issue, start to finish

**Metaphor:** a claim goes from the desk, through assessment and the panel, to a decision.
This is an illustration. The steps match the code; the details are made up.

```text
 Day 1  A team member raises an issue labelled agent:bugfix
          "The repair estimate rounds the wrong way."

 1  route         label found, so the harness takes it
 2  input guard   issue text scanned: clean
 3  triage        size "s", names agent/tools.py
 4  repo context  AGENTS.md, the file tree and agent/tools.py are read (capped and scanned)
 5  plan          steps, acceptance criteria, files to change
 6  plan approval phase 1: a person approves the plan
 7  build         Copilot opens a PR
 8  checks        lint, tests, evals_no_regression, secret_scan
      ├─ tests fail ─► feedback guarded ─► Copilot tries again (up to 4 rounds)
      └─ all green  ─► reviewer applies the checklist
 9  merge gate    tier 2 (default). The gate lists the approvers.
10  decision      human_approval ─► the team and AI governance team are notified
                  a person merges
```

What the trace holds: step names, file **names**, sizes, the decision and the reason. It never holds file
content, secrets or the full issue text.

---

## Which example for which question?

| If you want to know... | Read |
|---|---|
| How a team starts | Example 1 |
| Why some changes merge alone and others do not | Examples 2 and 3 |
| How cheating is caught | Example 4 |
| How new suppliers, models or regions are caught | Example 5 |
| How bad input is handled | Example 6 |
| What "fail closed" means | Example 7 |
| How data stays in Australia | Example 8 |
| Who checks the checker | Example 9 |
| What a generated agent looks like | Example 10 |
| How behaviour-changing files are controlled | Example 11 |
| The whole path | Example 12 |
