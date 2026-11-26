# Porting `workflow.py` to an ADK 2.0 Workflow

`IssueToMerge.run()` is written as a plain orchestrator so it can be tested and audited
before committing to a specific ADK 2.x API surface. Each step maps onto a graph node:

| `workflow.py` step | ADK 2.0 node type | Notes |
|---|---|---|
| route | function node | deterministic, reads `policy/routing.yaml` |
| triage | LLM agent node | `AdkTriager` |
| plan + spec gate | LLM agent node + HITL breakpoint | pause when `needs_human_approval` |
| build loop | loop / retry around a function node | calls the sandbox; cap from `routing.yaml` |
| review | LLM agent node | separate identity and ideally a different model |
| merge gate | function node | `nodes/merge_gate.decide`; returns required approvers |
| escalate | edge target from every node | notification + HITL |

Before porting:
1. Pin an exact `google-adk` version and read the 2.0 docs at adk.dev for graph workflows.
2. Don't wrap node code in broad `except Exception:` — ADK 2.0 relies on exceptions
   propagating for automatic retries, telemetry and HITL pauses.
3. Check deploy target. Community reports show friction deploying graph workflows to
   Agent Runtime; Cloud Run is the fallback. pyproject targets `agent_runtime` (agents-cli default, cloud platform direction); switch if the port hits that friction.
4. Keep `tests/test_workflow.py` passing by running the same fakes through the ported graph.

## The LLM adapters today (R6)

`adapters/adk_agents.py` is the only place that touches ADK for triage, planning and review. Checked
against google-adk 2.15.1 (pyproject allows `>=2.12,<3`; R3 pins it exactly):

- **Structured output.** Each role is an `LlmAgent(output_schema=<Pydantic model>)`
  ([LLM agents](https://adk.dev/agents/llm-agents/): in Python the final reply must be a JSON string
  matching the schema, and a Pydantic model is a supported schema type). The reply is parsed with
  `model_validate_json`; there is no regex scraping. A reply that fails the schema is retried once with a
  repair note that names only the problem fields, then raises `AgentOutputError`, and the workflow escalates.
  Other errors (network, quota) are not retried here and are not swallowed.
- **Runner reuse.** One `InMemoryRunner` per (role, model, instruction, schema), reused across calls. Each
  call gets a fresh session that is deleted afterwards, so nothing carries over between tasks. The final
  reply is the last non-empty, non-thought text of an `Event.is_final_response()` event.
- **Residency fails closed.** `residency.assert_model_backend` runs before every model call. Outside
  `HARNESS_ENV=local` the backend must be Vertex AI with an allowed `GOOGLE_CLOUD_LOCATION`; an AI Studio
  key, or a key set next to Vertex, is refused. The workflow escalates on a `ResidencyError`.
- **Models per role.** `HARNESS_MODEL_DEFAULT`, overridden by `HARNESS_MODEL_TRIAGE`, `_PLANNER` or
  `_REVIEWER`. If the planner and reviewer share a model the trace records a `config` warning (it does not block).
- **Pydantic schema note.** The schemas use bounds and a `Literal` but not `extra="forbid"`: Gemini's
  response-schema support for `additionalProperties` is not something we have confirmed, and ADK sends
  constraints to the model while Python re-validates them.

### Repo context

`nodes/repo_context.py` gives the planner and reviewer read-only context: `AGENTS.md`, the file tree and
a few files, through `GitHubPort.read_file` / `list_files` (the GitHub App needs `contents: read` only).
The planner's files are the ones triage named; the reviewer's are the plan's files. File names come from
model output, so they are untrusted: absolute paths, `..` and the `deny_paths` list in
`policy/routing.yaml` (`.env`, keys, secrets, tfvars, ...) are never read. Caps (`repo_context` in the same
file) are enforced before anything reaches a model, and the text is scanned by the input guard on the
`repo_context` surface; a block escalates the task. The trace records file names, counts and sizes, never content.

**Why not the GitHub MCP server for this.** Its `--read-only` mode would also work, but the model would
choose what to read (non-deterministic reads, more injected-text surface), tool results would reach the
model unless a plugin scanned them, and it brings credential and scope questions (audience-bound tokens,
no caller-token forwarding). A fixed, capped, scanned read by the harness is simpler to audit. Tracked in
the PR for R6 with the comparison.

**MCP and A2A are opt-in.** Neither is used by the harness. If a team adds an MCP server: allowlist each
server by exact host in `policy/capabilities.yaml` review (S3 flags new MCP toolsets), grant the least
scopes, use audience-bound credentials issued for that server, never forward a caller's token, and treat tool
output as untrusted input to the guard. Defer A2A until cross-agent delegation is a real requirement.
Protocol metadata (an MCP tool list, an A2A agent card) never grants access; tool authorisation is enforced in
code and platform IAM.

### Model Armor

`ModelArmorPlugin` is registered on the harness's own ADK `App` when Model Armor templates are configured
(`HARNESS_MODEL_ARMOR_PROMPT_TEMPLATE` and `_RESPONSE_TEMPLATE`; both are required outside `HARNESS_ENV=local`).
It screens the latest user content and the model's reply ([ADK Model Armor plugin](https://adk.dev/integrations/model-armor/)).
Both templates must be in one allowed location, and the harness keeps `block_on_screening_failure` on. A blocked
reply raises `AgentOutputError` straight away: it is never retried. The same templates feed the input guard.
See [`INPUT_GUARD.md`](INPUT_GUARD.md).

### Skills

`skills.py` loads a planner or reviewer skill only if `policy/routing.yaml` names it **and**
`policy/skills.lock.yaml` pins it: a full 40-character source revision (never a branch, tag or `latest`)
plus the SHA-256 of its `SKILL.md`. Nothing is fetched. A mismatch, a missing pin or a missing checkout
refuses to load and the workflow escalates. The trace records each skill's source, revision, SHA-256,
declared capabilities and owner. The only declared capability is `instructions`: a skill cannot grant tools,
permissions or egress. Skill names and the approved revision are `TODO(ai_governance)` (Q7); the lock is empty
until then. Every change to a skill or prompt needs review and a behaviour eval.
