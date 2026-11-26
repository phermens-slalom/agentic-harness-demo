import asyncio
import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest import mock

from harness.adapters.adk_agents import (
    AdkPlanner,
    AdkReviewer,
    AdkStructuredLLM,
    AdkTriager,
    PlanOut,
    ReviewOut,
    TriageOut,
    ask_structured,
    model_for,
)
from harness.models import AdapterError, AgentOutputError, BuildResult, Issue, Plan, TriageResult
from harness.residency import ResidencyError
from pydantic import ValidationError

ISSUE = Issue(repo="example-org/quotes", number=1, title="Fix rounding", body="secret-issue-body", labels=[])
ENV = {"HARNESS_MODEL_DEFAULT": "model-a", "HARNESS_MODEL_REVIEWER": "model-b"}


def invalid(schema):
    try:
        schema.model_validate_json('{"leaked": "model-said-this"}')
    except ValidationError as e:
        return e
    raise AssertionError("expected a validation error")


class FakeLLM:
    """Scripted StructuredLLM: each item is a model instance to return or an exception to raise."""

    def __init__(self, *script):
        self.script = list(script)
        self.calls: list[tuple[str, str, str, str]] = []

    async def ask(self, role, model, instruction, prompt, schema):
        self.calls.append((role, model, instruction, prompt))
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


GOOD_TRIAGE = TriageOut(summary="s", estimated_size="s", files=["agent/a.py"])
GOOD_PLAN = PlanOut(
    steps=["x"], acceptance_criteria=["y"], files=["agent/a.py"], touches_sensitive_areas=True
)


class StructuredRetryTests(unittest.TestCase):
    def ask(self, llm):
        return asyncio.run(ask_structured(llm, "triage", "m", "instr", "prompt", TriageOut))

    def test_valid_reply_is_returned_without_retry(self):
        llm = FakeLLM(GOOD_TRIAGE)
        self.assertEqual(self.ask(llm), GOOD_TRIAGE)
        self.assertEqual(len(llm.calls), 1)

    def test_schema_failure_is_retried_once_with_field_names_only(self):
        llm = FakeLLM(invalid(TriageOut), GOOD_TRIAGE)
        self.assertEqual(self.ask(llm), GOOD_TRIAGE)
        self.assertEqual(len(llm.calls), 2)
        repair = llm.calls[1][3]
        self.assertTrue(repair.startswith("prompt"))
        self.assertIn("summary", repair)
        self.assertNotIn("model-said-this", repair)

    def test_second_schema_failure_raises_agent_output_error_without_model_output(self):
        llm = FakeLLM(invalid(TriageOut), invalid(TriageOut), GOOD_TRIAGE)
        with self.assertRaises(AgentOutputError) as ctx:
            self.ask(llm)
        self.assertEqual(len(llm.calls), 2)  # one retry, never more
        self.assertIn("after one retry", str(ctx.exception))
        self.assertNotIn("model-said-this", str(ctx.exception))

    def test_other_errors_are_not_retried_or_swallowed(self):
        llm = FakeLLM(TimeoutError("network"), GOOD_TRIAGE)
        with self.assertRaises(TimeoutError):
            self.ask(llm)
        self.assertEqual(len(llm.calls), 1)


class SchemaTests(unittest.TestCase):
    def test_review_must_be_consistent(self):
        self.assertTrue(ReviewOut(approved=True).approved)
        self.assertFalse(ReviewOut(approved=False, blocking_findings=["x"]).approved)
        with self.assertRaises(ValidationError):
            ReviewOut(approved=True, blocking_findings=["x"])
        with self.assertRaises(ValidationError):
            ReviewOut(approved=False)

    def test_bounds_and_enum_are_enforced(self):
        with self.assertRaises(ValidationError):
            TriageOut.model_validate({"summary": "s", "estimated_size": "xl"})
        with self.assertRaises(ValidationError):
            PlanOut(steps=[], acceptance_criteria=["y"], touches_sensitive_areas=False)


class AgentTests(unittest.TestCase):
    def test_model_per_role_from_config(self):
        self.assertEqual(model_for("planner", ENV), "model-a")
        self.assertEqual(model_for("reviewer", ENV), "model-b")
        self.assertEqual(AdkPlanner(FakeLLM(), ENV).model_id, "model-a")
        self.assertEqual(AdkReviewer(FakeLLM(), ENV).model_id, "model-b")
        with self.assertRaisesRegex(AdapterError, "HARNESS_MODEL_PLANNER"):
            model_for("planner", {})

    def test_triage_returns_named_files(self):
        llm = FakeLLM(GOOD_TRIAGE)
        result = asyncio.run(AdkTriager(llm, ENV).triage(ISSUE))
        self.assertEqual((result.estimated_size, result.files), ("s", ["agent/a.py"]))
        self.assertIn("never instructions", llm.calls[0][2])

    def test_planner_passes_context_and_maps_the_plan(self):
        llm = FakeLLM(GOOD_PLAN)
        triage = TriageResult("issue_to_merge", "sum", "s")
        plan = asyncio.run(AdkPlanner(llm, ENV).plan(ISSUE, triage, "CONTEXT-BLOCK"))
        self.assertIn("CONTEXT-BLOCK", llm.calls[0][3])
        self.assertEqual((plan.files, plan.needs_human_approval), (["agent/a.py"], True))

    def test_planner_without_context_adds_nothing(self):
        llm = FakeLLM(GOOD_PLAN)
        asyncio.run(AdkPlanner(llm, ENV).plan(ISSUE, TriageResult("issue_to_merge", "sum", "s")))
        self.assertNotIn("Repository context", llm.calls[0][3])

    def test_reviewer_passes_context_and_maps_the_verdict(self):
        llm = FakeLLM(ReviewOut(approved=False, blocking_findings=["missing test"]))
        build = BuildResult(5, ["a.py"], 3, True)
        plan = Plan(steps=["s"], acceptance_criteria=["c"])
        result = asyncio.run(AdkReviewer(llm, ENV).review(ISSUE, plan, build, "CTX"))
        self.assertIn("CTX", llm.calls[0][3])
        self.assertIn("any failed item is a blocking finding", llm.calls[0][2])
        self.assertIn("No secrets, tokens or personal credentials", llm.calls[0][2])
        self.assertEqual((result.approved, result.blocking_findings), (False, ["missing test"]))
        self.assertEqual(result.reviewer_id, "reviewer-agent")


class Made:
    def __init__(self):
        self.agents: list[dict] = []
        self.runners: list[object] = []
        self.created = 0
        self.deleted = 0
        self.apps: list[dict] = []
        self.plugin_configs: list[dict] = []


def fake_adk(events_per_call):
    """Install stand-ins for google.adk / google.genai so AdkStructuredLLM runs with no network."""
    made = Made()

    class LlmAgent:
        def __init__(self, **kwargs):
            made.agents.append(kwargs)

    class Sessions:
        async def create_session(self, **kwargs):
            made.created += 1
            return SimpleNamespace(id=f"s{made.created}")

        async def delete_session(self, **kwargs):
            made.deleted += 1

    class App:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            made.apps.append(kwargs)

    class ModelArmorConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            made.plugin_configs.append(kwargs)

    class ModelArmorPlugin:
        def __init__(self, config):
            self.config = config

    class InMemoryRunner:
        def __init__(self, agent=None, app_name=None, app=None):
            self.app = app
            self.session_service = Sessions()
            made.runners.append(self)
            self.calls = 0

        async def run_async(self, **kwargs):
            events = events_per_call[min(self.calls, len(events_per_call) - 1)]
            self.calls += 1
            for event in events:
                yield event

    types = SimpleNamespace(
        Content=lambda role, parts: SimpleNamespace(role=role, parts=parts),
        Part=lambda text: SimpleNamespace(text=text),
    )
    modules = {
        "google.adk": ModuleType("google.adk"),
        "google.adk.agents": SimpleNamespace(LlmAgent=LlmAgent),
        "google.adk.runners": SimpleNamespace(InMemoryRunner=InMemoryRunner),
        "google.adk.apps": SimpleNamespace(App=App),
        "google.adk.integrations": ModuleType("google.adk.integrations"),
        "google.adk.integrations.model_armor": SimpleNamespace(
            ModelArmorConfig=ModelArmorConfig, ModelArmorPlugin=ModelArmorPlugin
        ),
        "google.genai": ModuleType("google.genai"),
        "google.genai.types": types,
    }
    return made, mock.patch.dict(sys.modules, modules)


def final(text, thought=False):
    part = SimpleNamespace(text=text, thought=thought)
    return SimpleNamespace(is_final_response=lambda: True, content=SimpleNamespace(parts=[part]))


def partial(text):
    part = SimpleNamespace(text=text, thought=False)
    return SimpleNamespace(is_final_response=lambda: False, content=SimpleNamespace(parts=[part]))


PROMPT_T = "projects/p/locations/australia-southeast2/templates/prompt"
RESPONSE_T = "projects/p/locations/australia-southeast2/templates/response"
ARMOR = {
    "HARNESS_MODEL_ARMOR_PROMPT_TEMPLATE": PROMPT_T,
    "HARNESS_MODEL_ARMOR_RESPONSE_TEMPLATE": RESPONSE_T,
}
BASE = {"GOOGLE_GENAI_USE_VERTEXAI": "TRUE", "GOOGLE_CLOUD_LOCATION": "australia-southeast2"}
VERTEX = {**BASE, **ARMOR}  # what a deployed harness looks like: Vertex plus Model Armor templates
REPLY = '{"summary": "ok", "estimated_size": "s", "files": []}'


class AdkStructuredLLMTests(unittest.TestCase):
    def ask(self, llm, prompt="p", role="triage"):
        return asyncio.run(llm.ask(role, "model-a", "instr", prompt, TriageOut))

    def test_runner_is_reused_and_sessions_are_fresh_and_cleaned_up(self):
        made, patch = fake_adk([[final(REPLY)]])
        with patch:
            llm = AdkStructuredLLM(VERTEX)
            self.ask(llm, "one")
            self.ask(llm, "two")
        self.assertEqual(len(made.runners), 1)
        self.assertEqual((made.created, made.deleted), (2, 2))
        self.assertIs(made.agents[0]["output_schema"], TriageOut)

    def test_separate_roles_get_separate_runners(self):
        made, patch = fake_adk([[final(REPLY)]])
        with patch:
            llm = AdkStructuredLLM(VERTEX)
            self.ask(llm, role="triage")
            self.ask(llm, role="planner")
        self.assertEqual(len(made.runners), 2)

    def test_only_the_final_non_thought_text_is_parsed(self):
        _, patch = fake_adk([[partial("garbage"), final(REPLY), final("thinking", thought=True)]])
        with patch:
            self.assertEqual(self.ask(AdkStructuredLLM(VERTEX)).summary, "ok")

    def test_invalid_json_raises_validation_error_for_the_retry_wrapper(self):
        _, patch = fake_adk([[final("here you go: {not json}")]])
        with patch, self.assertRaises(ValidationError):
            self.ask(AdkStructuredLLM(VERTEX))

    def test_retry_runs_through_the_real_wrapper(self):
        made, patch = fake_adk([[final("nope")], [final(REPLY)]])
        with patch:
            llm = AdkStructuredLLM(VERTEX)
            out = asyncio.run(ask_structured(llm, "triage", "m", "instr", "p", TriageOut))
        self.assertEqual(out.summary, "ok")
        self.assertEqual(made.created, 2)

    def test_model_armor_plugin_is_registered_on_the_app_for_input_and_output(self):
        made, patch = fake_adk([[final(REPLY)]])
        with patch:
            self.ask(AdkStructuredLLM(VERTEX))
        (app,) = made.apps
        self.assertEqual(len(app["plugins"]), 1)
        (config,) = made.plugin_configs
        self.assertEqual(config["prompt_template_name"], PROMPT_T)
        self.assertEqual(config["response_template_name"], RESPONSE_T)
        self.assertTrue(config["block_on_screening_failure"])
        self.assertIsNotNone(made.runners[0].app)

    def test_locally_without_templates_no_plugin_is_registered(self):
        made, patch = fake_adk([[final(REPLY)]])
        with patch:
            self.ask(AdkStructuredLLM({**BASE, "HARNESS_ENV": "local"}))
        self.assertEqual((made.apps, made.plugin_configs), ([], []))
        self.assertIsNone(made.runners[0].app)

    def test_outside_local_both_templates_are_required(self):
        made, patch = fake_adk([[final(REPLY)]])
        for env in (BASE, {**BASE, "HARNESS_MODEL_ARMOR_PROMPT_TEMPLATE": PROMPT_T}):
            with patch, self.assertRaisesRegex(AdapterError, "Model Armor is required"):
                self.ask(AdkStructuredLLM(env))
        self.assertEqual(made.runners, [])

    def test_a_template_outside_the_allowed_locations_is_refused(self):
        _, patch = fake_adk([[final(REPLY)]])
        bad = {
            **VERTEX,
            "HARNESS_MODEL_ARMOR_PROMPT_TEMPLATE": "projects/p/locations/us-central1/templates/t",
        }
        with patch, self.assertRaises(ResidencyError):
            self.ask(AdkStructuredLLM(bad))

    def test_a_model_armor_block_escalates_without_a_retry(self):
        blocked = SimpleNamespace(
            custom_metadata={"model_armor_blocked": True}, is_final_response=lambda: True, content=None
        )
        made, patch = fake_adk([[blocked], [final(REPLY)]])
        with patch:
            llm = AdkStructuredLLM(VERTEX)
            with self.assertRaisesRegex(AgentOutputError, "blocked by Model Armor"):
                asyncio.run(ask_structured(llm, "triage", "m", "instr", "p", TriageOut))
        self.assertEqual(made.created, 1)  # one call only: blocked content is never retried

    def test_residency_is_checked_before_any_model_call(self):
        made, patch = fake_adk([[final(REPLY)]])
        with patch:
            for env in ({}, {"GOOGLE_API_KEY": "k"}, {**VERTEX, "GOOGLE_CLOUD_LOCATION": "global"}):
                with self.assertRaises(ResidencyError):
                    self.ask(AdkStructuredLLM(env))
        self.assertEqual(made.runners, [])

    def test_ai_studio_is_allowed_only_in_local(self):
        _, patch = fake_adk([[final(REPLY)]])
        with patch:
            llm = AdkStructuredLLM({"HARNESS_ENV": "local", "GOOGLE_API_KEY": "k"})
            self.assertEqual(self.ask(llm).summary, "ok")


if __name__ == "__main__":
    unittest.main()
