# CI-only holdout evaluations

The holdout suite is the independent check against an agent gaming the visible golden set. The
coding agent must not be able to read, modify, or choose these cases while it is building a PR.

Store holdout cases outside the generated repository (for example, in a restricted repository or
Cloud Storage bucket). CI retrieves them with a narrowly scoped Workload Identity Federation
service account after the agent-authored test job has completed. Keep the data source and evaluator
configuration under trusted owner control; fail closed if the suite is unavailable or incomplete.

Do not copy holdout prompts, expected answers, or hidden tests into workflow logs, artefacts,
comments, or feedback sent to the coding agent. The holdout runner and access policy are tracked in
roadmap item E3.
