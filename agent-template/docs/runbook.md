# Runbook: __AGENT_NAME__

PLACEHOLDER. The AI governance team must approve this before the agent goes live.

## What it does and who owns it
Owner: __OWNER__ (division: __DIVISION__).

## Normal operation
- Expected traffic, latency and cost:
- Dashboards and alerts:

## Local tool diagnostics

From the generated repository, run this credential-free demo. It exercises an
allowed service-history lookup and one rejected by tool input validation:

```bash
uv run pytest -q tests/test_telemetry.py::test_tool_diagnostics_are_redacted --log-cli-level=INFO
```

Look for `agent.telemetry` records like this (IDs abbreviated):

```json
{"event":"tool.completed","request_id":"a917...","tool":"get_service_history","outcome":"rejected","duration_ms":0.16,"instruction_sha256":"7dd2..."}
```

Match `request_id` across tools for one ADK invocation. Check `outcome` for
`ok`, `rejected` (input validation), `needs_inspection` (no estimate), `failed`
(exception), or `unknown` (unrecognised status). `duration_ms` measures only the
tool call, and `instruction_sha256` identifies the effective instructions.
These diagnostics do not capture prompts, tool inputs or outputs, or exception
details. The example uses only Python logging and configures no exporter. Before
enabling platform export or verbose ADK logging, review those independent
settings with `platform_team`; this diagnostic schema does not sanitise them.

## Governed runtime skill

The [garage-summary skill](../agent/skills/garage-summary/SKILL.md) is supplied
by the starter template and owned by __OWNER__ (__DIVISION__). Its only capability
is formatting garage summaries for mechanics. The agent binds its text at startup after
checking the SHA-256 pin in [`agent/prompts.py`](../agent/prompts.py). It does not
discover or download skills, read skill scripts, or add tools, permissions,
credentials or egress. This runtime skill is separate from contributor guidance
in [`AGENTS.md`](../AGENTS.md) and from the parent harness's skill catalogue.

Review changes to the skill text and pin together as behaviour changes. Generate
the pin from UTF-8 text with LF line endings. Run local tests and the skill eval
before accepting the revision; require the repository's protected review path
(the policy-derived ruleset when installed). The hash detects drift from
reviewed content; it is not a substitute for review or platform authorisation.

Use the approved non-production model and grading regions for the live eval.
Replace `APPROVED_EVAL_REGION` with the approved grading region; don't fall back
to the CLI default if the managed evaluator isn't available there.

```bash
agents-cli eval run --dataset evals/garage-skill.json --metrics final_response_quality --region APPROVED_EVAL_REGION
```

## Common faults
| Symptom | Likely cause | First action | Escalate to |
|---|---|---|---|
| Tool calls failing | Downstream system unavailable | Check the downstream status | Provider team |
| Answers off-topic or unsafe | Prompt or model drift | Compare against eval baseline | Application team |
| Platform errors | Governed platform service issue | Check status, raise a provider support case | AI governance team |

## Changes and rollback
Every change is a reviewed PR; no console changes. Roll back by reverting the PR and redeploying.
