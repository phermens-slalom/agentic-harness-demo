"""Tools the agent can call. Plain functions with type hints and docstrings: ADK uses
them as the tool schema. EXAMPLE tools for a mechanic assistant; replace with your own.
Keep tools deterministic and side-effect free where possible so they are easy to test.
"""

import json
from pathlib import Path

_DATA = json.loads((Path(__file__).parent / "data" / "vehicles.json").read_text())
_RATES = {"brakes": 320.0, "oil change": 90.0, "battery": 450.0}  # PLACEHOLDER pricing


def get_service_history(vin: str) -> dict:
    """Return a vehicle's details and service history.

    Args:
        vin: The vehicle identification number.
    """
    vehicle = _DATA.get(vin)
    if vehicle is None or vin.startswith("_"):
        return {"status": "error", "message": f"unknown vehicle {vin}"}
    return {"status": "ok", "vehicle": vehicle}


def estimate_repair(vin: str, issue: str) -> dict:
    """Estimate the cost of a repair for a known vehicle.

    Args:
        vin: The vehicle identification number.
        issue: Short description of the fault, e.g. "brakes".
    """
    if get_service_history(vin)["status"] != "ok":
        return {"status": "error", "message": f"unknown vehicle {vin}"}
    for keyword, cost in _RATES.items():
        if keyword in issue.lower():
            return {
                "status": "ok",
                "issue": keyword,
                "estimate": cost,
                "currency": "AUD",
            }
    return {
        "status": "needs_inspection",
        "message": "no standard estimate; recommend an inspection",
    }
