"""Data-residency guard. Deterministic; fails closed on unknown or global locations."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from pathlib import Path

from .policy_validation import Residency as ResidencySchema
from .policy_validation import load_policy_file

POLICY_DIR = Path(__file__).resolve().parents[2] / "policy"


class ResidencyError(RuntimeError):
    pass


def allowed_locations(path: Path | None = None) -> list[str]:
    return load_policy_file(path or POLICY_DIR / "residency.yaml", ResidencySchema)["allowed_locations"]


def assert_allowed(location: str | None, allowed: list[str] | None = None) -> str:
    allowed = allowed if allowed is not None else allowed_locations()
    if not location:
        raise ResidencyError(f"location not set; set one of {allowed}")
    if location not in allowed:
        raise ResidencyError(
            f"location {location!r} not allowed (global endpoints carry no residency guarantee); "
            f"allowed: {allowed}"
        )
    return location


_TRUE = ("true", "1")


def assert_model_backend(env: Mapping[str, str] | None = None, allowed: list[str] | None = None) -> str:
    """Return "vertex" or "ai-studio"; raise unless the model backend meets residency.

    Fails closed: outside HARNESS_ENV=local the only acceptable backend is Vertex AI with an allowed
    location. AI Studio / API keys have no residency guarantee, and a Vertex API key (express mode)
    has no location control, so a key next to Vertex is rejected too.
    """
    env = os.environ if env is None else env
    local = env.get("HARNESS_ENV", "").strip().lower() == "local"
    vertex = env.get("GOOGLE_GENAI_USE_VERTEXAI", "").strip().lower() in _TRUE
    if vertex:
        if env.get("GOOGLE_API_KEY") and not local:
            raise ResidencyError("GOOGLE_API_KEY is set next to Vertex AI; unset it (no location control)")
        assert_allowed(env.get("GOOGLE_CLOUD_LOCATION"), allowed)
        return "vertex"
    if local:
        return "ai-studio"
    raise ResidencyError(
        "model backend is not Vertex AI; AI Studio keys have no residency guarantee and are allowed "
        "only when HARNESS_ENV=local. Set GOOGLE_GENAI_USE_VERTEXAI=TRUE with an allowed "
        "GOOGLE_CLOUD_LOCATION"
    )


_TEMPLATE = re.compile(r"^projects/([^/\s]+)/locations/([a-z0-9-]+)/templates/([A-Za-z0-9_-]{1,63})$")


def template_location(template: str, allowed: list[str] | None = None) -> str:
    """Return the location of a Model Armor template resource name, if it is an allowed location.

    The name must be the full `projects/{project}/locations/{location}/templates/{template}`. The
    location picks the regional endpoint (`modelarmor.{location}.rep.googleapis.com`), so a template
    outside the allowed locations would send text outside them.
    """
    match = _TEMPLATE.match(template)
    if not match:
        raise ResidencyError(
            "Model Armor template must be a full name: projects/{project}/locations/{location}/templates/{template}"
        )
    return assert_allowed(match.group(2), allowed)
