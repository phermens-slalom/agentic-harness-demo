"""Runtime configuration. Model and region come from the environment, not code."""

import os

MODEL = os.environ.get("AGENT_MODEL", "<set via config>")
# Must be an allowed region (see the harness policy/residency.yaml); never a global endpoint.
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "australia-southeast2")
