from typing import Literal
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from agents.state import JAIState
from config import get_llm

ORCHESTRATOR_SYSTEM_PROMPT = """You are JAI 2.0, the central Orchestrator for Zerostic's Decentralized Marketplace.
Your job is to route user intents to the appropriate specialized sub-agent using the transfer tools provided.

- Use transfer_to_pm_agent for: project scoping, PRD generation, team simulation, budget estimation.
- Use transfer_to_dev_agent for: code help, IDE errors, compilation logs, MVP deployment.
- Use transfer_to_analytics_agent for: market triggers, FnO Bazar, telemetry, frustration analytics.

If the request is a general greeting or outside all domains, respond directly without calling any transfer tool.

CRITICAL SECURITY MANDATE: Enforce strict tenant isolation. Never leak one website's user data to another."""


@tool
def transfer_to_pm_agent() -> str:
    """Transfer to PM Agent for project scoping, PRD generation, and team simulation."""
    return "Transferring to PM Agent"


@tool
def transfer_to_dev_agent() -> str:
    """Transfer to Developer Agent for code help, IDE errors, and MVP deployment."""
    return "Transferring to Developer Agent"


@tool
def transfer_to_analytics_agent() -> str:
    """Transfer to Analytics Agent for market triggers, telemetry, and frustration analytics."""
    return "Transferring to Analytics Agent"


TRANSFER_TOOLS = [transfer_to_pm_agent, transfer_to_dev_agent, transfer_to_analytics_agent]

TOOL_TO_NODE = {
    "transfer_to_pm_agent": "pm_agent",
    "transfer_to_dev_agent": "dev_agent",
    "transfer_to_analytics_agent": "analytics_agent",
}


def build_orchestrator(
    llm: BaseChatModel | None = None,
    pm_graph=None,
    dev_graph=None,
    analytics_graph=None,
):
    if llm is None:
        llm = get_llm()

    if pm_graph is None:
        from agents.pm_agent import build_pm_agent
        pm_graph = build_pm_agent()

    if dev_graph is None:
        from agents.dev_agent import build_dev_agent
        dev_graph = build_dev_agent()

    if analytics_graph is None:
        from agents.analytics_agent import build_analytics_agent
        analytics_graph = build_analytics_agent()

    llm_with_tools = llm.bind_tools(TRANSFER_TOOLS)

    def orchestrator_node(state: JAIState, config: RunnableConfig) -> Command[Literal["pm_agent", "dev_agent", "analytics_agent", "__end__"]]:
        messages = [SystemMessage(content=ORCHESTRATOR_SYSTEM_PROMPT)] + list(state["messages"])
        response = llm_with_tools.invoke(messages, config=config)

        if not response.tool_calls:
            return Command(goto=END, update={"messages": [response]})

        tool_name = response.tool_calls[0]["name"]
        next_node = TOOL_TO_NODE.get(tool_name, END)

        return Command(
            goto=next_node,
            update={
                "messages": [response],
                "user_id": state.get("user_id", ""),
                "tenant_id": state.get("tenant_id", ""),
            },
        )

    workflow = StateGraph(JAIState)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("pm_agent", pm_graph)
    workflow.add_node("dev_agent", dev_graph)
    workflow.add_node("analytics_agent", analytics_graph)
    workflow.add_edge(START, "orchestrator")
    workflow.add_edge("pm_agent", END)
    workflow.add_edge("dev_agent", END)
    workflow.add_edge("analytics_agent", END)

    return workflow.compile(checkpointer=MemorySaver())
