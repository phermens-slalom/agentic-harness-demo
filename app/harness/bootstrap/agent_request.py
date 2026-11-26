"""Deterministic, untrusted draft parsing for the AgentRequest issue form.

The access port must use trusted identity and repository information, never issue text.
Drafts are untrusted; this module does not scan text or authorise a build.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from ..ports import RequesterAccess
from .spec import AgentSpec


class AgentRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    name: str = ""
    division: str = ""
    owner: str = ""
    sponsor: str = ""
    problem: str = ""
    outcome: str = ""
    systems: str = ""
    data: str = ""
    classification_choice: str = ""
    classification: str = ""
    approvals: str = ""

    HEADINGS: ClassVar[dict[str, str]] = {
        "Agent name": "name",
        "Division": "division",
        "Owner": "owner",
        "Sponsor": "sponsor",
        "Problem and people": "problem",
        "Successful outcome": "outcome",
        "Systems": "systems",
        "Data": "data",
        "Data classification": "classification_choice",
        "Classification name": "classification",
        "Action approvals": "approvals",
    }

    @classmethod
    def from_issue_body(cls, body: str) -> AgentRequest:
        """Parse GitHub's form headings; reject unrecognised or repeated sections."""
        fields: dict[str, str] = {}
        current: str | None = None
        lines: list[str] = []
        for line in body.splitlines():
            if line.startswith("### "):
                if current is not None:
                    fields[current] = "\n".join(lines).strip()
                heading = line[4:].strip()
                if heading not in cls.HEADINGS:
                    raise ValueError("unrecognised AgentRequest section")
                current = cls.HEADINGS[heading]
                if current in fields:
                    raise ValueError("duplicate AgentRequest section")
                lines = []
            elif current is None:
                if line.strip():
                    raise ValueError("text outside AgentRequest sections")
            else:
                lines.append(line)
        if current is not None:
            fields[current] = "\n".join(lines).strip()
        return cls.model_validate(fields)

    def missing_or_unclear(self) -> list[str]:
        unclear = {
            "",
            "_no response_",
            "not sure",
            "i am not sure",
            "i don't know",
            "unknown",
            "unsure",
            "tbd",
            "todo",
        }
        missing = [
            field
            for field in type(self).model_fields
            if field != "classification_choice" and getattr(self, field).strip().casefold() in unclear
        ]
        if self.classification_choice != "I know the classification" and "classification" not in missing:
            missing.append("classification")
        return sorted(missing)

    def to_spec(self) -> tuple[AgentSpec | None, list[str]]:
        """Return a review-only spec candidate and all validation issues."""
        missing = self.missing_or_unclear()
        if missing:
            return None, [f"missing or unclear: {field}" for field in missing]
        spec = AgentSpec(
            name=self.name,
            division=self.division,
            owner=self.owner,
            sponsor=self.sponsor,
            classification=self.classification,
            description=self.problem,
        )
        problems = spec.validate()
        return (None if problems else spec), problems

    def mission_brief(self) -> dict[str, str]:
        """Return untrusted draft fields, not an approved or rendered document."""
        return {
            "name": self.name,
            "division": self.division,
            "owner": self.owner,
            "sponsor": self.sponsor,
            "problem_and_people": self.problem,
            "successful_outcome": self.outcome,
            "systems": self.systems,
            "data": self.data,
            "classification": self.classification,
            "action_approvals": self.approvals,
        }


@dataclass(frozen=True)
class RequestDraft:
    request: AgentRequest | None
    missing_or_unclear: list[str]
    message: str


def parse_request(*, repo: str, requester: str, body: str, access: RequesterAccess) -> RequestDraft:
    """Accept a draft only after a trusted access lookup; never start a build.

    The caller must take repo and requester from authenticated issue metadata, not from the
    submitted body. The hosted lookup and authentication belong to I7.
    """
    if not repo.strip() or not requester.strip():
        raise ValueError("repository and authenticated requester are required")
    allowed = access.has_access(repo, requester)
    if type(allowed) is not bool:
        raise TypeError("requester access lookup must return a boolean")
    if not allowed:
        return RequestDraft(None, [], "Sorry, you need access to this repository to request an agent.")
    request = AgentRequest.from_issue_body(body)
    return RequestDraft(request, request.missing_or_unclear(), "")
