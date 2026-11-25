"""Load runtime skills for the harness's own planner and reviewer from an approved, pinned revision.

A skill is a behaviour-changing input, so it loads only if it is named in policy/routing.yaml, pinned
in policy/skills.lock.yaml, and its SKILL.md still matches the pinned SHA-256. Nothing is fetched,
nothing floats, and a skill cannot grant tools, permissions or egress (those stay in code and IAM).
These are the harness's own skills; the generated agent's runtime skill is separate (A3).
"""

from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from .models import AdapterError
from .policy import POLICY_DIR, Routing
from .policy_validation import SkillsLock, load_policy_file

_REVISION = re.compile(r"[0-9a-f]{40}")


class SkillError(AdapterError):
    pass


@dataclass(frozen=True)
class SkillProvenance:
    name: str
    source: str
    revision: str
    sha256: str
    capabilities: tuple[str, ...]
    owner: str

    def as_trace(self) -> dict[str, object]:
        return {
            "name": self.name,
            "source": self.source,
            "revision": self.revision,
            "sha256": self.sha256,
            "capabilities": list(self.capabilities),
            "owner": self.owner,
        }


@dataclass(frozen=True)
class LoadedSkills:
    text: str = ""
    provenance: list[SkillProvenance] = field(default_factory=list)


def load_skills(
    role: str,
    env: Mapping[str, str] | None = None,
    routing: Routing | None = None,
    lock_path: Path | None = None,
) -> LoadedSkills:
    """Concatenate the pinned SKILL.md files for `role`; empty when routing names none."""
    names = (routing or Routing.load()).skills.get(role, [])
    if not names:
        return LoadedSkills()
    env = os.environ if env is None else env
    lock = load_policy_file(lock_path or POLICY_DIR / "skills.lock.yaml", SkillsLock)
    if not lock["source"] or not _REVISION.fullmatch(lock["revision"]):
        raise SkillError("skills.lock.yaml needs a source and a full 40-character commit revision")
    root = env.get("HARNESS_SKILLS_DIR")
    if not root:
        raise SkillError(f"skills are configured for {role} but HARNESS_SKILLS_DIR is not set")
    texts: list[str] = []
    provenance: list[SkillProvenance] = []
    for name in names:
        pinned = lock["skills"].get(name)
        if pinned is None:
            raise SkillError(f"skill {name!r} is not pinned in skills.lock.yaml")
        path = Path(root) / name / "SKILL.md"
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise SkillError(f"skill {name!r} not found under HARNESS_SKILLS_DIR") from exc
        digest = hashlib.sha256(data).hexdigest()
        if digest != pinned["sha256"]:
            raise SkillError(f"skill {name!r} does not match its pinned SHA-256 (got {digest[:12]}...)")
        texts.append(data.decode("utf-8"))
        provenance.append(
            SkillProvenance(
                name, lock["source"], lock["revision"], digest, tuple(pinned["capabilities"]), pinned["owner"]
            )
        )
    return LoadedSkills("\n".join(texts), provenance)
