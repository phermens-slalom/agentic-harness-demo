# CI-only holdout evaluations

The holdout suite is the independent check against an agent gaming the visible golden set. The
coding agent must not be able to read, modify, or choose these cases while it is building a PR.

Store holdout cases outside the generated repository (for example, in a restricted repository or
Cloud Storage bucket). CI retrieves them with a narrowly scoped Workload Identity Federation
service account after the agent-authored test job has completed. Keep the data source and evaluator
configuration under trusted owner control; fail closed if the suite is unavailable or incomplete.

Merely keeping the cases in a separate repository or bucket does not hide a prompt from
PR-authored code that processes it. Nor does a GitHub Actions runner prevent that code from
reading credentials available to its job. A reviewed isolation design is still needed before
this requirement can be marked complete; a deterministic scan is not a sandbox.

Do not copy holdout prompts, expected answers, or hidden tests into workflow logs, artefacts,
comments, or feedback sent to the coding agent. The holdout runner and access policy are tracked in
roadmap item E3.
