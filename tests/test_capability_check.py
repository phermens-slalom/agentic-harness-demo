import unittest

from harness.models import BuildResult, Decision, ReviewResult
from harness.nodes.capability_check import (
    approvers_from,
    detect_data_stores,
    detect_hosts,
    detect_models,
    detect_new_dependencies,
    detect_new_tool_functions,
    detect_protocols,
    detect_regions,
    find_new_capabilities,
)
from harness.nodes.diff_parse import FileDiff, parse_diff
from harness.nodes.merge_gate import decide
from harness.policy import CapabilityPolicy, RiskPolicy

POLICY = CapabilityPolicy.load()
CHECKS = {"lint": True, "tests": True, "evals_no_regression": True, "secret_scan": True}


def added(path: str, *lines: str) -> str:
    body = "".join(f"+{line}\n" for line in lines)
    return f"--- a/{path}\n+++ b/{path}\n@@ -0,0 +1,{len(lines)} @@\n{body}"


def kinds(diff: str, egress=()):
    return sorted((f.kind, f.detail) for f in find_new_capabilities(diff, POLICY, egress))


class DiffParseTests(unittest.TestCase):
    def test_collects_added_and_removed_lines_per_file(self):
        diff = "--- a/a.py\n+++ b/a.py\n@@ -1,2 +1,2 @@\n keep\n-old\n+new\n"
        (f,) = parse_diff(diff)
        self.assertEqual((f.path, f.added, f.removed), ("a.py", ["new"], ["old"]))

    def test_added_line_that_looks_like_a_header_does_not_switch_files(self):
        diff = added("a.py", "x = 1", "++ b/docs/x.md", "y = 2")
        (f,) = parse_diff(diff)
        self.assertEqual(f.path, "a.py")
        self.assertEqual(f.added, ["x = 1", "++ b/docs/x.md", "y = 2"])

    def test_deleted_file_has_no_added_lines(self):
        self.assertEqual(parse_diff("--- a/x.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-gone\n"), [])


class ModelTests(unittest.TestCase):
    def test_new_model_ids_are_detected(self):
        self.assertEqual(detect_models('MODEL = "gemini-2.5-flash"'), ["gemini-2.5-flash"])
        self.assertEqual(detect_models("model: Claude-Opus-5"), ["claude-opus-5"])
        self.assertEqual(detect_models('"text-embedding-005"'), ["text-embedding-005"])

    def test_benign_look_alikes(self):
        self.assertEqual(detect_models("gemini = load()"), [])
        self.assertEqual(detect_models("the gemini team"), [])
        self.assertEqual(kinds(added("docs/models.md", "Use gemini-2.5-flash")), [])
        self.assertEqual(kinds(added("agent/a.py", "# was gemini-2.5-flash")), [])

    def test_allowlisted_model_is_quiet(self):
        policy = CapabilityPolicy.load()
        object.__setattr__(policy, "allowed_models", frozenset({"gemini-2.5-flash"}))
        self.assertEqual(find_new_capabilities(added("a.py", 'M = "gemini-2.5-flash"'), policy), [])


class HostTests(unittest.TestCase):
    def test_new_hosts_are_detected(self):
        self.assertEqual(
            detect_hosts('requests.get("https://API.Example.com.au/v1")'), ["api.example.com.au"]
        )
        self.assertEqual(
            detect_hosts("endpoint = 'aiplatform.googleapis.com'"), ["aiplatform.googleapis.com"]
        )
        self.assertEqual(detect_hosts("wss://u:p@stream.vendor.io:8443/x"), ["stream.vendor.io"])

    def test_benign_look_alikes(self):
        self.assertEqual(detect_hosts("see section 3.2 and v1.2.3"), [])
        self.assertEqual(detect_hosts("https://${HOST}/path"), [])
        self.assertEqual(kinds(added("a.py", 'U = "http://localhost:8080"')), [])
        self.assertEqual(kinds(added("a.py", 'U = "https://example.com/docs"')), [])
        self.assertEqual(kinds(added("a.py", "# https://evil.example.net/x")), [])
        self.assertEqual(kinds(added("docs/runbook.md", "Call https://api.vendor.io")), [])
        self.assertEqual(kinds(added("tests/test_x.py", 'URL = "https://api.vendor.io"')), [])

    def test_undeclared_host_adds_ai_governance_and_declared_host_only_security(self):
        diff = added("agent/a.py", 'URL = "https://api.vendor.io/x"')
        (undeclared,) = find_new_capabilities(diff, POLICY)
        self.assertEqual(undeclared.approvers, ("security", "ai_governance"))
        (declared,) = find_new_capabilities(diff, POLICY, ["api.vendor.io"])
        self.assertEqual(declared.approvers, ("security",))


class RegionTests(unittest.TestCase):
    def test_non_allowed_regions_and_global_are_detected(self):
        self.assertEqual(detect_regions('LOCATION = "us-central1"'), ["us-central1"])
        self.assertEqual(detect_regions('location="global"'), ["global"])
        self.assertEqual(detect_regions("projects/p/locations/global/x"), ["global"])

    def test_benign_look_alikes(self):
        self.assertEqual(kinds(added("a.py", 'LOCATION = "australia-southeast2"')), [])
        self.assertEqual(detect_regions("the global average"), [])
        self.assertEqual(detect_regions("us-central"), [])
        self.assertEqual(kinds(added("docs/x.md", "us-central1")), [])
        self.assertEqual(kinds(added("a.py", "# us-central1 is not allowed")), [])


class DataStoreTests(unittest.TestCase):
    def test_new_stores_are_detected(self):
        cases = {
            "bigquery": "client = bigquery.Client()",
            "firestore": "from google.cloud import firestore",
            "spanner": "db = spanner.Client()",
            "gcs": 'path = "gs://bucket/obj"',
            "memory_bank": "svc = VertexAiMemoryBankService()",
        }
        for name, line in cases.items():
            self.assertEqual(detect_data_stores(line), [name], line)

    def test_benign_look_alikes(self):
        self.assertEqual(detect_data_stores("storage_class = 'standard'"), [])
        self.assertEqual(detect_data_stores("bigquery_note = 1"), [])
        self.assertEqual(kinds(added("agent/a.py", "# client = bigquery.Client()")), [])
        self.assertEqual(kinds(added("docs/x.md", "from google.cloud import spanner")), [])
        self.assertEqual(kinds(added("tests/test_a.py", "client = firestore.Client()")), [])


class DependencyTests(unittest.TestCase):
    def deps(self, path, added_lines, removed_lines=()):
        return detect_new_dependencies(FileDiff(path, list(added_lines), list(removed_lines)))

    def test_new_dependencies_per_manifest(self):
        self.assertEqual(
            self.deps("requirements.txt", ["Requests_Lib==2.0", "-r other.txt"]), ["requests-lib"]
        )
        self.assertEqual(self.deps("pyproject.toml", ['    "httpx[http2]>=0.27",']), ["httpx"])
        self.assertEqual(self.deps("web/package.json", ['    "left-pad": "^1.3.0",']), ["left-pad"])
        self.assertEqual(self.deps("go.mod", ["\tgithub.com/acme/lib v1.2.3"]), ["github.com/acme/lib"])

    def test_version_bump_is_not_a_new_dependency(self):
        self.assertEqual(self.deps("requirements.txt", ["requests==2.32"], ["requests==2.31"]), [])
        self.assertEqual(self.deps("pyproject.toml", ['"httpx>=0.28",'], ['"httpx>=0.27",']), [])
        self.assertEqual(self.deps("package.json", ['"version": "1.0.1",']), [])

    def test_benign_look_alikes(self):
        self.assertEqual(self.deps("requirements.txt", ["# requests", ""]), [])
        self.assertEqual(self.deps("pyproject.toml", ['name = "agent"', 'requires-python = ">=3.11"']), [])
        self.assertEqual(self.deps("agent/config.py", ['"requests",']), [])
        self.assertEqual(kinds(added("docs/x.md", '"requests",')), [])

    def test_allowlisted_dependency_is_quiet(self):
        policy = CapabilityPolicy.load()
        object.__setattr__(policy, "allowed_dependencies", frozenset({"httpx"}))
        self.assertEqual(find_new_capabilities(added("pyproject.toml", '"httpx>=0.27",'), policy), [])


class ToolAndProtocolTests(unittest.TestCase):
    def test_protocol_and_delegation_hits(self):
        self.assertEqual(detect_protocols("toolset = McpToolset(connection_params=p)"), ["mcp"])
        self.assertEqual(detect_protocols('{"mcpServers": {}}'), ["mcp"])
        self.assertEqual(detect_protocols("peer = RemoteA2aAgent(name='x')"), ["a2a"])
        self.assertEqual(detect_protocols("sub_agents=[other]"), ["delegation"])
        self.assertEqual(detect_protocols("t = AgentTool(agent=other)"), ["delegation"])
        self.assertEqual(detect_protocols("t = FunctionTool(fn)"), ["toolset"])

    def test_new_public_tool_function_in_tools_module(self):
        self.assertEqual(
            detect_new_tool_functions("agent/tools.py", "def book_visit(x: str) -> str:"), ["book_visit"]
        )
        self.assertEqual(detect_new_tool_functions("agent/tools.py", "async def refund(x):"), ["refund"])
        self.assertEqual(detect_new_tool_functions("agent/tools/refunds.py", "def refund(x):"), ["refund"])

    def test_benign_look_alikes(self):
        self.assertEqual(detect_new_tool_functions("agent/tools.py", "def _helper(x):"), [])
        self.assertEqual(detect_new_tool_functions("agent/tools.py", "    def nested(x):"), [])
        self.assertEqual(detect_new_tool_functions("agent/util.py", "def refund(x):"), [])
        self.assertEqual(detect_protocols("the mcp of the matter"), [])
        self.assertEqual(kinds(added("agent/a.py", "# peer = RemoteA2aAgent()")), [])
        self.assertEqual(kinds(added("tests/test_a.py", "t = McpToolset()")), [])

    def test_tool_and_protocol_hits_route_to_security_and_ai_governance(self):
        found = find_new_capabilities(added("agent/tools.py", "def refund(x):"), POLICY)
        self.assertEqual(approvers_from(found), ["security", "ai_governance"])


class GateIntegrationTests(unittest.TestCase):
    def build(self, files, diff, lines=5):
        return BuildResult(1, files, lines, True, checks=dict(CHECKS), diff=diff)

    def test_capability_adds_approvers_and_reason_and_blocks_auto_merge(self):
        policy = RiskPolicy.load(phase=3)
        clean = self.build(["agent/a.py"], added("agent/a.py", "x = 1"))
        # tier 2 by default, so use a tier-1 file to prove auto-merge is withdrawn
        tier1_clean = self.build(["tests/test_a.py"], added("tests/test_a.py", "assert True"))
        self.assertEqual(decide(policy, tier1_clean, ReviewResult(True)).decision, Decision.AUTO_MERGE)
        dep = self.build(["requirements.txt", "tests/test_a.py"], added("requirements.txt", "evilpkg==1.0"))
        result = decide(policy, dep, ReviewResult(True))
        self.assertEqual(result.decision, Decision.HUMAN_APPROVAL)
        self.assertIn("security", result.required_approvers)
        self.assertIn("new capabilities: dependency evilpkg (requirements.txt)", result.reason)
        self.assertEqual(result.new_capabilities, ["dependency evilpkg (requirements.txt)"])
        self.assertEqual(decide(policy, clean, ReviewResult(True)).new_capabilities, [])

    def test_capability_alone_never_escalates_or_rejects(self):
        policy = RiskPolicy.load(phase=1)
        build = self.build(["agent/a.py"], added("agent/a.py", 'U = "https://api.vendor.io"'))
        result = decide(policy, build, ReviewResult(True))
        self.assertEqual(result.decision, Decision.HUMAN_APPROVAL)
        self.assertEqual(result.required_approvers[:2], ["app_team", "ai_governance"])
        self.assertIn("security", result.required_approvers)

    def test_capability_never_overrides_a_stronger_decision(self):
        policy = RiskPolicy.load(phase=3)
        diff = added("agent/a.py", 'U = "https://api.vendor.io"')
        failing = BuildResult(1, ["agent/a.py"], 5, True, checks={**CHECKS, "tests": False}, diff=diff)
        result = decide(policy, failing, ReviewResult(True))
        self.assertEqual(result.decision, Decision.ESCALATED)
        self.assertIn("security", result.required_approvers)

    def test_declared_egress_host_needs_security_but_not_extra_ai_governance(self):
        policy = RiskPolicy.load(phase=1)
        build = self.build(["agent/a.py"], added("agent/a.py", 'U = "https://api.vendor.io"'))
        declared = decide(policy, build, ReviewResult(True), egress_hosts=["api.vendor.io"])
        self.assertEqual(declared.required_approvers, ["app_team", "ai_governance", "security"])

    def test_reason_is_capped_and_contains_names_not_source_lines(self):
        lines = [f'U{i} = "https://h{i}.vendor.io/secret-token-{i}"' for i in range(8)]
        build = self.build(["agent/a.py"], added("agent/a.py", *lines))
        result = decide(RiskPolicy.load(phase=1), build, ReviewResult(True))
        self.assertIn("+3 more", result.reason)
        self.assertNotIn("secret-token", result.reason)


class CapabilityPolicyTests(unittest.TestCase):
    def test_repository_policy_loads_with_residency_regions(self):
        self.assertEqual(POLICY.allowed_regions, {"australia-southeast1", "australia-southeast2"})
        self.assertTrue(POLICY.ignores("docs/a.md") and POLICY.ignores("pkg/test_x.py"))
        self.assertFalse(POLICY.ignores("tests/conftest.py"))


if __name__ == "__main__":
    unittest.main()
