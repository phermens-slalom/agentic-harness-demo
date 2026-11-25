"""Deterministic input guard: scan untrusted text before an LLM reads it. Never calls an LLM.
Fails closed by default: a crash or an incomplete scan blocks, it is not treated as clean."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..models import Issue
from ..policy import POLICY_DIR
from ..policy_validation import InputGuard as InputGuardSchema
from ..policy_validation import load_policy_file
from ..ports import InputScanner


@dataclass
class GuardResult:
    ok: bool  # False = the workflow must stop; in shadow mode this is always True
    reason: str = ""
    rule_ids: tuple[str, ...] = ()
    shadow_hit: bool = False  # shadow mode only: enforce mode would have blocked


@dataclass
class InputGuard:
    scanner: InputScanner
    surfaces: dict[str, str]  # surface -> scanner channel
    fail_closed: bool = True
    mode: str = "enforce"  # "shadow" | "enforce"

    @classmethod
    def load(cls, scanner: InputScanner, path: Path | None = None) -> InputGuard | None:
        """None when the policy disables the guard."""
        data = load_policy_file(path or POLICY_DIR / "input_guard.yaml", InputGuardSchema)
        if not data["enabled"]:
            return None
        mode = data.get("mode", "enforce")
        if mode not in ("shadow", "enforce"):
            raise ValueError(f"input_guard mode must be shadow or enforce, got {mode!r}")
        return cls(scanner, dict(data["surfaces"]), bool(data["fail_closed"]), mode)

    def check(self, surface: str, text: str) -> GuardResult:
        r = self._check(surface, text)
        if self.mode == "shadow" and not r.ok:
            return GuardResult(True, r.reason, r.rule_ids, shadow_hit=True)
        return r

    def _check(self, surface: str, text: str) -> GuardResult:
        channel = self.surfaces.get(surface)
        if channel is None or not text:
            return GuardResult(True)
        try:
            v = self.scanner.scan(text, channel)
        except Exception as e:  # noqa: BLE001 - scanner failure must not silently become a pass
            if self.fail_closed:
                return GuardResult(False, f"{surface}: scanner failed ({type(e).__name__}); failing closed")
            return GuardResult(True)
        if v.blocked:
            return GuardResult(
                False,
                f"{surface}: input guard matched {', '.join(v.rule_ids) or 'a rule'}",
                tuple(v.rule_ids),
            )
        if not v.complete and self.fail_closed:
            return GuardResult(False, f"{surface}: input not fully inspected; failing closed")
        return GuardResult(True)

    def check_issue(self, issue: Issue) -> GuardResult:
        return self.check("issue", f"{issue.title}\n\n{issue.body}")
