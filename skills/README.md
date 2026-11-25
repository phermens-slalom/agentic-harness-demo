Skills come from the project's pinned skills repository, not from a vendored third-party repo.

    export HARNESS_SKILLS_DIR=/path/to/skills-repository-checkout   # pin to a commit

List the skill names to load per role in `policy/routing.yaml` (`skills.planner`,
`skills.reviewer`); `adapters/adk_agents.py` reads `$HARNESS_SKILLS_DIR/<name>/SKILL.md`.
Review upstream diffs before bumping the pin: these files change agent behaviour.
