"""Content-free diagnostics for the starter's ADK function tools."""

import json
import logging
from collections.abc import Callable
from hashlib import sha256
from time import perf_counter
from typing import Any

from google.adk.tools import FunctionTool, ToolContext

logger = logging.getLogger(__name__)
_OUTCOMES = {"ok": "ok", "error": "rejected", "needs_inspection": "needs_inspection"}


class ObservedTool(FunctionTool):
    def __init__(self, func: Callable[..., Any], *, instruction: str):
        super().__init__(func)
        self._instruction_revision = sha256(instruction.encode("utf-8")).hexdigest()

    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> Any:
        start = perf_counter()
        outcome = "failed"
        try:
            response = await super().run_async(args=args, tool_context=tool_context)
            status = response.get("status") if isinstance(response, dict) else None
            outcome = _OUTCOMES.get(status, "unknown") if isinstance(status, str) else "unknown"
            return response
        finally:
            if logger.isEnabledFor(logging.INFO):
                logger.info(
                    "%s",
                    json.dumps(
                        {
                            "event": "tool.completed",
                            "request_id": sha256(tool_context.invocation_id.encode("utf-8")).hexdigest(),
                            "tool": self.name,
                            "outcome": outcome,
                            "duration_ms": round((perf_counter() - start) * 1000, 3),
                            "instruction_sha256": self._instruction_revision,
                        }
                    ),
                )
