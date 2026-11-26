"""Run several InputScanners on the same text; the text is blocked if any one blocks it.

Fails closed: a scanner that raises counts as a block (and an incomplete scan), so one scanner's
outage can never turn into a pass, whatever the guard's own `fail_closed` setting. Every scanner runs
even after one blocks, so the trace shows all the rules that matched. Only error class names are kept.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence

from ..models import AdapterError, ScanVerdict
from ..ports import InputScanner


class CompositeScanner:
    def __init__(self, scanners: Sequence[tuple[str, InputScanner]]) -> None:
        if not scanners:
            raise ValueError("CompositeScanner needs at least one scanner; none would be a silent pass")
        self.scanners = list(scanners)

    def scan(self, text: str, channel: str) -> ScanVerdict:
        blocked = False
        complete = True
        rules: list[str] = []
        severity = "none"
        for name, scanner in self.scanners:
            try:
                verdict = scanner.scan(text, channel)
            except Exception as exc:  # noqa: BLE001 - a failing scanner must block, never pass
                blocked, complete = True, False
                rules.append(f"ERR-{name}-{type(exc).__name__}")
                severity = "high"
                continue
            blocked = blocked or verdict.blocked
            complete = complete and verdict.complete
            rules.extend(r for r in verdict.rule_ids if r not in rules)
            if verdict.severity != "none":
                severity = verdict.severity
        return ScanVerdict(blocked=blocked, complete=complete, rule_ids=rules, severity=severity)


def default_scanner(
    env: Mapping[str, str] | None = None, *, require_model_armor_outside_local: bool = True
) -> InputScanner:
    """Sunglasses always, plus Model Armor when `HARNESS_MODEL_ARMOR_PROMPT_TEMPLATE` is set.

    Outside `HARNESS_ENV=local` a Model Armor template is required (policy/input_guard.yaml). Imports
    are lazy, so a missing extra fails here, at start-up, not silently later.
    """
    from .model_armor_scanner import ModelArmorScanner
    from .sunglasses_scanner import SunglassesScanner

    env = os.environ if env is None else env
    local = env.get("HARNESS_ENV", "").strip().lower() == "local"
    template = env.get("HARNESS_MODEL_ARMOR_PROMPT_TEMPLATE")
    sunglasses = SunglassesScanner()
    if template:
        return CompositeScanner([("model_armor", ModelArmorScanner(template)), ("sunglasses", sunglasses)])
    if require_model_armor_outside_local and not local:
        raise AdapterError(
            "Model Armor is required outside HARNESS_ENV=local: set HARNESS_MODEL_ARMOR_PROMPT_TEMPLATE "
            "to a full template name in an allowed location"
        )
    return sunglasses
