# Alignment summary (11 Nov 2026)

Source precedence: repository requirements and the illustrative, adaptable RACI policy, then public platform documentation.

## Changed
- **Spine**: the eight-stage golden workflow and adaptable example RACI are policy data (`policy/`), validated in tests. The issue-to-merge loop is the Build/Verify stages only.
- **Merge gate**: auto-merge is phase-flagged and off in Phase 1. Gate returns required approvers derived from paths (`*.tf` → `platform_team`, privileged YAML → `security`, prod → `product_owner` + `architecture`) on top of `app_team` + `ai_governance`.
- **Required checks**: `lint`, `tests`, `evals_no_regression`, `secret_scan`; a failing check feeds back into the build loop.
- **Builder**: GitHub Copilot via `GitHubPort` is the default. Cloud Run sandbox kept as optional.
- **Residency**: guard on Vertex location; allowed regions in `policy/residency.yaml`.
- **Reviewer**: applies the review checklist.
- **Deploy target** in `[tool.agents-cli]`: `agent_runtime` (agents-cli default). ADK_PORT.md still notes graph-workflow friction there. This is the legacy config format; agents-cli >= 0.2 warns and expects `agents-cli-manifest.yaml` (migrate with `agents-cli scaffold upgrade`).
- **Bootstrap CLI** with the three stages from the POC plan.

## Removed
- Vendored skills → pinned skills repository via `HARNESS_SKILLS_DIR`.
- Gemini CLI / Antigravity as default coding agent; Pub/Sub trigger assumption; stub trigger workflow; `infra/**` rule (replaced by `*.tf` rule).
- Python dependencies were already minimal (`pyyaml`; ADK optional); only `ruff` added to dev.

## Assumptions to confirm
- Which files are "privileged YAML"; GitHub role-to-team mappings; the actual infrastructure repository and file layout. `workload-infrastructure` and `platform.tf` are illustrative only.
- Copilot coding agent assignment API and `agents-cli eval compare` flags (marked TODO/verify).
- Pinned skills repository names for planner and reviewer.
- Harness hosting and webhook ingress route; the harness's own deployment target.
- Eval thresholds for bespoke agents remain a business decision; no owner or threshold is assigned here.
- Regional availability of memory services remains unconfirmed.
