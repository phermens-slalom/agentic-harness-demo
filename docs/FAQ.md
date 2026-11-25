# FAQ

Short answers. Longer explanations are linked. Unknown words are in the [Glossary](GLOSSARY.md).

## About the harness

**What is this repo, in one sentence?**
The rules, checks and approvals that let an AI coding agent build software for agents built with this harness safely. See the [Vision](VISION.md).

**Does it deploy anything?**
No. Deployment is gated and needs explicit human approval. The harness decides what a change needs to merge.

**Does an AI decide whether a change merges?**
No. The merge gate is plain code and never calls an LLM. AI is used to triage, plan and review. The gate reads paths, diffs and check results.

**Who is accountable?**
People. `policy/raci.yaml` is an illustrative, adaptable policy for roles and responsibilities; tailor it to the repository. The merge gate uses the repository's configured policy to determine required approvals.

**Is it finished?**
No. The gate, detectors, policy checks, workflow (with fakes) and bootstrap work. The real GitHub client, live evals, audit log and hosting are not built. See the [Roadmap](ROADMAP.md) and [Open questions](OPEN_QUESTIONS.md).

**Why can't it use the GitHub client today?**
GitHub's Copilot assignment API needs a kind of token that the "installation token only, no personal tokens" rule does not allow. security team has to decide. This is R2.

## Decisions it makes

**What does `auto_merge` need?**
Tier 1 (tests and docs), phase 3 or 4, all four required checks green, the reviewer approving, no tampering, and no new capability found. The policy file ships at phase 1, where nothing auto-merges.

**What are the four required checks?**
`lint`, `tests`, `evals_no_regression`, `secret_scan`.

**What happens if checks are missing?**
The gate escalates and names the missing checks. Missing is not treated as passing.

**Why did a tiny change need security review?**
Probably because it touched a control file, a sensitive path (`payments`, `auth`, `claims`, `pii`), an IAM file, or it added something new (a host, model, region, data store, dependency or tool link). The reason text says which.

**Why was `reject_to_planning` returned?**
The change is over 400 lines. Split the task.

**Can a new host or dependency be approved by the capability check?**
No. It only adds approvers. People approve.

## Running and fixing

**Which commands do I run before a PR?**
`uv run ruff check .`, `uv run ty check`, `uv run pytest -q`, and `uv run python evals/run_evals.py --out .m0-eval-report.json`. See [Getting started](GETTING_STARTED.md).

**CI reports a type error I cannot see locally.**
The `ty` version is not pinned, so CI can be newer than your machine. Run `uv sync --extra dev` and try again.

**`uv` warns that `VIRTUAL_ENV` does not match the project environment.**
It is harmless. You are inside the harness environment while working in a generated agent. Run `deactivate` or open a new terminal.

**On Windows, install fails with "Microsoft Visual C++ 14.0 or greater is required".**
A very new Python has no ready-made PyYAML build, so it tries to compile. Pin Python to 3.13 (3.12 also works).

**The end-to-end script prints odd characters on Windows.**
Set UTF-8 first: `$env:PYTHONIOENCODING = "utf-8"`.

**`agents-cli` is not found.**
Open a new terminal after `setup`, then run `agents-cli --version`. If it is still missing: `uv tool install --python 3.13 google-agents-cli`.

**The generated agent's `evals_no_regression` check fails.**
It is a stub that fails until it is wired to `agents-cli eval run` through Workload Identity Federation (E3).

**Why are CodeQL and dependency review skipped?**
They run only on public repos or when `GHAS_ENABLED=true`, set after GitHub Code Security is enabled.

**My AI Studio key is refused.**
It is allowed only when `HARNESS_ENV=local`. Elsewhere the models must come from Vertex AI in an allowed Australian region.

**My location is refused.**
Only the locations in `policy/residency.yaml` are allowed. `global` is never allowed.

## Changing the repo

**I changed a file in `policy/` and a test or eval failed. Can I loosen the threshold?**
No. Never weaken a gate, approval, threshold, baseline or golden task to make a test pass. Fix the cause. See [Contributing](CONTRIBUTING.md).

**Do I need an eval for every change?**
For anything under `policy/` or `app/harness/nodes/`, yes: a new or updated golden or adversarial task in `evals/golden_tasks/`.

**Where do instructions for generated agents live?**
`agent-template/AGENTS.md`. The root `AGENTS.md` is for agents working on this repo.

**Can I add another agent framework?**
No. Google ADK only.

**How do I add a skill?**
Name it in `policy/routing.yaml` and pin it in `policy/skills.lock.yaml` with a full commit and the file's fingerprint. This is a tier-3 change with an eval. The real skill names are still open (Q7).

**What do I do about a `TODO(owner)`?**
Do not invent the answer. Record the dependency and ask the appropriate role or owner.

## Security

**Can I use a personal access token?**
No. Use the GitHub App and Workload Identity Federation.

**Is the input guard on?**
It must be passed to the workflow, and its policy ships in `shadow` mode, which records matches without stopping the task. See [Security](SECURITY.md).

**Where do I report a security problem?**
TODO: UNCONFIRMED. No contact is named in the repo.
