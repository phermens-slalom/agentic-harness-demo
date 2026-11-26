# Changelog

What changed, newest first, in plain English. It is a summary of the work log in the [Roadmap](ROADMAP.md).
The roadmap work log has the detail and wins if they disagree.

The package version in `pyproject.toml` is `0.2.0`. TODO: UNCONFIRMED release and tagging practice. Tagged,
attested releases are planned (S5).

## 2026-11-26

- **E3 in progress.** Added required coverage and quality checks, 80% starter coverage and eval marks,
  pre-execution static scans, and an unwired regression comparator. AI Governance will approve the
  baseline. Live regression and isolated holdout evaluations remain open.
- **I1, request drafts.** Added the issue form, strict offline parser, repository-access contract and
  evals. Anyone with repository access may request an agent; hosted enforcement is I7. AI governance
  is the contact for reference template access, which W2 still needs.
- **Docs restructured.** Technical docs moved to `docs/tech/` (input guard, ADK port notes, project site), with an
  index; project-wide docs stay in `docs/`. The version-numbered alignment note was removed and its content moved
  here and into the open questions.
- **Work is recorded as done in its own PR.** The PR that does the work sets the roadmap item to `done` and adds
  the log entries. Merging is the approval, so no follow-up PRs are needed. R6, S2 and A2 were closed out this way.
- **H1 trimmed, H2 added.** The `run_evals.py` import-order fix is done. The preflight command and the
  generated-project acceptance test moved to a new item, H2, because they are new behaviour.
- **CI checks formatting, spelling and docs links.** `ruff format --check` and `codespell` now run in CI, and a new
  test fails on a broken docs link. Three files that were not clean were reformatted.
- **S2, Model Armor as the main scanner.** A Model Armor scanner and a composite scanner (blocked if either scanner
  blocks; any scanner error counts as a block) now sit behind the input guard beside Sunglasses. `ModelArmorPlugin`
  is registered on the harness's ADK app. Review findings and PR comments are now scanned too. `SUNGLASSES_EVALUATION.md`
  became `INPUT_GUARD.md`. CI plays back a fixture, so Model Armor has not run live. Eight golden tasks added.

## 2026-11-25

- **Project site.** A static site in `site/` summarises the vision, workflow, merge gate, architecture, safety,
  status, getting started and FAQ, with sources and a comparison with public tools. A Pages workflow publishes it
  and `tests/test_site.py` guards its links. Deploy steps and image prompts are in [Site](tech/SITE.md).
- **Australian spelling.** Skill provenance trace consumers must use the event name
  `behaviour_artefacts`. Generated evals now use the rubric group `starter_behaviour`,
  and the Makefile cleanup target is `clean-artefacts`.
- **M9 added to the roadmap: agent intake and authoring.** Planning only, no code. A person raises an
  `AgentRequest` issue and an intake agent asks them plain-language questions, adds the agent to the division's
  agent repo, writes its code and evals, and opens a PR. It never approves or merges. Agents reach other systems
  only through a curated connector library, and a different model family reviews the result. Adds decisions D-13
  to D-15, items I1 to I7 and open questions Q13 to Q16.
- **R6, ADK adapters hardened.** Each AI role returns a checked, structured reply. A bad reply is retried once,
  then escalated. One runner is reused per role. Residency fails closed (AI Studio keys only for local use).
  The planner and reviewer get read-only, size-capped, scanned repo context. Skills load only from a pinned,
  fingerprinted version. Four golden tasks added. (PR #8)
- **S3, new-capability detectors.** The gate now spots new models, hosts, regions, data stores, dependencies
  and tool or protocol links in a diff, and adds approvers. Nine golden tasks added. (PR #7)
- **S4, Copilot environment in the template.** Generated repos get a Copilot setup workflow, a custom agent
  profile and a generated firewall-allowlist note. Checked against GitHub's docs. (PR #6)

## 2026-11-18

- **A1 to A3, starter agent.** The generated example agent is read-only, has redacted tool diagnostics and one
  pinned, guidance-only skill. The booking tool was removed. The runbook explains each.
- **M8, pilot readiness and the first part of E3.** A two-case starter eval set ships and survives generation.
  Live evals, an accepted baseline and CI gating are still to do.
- **H1, Python versions.** CI now tests Python 3.11, 3.12 and 3.13.
- **S1, security scanning.** Gitleaks (checked by SHA-256), CodeQL, dependency review and zizmor in CI.
  The harness's own secret patterns were removed in favour of Gitleaks.
- **R2 found blocked.** GitHub's Copilot assignment API needs a token type the harness rule does not allow.
  No client code was added that would look finished but fail. Needs a security team decision.
- **M0 complete, the gate is trustworthy.** Added the repo guide (H0) and the gate hardening G1 to G7:
  fail closed on missing checks, control files in tier 3, tamper detection, rule-based plan approval,
  case-insensitive path rules and rename handling, least-privilege CI with pinned actions, and strict
  policy validation.

## 2026-11-17

- **Roadmap created.** Twelve decisions (D-01 to D-12), eight milestones and twelve open questions (Q1 to Q12),
  from a gap analysis of the first working version.

## Before that

- **First working version.** The golden workflow and RACI as data, a merge gate, an issue-to-merge loop, the
  bootstrap CLI, the template, the dry-run evals, and the Sunglasses input guard with adversarial evals.
  Later changes tightened the risk tiers and added shadow mode.

### Design choices behind the first working version

Moved here from a former "alignment" note, which was removed so the docs stay generic.

- **Spine.** The eight-stage golden workflow and the adaptable example RACI are policy data in `policy/`,
  validated in tests. The issue-to-merge loop covers the Build and Verify stages only.
- **Merge gate.** Auto-merge is phase-flagged and off in phase 1. The gate returns the required approvers,
  derived from changed paths (`*.tf` to `platform_team`, privileged YAML to `security`, production paths to
  `product_owner` and `architecture`), on top of `app_team` and `ai_governance`.
- **Required checks.** `lint`, `tests`, `evals_no_regression` and `secret_scan`. A failing check feeds back
  into the build loop.
- **Builder.** GitHub Copilot through `GitHubPort` is the default. A Cloud Run sandbox builder is kept as an option.
- **Residency and review.** A guard on the Vertex location, with allowed regions in `policy/residency.yaml`.
  The reviewer applies the review checklist.
- **Bootstrap CLI.** Three stages: `new`, `check` and `plan`.
- **Deploy target.** `agent_runtime`, set in `agent-template/agents-cli-manifest.yaml`. The ADK 2.0 notes still
  mention graph-workflow friction on that target ([ADK port notes](tech/ADK_PORT.md)).
- **Removed.** Vendored skills (now a pinned skills repository through `HARNESS_SKILLS_DIR`); a Gemini CLI or
  Antigravity coding agent as the default; a Pub/Sub trigger assumption and its stub workflow; and the
  `infra/**` rule (replaced by the `*.tf` rule).
- **Dependencies.** Already minimal: `pyyaml` and `pydantic`, with ADK optional.
