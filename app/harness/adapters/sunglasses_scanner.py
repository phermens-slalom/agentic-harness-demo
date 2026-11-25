"""InputScanner over the sunglasses engine (MIT, local, no network, no LLM). Optional extra:
pip install ".[guard]". Import is lazy so the harness runs without it; the guard then fails closed."""

from __future__ import annotations

from ..models import ScanVerdict


class SunglassesScanner:
    def __init__(self) -> None:
        from sunglasses.engine import SunglassesEngine  # lazy: optional dependency

        self._engine = SunglassesEngine()

    def scan(self, text: str, channel: str) -> ScanVerdict:
        r = self._engine.scan(text, channel=channel)
        d = r.to_dict()
        ids = [f.get("id", "?") if isinstance(f, dict) else str(getattr(f, "id", "?")) for f in r.findings]
        return ScanVerdict(
            blocked=bool(d["threat_found"]),
            complete=bool(d["inspection_complete"]),
            rule_ids=ids,
            severity=str(d.get("severity", "none")),
        )
