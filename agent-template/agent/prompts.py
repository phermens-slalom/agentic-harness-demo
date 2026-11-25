"""Prompts live in one place so changes are easy to review and eval.

EXAMPLE: a workshop assistant that helps a mechanic. Replace with your agent's business
rules and flows.
"""

from hashlib import sha256
from importlib.resources import files

_GARAGE_SKILL_SHA256 = "bd12dbefe5bb3fd866e1ca65df956740f42a8257c148355fee17099933baa3fd"


def load_garage_skill() -> str:
    asset = files("agent").joinpath("skills", "garage-summary", "SKILL.md")
    text = asset.read_text(encoding="utf-8").replace("\r\n", "\n")
    if sha256(text.encode("utf-8")).hexdigest() != _GARAGE_SKILL_SHA256:
        raise ValueError("garage-summary does not match its approved SHA-256")
    return text.split("---\n", 2)[2].strip()


INSTRUCTION = """\
You are an assistant for a vehicle mechanic.
- Look up a vehicle's service history before recommending work.
- Give a repair estimate only after you know the vehicle and the reported issue.
- This agent is read-only. If asked to book, change, or cancel a service slot, explain
  that you cannot do so, even if the user confirms the request. Never claim a booking was made.
- If a tool returns an error or the vehicle is unknown, say so; never invent data.
"""
