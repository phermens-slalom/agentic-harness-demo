"""Run real ADK tool wrappers without a model or cloud credentials."""

import asyncio
import json
import logging

import pytest
from google.adk.agents.invocation_context import InvocationContext
from google.adk.sessions import InMemorySessionService, Session
from google.adk.tools import ToolContext
from google.genai.types import Content, Part


def _context() -> ToolContext:
    from agent.agent import root_agent

    return ToolContext(
        InvocationContext(
            invocation_id="private-invocation-id",
            agent=root_agent,
            session_service=InMemorySessionService(),
            session=Session(id="private-session", app_name="agent", user_id="private-user"),
            user_content=Content(role="user", parts=[Part(text="private-user-prompt")]),
        )
    )


def test_tool_diagnostics_are_redacted(caplog: pytest.LogCaptureFixture):
    from agent.agent import root_agent
    from agent.telemetry import ObservedTool

    tool = next(
        tool
        for tool in root_agent.tools
        if isinstance(tool, ObservedTool) and tool.name == "get_service_history"
    )
    context = _context()
    with caplog.at_level(logging.INFO, logger="agent.telemetry"):
        allowed = asyncio.run(tool.run_async(args={"vin": "1HGCM82633A004352"}, tool_context=context))
        denied = asyncio.run(tool.run_async(args={"vin": "private-unknown-vin"}, tool_context=context))

    assert allowed["status"] == "ok"
    assert denied["status"] == "error"
    records = [
        json.loads(record.getMessage()) for record in caplog.records if record.name == "agent.telemetry"
    ]
    allowed_log, denied_log = records
    assert [row["outcome"] for row in records] == ["ok", "rejected"]
    assert allowed_log["request_id"] == denied_log["request_id"]
    for row in records:
        assert set(row) == {"event", "request_id", "tool", "outcome", "duration_ms", "instruction_sha256"}
        assert row["event"] == "tool.completed"
        assert row["tool"] == "get_service_history"
        assert row["duration_ms"] >= 0
        assert len(row["instruction_sha256"]) == 64
    for private_value in (
        "1HGCM82633A004352",
        "private-unknown-vin",
        "private-invocation-id",
        "private-user-prompt",
        "private-session",
        "private-user",
        "front brake pad",
    ):
        assert private_value.lower() not in caplog.text.lower()


def test_tool_failure_diagnostic_omits_exception_text(caplog: pytest.LogCaptureFixture):
    from agent.telemetry import ObservedTool

    def broken_tool() -> dict:
        raise RuntimeError("private-exception-detail")

    tool = ObservedTool(broken_tool, instruction="private-instruction")
    with (
        caplog.at_level(logging.INFO, logger="agent.telemetry"),
        pytest.raises(RuntimeError, match="private-exception-detail"),
    ):
        asyncio.run(tool.run_async(args={}, tool_context=_context()))
    (record,) = caplog.records
    assert record.exc_info is None
    assert json.loads(record.getMessage())["outcome"] == "failed"
    assert "private-exception-detail" not in record.getMessage()
    assert "private-instruction" not in record.getMessage()
