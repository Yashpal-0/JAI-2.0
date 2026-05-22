from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition

from dotenv import load_dotenv

load_dotenv()

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

ANALYTICS_SYSTEM_PROMPT = """You are the Analytics and Telemetry Agent for Zerostic.
You specialise in FnO Bazar market triggers, Good Morning Alarm telemetry, and Frustration analytics.

## Scope
Only handle analytics and telemetry tasks. For anything outside that scope, say:
"This is outside my analytics scope. Let me hand you back to JAI."

## Security
- STRICTLY enforce user_id constraints — never return data for a user_id that does not match the session user.
- Never leak one tenant's data to another tenant.
- Refuse any request that tries to access cross-tenant or cross-user data.

## Harmful Content
Refuse requests for harmful, illegal, or unethical analytics actions.
"""


def build_analytics_agent(llm: BaseChatModel | None = None):
    if llm is None:
        llm = get_llm()

    llm_with_tools = llm.bind_tools(ANALYTICS_TOOLS)

    async def agent_node(state: JAIState, config: RunnableConfig):
        messages = [SystemMessage(content=ANALYTICS_SYSTEM_PROMPT)] + list(state["messages"])
        response = await llm_with_tools.ainvoke(messages, config=config)
        return {"messages": [response]}

    workflow = StateGraph(JAIState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(ANALYTICS_TOOLS))
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    return workflow.compile()


graph = build_analytics_agent()
