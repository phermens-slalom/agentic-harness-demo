import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import yaml
from harness.bootstrap import security_harness, template, terraform_plan
from harness.bootstrap.spec import AgentSpec

SPEC = AgentSpec(
    name="claims-triage",
    division="example-division",
    owner="a.owner",
    sponsor="s.sponsor",
    classification="internal",
    description="Triage claims",
    egress_hosts=["api.example.com.au"],
)


class BootstrapTests(unittest.TestCase):
    def test_spec_validation(self):
        self.assertEqual(SPEC.validate(), [])
        bad = replace(SPEC, location="global", egress_hosts=["*.example.com"], name="Bad Name")
        self.assertEqual(len(bad.validate()), 3)

    def test_render_then_scan_clean(self):
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "repo"
            template.render(SPEC, dest)
            instructions = (dest / "AGENTS.md").read_text()
            self.assertIn("claims-triage", instructions)
            self.assertIn("AI governance team and Security approval", instructions)
            self.assertIn("Use only policy-approved regions", instructions)
            agent_py = (dest / "agent/agent.py").read_text()
            self.assertIn('name="claims_triage"', agent_py)  # ADK needs an identifier
            for f in dest.rglob("*"):
                if f.is_file():
                    self.assertNotRegex(f.read_text(), r"__[A-Z_]+__", f.name)
            self.assertTrue(security_harness.scan(dest).ok)
            check = subprocess.run(
                [sys.executable, "-m", "agent.harness_bootstrap", "check", "."],
                cwd=dest,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            with self.assertRaises(FileExistsError):
                template.render(SPEC, dest)

    def test_render_ships_copilot_environment_with_rendered_allowlist(self):
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "repo"
            template.render(SPEC, dest)
            setup = yaml.safe_load((dest / ".github/workflows/copilot-setup-steps.yml").read_text())
            self.assertEqual(list(setup["jobs"]), ["copilot-setup-steps"])
            job = setup["jobs"]["copilot-setup-steps"]
            self.assertEqual(setup["permissions"], {})
            self.assertEqual(job["permissions"], {"contents": "read"})
            self.assertNotIn("id-token", job["permissions"])
            for step in job["steps"]:
                if "uses" in step:
                    self.assertRegex(step["uses"], r"@[0-9a-f]{40}$")
            self.assertTrue(any("agents-cli install" in s.get("run", "") for s in job["steps"]))
            agent = (dest / ".github/agents/agent-builder.agent.md").read_text()
            self.assertIn("name: agent-builder", agent)
            self.assertIn("target: github-copilot", agent)
            self.assertIn('tools: ["read", "edit", "search", "execute"]', agent)
            self.assertIn("AGENTS.md", agent)
            self.assertIn("not authorisation", agent)
            doc = (dest / "docs/copilot-agent-environment.md").read_text()
            self.assertIn("`https://api.example.com.au/`", doc)  # URL form: exact host only
            self.assertNotIn("`api.example.com.au`", doc)  # a bare domain would allow subdomains
            self.assertIn("`https://pypi.org/`", doc)
            self.assertIn("does **not** cover", doc)  # setup steps are outside the firewall

    def test_allowlist_lists_only_declared_egress_hosts(self):
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "repo"
            template.render(replace(SPEC, egress_hosts=["b.example.com.au", "a.example.com.au"]), dest)
            doc = (dest / "docs/copilot-agent-environment.md").read_text()
            self.assertLess(doc.index("a.example.com.au"), doc.index("b.example.com.au"))
            self.assertNotIn("api.example.com.au", doc)
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "repo"
            template.render(replace(SPEC, egress_hosts=[]), dest)
            doc = (dest / "docs/copilot-agent-environment.md").read_text()
            self.assertIn("declares no egress hosts", doc)

    def test_new_ships_a_consistent_eval_dataset_and_config(self):
        project = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "generated"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "harness.bootstrap.cli",
                    "new",
                    str(project / "spec.yaml.example"),
                    str(dest),
                ],
                cwd=project,
                check=True,
                capture_output=True,
                text=True,
            )
            eval_dir = dest / "tests" / "eval"
            config = yaml.safe_load((eval_dir / "eval_config.yaml").read_text(encoding="utf-8"))
            group = config["custom_metrics"][0]["metric_spec_parameters"]["rubric_group_key"]
            dataset = json.loads((eval_dir / "datasets" / "basic-dataset.json").read_text(encoding="utf-8"))
            cases = {case["eval_case_id"]: case for case in dataset["eval_cases"]}
            self.assertEqual(len(cases), len(dataset["eval_cases"]))
            for case_id in ("history-before-advice", "booking-unavailable"):
                case = cases[case_id]
                self.assertEqual(case["prompt"]["role"], "user")
                self.assertTrue(case["prompt"]["parts"][0]["text"].strip())
                self.assertTrue(case["rubric_groups"][group]["rubrics"])

    def test_scan_flags_problems(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            (r / "AGENTS.md").write_text("x")
            (r / "a.py").write_text("import langchain\nlocation = 'global'\n")
            checks = {f.check for f in security_harness.scan(r).findings}
            self.assertEqual(checks, {"required file", "framework", "residency"})

    def test_terraform_plan_order_and_approvers(self):
        prs = terraform_plan.plan_prs(SPEC)
        self.assertEqual([p.order for p in prs], [1, 2, 3])
        self.assertEqual(prs[0].approvers, ["ai_governance", "platform_team"])
        self.assertTrue(any(f.endswith("egress.tfvars") for f in prs[2].files))


if __name__ == "__main__":
    unittest.main()
