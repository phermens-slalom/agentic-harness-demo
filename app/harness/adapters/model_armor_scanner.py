"""InputScanner over Google Cloud Model Armor (`sanitizeUserPrompt`).

Model Armor is the primary scanner (D-09). Every untrusted surface the guard names is screened against
one prompt template, whatever the channel. Needs the `armor` extra (`google-cloud-modelarmor`), imported
lazily, plus Application Default Credentials. Against a regional endpoint only
(`modelarmor.{location}.rep.googleapis.com`); the template's location must be an allowed residency location.

Verdict mapping, checked against Google's Model Armor docs:
- `filterMatchState == MATCH_FOUND`  -> blocked
- `invocationResult != SUCCESS`      -> not complete (a skipped or failed filter is never "clean")
- Text over the filter limit is split into overlapping chunks, and any chunk that blocks blocks the text.
- Any call error raises ScannerError (class name only); the guard then fails closed.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from .. import residency
from ..models import AdapterError, ScanVerdict

# Enum values from google/cloud/modelarmor/v1/service.proto.
NO_MATCH_FOUND = 1
MATCH_FOUND = 2
SUCCESS = 1

# Model Armor documents a limit of 65,536 tokens (about 4 characters each) for the prompt injection and
# jailbreak filter; text past it is skipped. Chunking by characters at the token figure stays far below it.
CHUNK_CHARS = 65_536
OVERLAP_CHARS = 4_096

_FILTER_RESULTS = (
    "pi_and_jailbreak_filter_result",
    "rai_filter_result",
    "sdp_filter_result",
    "malicious_uri_filter_result",
    "csam_filter_filter_result",
    "virus_scan_filter_result",
)
_NESTED = ("inspect_result", "deidentify_result")
_DOCS_NAME = re.compile(r"[^A-Za-z0-9_.-]")


class ScannerError(AdapterError):
    """A scanner could not give a verdict. Never carries the scanned text."""


def _state(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _matched(filter_result: Any) -> bool:
    for name in _FILTER_RESULTS:
        sub = getattr(filter_result, name, None)
        if sub is None:
            continue
        if _state(getattr(sub, "match_state", 0)) == MATCH_FOUND:
            return True
        if any(
            _state(getattr(getattr(sub, nested, None), "match_state", 0)) == MATCH_FOUND for nested in _NESTED
        ):
            return True
    return False


def _chunks(text: str) -> list[str]:
    if len(text) <= CHUNK_CHARS:
        return [text]
    step = CHUNK_CHARS - OVERLAP_CHARS
    out = []
    for start in range(0, len(text), step):
        out.append(text[start : start + CHUNK_CHARS])
        if start + CHUNK_CHARS >= len(text):
            break
    return out


class ModelArmorScanner:
    def __init__(
        self,
        template: str,
        *,
        client: Any = None,
        allowed_locations: Sequence[str] | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.template = template
        self.location = residency.template_location(
            template, list(allowed_locations) if allowed_locations is not None else None
        )
        self.timeout_seconds = timeout_seconds
        self._client = client if client is not None else self._build_client(self.location)

    @staticmethod
    def _build_client(location: str) -> Any:
        try:
            from google.api_core.client_options import ClientOptions  # lazy: optional extra
            from google.cloud import modelarmor_v1
        except ImportError as exc:
            raise ScannerError("Model Armor needs the extra: pip install -e '.[armor]'") from exc
        return modelarmor_v1.ModelArmorClient(
            client_options=ClientOptions(api_endpoint=f"modelarmor.{location}.rep.googleapis.com")
        )

    def scan(self, text: str, channel: str) -> ScanVerdict:
        blocked = False
        complete = True
        rules: list[str] = []
        for chunk in _chunks(text):
            result = self._sanitise(chunk)
            if _state(result.filter_match_state) == MATCH_FOUND:
                blocked = True
            if _state(result.invocation_result) != SUCCESS:
                complete = False
            for name, filter_result in result.filter_results.items():
                rule = "MA-" + _DOCS_NAME.sub("", str(name))
                if _matched(filter_result) and rule not in rules:
                    rules.append(rule)
        if blocked and not rules:
            rules.append("MA-match")
        return ScanVerdict(
            blocked=blocked, complete=complete, rule_ids=rules, severity="high" if blocked else "none"
        )

    def _sanitise(self, text: str) -> Any:
        request = {"name": self.template, "user_prompt_data": {"text": text}}
        try:
            response = self._client.sanitize_user_prompt(request=request, timeout=self.timeout_seconds)
            return response.sanitization_result
        except Exception as exc:  # noqa: BLE001 - any failure must reach the guard as an error, not a pass
            raise ScannerError(f"Model Armor call failed ({type(exc).__name__})") from None
