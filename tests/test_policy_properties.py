from harness.models import BuildResult, Decision, ReviewResult
from harness.nodes.merge_gate import decide
from harness.policy import RiskPolicy
from hypothesis import given
from hypothesis import strategies as st


@given(st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=10), st.text(min_size=1, max_size=30))
def test_adding_a_file_never_lowers_tier(paths: list[str], extra: str) -> None:
    policy = RiskPolicy.load(phase=3)
    original = policy.tier_for_change(paths, 20)
    extended = policy.tier_for_change([*paths, extra], 20)
    assert extended >= original


@given(st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=10))
def test_case_and_separator_changes_do_not_change_tier(paths: list[str]) -> None:
    policy = RiskPolicy.load(phase=3)
    normalised = [path.replace("/", "\\") for path in paths]
    changed_case = [path.swapcase() for path in paths]
    assert policy.tier_for_change(paths, 20) == policy.tier_for_change(normalised, 20)
    assert policy.tier_for_change(paths, 20) == policy.tier_for_change(changed_case, 20)


@given(
    st.dictionaries(
        st.sampled_from(["lint", "tests", "coverage", "quality", "evals_no_regression", "secret_scan"]),
        st.booleans(),
        max_size=6,
    )
)
def test_missing_or_false_required_check_never_auto_merges(checks: dict[str, bool]) -> None:
    policy = RiskPolicy.load(phase=3)
    if any(checks.get(name) is not True for name in policy.required_checks):
        build = BuildResult(
            pr_number=1,
            changed_files=["tests/test_gate.py"],
            lines_changed=10,
            ci_green=True,
            checks=checks,
        )
        result = decide(policy, build, ReviewResult(approved=True))
        assert result.decision is not Decision.AUTO_MERGE


@given(st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=10))
def test_change_tier_is_at_least_the_maximum_file_tier(paths: list[str]) -> None:
    policy = RiskPolicy.load(phase=3)
    assert policy.tier_for_change(paths, 20) >= max(policy.tier_for_file(path) for path in paths)
