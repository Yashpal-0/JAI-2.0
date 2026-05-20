from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition

from agents.state import JAIState
from config import get_llm
from rag.pipeline import query_docs
from tools.pm_tools import autonomous_project_scoping, project_time_machine_simulator

PM_TOOLS = [autonomous_project_scoping, project_time_machine_simulator, query_docs]

PM_SYSTEM_PROMPT = """You are the Zerostic Product Manager Agent. You reside on pm.zerostic.com.
You handle project scoping, PRD generation, and team matchmaking analytics.
IMPORTANT: You must maintain strict tenant isolation. Never leak project details to cross-tenant users."""


def build_pm_agent(llm: BaseChatModel | None = None):
    if llm is None:
        llm = get_llm()

    llm_with_tools = llm.bind_tools(PM_TOOLS)

    def agent_node(state: JAIState):
        messages = [SystemMessage(content=PM_SYSTEM_PROMPT)] + list(state["messages"])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    workflow = StateGraph(JAIState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(PM_TOOLS))
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    return workflow.compile()
