"""Unit tests for the example tools. Replace alongside your own tools."""

from agent import tools

VIN = "1HGCM82633A004352"


def test_history_known_and_unknown():
    assert tools.get_service_history(VIN)["status"] == "ok"
    assert tools.get_service_history("NOPE")["status"] == "error"


def test_estimate_known_issue():
    r = tools.estimate_repair(VIN, "Squealing BRAKES")
    assert r["status"] == "ok" and r["estimate"] == 320.0


def test_estimate_unknown_issue_needs_inspection():
    assert tools.estimate_repair(VIN, "strange noise")["status"] == "needs_inspection"


def test_estimate_rejects_unknown_vehicle():
    assert tools.estimate_repair("NOPE", "brakes")["status"] == "error"
