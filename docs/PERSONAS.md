# Personas

Who works with the harness and the [delivery process](DELIVERY.md), which lanes they work in, how they come in,
and what they raise or approve. People are described by role only. There is one section per policy role.

Approvals here come from `policy/raci.yaml`, `policy/risk_tiers.yaml` and `policy/golden_workflow.yaml` as they
are today. The role ids in those files are `app_team`, `ai_governance`, `platform_team`, `security`,
`product_owner` and `architecture`.

**Mapping to policy roles.** Product manager is shown against the `product_owner` role and application engineer
against `app_team`. Whether those are the same people is **TODO: UNCONFIRMED**. Real team names are Q2.

## How a person comes in

| Entry | Status |
|---|---|
| **An external process orchestrator** | Proposed as the primary entry point for non-engineers (D-17, Not built). It would hold each journey as a case, route human tasks and be the UI. |
| `AgentRequest` issue form | Built. An offline parser turns it into an untrusted draft (I1). Any person with repository access may raise one. The hosted trigger is blocked (I7). |
| `agentic-bootstrap` CLI (`new`, `check`, `plan`) | Built for repo generation, checks and the cloud PR plan. |
| `agentic-bootstrap lane status\|next` | Proposed (DP3, Not built). An engineer convenience that reads the same lane-exit contract (DP10) as the orchestrator. |

```text
agentic-bootstrap lane status   # which lane a piece of work is in, and which exit requirements are unmet
agentic-bootstrap lane next     # check the exit requirements and say whether the work may move on
```

A command that reports is advisory. Only the gate and the approvers decide. An orchestrator approval never
replaces the merge gate or a GitHub review. **Ownership of the delivery process stays open (Q20).**

## The requester

Anyone with repository access may raise an `AgentRequest` (I1). The requester may or may not be the product
manager, and a request grants nothing: the draft is untrusted, and every step still passes the gate and the
named approvers. The requester is not a policy role.

## Product manager

- **Lanes:** Prototype (leads), Verify (consulted), Harden (production approval).
- **Comes in through:** the orchestrator (proposed), or the `AgentRequest` issue form today. The intake agent
  (I3, not built) would ask the questions and fill the Mission Brief.
- **Raises:** the request, the Mission Brief and the hypotheses to test.
- **Approves (today):** `product_owner` approves the `frame` and `release` stages and, with `architecture`,
  production-deploy changes (tier 3). `product_owner` is accountable for production deployment approval.

## Application engineer

- **Lanes:** Prototype, Verify, and Harden as the one who raises the work.
- **Comes in through:** the `agentic-bootstrap` CLI, the template and agent-repo PRs.
- **Raises:** agent code, evals, the golden data set, runbooks and the cloud PRs.
- **Approves (today):** `app_team` is a base approver on every agent PR and approves the `build` and `verify`
  stages. It is responsible and accountable for building, testing and deploying to non-prod.

## AI governance

- **Lanes:** Verify (review), Harden (review and sign-off), Operate (support and learning loop).
- **Comes in through:** agent-repo PRs and the review checklist.
- **Raises:** changes to the template, the review checklist and the golden workflow. In the `operate` stage it
  raises the learning-loop work.
- **Approves (today):** `ai_governance` is a base approver on every agent PR, and approves the `register`,
  `provision`, `connect`, `verify`, `release` and `operate` stages. With `security` it approves control-file
  changes (tier 3, `harness-controls`). It is accountable for agent-repo code review, handover into support and
  day-to-day support.

## Security

- **Lanes:** Harden (formal review, if D-16 and the lane proposal are agreed), informed when work enters
  Prototype, and the destination of anything the gate escalates. Today also `frame`, `register`, `provision`
  and `connect`.
- **Comes in through:** PRs that touch tier 3 paths, and the exceptions that escalate to it.
- **Raises:** decisions on tokens, residency, scanners and the control-file boundary (Q1, Q3, Q4, Q15).
- **Approves (today):** `security` approves control files (with `ai_governance`), privileged IAM config, sensitive
  domains and agent steering files (tier 3). It is responsible and accountable for "Security Architecture or
  design review of every change".
- **Unknown:** who the security-team reviewers are and the escalation process (Q19).

## Platform

- **Lanes:** Harden (provision and connect).
- **Comes in through:** the cloud-project PRs that `agentic-bootstrap plan` lists, and Terraform changes.
- **Raises:** hosting, ingress and landing-zone decisions (Q5, Q12).
- **Approves (today):** `platform_team` approves the `provision` stage and Terraform changes (tier 3). It
  approves ownership and versioning of the platform module and baseline.

## Architecture

- **Lanes:** Prototype and Verify (consulted, in the D-16 proposal), Harden (architecture review before
  production).
- **Comes in through:** agent-repo PRs and the release review.
- **Raises:** design concerns on the Mission Brief and the multi-agent shape of a system.
- **Approves (today):** `architecture` approves the `frame` and `release` stages and, with `product_owner`,
  production-deploy changes (tier 3). It is responsible and accountable for architecture review before
  production.

## Not decided

Which lane is "owned" by whom beyond approvals, and who owns the delivery process itself, are open (Q20).
