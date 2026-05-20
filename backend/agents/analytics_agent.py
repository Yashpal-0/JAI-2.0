from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition

from agents.state import JAIState
from config import get_llm
from rag.pipeline import query_docs
from tools.analytics_tools import (
    fno_bazar_market_trigger_watcher,
    good_morning_alarm_telemetry_parser,
    frustration_analytics_collector,
    synthetic_user_persona_matrix,
    cross_ecosystem_context_weaver,
)

ANALYTICS_TOOLS = [
    fno_bazar_market_trigger_watcher,
    good_morning_alarm_telemetry_parser,
    frustration_analytics_collector,
    synthetic_user_persona_matrix,
    cross_ecosystem_context_weaver,
    query_docs,
]

ANALYTICS_SYSTEM_PROMPT = """You are the Analytics and Telemetry Agent.
You monitor FnO Bazar triggers, Good Morning Alarm telemetry, and Frustration analytics.
IMPORTANT: Data routing must strictly enforce user_id constraints to prevent leaking one website's user data to another."""


def build_analytics_agent(llm: BaseChatModel | None = None):
    if llm is None:
        llm = get_llm()

    llm_with_tools = llm.bind_tools(ANALYTICS_TOOLS)

    def agent_node(state: JAIState, config: RunnableConfig):
        messages = [SystemMessage(content=ANALYTICS_SYSTEM_PROMPT)] + list(state["messages"])
        response = llm_with_tools.invoke(messages, config=config)
        return {"messages": [response]}

    workflow = StateGraph(JAIState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(ANALYTICS_TOOLS))
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    return workflow.compile()
