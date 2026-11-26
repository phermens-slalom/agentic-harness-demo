"""Exercise the generated repository's policy checks without cloud access."""

from agent.harness_bootstrap import main
from agent.security_harness import scan


def test_missing_required_files_fail_closed(tmp_path, capsys):
    assert main(["check", str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert "AGENTS.md" in output
    assert ".github/CODEOWNERS" in output


def test_clean_repo_passes_check(tmp_path, capsys):
    (tmp_path / "AGENTS.md").write_text("Agent guide", encoding="utf-8")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "CODEOWNERS").write_text("* @team", encoding="utf-8")
    assert main(["check", str(tmp_path)]) == 0
    assert "no findings" in capsys.readouterr().out


def test_forbidden_framework_and_global_location_are_reported(tmp_path):
    (tmp_path / "AGENTS.md").write_text("Agent guide", encoding="utf-8")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "CODEOWNERS").write_text("* @team", encoding="utf-8")
    (tmp_path / "bad.py").write_text('import langchain\nlocation = "global"\n', encoding="utf-8")
    report = scan(tmp_path)
    assert not report.ok
    assert {finding.check for finding in report.findings} == {"framework", "residency"}
    assert all(finding.path == "bad.py" for finding in report.findings)
    assert "bad.py" in report.to_markdown()
