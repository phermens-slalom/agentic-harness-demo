"""Agent spec: the machine-readable slice of an agent brief the bootstrap needs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .. import residency

SLUG = re.compile(r"^[a-z][a-z0-9-]{2,40}$")
HOST = re.compile(r"^(?!-)[a-z0-9-]+(\.[a-z0-9-]+)+$")
REQUIRED = ("name", "division", "owner", "sponsor", "classification", "description")


@dataclass
class AgentSpec:
    name: str
    division: str
    owner: str
    sponsor: str
    classification: str
    description: str
    location: str = "australia-southeast2"
    environments: list[str] = field(default_factory=lambda: ["nonprod", "prod"])
    egress_hosts: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> AgentSpec:
        data = yaml.safe_load(Path(path).read_text()) or {}
        missing = [k for k in REQUIRED if not data.get(k)]
        if missing:
            raise ValueError(f"spec missing required fields: {missing}")
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def validate(self) -> list[str]:
        problems = []
        if not SLUG.match(self.name):
            problems.append(f"name {self.name!r} must be a lowercase slug (3-41 chars)")
        if not SLUG.match(self.division):
            problems.append(f"division {self.division!r} must be a lowercase slug")
        try:
            residency.assert_allowed(self.location)
        except residency.ResidencyError as e:
            problems.append(str(e))
        for h in self.egress_hosts:
            if not HOST.match(h):
                problems.append(
                    f"egress host {h!r} must be an exact hostname (no wildcards, schemes or paths)"
                )
        return problems
