# Contributing

How to change this repo safely. These rules come from [`AGENTS.md`](../AGENTS.md) and the
[Roadmap](ROADMAP.md). They apply to people and to coding agents alike.

## The short version

1. Pick work from the [Roadmap](ROADMAP.md). Take the top `todo` item whose dependencies are `done`.
2. One item is one branch and one pull request.
3. Write the tests first. Run the checks. Update the docs, and set the roadmap item to `done` in the same PR.
4. Never weaken a gate, an approval, a threshold, a baseline or a golden task to make a test pass.

## The rules that must hold

| Rule | Why |
|---|---|
| The merge gate never calls an LLM. | It must be predictable and auditable. |
| Use Google ADK only. Do not add another agent framework. | One framework to review. |
| Never weaken a gate, approval, threshold, baseline or golden task to make a test pass. | It would hide a real problem. |
| A change under `policy/` or `app/harness/nodes/` needs a new or updated golden or adversarial eval. | Proves the change behaves. |
| Prompts and skills change behaviour. Keep their approved source and version. Review them. Add behaviour evals. | A small text edit can change what an agent does. |
| Prompts are not permission. Enforce tool access and side-effect checks in code or platform IAM. | A prompt can be ignored or overridden. |
| No secrets, credentials, full issue bodies or sensitive tool data in source, traces or audit records. | They would leak. |
| Use the GitHub App and Workload Identity Federation. No personal tokens. | Short-lived, traceable access. |
| Every change is a reviewed PR. Do not assume console-only changes. | Everything stays reviewable. |
| Keep the residency and egress limits. | Data stays in Australia. Agents call only approved hosts. |
| If a `TODO(<owner>)` blocks a decision, do not invent the answer. Record the dependency and ask the appropriate role or owner. | The owner decides. |

## The checks

Run all of these before you open a PR. CI runs the same ones, so a failure here is a failure there.

```bash
uv run ruff check .
uv run ruff format --check .      # apply with: uv run ruff format .
uv run codespell                  # settings are in pyproject.toml
uv run ty check
uv run pytest -q
uv run python evals/run_evals.py --out .m0-eval-report.json
```

CI runs on Python 3.11, 3.12 and 3.13. The `ty` version is not pinned, so CI can be newer than your machine.
If CI reports a type error you cannot see locally, run `uv sync --extra dev` and try again.

Do not commit the generated eval report (`.m0-eval-report.json`).

## Definition of done

A change is done when:

- All the checks pass, locally and in CI.
- Behaviour changes have tests. Gate or policy changes also have a golden or adversarial task in `evals/golden_tasks/`.
- The gate still never calls an LLM. No new agent framework. No personal tokens.
- Related docs are updated (`README.md`, `docs/*.md`).
- The roadmap item is set to `done` (or left `doing` or `blocked`, saying what is left) and a dated work-log entry is added, in this same PR. Merging is the approval: do not open a follow-up PR just to mark the work done.
- Anything that needs a stakeholder is marked `TODO(<owner>)` and listed in [Open questions](OPEN_QUESTIONS.md).

## Step by step

1. **Read the roadmap item.** Check its "Done when" list and its prompt.
2. **Branch.** The roadmap suggests `roadmap/<id>-<slug>`.
3. **Plan first** if the item says so (security, policy or design changes).
4. **Test first.** Write the tests and watch them fail. Then change the code.
5. **Keep it small.** The generated-agent rule is about 150 changed lines per PR. Split larger work.
6. **Add evals** for gate, policy and node changes. Put them in `evals/golden_tasks/`.
7. **Update docs and the roadmap**, in the same PR. Set the item to `done` here, not in a later PR.
8. **Open a pull request.** Use a short, conventional commit message, for example `feat(gate): ...` or `fix(template): ...`.
9. **Say what you could not verify.** Cite sources. Mark unknowns `TODO(verify)` or `TODO: UNCONFIRMED`.

## Choosing the model and effort (when using a coding agent)

From the roadmap: use the strongest model with high effort for anything security-relevant, policy-shaping
or architectural. Use a mid-size model for well-specified work and a small one for mechanical cleanup.
When a change touches the merge gate, lean towards more effort.

## Where to put things

| Change | Goes in |
|---|---|
| Who approves what, tiers, required checks | `policy/risk_tiers.yaml` |
| Allowed regions | `policy/residency.yaml` |
| New-capability allowlists | `policy/capabilities.yaml` |
| Gate logic | `app/harness/nodes/` |
| Instructions for generated agents | `agent-template/AGENTS.md` (not the root `AGENTS.md`) |
| Instructions for agents working on this repo | `AGENTS.md` (`CLAUDE.md` just imports it) |

## Things that need a person to approve

Files that control the gate or agent behaviour are always tier 3 and never auto-merge: workflows, CODEOWNERS,
rulesets, agent profiles, eval thresholds and baselines, `policy/`, skills, prompts, and agent instruction
files. AI governance team and security team approve these. See [Security](SECURITY.md).

## Still to be decided

- TODO: UNCONFIRMED: a licence for the repo.
- TODO: UNCONFIRMED: a code of conduct.
- TODO: UNCONFIRMED: review turnaround. The roadmap mentions a 2-business-day review target for AI governance team (O2).
- TODO: UNCONFIRMED: the real GitHub team names for CODEOWNERS (Q2).
