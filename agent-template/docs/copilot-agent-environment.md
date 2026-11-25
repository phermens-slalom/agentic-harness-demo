# Copilot coding agent environment

Generated for `__AGENT_NAME__`. The setup steps and the custom agent live in the repository;
the network firewall does not.

| What | Where | Enforced by |
|---|---|---|
| Setup steps | `.github/workflows/copilot-setup-steps.yml` | GitHub Actions; only runs from the default branch |
| Custom agent | `.github/agents/agent-builder.agent.md` | GitHub; the `tools` list narrows its tools, but it is not an authorisation boundary |
| Firewall allowlist | Repository Settings > Copilot > Internet access (or the organisation setting) | GitHub settings, not a file in this repo |

## Firewall allowlist

GitHub does not read the allowlist from a repository file. A repository admin adds the entries below
under Settings > Copilot > Internet access > Custom allowlist, and only if the organisation allows
repository custom rules. Changing the allowlist needs `ai_governance` and Security approval.

Entries are URLs, not bare domains: GitHub allows a bare domain together with all its subdomains,
while a URL allows only that scheme and host. The agent's approved egress hosts:

__EGRESS_ALLOWLIST__

GitHub's recommended allowlist already covers common Python package hosts. These only need adding if
that allowlist is disabled:

__PACKAGE_ALLOWLIST__

TODO(Security): replace the package hosts with the internal package mirror.

## Limits to know about

- The firewall covers processes the agent starts through its shell tool. It does **not** cover
  the setup steps, which run unfiltered, or MCP servers other than the built-in ones. Keep the setup
  steps limited to pinned, reviewed installs.
- Copilot code review reuses `copilot-setup-steps.yml` unless a `copilot-code-review.yml` exists.
- GitHub says the firewall is not a comprehensive security control, so keep review and the merge gate
  in place.
