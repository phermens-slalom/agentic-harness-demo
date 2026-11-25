"""__AGENT_NAME__: __DESCRIPTION__

Owner: __OWNER__ | Division: __DIVISION__
Google ADK is the only agent framework. Model name comes from config, not code.
The mechanic example below is a placeholder; replace tools, prompts and evals together.
"""

from google.adk.agents import Agent

from . import config, prompts, tools
from .telemetry import ObservedTool

_INSTRUCTION = f"{prompts.INSTRUCTION}\nGarage summary skill:\n{prompts.load_garage_skill()}"

root_agent = Agent(
    name="__AGENT_ID__",
    model=config.MODEL,
    description="__DESCRIPTION__",
    instruction=_INSTRUCTION,
    tools=[
        ObservedTool(tool, instruction=_INSTRUCTION)
        for tool in (tools.get_service_history, tools.estimate_repair)
    ],
)
