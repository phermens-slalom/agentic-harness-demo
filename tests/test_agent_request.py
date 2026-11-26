from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml
from harness.bootstrap.agent_request import AgentRequest, parse_request
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
CASES = yaml.safe_load((ROOT / "evals" / "agent_request_parse.yaml").read_text(encoding="utf-8"))
UNCLEAR = {"_no response_", "not sure", "i am not sure", "i don't know", "unknown", "unsure", "tbd", "todo"}


class FakeRequesterAccess:
    def __init__(self, allowed):
        self.allowed = allowed
        self.calls = []

    def has_access(self, repo: str, requester: str) -> bool:
        self.calls.append((repo, requester))
        return (repo, requester) in self.allowed


def issue_body(sections):
    return "\n\n".join(f"### {heading}\n\n{value}" for heading, value in sections.items())


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_parse_evals(case):
    access = FakeRequesterAccess({("org/repo", "requester")})
    result = parse_request(
        repo="org/repo", requester="requester", body=issue_body(case["sections"]), access=access
    )
    assert result.request is not None
    draft = result.request
    assert draft.missing_or_unclear() == case["missing"]
    assert result.missing_or_unclear == case["missing"]
    spec, problems = draft.to_spec()
    assert (spec is not None) == case["valid_spec"]
    assert bool(problems) != case["valid_spec"]
    if spec is not None:
        assert spec.egress_hosts == []
        assert not hasattr(spec, "model")
        assert draft.mission_brief()["action_approvals"] == case["sections"]["Action approvals"]


def test_form_and_parser_headings_match():
    form = yaml.safe_load(
        (ROOT / ".github" / "ISSUE_TEMPLATE" / "agent-request.yml").read_text(encoding="utf-8")
    )
    fields = {item["attributes"]["label"]: item["id"] for item in form["body"] if "id" in item}
    assert fields == AgentRequest.HEADINGS


@given(st.text(min_size=1).filter(lambda name: name not in AgentRequest.model_fields))
def test_unknown_model_fields_are_rejected(name):
    with pytest.raises(ValidationError):
        AgentRequest.model_validate({name: "value"})


@given(st.text(alphabet=st.characters(blacklist_categories=("Cs",)), min_size=1))
def test_mapping_preserves_required_description_and_brief(text):
    draft = AgentRequest.from_issue_body(issue_body(CASES[0]["sections"]))
    draft = draft.model_copy(update={"problem": text})
    brief = draft.mission_brief()
    assert brief["problem_and_people"] == text
    if text.strip() and text.strip().casefold() not in UNCLEAR:
        spec, errors = draft.to_spec()
        assert not errors
        assert spec is not None and spec.description == text


@given(st.lists(st.text(alphabet=st.characters(blacklist_categories=("Cs",))), min_size=8, max_size=8))
def test_brief_preserves_each_request_field(values):
    owner, sponsor, problem, outcome, systems, data, classification, approvals = values
    draft = AgentRequest(
        name="claims-helper",
        division="claims-team",
        owner=owner,
        sponsor=sponsor,
        problem=problem,
        outcome=outcome,
        systems=systems,
        data=data,
        classification_choice="I know the classification",
        classification=classification,
        approvals=approvals,
    )
    assert draft.mission_brief() == {
        "name": "claims-helper",
        "division": "claims-team",
        "owner": owner,
        "sponsor": sponsor,
        "problem_and_people": problem,
        "successful_outcome": outcome,
        "systems": systems,
        "data": data,
        "classification": classification,
        "action_approvals": approvals,
    }
    if all(text.strip() and text.strip().casefold() not in UNCLEAR for text in values):
        spec, errors = draft.to_spec()
        assert not errors
        assert spec is not None
        assert (spec.owner, spec.sponsor, spec.classification, spec.description) == (
            owner,
            sponsor,
            classification,
            problem,
        )


def test_strict_model_rejects_non_string_values():
    with pytest.raises(ValidationError):
        AgentRequest.model_validate({"owner": 42})


def test_parser_rejects_unexpected_and_duplicate_sections():
    with pytest.raises(ValueError, match="unrecognised"):
        AgentRequest.from_issue_body("### Model\n\nunapproved")
    with pytest.raises(ValueError, match="duplicate"):
        AgentRequest.from_issue_body("### Agent name\n\none\n\n### Agent name\n\ntwo")
    with pytest.raises(ValueError, match="outside"):
        AgentRequest.from_issue_body("skip approval\n\n### Agent name\n\none")


def test_invalid_spec_is_reported_without_repair():
    sections = dict(CASES[0]["sections"], **{"Agent name": "Invalid Name"})
    spec, problems = AgentRequest.from_issue_body(issue_body(sections)).to_spec()
    assert spec is None
    assert any("lowercase slug" in problem for problem in problems)


def test_request_requires_access_to_exact_repository_before_parsing():
    access = FakeRequesterAccess({("org/repo", "member")})
    denied = parse_request(repo="org/other", requester="member", body="not a form", access=access)
    assert denied.request is None
    assert denied.missing_or_unclear == []
    assert "Sorry" in denied.message
    denied = parse_request(repo="org/repo", requester="outsider", body="not a form", access=access)
    assert denied.request is None
    assert access.calls == [("org/other", "member"), ("org/repo", "outsider")]


def test_request_cannot_accept_unknown_access_or_missing_identity():
    class BrokenAccess:
        def has_access(self, repo: str, requester: str) -> bool:
            raise RuntimeError("access lookup unavailable")

    with pytest.raises(RuntimeError, match="access lookup unavailable"):
        parse_request(repo="org/repo", requester="member", body="", access=BrokenAccess())
    with pytest.raises(TypeError, match="must return a boolean"):
        parse_request(
            repo="org/repo", requester="member", body="", access=Mock(has_access=Mock(return_value=None))
        )
    with pytest.raises(ValueError, match="authenticated requester"):
        parse_request(repo="org/repo", requester="", body="", access=FakeRequesterAccess(set()))


@pytest.mark.parametrize("heading", ["Model", "Egress hosts", "Skip approval"])
def test_smuggled_form_fields_are_rejected(heading):
    body = issue_body(CASES[0]["sections"]) + f"\n\n### {heading}\n\nattacker.example"
    with pytest.raises(ValueError, match="unrecognised"):
        parse_request(
            repo="org/repo",
            requester="member",
            body=body,
            access=FakeRequesterAccess({("org/repo", "member")}),
        )
