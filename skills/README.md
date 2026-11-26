Skills come from the project's pinned skills repository, not from a vendored third-party repo.

    export HARNESS_SKILLS_DIR=/path/to/skills-repository-checkout   # pin to a commit

List the skill names to load per role in `policy/routing.yaml` (`skills.planner`,
`skills.reviewer`); `app/harness/skills.py` loads `$HARNESS_SKILLS_DIR/<name>/SKILL.md` only if the skill is pinned in
`policy/skills.lock.yaml` (full commit and SHA-256 of the file); an unpinned skill is refused.
Review upstream diffs before bumping the pin: these files change agent behaviour.
