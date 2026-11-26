# Harness roadmap and work log

The backlog for the **harness** itself (not the agents built on it). It holds the decisions we've
made, the work grouped into milestones, a ready-to-run Claude Code prompt for every item, and an
append-only work log at the bottom.

- **Scope:** `app/harness`, `policy/`, `evals/`, `agent-template/`, CI, and the harness's own infra.
- **Inputs, in order of precedence:** repository requirements and the illustrative, adaptable RACI policy, then prior
  architecture notes, then public platform documentation, then industry practice.
- **Baseline:** repository snapshot reviewed on 12 Nov 2026.

## How to use this file

1. Pick the top `todo` item in the current milestone whose `Depends on` items are `done`.
2. Open Claude Code in the repo root. Set the model and effort level listed on the item. For items
   marked **plan first**, start in plan mode and approve the plan before any edits.
3. Paste the item's prompt. Each prompt is self-contained, but they all say "read the item in
   `docs/ROADMAP.md`" so the agent sees the acceptance criteria.
4. One item = one branch (`roadmap/<id>-<slug>`) = one PR. In that same PR, the agent sets the item's status
   to `done`, ticks its "Done when" boxes and adds a work-log entry. Merging the PR is the approval, so a merged
   PR means the item is done. There are no follow-up PRs to close out earlier work. If part of the work is
   unfinished, leave the item `doing` or `blocked` and say what is left.
5. If you change an item mid-way, edit it here first. This file is the spec, and the prompt is only a
   pointer to it.

**Status:** `todo` · `doing` · `blocked (reason)` · `review` · `done` · `dropped (reason)`
`done` is set in the PR that does the work, so no PR number is needed (the merge commit links to the PR). `review`
is only for work that is merged but still has a step outside the repository to finish, such as a live run. List
that step in the item. Older entries may read `done (PR #n)` or `done (working tree)`; both mean done.
**Priority:** P0 = before the agent discussion next week · P1 = before the pilot agent · P2 = after the pilot
**Size:** S ≤ half a day · M ≤ 2 days · L > 2 days (split it if you can)

**Choosing the model and effort.** Use Opus with high or extra-high effort for anything security-relevant,
policy-shaping, or architectural: in those areas a subtle mistake becomes a control failure. Use Sonnet
for well-specified implementation work, and Haiku for mechanical cleanup. When an item touches the merge
gate, lean towards more effort, not less.

### Definition of done (applies to every item)

- `ruff check .`, `ruff format --check .`, `codespell`, `ty check`, `pytest -q` and `python evals/run_evals.py` all pass locally and in CI.
- Behaviour changes come with tests. Gate or policy changes also get a golden or adversarial eval task
  (`evals/golden_tasks/`).
- The merge gate still never calls an LLM. No new agent framework (ADK only). No personal tokens.
- Docs touched where behaviour changed (`README.md`, `docs/*.md`).
- This file: item status set to `done`, and a dated entry added to the work log, in the same PR.
- Anything that needs a stakeholder decision is marked `TODO(<owner>)` in code and listed under
  [Open questions](#open-questions), not guessed silently.

> **Why a markdown file and not only GitHub Issues?** Issues are the better long-term tracker, and each
> ID below is stable so it can be mirrored into an issue or a Project board. But the coding agent needs
> the plan, the decisions and the acceptance criteria in the repo, versioned alongside the code they
> describe. Keep this file as the spec, and link each item to its issue or PR once one exists.

---

## Decisions

Decisions are lightweight ADRs (architecture decision records) written to unblock the work. A decision
marked *proposed* gets built behind config or a port, so it can be reversed cheaply when the appropriate role or owner
rules on it.

| ID | Decision | Why | Status / owner |
|---|---|---|---|
| D-01 | **The merge gate fails closed on missing evidence.** No checks reported, an unknown check state, or a missing required check means escalate, never auto-merge. | Today an empty check report can auto-merge at phase 3. Unknown is not green. | Accepted |
| D-02 | **The files that control the gate are tier 3 and never auto-merge.** That covers policy, CI workflows, CODEOWNERS, rulesets, eval thresholds and baselines, skills/prompts/agent steering files, and tool/agent definitions. AI governance team and security team approve. | Otherwise an agent can edit the grader, permissions, or behaviour that governs it (reward hacking and excessive agency). | Proposed (security team) |
| D-03 | **GitHub enforces the gate, and the harness only decides.** The gate's decision is published as a required check run (`harness/merge-gate`) via the GitHub App, and a repository ruleset requires it. CODEOWNERS is *generated* from `policy/risk_tiers.yaml`. | One source of truth for policy, which GitHub enforces even if the harness is down or bypassed. | Accepted |
| D-04 | **Plan approval by a human is deterministic.** It is always required in phases 1 and 2. From phase 3 it is required when the predicted tier (from the files the plan names plus the issue's labels) is ≥ 2. The LLM's `touches_sensitive_areas` flag can only *add* an approval, never remove one. | An injected issue must not be able to switch off the human checkpoint. | Accepted |
| D-05 | **Runtime: an ADK 2.0 Workflow hosted on Cloud Run** (`australia-southeast2`). Sessions are persisted to Cloud SQL for Postgres in the same region through ADK's database session service. Agent Runtime stays the target for the *agents*, and moving the harness there can be revisited later. | Durable human-approval pauses that survive restarts. A webhook receiver needs plain HTTP anyway. Avoids the reported friction deploying graph workflows to Agent Runtime. | Proposed (platform team) |
| D-06 | **Ingress runs through a queue.** A Cloud Run receiver verifies the GitHub webhook signature, dedupes on `X-GitHub-Delivery`, and enqueues to Cloud Tasks. Workers are idempotent per `(repo, issue)`. | Redelivered webhooks must not start a second Copilot assignment, and bursts must not flood Copilot. | Proposed (platform team ingress route) |
| D-07 | **Audit and telemetry:** OpenTelemetry traces cover workflow, model, tool, handoff and approval operations and go to Cloud Trace (ADK emits GenAI conventions). Every gate decision is also written as an append-only row in BigQuery (`australia-southeast2`) with policy and behaviour-artefact revisions, its inputs and approvers. | Reviewers need to explain why an action happened without retaining secrets or sensitive prompt/tool payloads. In-memory traces are lost on exit. | Proposed (AI governance team) |
| D-08 | **Use what exists before building security (the ladder's Curate rung).** Use gitleaks (pinned) in CI and GitHub secret scanning with push protection where licensed, plus CodeQL, `dependency-review-action` and `zizmor`. `agentic-bootstrap check` keeps only harness-specific rules. | Building our own secret regexes is the ladder's "Code" rung, when an existing tool covers it. | Accepted |
| D-09 | **Model Armor is the primary input scanner, and Sunglasses is a cheap tripwire beside it.** Both sit behind the `InputScanner` port. The harness's own ADK app also registers ADK's `ModelArmorPlugin`. | Pattern matchers miss novel phrasing; adoption of a semantic scanner remains a proposal. | Proposed (security team) |
| D-10 | **Copilot stays the default builder, but residency is an explicit gate on it.** Builder residency becomes policy. If GitHub can't confirm Australian processing for the coding agent, the Cloud Run sandbox builder (Gemini CLI, Melbourne) becomes the fallback for classified repos. | `residency.py` only guards Vertex today. Copilot's in-region processing was US/EU only as of April 2026. | Proposed (security team). **Possible blocker** |
| D-11 | **Phase promotion is evidence-based.** The gate runs in shadow mode at the next phase, and a phase is raised only once the agreed thresholds are met (draft in O3). | Today the rule is "raise after the evals show it's trustworthy", with no criteria. | Proposed (Unassigned) |
| D-12 | **The template is based on an existing reference agent template, pinned by git ref, with a project-specific overlay on top.** `agent-template/` becomes the overlay plus a fallback. Generated repos can be upgraded in place (Copier-style). | Matches prior requirements: the bootstrap starts from existing reference agent template plus project-specific overlay, and must respect teams already on the current version. | Proposed (Unassigned) |
| D-13 | **An `AgentRequest` issue starts an intake agent that authors the agent.** Any person with access to the repository may raise an `AgentRequest` GitHub issue. An ADK intake agent interviews them in plain language on the issue, runs `agentic-bootstrap` to add the agent to the division's existing agent repo, writes the agent's Python (prompts, tools, evals) from their answers, and opens a PR. It only ever *raises* PRs. It never approves, merges, edits gate-controlling files outside the normal PR path, or sets business-owned thresholds. Every PR goes through the merge gate and the named approvers. The first build is a local/CLI prototype against fakes; the hosted trigger follows R2, R3 and R4. | People who own a business problem should not need to write Python, evals and CI config to get an agent. The harness already governs what an AI builder may change, so the intake agent is one more governed builder. | Proposed (AI governance team) |
| D-14 | **Generated agents reach outside systems only through a curated connector library.** The library contains tool templates reviewed by the designated teams (read and write patterns, declared egress hosts, IAM notes, approvers). The intake agent composes and configures them. A need the library cannot meet is flagged for a human build, never improvised. A connector that writes needs the trusted-approval boundary from A1. | The LLM must not invent integrations, hosts or credentials. A fixed library keeps the security team's review load bounded and keeps S3's new-capability detectors meaningful. | Proposed (AI governance team, security team) |
| D-15 | **A different model family reviews what the intake agent generates.** Generator and reviewer are different model families, subject to residency (D-10, `policy/residency.yaml`). Until a second family is approved for use in Australia, use two roles with separate prompts and context and record the gap. The reviewer scores the agent against its Mission Brief and proposes adversarial eval cases. Its opinion is advisory: the merge gate and `agentic-bootstrap check` still decide. | One model grading its own output shares its blind spots. | Proposed (security team) |

---

## Milestones at a glance

| Milestone | Theme | Items | Target |
|---|---|---|---|
| **M0** | Make the gate trustworthy | H0, G1–G7 | P0, this week |
| **M1** | Real GitHub, enforced | R1, R2, R7, S4 | P1 |
| **M2** | Durable, controllable runtime | R3, R4, R5, R6 | P1 |
| **M3** | Security: use what exists | S1, S2, S3, S5, D1 | P1 (D1 is a blocker check) |
| **M4** | Observability, audit, learning loop | O1, O2, O3 | P1 / P2 |
| **M5** | Evals that measure the agents | E1, E2, E3 | P1 / P2 |
| **M6** | Golden-workflow coverage | W1–W5 | P2 |
| **M7** | Hygiene | H1 | Any time |
| **M8** | Generated agent ready for the pilot | E3, H2, A1–A3 | P1 |
| **M9** | Agent intake and authoring | I1–I7 | P1 (offline prototype first; hosted trigger after R2–R4) |

Recommended order: **H0 → G1 → G2 → G5 → G3 → G4 → G6 → G7**, then **R2 → R1 → D1**, then
**R3 → R4 → R5**, then **O1** and the rest. **S4** can run in parallel after G6.
Start the offline M9 work (**I1 → I2 → I3 → I4 → I5 → I6**) in parallel with M8. It runs against fakes and
does not wait on R2; only **I7**, the hosted trigger, does.
Start the offline M8 work on the embedded template in parallel; it does not depend on W2 or on
standing up the parent harness runtime.

---

## M0 · Make the gate trustworthy

### H0 · Root `AGENTS.md` / `CLAUDE.md` for the harness repo
- **Status:** done (working tree) · **Priority:** P0 · **Size:** S · **Depends on:** none
- **Model / effort:** Sonnet 5.5 · medium
- **Why:** Every later prompt benefits when the agent loads the ground rules automatically. Only
  `agent-template/` has an `AGENTS.md` today. Writing these files first is standard harness practice
  ("guides before sensors").
- **Done when:**
  - [ ] `AGENTS.md` at the root: commands (install, lint, ty, test, evals, e2e), layout, the ground rules
        from the README, "never weaken a gate to make a test pass", and a pointer to this file.
  - [ ] `CLAUDE.md` is a one-line `@AGENTS.md` import, so Copilot and Claude Code share one source.
  - [ ] `AGENTS.md` is under 120 lines and every command in it actually runs.
  - [ ] Instructions preserve governed skill/prompt provenance, avoid putting secrets or sensitive
        prompt/tool data in traces, and treat prompts as guidance rather than authorisation.

```text
Read docs/ROADMAP.md item H0 and its "Done when" list, plus README.md, pyproject.toml, Makefile and
.github/workflows/ci.yml.

Create a root AGENTS.md for this harness repo (not agent-template/AGENTS.md, which is for generated
agents). Include: exact commands to install (.[dev]), lint (ruff), type-check (ty), test (pytest),
run evals (python evals/run_evals.py) and run e2e (scripts/e2e.py); a short layout map; the ground
rules from README "Ground rules"; and these rules for coding agents: never weaken a gate, threshold
or golden task to make a test pass; any change under policy/ or app/harness/nodes/ needs a new or
updated eval task; ask rather than guess when a TODO(<owner>) is involved. Point to docs/ROADMAP.md
as the backlog. Keep it under 120 lines.

Create CLAUDE.md containing only "@AGENTS.md". Run every command you list to confirm it works.
Update H0's status in docs/ROADMAP.md and add a dated work-log entry. One commit,
conventional-commit message.
```

### G1 · Fail closed when check evidence is missing
- **Status:** done (working tree) · **Priority:** P0 · **Size:** S · **Depends on:** none · **Decision:** D-01
- **Model / effort:** Sonnet 5.5 · high
- **Why (verified):** `RiskPolicy.missing_checks()` returns `[]` for an empty report, and
  `BuildResult.passed` is `True` when `ci_green` is true and there are no checks. So a tier-1 PR with
  *no checks reported* reaches `AUTO_MERGE` at phase 3. The golden task `quotes-150-add-tests-phase3`
  encodes this behaviour as expected.
- **Done when:**
  - [ ] The gate escalates when `build.checks` is empty, or when any `required_checks` entry is missing
        or not `True`. The reason names the missing checks.
  - [ ] `CopilotBuilder` no longer derives `ci_green=True` from an empty snapshot.
  - [ ] Golden tasks that relied on implicit green now list all four checks explicitly. A new adversarial
        task, `adv-gate-no-checks-reported`, expects `escalated` at phase 3.
  - [ ] Unit tests cover: empty checks, one missing check, a check reported as `False`, all green.

```text
Read docs/ROADMAP.md item G1 and decision D-01. Then read app/harness/policy.py (missing_checks),
app/harness/models.py (BuildResult.passed), app/harness/nodes/merge_gate.py,
app/harness/adapters/copilot_builder.py, tests/test_workflow.py, tests/test_policy.py and
evals/golden_tasks/*.yaml.

Bug: an empty check report is treated as "unknown, so fine", and a tier-1 PR with no checks
auto-merges at phase 3. Fix it so the gate fails closed: decision ESCALATED when checks are empty, or
when any policy.required_checks entry is absent or not True. Keep the change small and boring; this is
code the risk team audits. Keep the existing precedence of the gate's rules unless the new rule must
come first; explain in a code comment why.

Also stop CopilotBuilder computing ci_green=True from an empty snapshot. Update golden tasks that
relied on implicit green to list all four checks explicitly, and add an adversarial task
"adv-gate-no-checks-reported" (phase 3, tier-1 files, checks: {}) expecting escalated. Write the
unit tests in the "Done when" list first and watch them fail, then fix. Run ruff, ty, pytest and
evals. Update the item status and add a work-log entry in docs/ROADMAP.md.
```

### G2 · Put the files that control the gate in tier 3
- **Status:** done (working tree) · **Priority:** P0 · **Size:** S · **Depends on:** G1 · **Decision:** D-02
- **Model / effort:** Opus 5.5 · high
- **Why (verified at phase 3):** `.github/workflows/**`, `.github/CODEOWNERS`, `evals/thresholds.yaml`
  and `evals/baseline/**` are only tier 2, with no specific approver. `skills/**/SKILL.md`, any `*.md`
  prompt, and any `.py` under `tests/` other than `conftest.py` are tier 1 and **auto-merge**.
- **Done when:**
  - [ ] A new `harness-controls` rule (tier 3, approvers `ai_governance` and `security`) sits *before*
        `tests-and-docs`. It covers: `.github/workflows/**`, `.github/CODEOWNERS`, `CODEOWNERS`,
        `.github/rulesets/**`, `.github/copilot-setup-steps.yml`, `.github/agents/**`, `evals/thresholds*`,
        `evals/baseline/**`, `policy/**`, skill trees/lockfiles, `**/SKILL.md`, `**/prompts/**`,
        prompt markdown/Python files, and `**/*.prompt*`.
  - [ ] `tests-and-docs` is narrowed to `**/test_*.py`, `**/*_test.py`, `**/*_test.go`, `docs/**`,
        `README.md`, `CHANGELOG.md`. A bare `tests/**` no longer counts as tier 1.
  - [ ] One adversarial golden task per newly covered path family, each expecting `human_approval` at
        tier 3 at phase 3.
  - [ ] `docs/tech/INPUT_GUARD.md` and the policy comments are updated. `TODO(security)`
        sign-off marker added.

```text
Read docs/ROADMAP.md item G2 and decision D-02, then policy/risk_tiers.yaml, app/harness/policy.py,
evals/golden_tasks/adversarial_tasks.yaml and docs/tech/INPUT_GUARD.md.

Threat model: an agent (or a prompt injection steering it) that can edit the things that grade it can
make any change pass. Today CI workflows, CODEOWNERS and eval thresholds/baselines are tier 2 with no
specific approver, and SKILL.md files, markdown prompts and non-conftest Python under tests/ are
tier 1 (auto-merge at phase 3).

Add a "harness-controls" rule (tier 3, approvers [ai_governance, security]) with the paths listed in
the item, placed so first-match-wins picks it before tests-and-docs. Narrow tests-and-docs as
specified. Before editing, write a short table in your plan of every path that changes tier and
its old/new tier, and check that nothing which should stay tier 1 (plain test_*.py, docs/**) moves.
Add one adversarial golden task per newly covered path family. Do not touch merge_gate.py logic.
Run ruff, ty, pytest and evals. Update the policy comments, docs/tech/INPUT_GUARD.md, the item status
and the work log.
```

### G3 · Detect test and eval tampering
- **Status:** done (working tree) · **Priority:** P0 · **Size:** M · **Depends on:** G2
- **Model / effort:** Opus 5.5 · high · **plan first**
- **Why:** Reward hacking is the best-documented failure of coding agents: deleting tests, adding skips,
  weakening asserts, editing the eval thresholds (EvilGenie, 2025, and later work). File-edit detection
  is cheap and catches the explicit cases. Holdout tests catch the rest.
- **Done when:**
  - [ ] A new deterministic module, `app/harness/nodes/tamper_check.py`, reads a unified diff (`PRSnapshot`
        gains an optional `diff: str`) and returns findings for: deleted test files or test functions;
        added `skip`/`skipif`/`xfail`/`pytest.mark.skip`/`unittest.skip`/`@Disabled`/`t.Skip(`; net
        removal of `assert` lines in test files; edits to `evals/baseline/**`; lowered numbers in
        `evals/thresholds*`; edits to `conftest.py`, `pytest.ini`, `pyproject [tool.pytest]` or
        `setup.cfg [tool:pytest]`.
  - [ ] The gate escalates on any finding (reason lists them). It stays deterministic.
  - [ ] Each finding type has a unit test, a benign case that must not trigger, and an adversarial golden task.
  - [ ] `agent-template/` gains an `evals/holdout/README.md` describing CI-only holdout cases the coding
        agent never sees. (Implementing the holdout runner is tracked in E3.)

```text
Read docs/ROADMAP.md item G3. Then read app/harness/models.py (PRSnapshot, BuildResult),
app/harness/nodes/merge_gate.py, app/harness/adapters/copilot_builder.py and
evals/golden_tasks/adversarial_tasks.yaml.

Goal: a deterministic tamper check that stops an agent "passing" by weakening its tests or evals.
Start in plan mode and propose: the data flow (an optional unified diff on PRSnapshot/BuildResult,
passed to the gate), the detector list from "Done when", how to parse diffs with the standard library
only (no new dependency), and the false-positive cases you will test (e.g. renaming a test file,
moving an assert into a helper, a legitimate threshold increase).

After I approve: implement app/harness/nodes/tamper_check.py, call it from merge_gate.decide (escalate
on any finding, reason lists the findings), and add unit tests plus one adversarial golden task per
detector. Keep each detector a small, named, separately tested function so the risk team can read it.
Add agent-template/evals/holdout/README.md as described. Run ruff, ty, pytest and evals. Update the
item status and the work log.
```

### G4 · Make plan approval deterministic
- **Status:** done (working tree) · **Priority:** P0 · **Size:** S · **Depends on:** G1 · **Decision:** D-04
- **Model / effort:** Sonnet 5.5 · medium
- **Why:** `workflow.py` asks for plan approval only when the planner LLM sets
  `touches_sensitive_areas`. An injected issue can talk it out of that. The docstring says
  "HITL if tier 2+", which isn't what the code does.
- **Done when:**
  - [ ] `policy/risk_tiers.yaml` phases gain `plan_approval: always | tier_at_least_2`. Phases 1–2 are
        `always`, phases 3–4 `tier_at_least_2`.
  - [ ] `Plan` gains `files: list[str]` (the files it intends to change). The predicted tier is
        `policy.tier_for_change(plan.files, 0)`, with a missing list treated as the default tier.
  - [ ] The LLM flag can only add an approval. Tests prove the flag set to `False` cannot skip an
        approval that the policy requires.
  - [ ] `AdkPlanner`'s JSON contract asks for `files`. Docstrings are corrected.

```text
Read docs/ROADMAP.md item G4 and decision D-04, then app/harness/workflow.py (step 3),
app/harness/models.py (Plan), app/harness/policy.py, policy/risk_tiers.yaml,
app/harness/adapters/adk_agents.py (AdkPlanner) and tests/test_workflow.py.

Make the plan-approval decision deterministic, as the item describes. A per-phase plan_approval
setting in risk_tiers.yaml; Plan gets a files list; predicted tier from policy.tier_for_change on
those files (no files = default tier); the LLM's touches_sensitive_areas can only ADD a requirement.
Record in the trace which rule required approval. Update FakePlanner, AdkPlanner's JSON contract,
the workflow docstring and tests (including "LLM says not sensitive, policy still requires
approval"). Run ruff, ty, pytest and evals. Update the item status and the work log.
```

### G5 · Case-insensitive path matching, rename handling, and property tests for gate invariants
- **Status:** done (working tree) · **Priority:** P0 · **Size:** S · **Depends on:** G2
- **Model / effort:** Sonnet 5.5 · high
- **Why (verified):** `fnmatch` is case-sensitive on Linux, so `Payments/x.py` skips the sensitive-domains
  rule and `agents.md` auto-merges at tier 1. For renames, only the new path is evaluated, so moving a
  file out of `prod/` is judged on its new location only.
- **Done when:**
  - [ ] Matching lowercases both the path and the pattern explicitly (independent of OS). `\` is
        normalised to `/`.
  - [ ] `PRSnapshot`/`BuildResult` carry `previous_paths`, and tiering uses both old and new paths.
  - [ ] `hypothesis` is added to dev deps. Property tests check that: the gate never auto-merges when a
        required check is missing or false; adding a file never lowers the tier; tier ≥ the max of the
        per-file tiers; changing the case of a path never changes its tier.

```text
Read docs/ROADMAP.md item G5, then app/harness/policy.py (_matches, tier_for_change),
app/harness/models.py and tests/test_policy.py.

Fix path matching so it is case-insensitive and separator-normalised on every OS (don't rely on
fnmatch's platform behaviour; normalise explicitly and use fnmatchcase). Add previous_paths (renamed
from) to PRSnapshot and BuildResult and include them in tiering and approver derivation; update
CopilotBuilder and the fakes. Add hypothesis to the dev extra and write property-based tests for the
four invariants in the item. Add regression tests for "Payments/x.py" and "agents.md". Run ruff, ty,
pytest and evals. Update the item status and the work log.
```

### G6 · Least-privilege CI credentials in the agent template
- **Status:** done (working tree) · **Priority:** P0 · **Size:** S · **Depends on:** none
- **Model / effort:** Opus 5.5 · high
- **Why:** `agent-template/.github/workflows/agent-checks.yml` grants `id-token: write` at workflow level,
  so agent-authored test code in the `tests` job can mint cloud credentials through Workload Identity
  Federation (WIF).
- **Done when:**
  - [ ] Workflow-level `permissions: {}`. Each job declares only what it needs, and only
        `evals_no_regression` gets `id-token: write`.
  - [ ] All third-party actions are pinned to a full commit SHA, with the version in a comment.
  - [ ] `evals_no_regression` runs in a GitHub `environment: agent-evals-nonprod`.
  - [ ] `deployment/terraform/README.md` documents the WIF provider attribute condition (repository,
        `pull_request` event, environment) and a non-prod-only service account with Vertex user rights
        only. `TODO(platform_team)` added.
  - [ ] `zizmor` passes on both workflows (it's also wired into CI in S1).

```text
Read docs/ROADMAP.md item G6, agent-template/.github/workflows/agent-checks.yml,
.github/workflows/ci.yml and deployment/terraform/README.md.

Harden the generated agent's CI. Workflow-level permissions: {}; per-job least privilege; only
evals_no_regression gets id-token: write and runs in environment agent-evals-nonprod. Pin every
action to a full commit SHA with a "# vX.Y.Z" comment (look up the current SHAs; do not invent
them, and if you can't verify one, leave a TODO and tell me). Document the WIF attribute condition
and a non-prod-only service account in deployment/terraform/README.md with TODO(platform_team).
Do the same SHA pinning in the harness's own ci.yml. Run zizmor if it is available (uvx zizmor) and
fix what it reports. Update the item status and the work log.
```

### G7 · Schema-validate the policy files
- **Status:** done (working tree) · **Priority:** P0 · **Size:** S · **Depends on:** G2, G4
- **Model / effort:** Sonnet 5.5 · medium
- **Why:** A typo in `risk_tiers.yaml` (`teir: 3`, or an approver not in `raci.yaml`) silently changes
  behaviour.
- **Done when:**
  - [ ] Pydantic models (or JSON Schema plus a validator) for every file in `policy/`. `extra="forbid"`.
  - [ ] Cross-file checks: every approver and role exists in `raci.yaml`; every `required_checks` name
        exists as a job in `agent-template/.github/workflows/agent-checks.yml`; every route target is a
        known workflow.
  - [ ] `agentic-harness policy validate` CLI (or a `pytest` test) runs in CI. Bad-file fixtures prove it fails.

```text
Read docs/ROADMAP.md item G7 and every file in policy/, plus app/harness/policy.py, golden.py,
residency.py and nodes/input_guard.py.

Add strict schema validation for each policy file (pydantic v2 with extra="forbid" is fine as a new
runtime dependency; justify it in the PR body) and the cross-file checks in the item. The loaders
should validate on load so a bad file fails fast. Add a CI-visible test with deliberately broken
fixtures under tests/fixtures/policy_bad/. Do not change policy semantics. Run ruff, ty, pytest and
evals. Update the item status and the work log.
```

---

## M1 · Real GitHub, enforced

### R1 · Publish the gate as a required check run, and generate CODEOWNERS from policy
- **Status:** todo · **Priority:** P1 · **Size:** L · **Depends on:** G1, G2, R2 (the client) · **Decision:** D-03
- **Model / effort:** Opus 5.5 · extra-high · **plan first**
- **Why:** Today the gate's decision is advisory, so nothing stops a merge. The template's CODEOWNERS has
  already drifted from `risk_tiers.yaml` (e.g. `AGENTS.md` should go to `security`).
- **Done when:**
  - [ ] The gate's result is posted as a check run named `harness/merge-gate`, with a summary of tier,
        reason and required approvers. Conclusion: `success` only for AUTO_MERGE, or for HUMAN_APPROVAL
        once the required approvals are present; otherwise `action_required` or `failure`.
  - [ ] The gate re-evaluates on `pull_request.synchronize` and on `pull_request_review`. A new push
        invalidates the previous result.
  - [ ] `agentic-harness codeowners render` turns `risk_tiers.yaml` + a team-slug map
        (`policy/github_teams.yaml`, `TODO(ai_governance)`) into `.github/CODEOWNERS`. CI fails if the
        committed file differs.
  - [ ] `agent-template/.github/rulesets/agent-repo.json`: requires `harness/merge-gate`, `lint`, `tests`,
        `evals_no_regression`, `secret_scan`; code-owner review; stale-review dismissal; no bypass for
        the GitHub App or the Copilot actor.

```text
Read docs/ROADMAP.md item R1 and decision D-03. Then read app/harness/nodes/merge_gate.py,
app/harness/policy.py, app/harness/ports.py, policy/risk_tiers.yaml, policy/raci.yaml and
agent-template/.github/.

Goal: GitHub enforces what the harness decides. Start in plan mode and propose: (1) a
ChecksPort/extension to GitHubPort for creating and updating check runs, and how gate results map
onto check-run conclusions; (2) the events that re-trigger the gate and how stale results are
invalidated; (3) a CODEOWNERS renderer driven by risk_tiers.yaml + a team-slug map, with a
drift check in CI; (4) a ruleset JSON for agent repos. Verify the GitHub REST endpoints for check
runs and rulesets against current docs.github.com pages and cite them in the plan; mark anything
unverified.

After approval, implement with fakes and tests only (the real HTTP client is R2). The gate stays
pure: posting the check run happens in the workflow, not in merge_gate.py. Update README layout
table, the item status and the work log.
```

### R2 · Real `GitHubPort` on the GitHub App, Copilot-aware
- **Status:** blocked (Copilot issue assignment requires GitHub App user-to-server auth; installation tokens are not supported) · **Priority:** P1 · **Size:** L · **Depends on:** G1
- **Model / effort:** Opus 5.5 · high · **plan first**
- **Blocker:** GitHub's current [Copilot API guide](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/use-cloud-agent-via-the-api)
  says the issue-assignment API requires a user token and lists GitHub App **user-to-server** tokens as
  an option. It does not accept the server-to-server installation token required by this roadmap's
  no-PAT contract. Do not silently switch auth models; resolve this with security team first.
- **Why:** The only `GitHubPort` today is a fake. Copilot PR workflows **wait for a human to approve them
  by default**, so `wait_for_checks` would hang forever. Assignment is now possible through REST
  `agent_assignment` (fields `target_repo`, `base_branch`, `custom_instructions`, `custom_agent`, `model`).
- **Done when:**
  - [ ] `adapters/github_app.py`: app JWT → installation token (short-lived, scoped to one repo), retry
        with backoff on 5xx and secondary rate limits, and no PATs anywhere.
  - [ ] `assign_to_copilot` uses `agent_assignment` with `base_branch` and `custom_instructions`. `model`
        comes from builder residency policy (D1).
  - [ ] `wait_for_checks` has a timeout and returns a distinct state, `awaiting_workflow_approval`, which
        the workflow routes to `HumanGate.notify`. It never blocks forever.
  - [ ] It returns a diff (for G3/R7), `previous_paths` (G5) and the PR author.
  - [ ] Contract tests run the same scenarios against `FakeGitHub` and recorded HTTP fixtures (respx or
        vcrpy). No live calls in CI.
  - [ ] `TODO(security)`: decide on the "skip approval for Copilot workflows" repo setting.

```text
Read docs/ROADMAP.md item R2. Then read app/harness/ports.py, adapters/copilot_builder.py,
adapters/fakes.py, models.py and workflow.py.

Implement a real GitHubPort on a GitHub App (installation tokens only, never a PAT). Start in plan
mode. Before planning, read the current GitHub docs for: assigning issues to Copilot via REST
(agent_assignment), Copilot coding agent workflow-approval behaviour, check runs, PR files (incl.
previous_filename) and the diff media type. Cite the URLs in your plan and flag anything you could not
verify.

Plan must cover: auth/token lifecycle, retries and rate limits, timeouts, the new
"awaiting_workflow_approval" outcome and how workflow.py handles it, which HTTP library (prefer
httpx; justify), and contract tests that run identical scenarios against FakeGitHub and recorded
fixtures. After approval implement it behind the .[github] extra. Update README, the item status and
the work log.
```

### R7 · The reviewer sees the diff, and lockout uses real GitHub identities
- **Status:** todo · **Priority:** P1 · **Size:** M · **Depends on:** R2
- **Model / effort:** Sonnet 5.5 · high
- **Why:** `AdkReviewer` reviews only file names (the diff fetch is a TODO). The lockout compares the
  reviewer's ID to the hard-coded string `"builder-agent"`.
- **Done when:**
  - [ ] The reviewer prompt gets the size-capped unified diff and the `AGENTS.md` excerpt. Oversized diffs
        go back to planning rather than being truncated silently.
  - [ ] Lockout: the gate compares the PR author (Copilot bot), the reviewer identity, and the GitHub
        users who approved. An approval by the issue author alone does not satisfy `app_team`.
  - [ ] The reviewer posts its findings as a `harness/review` check run (the AI governance team CLI pattern). In
        Phase 1 it is advisory (`neutral`).

```text
Read docs/ROADMAP.md item R7, app/harness/adapters/adk_agents.py (AdkReviewer),
nodes/merge_gate.py, models.py and policy/review_checklist.yaml.

Give the reviewer the real diff (from R2's GitHubPort) with a size cap from policy (over the cap =
REJECT_TO_PLANNING, not silent truncation). Replace the string-compare lockout with identity data:
PR author, reviewer identity, and the list of human approvers from GitHub, and enforce the rules in
the item. Post reviewer findings as a "harness/review" check run, neutral in Phase 1. Add tests
with fakes. Run ruff, ty, pytest and evals. Update the item status and the work log.
```

### S4 · Copilot environment in the template
- **Status:** done · **Priority:** P1 · **Size:** S · **Depends on:** G6
- **Model / effort:** Sonnet 5.5 · medium
- **Why:** The template has no `.github/workflows/copilot-setup-steps.yml`. Copilot's built-in firewall
  and setup steps are the "Configure" rung of the ladder, so use them before building our own sandbox.
- **Done when:**
  - [x] `.github/workflows/copilot-setup-steps.yml` (the path GitHub requires) with a single job named `copilot-setup-steps`. It installs uv and
        Python 3.13, then `agents-cli install`. Actions pinned by SHA, minimal permissions.
  - [x] The firewall allowlist is generated from `spec.egress_hosts` + package mirrors into
        `docs/copilot-agent-environment.md`, with `TODO(security)` for the approved package source. GitHub
        configures the firewall in GitHub settings, not from a file, so a repo admin
        applies the list; it is not enforced by the repo. Entries render as `https://host/` URLs,
        because a bare domain also allows all its subdomains. The firewall does not cover setup steps.
  - [x] A custom agent definition at `.github/agents/agent-builder.agent.md` (GitHub's naming) that points
        to `AGENTS.md`, with `tools` limited to read/edit/search/execute. `CopilotBuilder` passes
        `custom_agent` (`TODO(verify)` the exact identifier the API expects in R2).
  - [x] These paths are covered by `harness-controls` (G2). The policy listed
        `.github/copilot-setup-steps.yml`, which GitHub does not use. The real file,
        `.github/workflows/copilot-setup-steps.yml`, is covered by `.github/workflows/**`, so the wrong
        entry was removed. Adversarial tasks cover the setup file and the agent profile.

```text
Read docs/ROADMAP.md item S4, agent-template/.github/, agent-template/AGENTS.md,
app/harness/bootstrap/template.py and spec.py.

Check the current GitHub docs on customising the Copilot coding agent environment
(copilot-setup-steps.yml, firewall allowlist, custom agents) and cite them in the PR. Add the files
in the item to agent-template, rendering the firewall allowlist from spec.egress_hosts at bootstrap
time. Wire custom_agent into CopilotBuilder's assignment. Add bootstrap tests. Update the item status
and the work log.
```

---

## M2 · Durable, controllable runtime

### R3 · Port to an ADK 2.0 Workflow with persistent sessions
- **Status:** todo · **Priority:** P1 · **Size:** L · **Depends on:** G1, G4, R2 · **Decision:** D-05
- **Model / effort:** Opus 5.5 · extra-high · **plan first**
- **Why:** State is held in memory today. A paused plan approval can't survive a restart, and
  `CopilotBuilder._pr` is lost if the process dies. ADK 2.0 (GA May 2026) has graph workflows that can
  pause durably for human input, but they're only durable if the session store is.
- **Done when:**
  - [ ] An exact `google-adk` pin. `docs/tech/ADK_PORT.md` is updated with the verified API.
  - [ ] Each step in `workflow.py` is an ADK node, per the mapping in `docs/tech/ADK_PORT.md`. Plan approval is an
        ADK pause point. No broad `except` in nodes.
  - [ ] Database session service with SQLite locally and Cloud SQL Postgres (`australia-southeast2`) in
        cloud. A run resumes after a kill.
  - [ ] Idempotency key `(repo, issue_number)`. Re-running a finished or in-flight task is a no-op that
        returns the existing state.
  - [ ] `tests/test_workflow.py` runs unchanged against both the old orchestrator and the new graph
        (parametrised), and they produce identical outcomes on every golden task.

```text
Read docs/ROADMAP.md item R3, decision D-05, docs/tech/ADK_PORT.md, app/harness/workflow.py, ports.py,
models.py, adapters/ and tests/test_workflow.py.

Port the issue_to_merge orchestrator to an ADK 2.0 Workflow. Start in plan mode. First, read the
current ADK 2.0 Python docs at adk.dev (workflows/graphs, human-input pauses and resume, session
services, NodeInterruptedError guidance) and pick an exact google-adk version; cite the URLs. If the
docs and your memory disagree, trust the docs and say so.

Plan must show: the node graph, where the plan-approval pause sits and how it resumes, session-service
choice (SQLite local, Postgres in cloud), the idempotency key and what happens on a duplicate start,
and how you'll prove behavioural equivalence (the existing tests and evals parametrised over both
implementations). Keep the merge gate a pure function node. Keep the old orchestrator until
equivalence is proven; deleting it is a separate follow-up. Update docs/tech/ADK_PORT.md, README, the item status
and the work log.
```

### R4 · Webhook ingress via a queue
- **Status:** todo · **Priority:** P1 · **Size:** M · **Depends on:** R3 · **Decision:** D-06
- **Model / effort:** Sonnet 5.5 · high
- **Done when:**
  - [ ] A Cloud Run service (`app/harness/ingress/`) that verifies `X-Hub-Signature-256` with a
        constant-time comparison, rejects anything unsigned or stale, and dedupes on `X-GitHub-Delivery`
        (stored for 7 days).
  - [ ] It handles `issues.labeled`, `pull_request.synchronize`, `pull_request_review`, `check_suite.completed`
        and `check_run.completed`. Everything else gets a 204.
  - [ ] It enqueues to Cloud Tasks (a `TaskQueuePort` with an in-memory fake). Workers resume the R3
        workflow by idempotency key.
  - [ ] Unit tests: bad signature, replay, an unknown event, a duplicate delivery.
  - [ ] `deployment/terraform/README.md` has `TODO(platform_team)` for the ingress route.

```text
Read docs/ROADMAP.md item R4 and decision D-06, then app/harness/workflow.py (or the R3 graph),
deployment/terraform/README.md and the GitHub webhook docs for signature validation and delivery
headers (cite them).

Build a minimal Cloud Run webhook receiver (prefer the stdlib or a tiny ASGI app; justify any
framework) that verifies the signature, dedupes deliveries, filters events and enqueues through a
TaskQueuePort (Cloud Tasks adapter + in-memory fake). Workers resume or start the workflow by
idempotency key. No business logic in the receiver. Add tests for each case in the item. Update
the deployment README, the item status and the work log.
```

### R5 · Operational controls: kill switch, allowlist, concurrency, time and budget caps
- **Status:** todo · **Priority:** P1 · **Size:** S · **Depends on:** R3
- **Model / effort:** Sonnet 5.5 · medium
- **Why:** There's no way to pause the harness, no limit on blast radius, and no wall-clock cap. The
  Copilot builder reports 0 tokens, so its budget can't be tracked.
- **Done when:**
  - [ ] `policy/harness_controls.yaml`: `enabled` (global kill switch), `repos_allowlist`,
        `max_concurrent_tasks_per_repo`, `max_task_wall_clock_minutes`, `max_copilot_requests_per_task`,
        `max_tasks_per_day`.
  - [ ] Checked at task start and at every node. A breach escalates with a clear reason. A `harness:pause`
        label on a repo or issue stops new work.
  - [ ] `BuildResult` gains `premium_requests`, which the Copilot builder counts per loop.

```text
Read docs/ROADMAP.md item R5, app/harness/workflow.py, policy/routing.yaml and
adapters/copilot_builder.py.

Add policy/harness_controls.yaml with the controls in the item, loaded with schema validation (G7
style), and enforce them at task start and between nodes, escalating with explicit reasons. Add the
harness:pause label. Track premium_requests per Copilot loop and enforce the cap. Tests for each
control. Run ruff, ty, pytest and evals. Update the item status and the work log.
```

### R6 · Harden the ADK adapters, and give the planner repo context
- **Status:** done · **Priority:** P1 · **Size:** M · **Depends on:** R3 (can start in parallel on the current adapters)
- **Model / effort:** Sonnet 5.5 · high
- **Why:** The adapters pull JSON out of model text with a regex, don't retry, create a new runner per call,
  and only check residency when Vertex is used. The planner never sees the code, so it plans blind.
- **Done when:**
  - [x] Structured output via the agent's `output_schema` (Pydantic). Retry once on a schema failure,
        then escalate.
  - [x] Residency fails closed: AI Studio keys are allowed only when `HARNESS_ENV=local`.
  - [x] Read-only repo context for the planner and reviewer: `AGENTS.md`, the file tree, and up to N
        files the triage step names (through `GitHubPort.read_file`, or the GitHub MCP server's
        read-only toolset). Size-capped, and scanned by the input guard.
  - [x] Model per role from config. The reviewer's model must differ from the planner's, or a warning
        is recorded in the trace.
  - [x] Skills load only from an approved immutable skills-repository revision; record each skill's
        source/version and declared capabilities. Review and eval every behaviour-changing skill or
        prompt update; never load a floating `latest`.
  - [x] MCP is opt-in, not an implicit agent framework: if used, document per-server allowlisting,
        least scopes, audience-bound credentials and no caller-token forwarding. Defer A2A until
        cross-agent delegation is a requirement.
  - The real `read_file`/`list_files` on the GitHub App client arrive with R2 (blocked); the port, fake and
    workflow are done. Skill names, source and approved revision are `TODO(ai_governance)` (Q7): the lock is empty.
    The reviewer's context comes from the plan's files, which are derived from the triage-named files.

```text
Read docs/ROADMAP.md item R6, app/harness/adapters/adk_agents.py, residency.py, policy/routing.yaml
and the current ADK docs for LlmAgent output_schema and runners (cite them).

Harden the ADK adapters per the item: structured output with Pydantic schemas, one retry then
escalate, a reused runner, residency fail-closed outside HARNESS_ENV=local, and read-only repo
context for planner and reviewer via GitHubPort (size-capped and passed through the input guard).
If you consider the GitHub MCP server instead, compare both in the PR body and pick one. Add tests
using fakes (no network). Update the item status and the work log.
```

---

## M3 · Security: use what exists

### S1 · Use existing security scanning tools
- **Status:** done (working tree) · **Priority:** P1 · **Size:** S · **Depends on:** G6 · **Decision:** D-08
- **Model / effort:** Sonnet 5.5 · medium
- **Done when:**
  - [x] Template CI's `secret_scan` job runs Gitleaks CLI v8.30.1 (official release binary verified by
        SHA-256), scanning the PR commit range before `agentic-bootstrap check` runs harness-specific rules.
  - [x] Harness and template CI have CodeQL (Python), `actions/dependency-review-action`, and `zizmor`
        jobs.
  - [x] Generic secret regexes are removed from `security_harness.py`; docs explain why.
  - [x] `TODO(ai_governance)`: confirm availability and licensing for GitHub secret scanning and push
        protection. CodeQL and dependency review are gated on public visibility or `GHAS_ENABLED=true`
        until licensing is confirmed (Q11).

```text
Read docs/ROADMAP.md item S1 and decision D-08, then app/harness/bootstrap/security_harness.py,
.github/workflows/ci.yml and agent-template/.github/workflows/agent-checks.yml.

Use existing tools rather than our own: add the official Gitleaks CLI release binary to the
secret_scan job and verify its SHA-256, scan the PR commit range, then run `agentic-bootstrap check`.
Add CodeQL for Python, dependency-review-action and zizmor to both the harness and template CI, with
least-privilege permissions. Reduce security_harness.py to harness-specific checks; do not retain generic
secret regexes. Verify action names and current SHAs; don't invent them. Update tests, README, the item
status and the work log.
```

### S2 · Model Armor as the primary scanner, and scan every untrusted input
- **Status:** done · **Priority:** P1 · **Size:** M · **Depends on:** R6 · **Decision:** D-09
- **Model / effort:** Sonnet 5.5 · high
- **Why:** Sunglasses misses novel phrasing (two known gaps). Reviewer findings and PR comments are fed
  back to the builder without being scanned.
- **Done when:**
  - [x] `adapters/model_armor_scanner.py` implements `InputScanner` using the Model Armor API (regional
        endpoint, template ID from config). A composite scanner runs Model Armor and Sunglasses, and
        blocks if either does.
  - [x] The harness's ADK app registers `ModelArmorPlugin` for model input and output.
  - [x] New guarded inputs: `review_feedback`, `pr_comment`, `repo_context` (R6).
  - [x] Adversarial tasks for the two known gaps run against the composite scanner. A recorded fixture
        stands in for Model Armor in CI.
  - Model Armor has not been run against a live template (no approved project), so the CI fixture is authored
    from the documented response shape, not recorded. Only `australia-southeast2` among the allowed regions
    supports Model Armor, with three filters (Responsible AI, Sensitive Data Protection, prompt injection and
    jailbreak). `TODO(security)`: require templates outside local use, and what they screen.
    `PR comments` are scanned on a new `pr_comment` surface, but nothing fills them until R2.

```text
Read docs/ROADMAP.md item S2 and decision D-09, docs/tech/INPUT_GUARD.md, app/harness/ports.py,
nodes/input_guard.py, adapters/sunglasses_scanner.py, policy/input_guard.yaml and workflow.py.

Read the current Model Armor docs (sanitizeUserPrompt/sanitizeModelResponse, regional endpoints)
and the ADK Model Armor plugin page; cite them. Implement a ModelArmorScanner behind InputScanner
(lazy import, .[armor] extra), a CompositeScanner (block if any blocks; fail closed on any error),
register ModelArmorPlugin on the harness ADK app, and extend the guarded inputs to review feedback,
PR comments and repo context. CI uses a recorded fixture, never the live API. Update
docs/tech/INPUT_GUARD.md (renamed from SUNGLASSES_EVALUATION.md), the item status and the
work log.
```

### S3 · Detect new capabilities in a PR (model, host, region, data store, dependency)
- **Status:** done · **Priority:** P1 · **Size:** M · **Depends on:** G3 (shares the diff parsing)
- **Model / effort:** Opus 5.5 · high
- **Why:** This answers the open question about security-team review scope ("every PR, or every
  privileged file plus each new pattern, API, model or baseline change?") deterministically.
- **Done when:**
  - [x] Detectors over *added* diff lines for: new Gemini/Vertex model IDs, new hostnames or URLs, new
        GCP region strings, new data-store clients (BigQuery, Firestore, Spanner, GCS, memory service), and
        new dependency entries.
  - [x] Each hit adds `security` to the approvers, and its reason appears in the gate result and trace.
        Hosts not in the spec's `egress_hosts` also add `ai_governance`.
  - [x] Allowlists live in `policy/capabilities.yaml` (schema-validated). Tests cover each detector and
        its benign look-alikes.
  - [x] Review newly introduced tools/protocol endpoints and agent delegation (including MCP/A2A
        when enabled); protocol metadata never grants access by itself. Enforce tool authorisation
        in code/platform IAM, not in prompts; side-effecting or broader tools need owner review.
  - Starting allowlists in `policy/capabilities.yaml` are `TODO(security)`. Model, data-store and
    dependency allowlists start empty (every new one is reviewed). The agent spec's `egress_hosts` are not yet
    read at run time (needs repo file access, R2/R6), so `IssueToMerge(egress_hosts=...)` defaults to none and
    every non-allowlisted host is treated as undeclared. A hit withdraws auto-merge (it becomes
    `human_approval`), but never escalates or rejects.

```text
Read docs/ROADMAP.md item S3, the open question about security-review scope in the item's
Why, app/harness/nodes/tamper_check.py (from G3), merge_gate.py and policy/risk_tiers.yaml.

Build deterministic new-capability detectors over added diff lines, as listed. They add approvers;
they never auto-approve or block on their own. Allowlists in policy/capabilities.yaml. Keep each
detector small and separately tested with benign look-alikes (comments, test fixtures, docs). Add
golden tasks. Run ruff, ty, pytest and evals. Update the item status and the work log.
```

### S5 · Supply chain and protection for the harness repo itself
- **Status:** todo · **Priority:** P1 · **Size:** S · **Depends on:** R1 (CODEOWNERS renderer)
- **Model / effort:** Sonnet 5.5 · medium
- **Done when:**
  - [ ] A harness `.github/CODEOWNERS`: `policy/**` and `app/harness/nodes/**` need the security team and AI governance team. `evals/**` needs AI governance team.
  - [ ] Hash-pinned installs in CI (`uv export --format requirements-txt` with hashes, then
        `pip install --require-hashes`). `google-adk` and `sunglasses` pinned exactly.
  - [ ] Releases are tagged and attested with `actions/attest-build-provenance`. The template's
        `secret_scan` installs the harness by tag + SHA (replaces the `<pinned-sha>` placeholder).
  - [ ] Dependabot (or Renovate) for actions and Python, grouped weekly.

```text
Read docs/ROADMAP.md item S5, .github/, pyproject.toml, uv.lock and
agent-template/.github/workflows/agent-checks.yml.

Protect the harness repo: CODEOWNERS per the item, hash-pinned CI installs from uv.lock, exact pins
for google-adk and sunglasses, a release workflow that tags and attests build provenance, and
Dependabot config. Replace the <pinned-sha> placeholder with a documented release-pinning scheme.
Verify the action names and inputs against current docs. Update README, the item status and the
work log.
```

### D1 · Builder residency: check Copilot first, keep a fallback ready
- **Status:** todo · **Priority:** P1 · **Size:** M · **Depends on:** R2 · **Decision:** D-10
- **Model / effort:** Opus 5.5 · high (half research, half code)
- **Why:** As of April 2026, Copilot's in-region processing covered the US and EU, with Australia on
  GitHub's roadmap for "later 2026". Re-checked on 26 November 2026: GitHub's [Copilot with data residency](https://docs.github.com/en/enterprise-cloud@latest/admin/data-residency/github-copilot-with-data-residency)
  still lists the United States and European Union only and says more regions are planned "in the near future"
  (the "later 2026" wording is not on that page). Issue text and code go to whichever models Copilot uses. Today
  `residency.py` only guards Vertex. **This could block the default builder for classified repos.**
- **Done when:**
  - [ ] `docs/RESIDENCY.md` records what GitHub's current docs say for GHE.com in Australia and for the
        coding agent (with URLs and the date checked), plus the open questions for GitHub and security team.
  - [ ] `policy/residency.yaml` gains `builders:` with the residency status of each builder and the spec
        classifications it is allowed for. Bootstrap and the workflow refuse a builder that isn't allowed
        for the repo's classification.
  - [ ] `CloudRunJobBuilder` is no longer a stub: the job runs a pinned headless coding agent in Melbourne
        against the plan. The real Cloud Run call stays behind a port.

```text
Read docs/ROADMAP.md item D1 and decision D-10, policy/residency.yaml, app/harness/residency.py,
adapters/copilot_builder.py, adapters/sandbox_builder.py, sandbox/ and bootstrap/spec.py.

Part 1 (research, no code yet): check current GitHub docs and changelog for Copilot data residency
and the coding agent on GHE.com in Australia. Write docs/RESIDENCY.md with what is confirmed (URLs and
date), what is not, and the questions for GitHub and security team. Stop and show me the summary
before part 2.

Part 2: add per-builder residency to policy/residency.yaml (keyed by spec classification), enforce
it in bootstrap and in the workflow, and implement CloudRunJobBuilder behind a CloudRunPort (fake in
tests) plus the sandbox entrypoint. Update the item status and the work log.
```

---

## M4 · Observability, audit and the learning loop

### O1 · OpenTelemetry traces and an append-only audit log of gate decisions
- **Status:** todo · **Priority:** P1 · **Size:** M · **Depends on:** R3 · **Decision:** D-07
- **Model / effort:** Sonnet 5.5 · high
- **Done when:**
  - [ ] Traces exported to Cloud Trace using ADK's GCP exporter, with `OTEL_SERVICE_NAME=agentic-harness`.
        Each harness node, model call, tool call/result, retry, handoff and human approval is traced
        with its golden-workflow stage ID and applicable model, policy, prompt and skill revisions.
        Use OpenTelemetry GenAI conventions where stable; label custom attributes.
  - [ ] An `AuditPort` with a BigQuery adapter (`australia-southeast2`) and a local JSONL fake. One row
        per gate decision: task key, PR, policy git SHA plus a hash of `policy/`, tier, decision, reason,
        approvers, checks, guard and tamper findings, and model IDs used.
  - [ ] Insert-only: the dataset's IAM gives the harness service account `dataEditor` but no delete.
        Documented in the deployment README.
  - [ ] The trace and audit payloads never contain secrets or full issue bodies (size-capped, redacted).
        A test proves it. Define retention and read-access controls; capture latency, errors,
        token/premium-request use and cost without storing sensitive prompt or tool payloads.

```text
Read docs/ROADMAP.md item O1 and decision D-07, app/harness/models.py (TraceEvent, TaskOutcome),
workflow.py (or the R3 graph) and the ADK observability docs at adk.dev (cite them).

Add OpenTelemetry tracing (ADK's GCP exporter, behind config) and an AuditPort with BigQuery and
JSONL adapters writing one insert-only row per gate decision with the fields in the item. Include
the policy git SHA and a content hash of policy/. Redact and size-cap free text. Tests use the JSONL
fake only. Update deployment/terraform/README.md, the item status and the work log.
```

### O2 · Emit prior requirements success metrics
- **Status:** todo · **Priority:** P2 · **Size:** S · **Depends on:** O1
- **Model / effort:** Sonnet 5.5 · medium
- **Done when:**
  - [ ] Saved SQL views over the audit table for: share of agent PRs passing required checks first time;
        AI governance team review turnaround against the 2-business-day SLA; PRs waiting on AI governance team; escalation rate
        by reason; premium requests per merge; time from issue to merge.
  - [ ] `docs/METRICS.md` maps each view to the agreed success criteria, and names what we
        can't measure yet.

```text
Read docs/ROADMAP.md item O2 and the audit schema from O1. Write BigQuery SQL views
(deployment/bigquery/views/*.sql) for each metric in the item, plus docs/METRICS.md mapping them to
the agreed success measures and listing gaps. Add a test that runs each view's logic against the JSONL
fake via DuckDB (dev-only dependency) so the SQL is exercised in CI. Update the item status and the
work log.
```

### O3 · Shadow the gate at the next phase, capture human decisions, set promotion criteria
- **Status:** todo · **Priority:** P1 · **Size:** M · **Depends on:** O1 · **Decision:** D-11
- **Model / effort:** Opus 5.5 · high
- **Why:** Without evidence, the conversation about raising the phase rests on opinion. Every human
  override is also a free eval case.
- **Done when:**
  - [ ] The gate also computes the result at `phase + 1` and records it in the audit row (`shadow_decision`).
        It never affects the real result.
  - [ ] Human outcomes are captured: approved, changes requested, closed, or reverted within 14 days,
        each with reason text where available.
  - [ ] `agentic-harness golden harvest` turns disagreements and reverts into draft golden tasks for review.
  - [ ] `policy/risk_tiers.yaml` gains `promotion_criteria` (draft for owner assignment remains unresolved): ≥ 50 agent PRs
        observed at the current phase; ≥ 95% agreement between the shadow gate and humans on tier-1
        decisions; zero shadow auto-merges that humans rejected for a correctness or security reason;
        revert rate ≤ 2%; injection detection rate 1.0 on the adversarial set.
  - [ ] `agentic-harness phase report` prints whether each criterion is met.

```text
Read docs/ROADMAP.md item O3 and decision D-11, nodes/merge_gate.py, policy/risk_tiers.yaml,
evals/run_evals.py and the O1 audit schema.

Add shadow decisions at phase+1 (recorded, never acted on), human-outcome capture from GitHub events,
a "golden harvest" command that drafts golden tasks from disagreements and reverts, the
promotion_criteria block in risk_tiers.yaml marked TODO(owner), and a "phase report" command
that evaluates the criteria from audit data. The gate's real decision must be provably unaffected
(add a test). Update the item status and the work log.
```

---

## M5 · Evals that measure the agents

### E1 · Live eval replay against closed PRs from representative repositories
- **Status:** blocked (needs pilot repos and their history) · **Priority:** P1 · **Size:** L · **Depends on:** R2, R6
- **Model / effort:** Opus 5.5 · extra-high · **plan first**
- **Why:** `--mode live` is a `SystemExit` stub. Today's evals test policy and orchestration, not whether
  triage, plan, review and build are any good.
- **Done when:**
  - [ ] A golden-task format for replays: repo, base SHA, issue, the human PR's files, and hidden tests
        (taken from the human PR and never shown to the agent).
  - [ ] Live mode runs each task on a disposable fork or branch at the base SHA. Metrics: triage size
        accuracy, plan file-overlap with the human PR, hidden-test pass rate, reviewer agreement, iterations,
        premium requests, wall clock.
  - [ ] Component evals run triage, plan and review alone against frozen inputs (cheap, and safe to run
        nightly), using `agents-cli eval` or the Vertex AI evaluation service, whichever the project adopts.
  - [ ] A nightly workflow (manual trigger plus schedule) publishes results as an artefact and to the
        audit dataset. It isn't part of PR CI.

```text
Read docs/ROADMAP.md item E1, evals/run_evals.py, evals/golden_tasks/*.yaml, app/harness/adapters/
and the agents-cli eval docs (run `agents-cli eval --help` and cite what you find).

Design live evals. Start in plan mode: the replay task schema, how a task is isolated (fork/branch
at base SHA, cleanup), hidden tests taken from the human PR, the metric definitions in the item,
component-level evals for triage/plan/review on frozen inputs, cost controls, and where results go.
Keep dry-run mode and its thresholds unchanged. After approval, implement the schema, runner and
component evals with fakes and two synthetic example tasks; representative tasks are added later. Update
the item status and the work log.
```

### E2 · Measure how well the reviewer catches seeded defects
- **Status:** todo · **Priority:** P2 · **Size:** M · **Depends on:** R7
- **Model / effort:** Opus 5.5 · high
- **Done when:**
  - [ ] `evals/reviewer/` holds ~30 diffs: clean ones, and ones seeded with one defect per review checklist
        item (foreign framework, a global location, a wildcard egress host, a secret, a loosened Model
        Armor setting, missing evals, a missing runbook update, ...).
  - [ ] It reports precision and recall per checklist item, and the false-block rate on clean diffs.
  - [ ] Thresholds start out recorded but non-blocking, with `TODO(ai_governance)` to agree them before the
        reviewer counts towards any approval.

```text
Read docs/ROADMAP.md item E2, policy/review_checklist.yaml and adapters/adk_agents.py
(AdkReviewer). Build a seeded-defect reviewer eval set (one defect type per checklist item plus clean
diffs), a runner that reports per-item precision and recall and the clean false-block rate, and a
dry-run mode with a scripted reviewer so it runs in CI. Non-blocking thresholds for now. Update the
item status and the work log.
```

### E3 · Wire up real agent evals, coverage and quality checks in the template
- **Status:** doing · **Priority:** P1 · **Size:** M · **Depends on:** G6
- **Model / effort:** Sonnet 5.5 · high (needs network and `agents-cli` installed)
- **Why:** The template's `evals_no_regression` is hard-coded to `exit 1`, so every generated agent PR
  fails today. Prior requirements explicitly name **code coverage and code quality**.
- **Done when:**
  - [x] A fresh generated repo includes a small `agents-cli` dataset with a normal case and a
        guardrail case, plus explicit instructions for offline checks and approved live evals.
  - [ ] `evals_no_regression` runs `agents-cli eval run` and then compares against `evals/baseline/` with
        `max_regression` from `thresholds.yaml`. The gate must fail on missing, incompatible, or
        regressed evidence. Verify flags with `--help`; `eval compare` alone is a report, not a gate.
  - [x] New required checks, `coverage` (pytest-cov with `fail_under` from `thresholds.yaml`, default
        80%) and `quality` (ruff, ty, and a complexity limit), are added to the template and to
        `policy/risk_tiers.yaml` `required_checks`.
  - [ ] The holdout eval job from G3 runs CI-only cases from a location the coding agent can't read
        (a separate repo or a GCS path via WIF).
  - [ ] The e2e script's live mode exercises all of it.

The starter coverage and eval pass marks are 80%; AI Governance approves the baseline. The user accepts
the risk that GitHub Actions PR code may access job credentials, with deterministic pre-execution
scanning and minimised credentials. The live and holdout checks still need an accepted baseline,
approved evaluation regions and identities, and a reviewed holdout isolation design (Q18): executing
PR-authored code with holdout access exposes the cases. The preflight is a tripwire, not a sandbox,
and must itself be protected from PR changes by independent workflow enforcement or required reviews.
The installed `agents-cli` reports `eval run --dataset`, `--config`, `--region` and `--output`;
`eval compare BASELINE CANDIDATE` only reports differences and does not enforce a regression threshold.

```text
Read docs/ROADMAP.md item E3, agent-template/.github/workflows/agent-checks.yml,
agent-template/evals/, agent-template/pyproject.toml, policy/risk_tiers.yaml and scripts/e2e.py.

Replace the placeholder evals job with real agents-cli eval run plus a baseline comparison (check the
CLI's current flags with --help and cite them in the PR). Add coverage and quality as required
checks in both the template and risk_tiers.yaml (G7's cross-file check must still pass). Add the
holdout job reading from a location outside the repo via WIF. Run the e2e script with --live-evals if
credentials are available; otherwise say so. Update the item status and the work log.
```

---

## M6 · Golden-workflow coverage

### W1 · Checks and approvals for workload PRs in stage 3
- **Status:** todo · **Priority:** P2 · **Size:** S · **Depends on:** none
- **Model / effort:** Sonnet 5.5 · medium
- **Why:** Prior requirements call for schema, format and plan checks per folder, plus an identity/access
  dry run, and distinguish registering a host from approving egress. `terraform_plan.py` includes neither.
  `workload-infrastructure` and `platform.tf` are illustrative names; the actual repository layout is unknown.
- **Done when:**
  - [ ] Each `PRPlan` lists its `required_checks` and any separate approval needed per egress host,
        with `security` and `ai_governance` as applicable.
  - [ ] Egress PRs include Agent Registry entries for each exact host.
  - [ ] The infrastructure repository layout assumption is moved into config, marked `TODO(owner)`.
  - [ ] Define a cloud platform module contract and generate a reviewed, placeholder-valued baseline for the
        standard runtime, service identity/IAM and WIF, secrets, network/egress, telemetry and
        session/audit storage (plus queue/ingress when used). Do not invent module defaults:
        unresolved inputs or values are explicitly marked `TODO(platform_team)`.
  - [ ] Generated Terraform is formatted, validated, planned and policy-checked in CI; docs state
        safe placeholder semantics, required inputs, outputs, owners and replacement process.

```text
Read docs/ROADMAP.md item W1 and app/harness/bootstrap/terraform_plan.py, spec.py and the tests.
Extend PRPlan with required_checks and separate_approvals per the item, add registry entries for
each egress host, and move the illustrative infrastructure repository layout into a config file marked TODO(owner). Update
CLI JSON output, tests, the item status and the work log.
```

### W2 · Template from existing reference agent template plus a project-specific overlay, and in-place upgrades
- **Status:** blocked (awaiting access to the reference template from AI governance team) · **Priority:** P2 · **Size:** L · **Depends on:** none · **Decision:** D-12
- **Model / effort:** Opus 5.5 · high · **plan first**
- **Done when:**
  - [ ] `agentic-bootstrap new` takes a template source as a git URL and ref, and records it with the answers
        in `.agent-template.yaml` in the generated repo.
  - [ ] `agent-template/` becomes the harness overlay (AGENTS.md, CI, evals, rulesets, docs), applied on top of
        the base. The existing mechanic example stays as the offline fallback.
  - [ ] `agentic-bootstrap upgrade` does a three-way merge from the recorded ref to a new ref, and opens a PR
        rather than writing to main. Evaluate Copier against our own implementation, and record the choice.

```text
Read docs/ROADMAP.md item W2 and decision D-12, app/harness/bootstrap/template.py, cli.py, spec.py
and agent-template/.

Start in plan mode. Compare (a) adopting Copier (base + overlay, answers file, `copier update`) with
(b) extending our renderer, against: ADK-only and minimal-dependency rules, Windows support, three-way
merge quality, and how a project-specific overlay sits on an existing reference agent template base. Recommend one. After
approval, implement with a local fixture repo standing in for existing reference agent template. Update README,
the item status and the work log.
```

### W3 · Release review pack
- **Status:** todo · **Priority:** P2 · **Size:** S · **Depends on:** O1
- **Model / effort:** Sonnet 5.5 · medium
- **Done when:** `agentic-bootstrap pack <agent-repo>` produces a markdown and JSON pack for Architecture,
  the Product Owner and AI governance team: the Mission Brief, eval results against the baseline and thresholds, the
  security check report, the reviewer checklist report, open risks, and the runbook's completeness
  (placeholders flagged).

```text
Read docs/ROADMAP.md item W3, policy/golden_workflow.yaml (release stage),
agent-template/docs/ and app/harness/bootstrap/. Add `agentic-bootstrap pack` producing the review pack
described, failing (non-zero exit) when the runbook or mission brief still contains PLACEHOLDER.
Tests with a rendered template fixture. Update the item status and the work log.
```

### W4 · Register stage: pre-fill the CMDB and ServiceNow record
- **Status:** todo · **Priority:** P2 · **Size:** S · **Depends on:** none
- **Model / effort:** Sonnet 5.5 · low
- **Done when:** a `RegistrationPort` with a fake. `agentic-bootstrap register spec.yaml --dry-run` prints the
  "AI Agent" CI payload and the support-group request built from the spec (classification, owner,
  sponsor, division). The real ServiceNow adapter is `TODO(owner)`.

```text
Read docs/ROADMAP.md item W4, app/harness/bootstrap/spec.py and cli.py, and policy/golden_workflow.yaml
(register stage). Add a RegistrationPort, a fake, and `agentic-bootstrap register --dry-run` printing
the CMDB 'AI Agent' CI and support-group payloads from the spec. Mark the real adapter
TODO(owner). Tests. Update the item status and the work log.
```

### W5 · A GitHub-native `HumanGate` now, ready for Maestro later
- **Status:** todo · **Priority:** P1 · **Size:** M · **Depends on:** R3, R4
- **Model / effort:** Sonnet 5.5 · high
- **Done when:**
  - [ ] Plan approval is a comment on the issue with the plan. A code owner replies `/approve` or `/reject
        <reason>`, the reply resumes the ADK pause, and only users in the required team count.
  - [ ] `notify` posts to the issue or PR, and optionally to a Teams or Slack webhook (config).
  - [ ] The port is documented with a pause/resume token so a future workflow-engine adapter can drop in.

```text
Read docs/ROADMAP.md item W5, app/harness/ports.py (HumanGate), the R3 workflow and the R4 ingress.
Implement a GitHub-native HumanGate: plan posted as an issue comment, /approve or /reject from an
authorised team member resumes the paused workflow, everything else is ignored (and audited).
Document the pause/resume contract for a future Maestro adapter in docs/HITL.md. Tests with fakes.
Update the item status and the work log.
```

---

## M7 · Hygiene

### H1 · CI, packaging and repo tidy-up
- **Status:** doing · **Priority:** P2 · **Size:** S · **Depends on:** none
- **Model / effort:** Haiku 5.5 · medium
- **Done when:**
  - [x] Harness CI runs lint, `ty`, tests and dry-run evals on Python 3.11, 3.12 and 3.13 on Ubuntu
        (pinned 3.13 remains the local default).
  - [x] CI runs `ruff format --check` and `codespell`.
  - [ ] CI runs `scripts/e2e.py` (offline stages) on Ubuntu and Windows.
  - [x] `evals/run_evals.py` relies on the installed package: the late `sys.path` insert was removed, and the
        docstring says to install first (`uv sync --extra dev`).
  - [x] Stale doc lines are fixed. The alignment note (with its legacy `[tool.agents-cli]` line) was removed and
        its content moved to the changelog and the open questions.
  - The generated-project items that used to be here (the preflight command and the acceptance test) moved to
    [H2](#h2--generated-project-preflight-and-acceptance-test): they are new behaviour, not tidy-up.

```text
Read docs/ROADMAP.md item H1, .github/workflows/ci.yml, evals/run_evals.py, .gitignore
and scripts/e2e.py. Make the hygiene changes listed (matrix, ty, codespell,
offline e2e on ubuntu and windows, import-order fix, stale doc lines). No behaviour changes. Update
the item status and the work log.
```

---

## M8 · Generated agent ready for the pilot

The generated agent is a standalone ADK example, not a second copy of the harness. Start with
E3 and H2 (the generated-project checks), then add the runtime patterns below. The offline
acceptance bar is a fresh repo where a developer can run checks without cloud credentials, see an
allowed and a denied operation, inspect a redacted diagnostic, and identify what requires approval
before live evaluation or deployment. Exercise that path in H2's generated-project acceptance test.
The installed GitHub ruleset and policy-derived CODEOWNERS stay in R1; W2 can later carry these
patterns as an overlay without blocking work on the embedded template.

### H2 · Generated-project preflight and acceptance test
- **Status:** todo · **Priority:** P2 · **Size:** M · **Depends on:** none
- **Model / effort:** Sonnet 5.5 · high · **plan first**
- **Why:** Split out of H1. A preflight command and generated-output provenance are new behaviour, not tidy-up, so
  they get their own plan and review. Together with the acceptance test they are the offline acceptance bar
  described above.
- **Done when:**
  - [ ] The bootstrap CLI has a preflight/doctor path with actionable checks for Python/uv,
        `agents-cli`, cloud auth, project/region, template and skills revision; machine-readable
        `--json` output and stable exit semantics are covered by tests.
  - [ ] An offline generated-project acceptance test exercises `new`, `check`, evals and Terraform
        plan output from a clean checkout. Dry-run commands are repeatable and do not mutate cloud
        state; generated output records its template/CLI provenance.

```text
Read docs/ROADMAP.md item H2 and the M8 introduction, then app/harness/bootstrap/ (cli.py, spec.py,
template.py, security_harness.py, terraform_plan.py), scripts/e2e.py, tests/test_bootstrap.py and
agent-template/.

Start in plan mode. Propose: the preflight checks and what each reports, the stable exit codes and the
`--json` shape, where generated-output provenance is recorded (decide the file name in the plan), and how the
acceptance test stays offline and repeatable. No cloud calls, and nothing that mutates cloud state. Then
implement with tests. Update the item status, the docs (README, getting started) and the work log.
```

### A1 · Demonstrate a runtime authorisation boundary
- **Status:** review · **Priority:** P1 · **Size:** M · **Depends on:** none
- **Model / effort:** Opus 5.5 · high · **plan first**
- **Done when:**
  - [x] Start read-only, or keep a simulated write only if it refuses to proceed without trusted,
        operation-bound human approval checked outside the model. A tool argument, skill, or prompt
        assertion alone is not authorisation. Real writes and new integrations are out of scope.
  - [ ] Deterministic tests exercise allowed and denied paths; a behaviour eval verifies the agent
        does not claim a write occurred when it did not. The generated guide identifies which
        controls are local and which need platform IAM, Model Armor, or repository enforcement.
        Local wiring and tool checks are in place; the booking refusal case still needs a live run.

```text
Read docs/ROADMAP.md item A1, agent-template/agent/, README.md, docs/ and tests/. Compare a
read-only starter with an ADK confirmation-backed simulation. Propose the smallest verifiable
boundary first, then implement the agreed path and exercise it from a freshly generated repo.
```

### A2 · Show useful, redacted workload telemetry
- **Status:** done · **Priority:** P1 · **Size:** M · **Depends on:** none
- **Model / effort:** Sonnet 5.5 · high
- **Done when:**
  - [x] A credential-free example correlates a request with tool name, outcome, latency and
        available behaviour revisions. Use an allowlist of structured fields; no raw prompts, tool
        arguments, tool results, credentials, or unrestricted exception text. Tests demonstrate this.
  - [x] The runbook shows a diagnostic and how to interpret it. The example configures no exporter;
        the runbook directs teams to the approved platform path. O1 remains the parent harness's audit work.

```text
Read docs/ROADMAP.md item A2 and O1. Add and test the minimal local telemetry example to the
generated workload, update its runbook, and verify it after generation without cloud credentials.
```

### A3 · Demonstrate one governed runtime skill
- **Status:** review · **Priority:** P1 · **Size:** M · **Depends on:** none
- **Model / effort:** Opus 5.5 · high · **plan first**
- **Done when:**
  - [x] Ship one harmless runtime skill with an explicit source, immutable revision, ownership and
        declared capabilities. Distinguish it from contributor instructions in `AGENTS.md` and the
        parent planner/reviewer skills in R6. No floating revisions or network fetches by default.
  - [x] The skill cannot grant tools, permissions or egress. A test demonstrates the permission
        boundary, and a behaviour eval covers the skill's intended use. Document review and eval
        requirements for changes; use R1 for repository enforcement when installed. Live behaviour
        scoring still needs the approved non-production setup.

```text
Read docs/ROADMAP.md item A3 and R6 and the generated agent guide. Study the ADK recipe for runtime
skills, then propose and implement the smallest reviewable example without changing tool permissions.
Verify provenance and skill behaviour from a generated repo.
```

---

## M9 · Agent intake and authoring

Today a team needs engineers to turn a bootstrapped starter into an agent that does something useful:
write the prompts, tools and evals, and tailor them. M9 adds an **intake agent** (D-13) so a person with
repository access can raise an `AgentRequest` issue, answer plain-language questions, and get a PR that
holds a working, tested, governed agent. Later changes ("also notify the team", "raise the PRs in Java")
are comments on the issue or PR.

How it fits, end to end:

```text
AgentRequest issue ─► I3 intake agent (ADK, reads only guarded text)
   ▲  Q&A on the issue        │ answers fill the Mission Brief and spec.yaml (I1)
   │                          ▼
   │              I4 agentic-bootstrap add ─► agent folder in the division's agent repo (branch)
   │                          │ composes connectors from the library (I2), writes prompts, tools, evals
   │                          ▼
   │              I5 agentic-bootstrap check + tests + cross-model review ─► findings on the PR
   │                          ▼
   └─ I6 comments ─► revise ─► PR ─► existing merge gate and approvers (never the intake agent)
```

Boundaries that hold for every item in M9:

- The intake agent is a **builder identity**. It cannot approve or merge, and the reviewer lockout (R7)
  applies to it as it does to Copilot.
- Requester text (issue body, answers, comments) is untrusted. It passes the input guard (S2) before any
  model sees it, and it never lands in traces, audit rows or source in full.
- Under D-02 the files this agent writes (prompts, tool definitions, eval thresholds) are **tier 3**, so
  AI governance team and security team approve every intake-authored agent. Q16 asks whether connector-only agents
  may use a lighter route. Do not loosen the tier in code before it is answered.
- It proposes capabilities and never grants them. New hosts, models, regions, data stores and
  dependencies are surfaced by S3's detectors and need the named approvers. Egress goes in the spec's
  `egress_hosts` and is approved there.
- It does not choose agent-specific pass marks. It drafts cases and proposes no reduction to the
  agreed 80% starter marks; higher agent-specific thresholds need business-owner review.
- Stop conditions: a request that needs something outside the connector library, a missing answer after
  the question limit, or a failed guard. Each ends with a clear comment and a human handoff, never a guess.

### I1 · `AgentRequest` form and the request model
- **Status:** done · **Priority:** P1 · **Size:** M · **Depends on:** none
- **Model / effort:** Sonnet 5.5 · high
- **Why:** Everything else needs a stable, validated shape for "what the requester wants". It must be
  plain enough for a non-technical owner and strict enough to become the Mission Brief and `spec.yaml`.
- **Done when:**
  - [x] `.github/ISSUE_TEMPLATE/agent-request.yml` (GitHub issue form) asks for: the problem and who has
        it, the outcome that counts as success, systems it should read from or write to, the data
        involved (with a classification choice), who approves its actions, and the division. No jargon.
  - [x] A Pydantic `AgentRequest` model (`strict=True`, `extra="forbid"`) parses the issue into a draft
        plus a list of **missing or unclear fields**, and maps to `AgentSpec` and a Mission Brief.
        A `spec` that cannot validate (`AgentSpec.validate`) is reported, not patched.
  - [x] Only a request from a person allowed to raise one is accepted (Q13); others get a polite no.
  - [x] Property tests: unknown fields are rejected, and the mapping is lossless for required fields.
  - [x] Golden and adversarial eval tasks for the parse step, including an issue body that tries to
        smuggle in a host, a model, or an instruction to skip approval.

The offline `parse_request` entry point requires a trusted `RequesterAccess` lookup for the exact
repository and authenticated human author. The caller must take both identities from trusted issue
metadata, not the issue body. The real GitHub access lookup and authenticated event wiring are I7;
the offline tests use a fake. A successful lookup accepts a draft only, not a build or approval.
The draft is untrusted and must pass the input guard before reaching a model. The Mission Brief is a
structured draft and the spec is a review-only candidate: no host, model or approval is granted by text.
The issue form asks for a sponsor but the sponsorship rule before spending budget or creating a branch
is still open (Q17); I7 must not guess it. Parsing eval cases run with pytest.

```text
Read docs/ROADMAP.md item I1 and decisions D-13 to D-15, app/harness/bootstrap/spec.py,
agent-template/docs/mission-brief.md and policy_validation.py. Add the issue form and the AgentRequest
model with tests and eval tasks. Reuse AgentSpec rather than duplicating its rules. Do not add LLM calls
in this item; parsing is deterministic.
```

### I2 · Curated connector library
- **Status:** todo · **Priority:** P1 · **Size:** L (split per connector) · **Depends on:** A1, S3 · **plan first**
- **Model / effort:** Opus 5.5 · high
- **Why:** D-14. The intake agent can only be trusted to author useful agents if the ways to reach real
  systems are fixed, reviewed and tested ahead of time.
- **Done when:**
  - [ ] A `connectors/` registry where each connector is a typed ADK tool template plus a manifest:
        name, version, `read` or `write`, declared egress hosts, required IAM roles, data stores touched,
        approver roles, and a fingerprint pinned the way skills are (`policy/skills.lock.yaml` pattern).
        A schema-validated policy file lists approved connectors (extends G7).
  - [ ] First slice is **read-only**: GitHub read, a Jira read connector (shape depends on Q9 and the
        Omni route in Q14), BigQuery read, and spreadsheet/CSV parse. Writes follow once A1's boundary
        exists, and each write connector refuses to run without trusted, operation-bound approval.
  - [ ] Each connector has deterministic unit tests, an allowed and a denied path, and a behaviour eval.
  - [ ] Using a connector adds its hosts to `egress_hosts` and its approvers to the PR through S3; it
        never adds them silently.
  - [ ] A README explains how an app team or AI governance team proposes a new connector.

```text
Read docs/ROADMAP.md item I2, A1, A3, S3 and agent-template/agent/. Propose the connector manifest and
the first read-only connectors in plan mode, then implement the agreed slice. Do not call real systems:
use recorded fakes. Do not add another agent framework.
```

### I3 · Intake agent: the Q&A loop (local prototype)
- **Status:** todo · **Priority:** P1 · **Size:** L · **Depends on:** I1, I2, R6 · **plan first**
- **Model / effort:** Opus 5.5 · high
- **Why:** The core of the feature. It turns a rough request into a complete, consistent brief by asking
  only what it needs, in the requester's language.
- **Done when:**
  - [ ] An ADK agent behind a port (`IntakeAgent`) reads the issue and prior comments through an
        `IssueSource` port (Q9) and posts the next question or a "ready to build" summary through a
        `CommentSink` port. A fake source and sink run the whole loop offline; no real GitHub call.
  - [ ] It asks one to three questions at a time, at most a fixed number of rounds (from `routing.yaml`),
        and each question names which brief field it fills. It never asks for secrets, and tells the
        requester not to paste them.
  - [ ] It checks the request against the connector library (I2) and says plainly what the library
        cannot do, before any build.
  - [ ] Output is a validated `AgentRequest` plus a Mission Brief draft. Fields it cannot fill stay
        `TODO(<owner>)`.
  - [ ] Every inbound text passes the input guard; outputs are structured Pydantic models (the R6
        pattern). Token, round and time caps escalate to a human rather than looping.
  - [ ] Evals: ordinary requests, vague requests, requests the library cannot meet, and adversarial
        comments (attempts to widen scope, add a host, or ask it to approve itself).

```text
Read docs/ROADMAP.md item I3, D-13, ports.py, adk_agents.py and workflow.py. Plan the ports and the
conversation state first, then implement against fakes. Keep the LLM out of every decision a rule can
make (is the field filled? is the host allowed? is the connector approved?). Add golden and adversarial
eval tasks.
```

### I4 · Authoring: `agentic-bootstrap add` and agent generation
- **Status:** todo · **Priority:** P1 · **Size:** L · **Depends on:** I1, I2, I3 · **plan first**
- **Model / effort:** Opus 5.5 · high
- **Why:** The Q&A is worthless unless it ends in a reviewable PR. `agentic-bootstrap new` makes a whole repo,
  but prior requirements specify one agent repository per division, so a new command must add an agent to an existing one.
- **Done when:**
  - [ ] `agentic-bootstrap add` creates an agent folder from the template in an existing division repo on a
        new branch, fills names, egress hosts, CODEOWNERS entries and the Mission Brief, and refuses to
        touch files outside that folder (plus the declared shared files). Layout questions are recorded
        against W2 and D-12 so the two do not diverge.
  - [ ] The generator writes `prompts.py`, wires connectors in `tools.py` and `agent.py`, and drafts
        `evals/golden_set.yaml` and `tests/eval/` cases from the brief's hypotheses (one case per
        guardrail). It uses the template's guardrail pattern for every write connector.
  - [ ] PRs stay under the size limit; larger agents split into reviewable PRs.
  - [ ] Generated output passes `agents-cli lint`, `uv run pytest` and `agentic-bootstrap check` in a
        fresh-repo acceptance test, in line with H2's generated-project check.
  - [ ] The PR body states, in plain language, what the agent does, what it can touch, what needs
        approval and why, and what is still `TODO`.

```text
Read docs/ROADMAP.md item I4, W2, D-12, app/harness/bootstrap/ and agent-template/. Plan the `add`
command and its file allowlist, then implement. Add tests that the command cannot write outside its
folder and that generated agents pass the template's own checks.
```

### I5 · Cross-model review and eval generation
- **Status:** todo · **Priority:** P1 · **Size:** M · **Depends on:** I4, E3, D1 · **plan first**
- **Model / effort:** Opus 5.5 · high
- **Why:** D-15. LLM-authored code needs an independent check beyond tests the same model wrote.
- **Done when:**
  - [ ] A reviewer role built on a different model family from the generator (Q15) runs against the
        agent's diff and Mission Brief, and reports: brief coverage, unsupported claims, guardrail gaps,
        and risky tool use. The report is a structured, advisory PR comment.
  - [ ] It proposes adversarial eval cases (prompt injection, out-of-scope asks, data leakage) that go in
        as a separate commit for human review. It never edits baselines or thresholds.
  - [ ] `agentic-bootstrap check` and the template's required checks run on every revision and their
        results are posted alongside. The merge gate's behaviour is unchanged.
  - [ ] A seeded-defect eval (like E2) measures how often the reviewer catches planted problems in
        generated agents, and the result is tracked.

```text
Read docs/ROADMAP.md item I5, D-15, E2, E3, residency.py and adk_agents.py. Plan the reviewer role and
the residency handling for a second model family, then implement behind the existing ports with fakes.
Do not weaken or bypass `agentic-bootstrap check`.
```

### I6 · Tailoring through issue and PR comments, and `AgentChange`
- **Status:** todo · **Priority:** P1 · **Size:** M · **Depends on:** I3, I4, I5, R5
- **Model / effort:** Opus 5.5 · high
- **Why:** Most real value is in the second and third iteration. Requesters should say what they want
  changed, and the agent should turn that into a safe revision.
- **Done when:**
  - [ ] A comment from an allowed person on the `AgentRequest` issue or its PR is classified (answer,
        change request, question, out of scope) and handled. Change requests produce a new commit and a
        short "what changed and why" reply; each revision re-runs checks (I5).
  - [ ] Revisions that would add a host, data store, model, region or write capability are flagged,
        explained and left for the named approvers; the agent never applies one on its own say-so.
  - [ ] An `AgentChange` issue type does the same for an **existing** agent, through the same flow.
  - [ ] Concurrency, loop and budget caps from R5; the kill switch stops it. A human can say "stop" and
        "take over" at any time.
  - [ ] Adversarial evals for comment injection, privilege-widening requests and attempts to have the
        agent approve its own PR.

```text
Read docs/ROADMAP.md item I6, I3 to I5, R5 and R7. Plan the comment-classification states first, then
implement against fakes. Every path that could widen access must end at a human approver.
```

### I7 · Hosted trigger
- **Status:** blocked (R2, R3, R4, Q5, Q17) · **Priority:** P1 · **Size:** M · **Depends on:** I3, I6, R2, R3, R4
- **Model / effort:** Sonnet 5.5 · high
- **Why:** Once the prototype works offline, the intake agent has to start when an `AgentRequest` issue is
  opened and run on the harness's runtime, not on someone's machine.
- **Done when:**
  - [ ] `AgentRequest` and `AgentChange` issues route through the R4 webhook ingress to the R3 workflow,
        idempotent per `(repo, issue)`, using the GitHub App only (no personal tokens).
  - [ ] The real `IssueSource`, `CommentSink` and repo-write adapters sit behind the same ports the
        prototype used; the offline evals still pass unchanged.
  - [ ] Verify the human issue author's current repository access using trusted metadata and the
        `RequesterAccess` port. Enforce the agreed sponsorship rule (Q17) before spending budget
        or creating a branch.
  - [ ] Traces and audit rows (O1) record who raised the request, what was asked, what was generated
        and who approved, without issue bodies or secrets.
  - [ ] If R3/R4 slip, record a decision on whether a thin GitHub Actions trigger is an acceptable
        interim. It needs security-team sign-off on secrets, WIF and residency first.

```text
Read docs/ROADMAP.md item I7, R3, R4, R2 and I3. Wire the intake workflow into the hosted runtime
behind the existing ports. Do not change the prototype's behaviour or its evals.
```

---

## Open questions

These block or shape items above. Ask them in the session with the agent teams next week.

| # | Question | Blocks | Suggested owner |
|---|---|---|---|
| Q1 | Which files count as "privileged YAML"? | G2, R1 | security team |
| Q2 | Real GitHub role-to-team mappings per role (application, AI governance, platform, security, product and architecture roles) | R1, S5 | AI governance team |
| Q3 | Is the Copilot coding agent acceptable for each data classification, given residency? | D1 | security team |
| Q4 | Who approves workflow runs on Copilot PRs, and should we enable "skip approval"? | R2 | security team |
| Q5 | Harness hosting (Cloud Run + Cloud SQL in Melbourne?) and the webhook ingress route | R3, R4 | platform team |
| Q7 | pinned skills repository skill names for planner and reviewer | R6 | AI governance team |
| Q9 | Do agent work items come from GitHub Issues, or from Jira / Jira Align? | R4 (may need an `IssueSource` port) | Unassigned |
| Q10 | Phase promotion criteria (draft in O3) | O3 | Unassigned |
| Q11 | Is GitHub Advanced Security licensed (secret scanning, push protection, CodeQL, dependency review)? | S1 | AI governance team |
| Q12 | Actual infrastructure repository and file layout (`workload-infrastructure` and `platform.tf` are illustrative only) | W1 | platform_team |
| Q14 | Who owns and reviews the connector library, which connectors come first, and how do Jira and other internal APIs reach agents (the approved connector gateway)? | I2 | AI governance team, platform team and approved connector platform |
| Q15 | Which second model family, if any, is approved for cross-model review under Australian residency? | I5 | security team |
| Q16 | Should agents built only from approved connectors stay tier 3 under D-02, or may they use a lighter approval route? | M9 | security team, AI governance team |
| Q17 | Who sponsors a request before the intake agent spends budget or creates a branch, and how is sponsorship verified? | I7 | Unassigned |
| Q18 | Which approved evaluation project, regions and WIF identity should be used, and how can holdouts remain hidden from PR-authored code? | E3 | security team and platform team |

Resolved: Q6's contact is the AI governance team; W2 still needs the actual template and bootstrap access.
Q13's requester eligibility is any person with repository access; the separate sponsorship question is Q17.
Q8's starter marks are 80% coverage and eval pass mark, with baseline approval by AI Governance.

---

## References

- NIST, *AI Risk Management Framework: Generative AI Profile*: https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf
- OWASP, *Top 10 for Agentic Applications 2026*: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
- MCP authorisation specification: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/authorization/index.mdx
- A2A, *Protocol specification*: https://a2a-protocol.org/latest/specification/
- OpenTelemetry, *GenAI agent span conventions*: https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/
- Google Cloud, *Build an agent with ADK and Agents CLI*: https://docs.cloud.google.com/gemini-enterprise-agent-platform/agents/quickstart-adk
- Anthropic, *Effective harnesses for long-running agents*: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Addy Osmani, *Agent harness engineering*: https://addyosmani.com/blog/agent-harness-engineering/
- EvilGenie, a reward-hacking benchmark: https://arxiv.org/abs/2511.21654
- ADK 2.0: https://adk.dev/2.0/ · pause and resume: https://developers.googleblog.com/build-long-running-ai-agents-that-pause-resume-and-never-lose-context-with-adk/
- ADK Model Armor plugin: https://adk.dev/integrations/model-armor/ · ADK traces: https://adk.dev/observability/traces/
- Copilot data residency (US/EU): https://github.blog/changelog/2026-04-13-copilot-data-residency-in-us-eu-and-fedramp-compliance-now-available/
- Copilot coding agent on GHE.com: https://github.blog/changelog/2025-08-27-copilot-coding-agent-is-now-available-in-github-enterprise-cloud-with-data-residency/
- Skipping approval for Copilot workflows: https://github.blog/changelog/2026-03-13-optionally-skip-approval-for-copilot-coding-agent-actions-workflows/
- Copilot agent risks and mitigations: https://docs.github.com/en/copilot/concepts/agents/cloud-agent/risks-and-mitigations
- Assigning issues to Copilot via the API: https://github.blog/changelog/2025-12-03-assign-issues-to-copilot-using-the-api/
- Governing agents in GitHub Enterprise: https://wellarchitected.github.com/library/governance/recommendations/governing-agents/

---

## Work log

Append-only, newest first. One entry per PR or working session: the date, the item IDs, what changed, and
anything learned that should change this plan. Never rewrite old entries; correct them with a new one.

### 2026-11-26 · Site refresh: roadmap and glossary pages, accuracy pass
- Rebuilt the site's status, blockers, golden-path stage states, architecture views and headline figures from the
  repo as it stands (265 tests, 65 scored golden tasks, two open gaps, six required checks). Added `roadmap.html`
  (milestone value, next steps, waiting-on-people table) and `glossary.html`. Added eight gate-replay scenarios taken
  from golden tasks. Human decisions now use orange instead of indigo in the loop diagram, with text labels.
- Replaced "TODO: UNCONFIRMED" on the site with "to be validated" wording. The docs keep their own marker.
- Re-checked vendor facts, with the page for each in the site's validation log. R2 holds: the issue-assignment APIs
  need a user token and the agent-tasks API refuses installation tokens. D-10 holds: GitHub's
  [Copilot with data residency](https://docs.github.com/en/enterprise-cloud@latest/admin/data-residency/github-copilot-with-data-residency) lists the US and EU only (D1 now records this). The generative AI locations
  page lists Sydney and not Melbourne for Gemini. AGENTS.md, C4 and the CNCF article were read and match. Still
  unchecked: `genai.owasp.org`, the Gitleaks `v8.30.1` release binary and its SHA-256, and the tag names behind the
  Pages action pins.
- Docs fixed on the way: `ARCHITECTURE.md` (request parser, `RequesterAccess`, template preflight, coverage and
  eval comparator, CI steps, `armor` extra), glossary roadmap codes (D-15, Q18, M9, I1 to I7) and a stale blocker row
  (I1 became I7). No policy, gate or node behaviour changed, so no new eval.

### 2026-11-26 · E3 coverage, quality and preflight
- Added required `coverage` and `quality` jobs and policy entries. The 80% starter coverage mark
  is enforced; quality runs Ruff, its complexity rule and ty. Added adversarial evals for missing checks
  and edits to the coverage helper, and starter tests exceeding the coverage mark.
- Added base-revision static parsing, Gitleaks and an input tripwire ahead of dependent jobs. Added
  a fail-closed regression comparator, not yet wired to live evals. AI Governance approves the baseline.
  The user accepts GitHub Actions credential exposure risk; scans do not provide isolation.
- Live eval regression, an accepted baseline, holdout isolation and live end-to-end verification remain
  open; see Q18. E3 stays doing.

### 2026-11-26 · I1 request form and offline parsing
- Added the GitHub request form, strict deterministic draft model, review-only spec and brief mapping,
  repository-access port, property tests and offline parsing eval cases. Unauthorised requests are refused;
  no input is sent to a model and no capability or build is authorised by a draft.
- Q13: any person with repository access may request an agent. The hosted access lookup remains I7.
  Sponsorship before spending or branching was not specified and is tracked separately as Q17.
- Q6: the AI governance team is the contact for reference template access. W2 remains blocked until
  access is actually available.

### 2026-11-25 · Project site for GitHub Pages
- Added `site/`: a static, no-build, no-third-party-requests project site (vision, golden workflow, a replay of
  documented merge-gate outputs, C4 architecture, safety controls and limits, status, comparison with public
  tools, getting started, FAQ and sources), with hand-drawn SVG art. Added `.github/workflows/pages.yml`
  (SHA-pinned official Pages actions, least-privilege permissions; zizmor offline run clean),
  `tests/test_site.py` (links, anchors, assets, no third-party loads, pinned workflow) and `docs/SITE.md`
  (deploy steps, maintenance rules, sources, image prompts).
- No policy, gate or node behaviour changed, so no new eval. The site makes claims about the repo, so the
  tests fail on dead links into the repo.
- Learned: `docs.github.com`, `adk.dev`, Google Cloud docs, `agents.md`, `c4model.com` and OWASP were not
  reachable from the build session. Copilot, Vertex AI region and Workload Identity Federation statements
  are cited to this repo's docs only. TODO(verify) once those hosts are reachable.
- Open: publishing a Pages site makes it public by default. Whether that is acceptable for a repo marked
  "not yet reviewed by security" is for the AI governance team and security team (Q-new, not yet numbered).

### 2026-11-25 · Added M9 (agent intake and authoring) to the roadmap
- Planning only; no code. Added decisions D-13 to D-15, milestone M9 with items I1 to I7, and open
  questions Q13 to Q16. Scope: an `AgentRequest` issue starts an intake agent that interviews the
  requester on the issue, uses `agentic-bootstrap` to add an LLM-authored agent to the division's agent repo,
  checks it (including cross-model review), and takes tailoring through comments.
- Design choices (individual attribution omitted): the agent is authored as Python in the repo (not a declarative runtime);
  humans approve every sensitive capability; the first build is a local prototype against fakes; the
  agent lives in the division's existing repo; the agent draws only on a curated connector library;
  the reviewer is a different model family where residency allows.
- Consequence to watch: under D-02 everything the intake agent writes is tier 3, so review load stays
  high until Q16 is answered.

### 2026-11-26 · Docs restructure, and recording "done" in the PR that does the work
- New rule (in `AGENTS.md`, `docs/CONTRIBUTING.md` and the "How to use this file" section above): the PR that does
  the work sets the item to `done`, ticks its boxes and adds the work-log and changelog entries. Merging is the
  approval, so no follow-up PR is needed to close out earlier work. `review` now means merged but still waiting on a
  step outside the repository, such as a live run. Applied here: R6, S2 and A2 are `done`. A1 and A3 stay `review`
  because each still has a live run to do.
- Removed `docs/ALIGNMENT_V4.md`: a version-numbered note about an earlier skeleton does not fit a generic harness.
  Its design choices moved to the changelog, its open assumptions were already in the open questions (one line
  added), and its stale legacy-config line is gone (H1 stale-doc item ticked).
- Moved the technical docs into `docs/tech/` (`ADK_PORT.md`, `INPUT_GUARD.md`, `SITE.md`) with an index; project-wide docs
  stay in `docs/`. Updated every link and path. Older work-log entries are left as written: read `docs/ADK_PORT.md`,
  `docs/INPUT_GUARD.md` and `docs/SITE.md` there as `docs/tech/...`.
- H1 trimmed and split. The `run_evals.py` import-order item is done (it now relies on the installed package, so the
  late `sys.path` insert is gone). The preflight command and the generated-project acceptance test moved to a new
  item, H2 (M8, plan first), because they are new behaviour and not tidy-up. H1 is `doing`: only the e2e job in CI
  (Ubuntu and Windows) is left.
- The site's milestone strip was out of date (it said H1 was done and S2 was open); it now matches the roadmap.
- Formatting and spelling: ran `ruff format` on three files that were not clean. CI now runs `ruff format --check`
  and `codespell` (settings in `pyproject.toml`), so neither can drift again. Added `tests/test_docs.py`, which fails
  CI on a broken docs link or heading anchor. The commands are in `AGENTS.md` and the contributing guide.
- Comment-only path fixes in `app/harness/workflow.py`, `policy/risk_tiers.yaml`, `.github/workflows/pages.yml` and
  `tests/test_site.py`. No behaviour changed, so no new eval was added. `.github/workflows/ci.yml` gained two steps
  (a control file; no new actions).

### 2026-11-26 · S2 Model Armor as the primary scanner
- Added `ModelArmorScanner` (`sanitizeUserPrompt` on the regional endpoint, template from config, residency-checked,
  chunked over the documented limit, any call error raises), `CompositeScanner` (blocked if any scanner blocks, a
  scanner error blocks, at least one scanner required) and `default_scanner` (Model Armor required outside
  `HARNESS_ENV=local`). Added the `armor` extra (`google-cloud-modelarmor==0.7.5`) and refreshed `uv.lock`.
- Registered `ModelArmorPlugin` on the harness's ADK `App` for model input and output; a blocked reply escalates
  and is not retried. New guarded surfaces: `review_feedback` and `pr_comment` (with `repo_context` from R6).
  `PRSnapshot` and `BuildResult` gained `comments`. The policy check now fails if a scanned surface is missing.
- Docs read on cloud.google.com and adk.dev (cited in `docs/INPUT_GUARD.md`); `google-adk` 2.15.1 and
  `google-cloud-modelarmor` 0.7.5 checked against the installed packages. Found that only Melbourne supports
  Model Armor among the allowed regions, with limited filters. Renamed `SUNGLASSES_EVALUATION.md` to `INPUT_GUARD.md`.
- Added 8 golden tasks (composite plus the new surfaces) and runner support for `scanner: composite`,
  `scenario.reviews` and `builds[].comments`. A mutation test now also covers a blind Model Armor, and the blind
  Sunglasses test asserts detection below 1.0, since the composite tasks are still caught by Model Armor.
- Not done: no live call to Model Armor. The fixture is authored, not recorded.

### 2026-11-25 · Rename `repo-template/` to `agent-template/`
- Renamed the folder and updated every live reference: the template path in `bootstrap/template.py` and
  `policy_validation.py`, the `ty` exclude in `pyproject.toml`, the tests, `AGENTS.md`, `README.md`, the roadmap
  items and prompts, and the docs. Behaviour is unchanged.
- Older work-log entries are left as written (the log is append-only). Where they say `repo-template/`, read
  `agent-template/`.

### 2026-11-25 · R6 ADK adapter hardening and repo context
- Rewrote `adk_agents.py`: Pydantic `output_schema` per role, one retry then `AgentOutputError` (the workflow
  now escalates on adapter and residency errors), one reused `InMemoryRunner` per role with a fresh session per
  call, and `residency.assert_model_backend` (AI Studio only when `HARNESS_ENV=local`, a key next to Vertex
  refused). Checked against google-adk 2.15.1; adk.dev was not reachable from the session, so the API was read
  from the installed package and the `google/adk-docs` source on GitHub.
- Added read-only repo context (`nodes/repo_context.py`, `GitHubPort.read_file`/`list_files`, caps and a deny
  list in `policy/routing.yaml`, guard surface `repo_context`) and chose `GitHubPort` over the GitHub MCP server.
  Added `skills.py` with `policy/skills.lock.yaml` (pinned revision + SHA-256, instructions-only capability) and
  a trace warning when planner and reviewer share a model.
- Added 4 golden tasks (2 injected-context, 1 skills-lock edit, 1 clean-context) and runner support for
  `repo_files`/`triage_files`. The adapters were not run against live Vertex; that needs an approved project.
- Starting caps, deny list and the empty skills lock remain proposals, marked `TODO(ai_governance)`.

### 2026-11-25 · S3 new-capability detectors
- Added `nodes/capability_check.py` (hunk-aware `nodes/diff_parse.py`, one small function per detector) and
  `policy/capabilities.yaml` (schema-validated; approver roles must exist in `raci.yaml`; allowed regions must
  be within `residency.yaml`). The gate adds the approvers, appends the names (never source lines) to the
  reason and trace, and turns would-be `auto_merge` into `human_approval`. Comments, docs and per-test files
  are ignored; a version bump is not a new dependency; a spec-declared host still needs `security`.
- Added 9 golden tasks (8 adversarial, plus one benign look-alike task that must still auto-merge) and
  `egress_hosts` support in the eval runner. 49 tasks pass at 100% accuracy.
- Known limits: lock-file-only dependency changes and capabilities added outside the diff are not seen;
  pattern matches are review routing, not authorisation.

### 2026-11-25 · S4 Copilot environment in the template
- Added `copilot-setup-steps.yml` (single `copilot-setup-steps` job, SHA-pinned actions, `contents: read`
  only), the `agent-builder` custom agent, and a generated `docs/copilot-agent-environment.md` listing the
  firewall allowlist from `spec.egress_hosts` plus package hosts. `CopilotBuilder` now passes
  `custom_agent`; `GitHubPort.assign_to_copilot` gained an optional `custom_agent` argument.
- Learned from GitHub's docs source: the firewall allowlist is set in Settings > Copilot > Internet
  access, not from a repo file, so the generated list is guidance for an admin. The `custom_agent`
  identifier format is not documented; `agent-builder` (file name) is assumed and marked `TODO(verify)`.
- docs.github.com was unreachable from this session; the docs were read from the `github/docs` source
  on raw.githubusercontent.com instead. The custom-agent file location (`.github/agents`) was not
  confirmed on a page and rests on this roadmap.
- Re-checked against the rendered docs.github.com pages and changed the repo where they disagreed:
  the custom agent file is `agent-builder.agent.md` (the documented suffix) with an explicit `tools` list;
  firewall entries render as URLs (a bare domain also allows subdomains); the setup steps are noted as
  outside the firewall; and the wrong policy path `.github/copilot-setup-steps.yml` was removed (the real file is
  covered by `.github/workflows/**`), with two adversarial tasks. Python hosts are already in
  GitHub's recommended allowlist. The `custom_agent` identifier format is still undocumented.
- Validation: ruff, ty, tests and the offline evals pass.

### 2026-11-18 · A1–A3 starter-agent improvements
- Removed the simulated booking capability. The generated agent exposes only service history and
  repair estimates; the refusal eval covers a booking request even with an explicit confirmation.
- Added local redacted diagnostics and one digest-pinned, instruction-only workshop skill. The
  runbook documents both and explains what remains a platform or review responsibility.
- The starter behaviour evals still need an approved live run. The required CI eval gate and accepted
  baseline remain E3 work.

### 2026-11-18 · M8 starter-agent pilot and first E3 slice
- Added child-agent acceptance criteria for runtime authorisation, redacted diagnostics and governed
  skills. R1 and O1 retain responsibility for repository enforcement and parent audit respectively.
- Shipped a two-case eval dataset and tested that it survives generation. The e2e live path requires
  explicit allowed regions for inference and grading. Live evaluation, accepted baseline evidence
  and CI gating are still E3 work; no required check was relaxed.
- Verified with Agents CLI 1.13.0's dataset parser, ruff, ty and Windows offline e2e: 75 harness
  tests, 38 offline harness eval scenarios and 5 generated-agent tests.

### 2026-11-18 · H1 Python compatibility checks
- Expanded harness CI to Python 3.11, 3.12 and 3.13 with type-checking and separate eval reports for
  each version. The remaining H1 work stays on the roadmap.
- PR validation exposed a dependency-review API `403` in the demo repository. Aligned dependency
  review with the existing GitHub Code Security gate in both workflows.

### 2026-11-18 · S1 security scanning completed in working tree
- Added Gitleaks CLI v8.30.1 with verified release-binary SHA-256 to harness and template CI; the
  template's required `secret_scan` then runs its standalone harness policy checker. Added CodeQL,
  dependency review and zizmor jobs with least-privilege permissions.
- Removed generic secret regexes from `security_harness.py`; generated repositories receive a
  dependency-free `agentic-bootstrap check`. Updated tests and both READMEs.
- GitHub secret scanning and push protection remain an open licensing question (Q11); CodeQL uploads are gated to public repositories or `GHAS_ENABLED=true`.
- Validation: 74 tests, ruff, ty, 38 eval tasks, Windows end-to-end bootstrap, generated CLI install/run,
  strict zizmor collection, Gitleaks against the changed test diff, and `git diff --check` passed.

### 2026-11-18 · R2 blocked on Copilot assignment authentication
- Verified GitHub's current Copilot API guide: assigning an issue to Copilot requires a user-to-server
  token; GitHub App installation tokens are not supported for that operation.
- Kept the installation-token-only security requirement. No client code was added that would appear
  functional but fail at assignment time. R2 needs a security team decision before
  implementation; R1 remains dependent on the R2 client.
- Corrected the recommended order to put R2 before R1, matching R1's explicit dependency.

### 2026-11-18 · M0 completed in working tree
- Added the ADK/skills governance, optional MCP/A2A boundary, tool-level observability, cloud platform Terraform
  contract, and CLI preflight/acceptance-test inputs to their existing roadmap items; added references
  to NIST, OWASP, MCP, A2A, OpenTelemetry and Google ADK/Agents CLI.
- Completed H0 and G1–G7: deterministic plan approval, fail-closed checks, tier-3 harness controls,
  diff-based tamper checks, cross-platform path/rename handling, least-privilege pinned workflows,
  strict schema validation and cross-file policy checks.
- Validation: 74 tests, lint, type-check, 38 golden evaluations (100% decision/tier/approver accuracy),
  Windows end-to-end bootstrap, and `zizmor` all pass. Two previously documented Sunglasses detection
  gaps remain open; the known-gap tests continue to report them.
- Added a holdout-eval design note and Windows UTF-8 setup for the end-to-end command. No stakeholder
  values were invented; the WIF/cloud platform-specific details remain marked for platform team.

### 2026-11-17 · Roadmap created
- Turned the repository gap analysis into this roadmap: decisions D-01 to D-12, eight milestones,
  and questions Q1 to Q12.
- Confirmed by running the gate against the real policy at phase 3: a PR with no checks reported
  auto-merges (G1); `SKILL.md`, markdown prompts and non-conftest `tests/**` Python are tier 1 (G2);
  workflows, CODEOWNERS and eval thresholds/baselines are tier 2 (G2); case-sensitive path matching lets
  `Payments/` and `agents.md` through (G5).
- Not verified: the full `pytest` suite (the analysis sandbox couldn't install packages). Re-run locally
  before starting G1.
