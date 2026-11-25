# Changelog

What changed, newest first, in plain English. It is a summary of the work log in the [Roadmap](ROADMAP.md).
The roadmap work log has the detail and wins if they disagree.

The package version in `pyproject.toml` is `0.2.0`. TODO: UNCONFIRMED release and tagging practice. Tagged,
attested releases are planned (S5).

## 2026-11-25

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
