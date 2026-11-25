The harness's own infrastructure follows the same reviewed-PR process as other cloud workloads:
every change is a reviewed PR, never a console change.

- Use `workload-infrastructure` as an illustrative Terraform repository name, with `platform.tf` as
  an example file. The actual repository and layout are not confirmed (`TODO(platform_team)`).
  `agentic-bootstrap plan` prints the three-stage plan; it does not provision infrastructure.
- The platform team reviews Terraform changes (`*.tf`).
- Region from `policy/residency.yaml`; no global endpoints.
- GitHub access via a GitHub App; CI auth via the landing zone's WIF pool. No personal tokens.
- `agents-cli scaffold enhance` / `agents-cli infra cicd` output is a starting point only:
  review it against applicable security policies and fold it into the modules above.
- The webhook entry point (GitHub App events -> harness) needs an ingress route agreed
  with the platform team. Only the optional sandbox adapter needs a Cloud Run Job.

## Agent-evals Workload Identity Federation

The generated agent workflow grants `id-token: write` only to `evals_no_regression`, and that job
runs in the GitHub environment `agent-evals-nonprod`. Configure its WIF provider to require the
exact repository, the `pull_request` event, and that environment in the provider attribute
condition. Bind only the non-production evaluation service account to that provider. Grant that
account Vertex AI inference/evaluation permissions only; it must not deploy agents, change IAM, or
access production resources.

Use the GitHub OIDC claims for repository, event name, and environment as the condition inputs.
**TODO(platform_team):** confirm the landing-zone provider's claim mapping, repository identity,
service-account name, and minimum Vertex role(s); keep all values environment-specific. Never put
service-account keys or personal tokens in the workflow.
