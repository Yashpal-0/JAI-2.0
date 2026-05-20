from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition

from agents.state import JAIState
from config import get_llm
from rag.pipeline import query_docs
from tools.dev_tools import applab_code_tutor_handler, ai_shadow_replay_emulator, generative_venture_mvp_deployer

DEV_TOOLS = [applab_code_tutor_handler, ai_shadow_replay_emulator, generative_venture_mvp_deployer, query_docs]

DEV_SYSTEM_PROMPT = """You are the Zerostic Developer Agent. You reside on dev.zerostic.com.
You guide freelancers through the AppLab sandboxed IDE, parse compilation logs, and deploy MVPs.
IMPORTANT: You must maintain strict tenant isolation. Never leak codebase access or logs to unauthorized users."""


def build_dev_agent(llm: BaseChatModel | None = None):
    if llm is None:
        llm = get_llm()

    llm_with_tools = llm.bind_tools(DEV_TOOLS)

    def agent_node(state: JAIState, config: RunnableConfig):
        messages = [SystemMessage(content=DEV_SYSTEM_PROMPT)] + list(state["messages"])
        response = llm_with_tools.invoke(messages, config=config)
        return {"messages": [response]}

    workflow = StateGraph(JAIState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(DEV_TOOLS))
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    return workflow.compile()
