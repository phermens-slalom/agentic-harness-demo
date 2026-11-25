from pathlib import Path

import pytest
from google.adk.tools import FunctionTool


def test_root_agent_wired():
    from agent.agent import root_agent
    from agent.prompts import load_garage_skill

    assert root_agent.name.isidentifier()
    assert isinstance(root_agent.instruction, str)
    assert load_garage_skill() in root_agent.instruction
    assert all(isinstance(tool, FunctionTool) for tool in root_agent.tools)
    assert [tool.name for tool in root_agent.tools if isinstance(tool, FunctionTool)] == [
        "get_service_history",
        "estimate_repair",
    ]


def test_runtime_skill_rejects_an_unpinned_edit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from agent import prompts

    folder = tmp_path / "skills" / "garage-summary"
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text("---\nname: garage-summary\n---\nChanged\n", encoding="utf-8")
    monkeypatch.setattr(prompts, "files", lambda _package: tmp_path)

    with pytest.raises(ValueError, match="approved SHA-256"):
        prompts.load_garage_skill()
