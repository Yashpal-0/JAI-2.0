import asyncio
import pytest
from langchain_core.messages import HumanMessage, AIMessage


def make_fake_llm(response_content: str = "I can help with that.", tool_calls: list = None):
    from langchain_core.language_models import BaseChatModel
    from langchain_core.outputs import ChatResult, ChatGeneration
    from langchain_core.runnables import Runnable

    class _FakeLLM(BaseChatModel):
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            msg = AIMessage(content=response_content, tool_calls=tool_calls or [])
            return ChatResult(generations=[ChatGeneration(message=msg)])

        @property
        def _llm_type(self):
            return "fake"

        def bind_tools(self, tools, **kwargs):
            # Return self since the fake LLM doesn't actually use tools
            return self

    return _FakeLLM()



def test_analytics_agent_graph_compiles():
    from agents.analytics_agent import build_analytics_agent
    graph = build_analytics_agent(llm=make_fake_llm())
    assert graph is not None


def test_analytics_agent_returns_ai_message():
    from agents.analytics_agent import build_analytics_agent
    graph = build_analytics_agent(llm=make_fake_llm("Market watcher set for NIFTY."))
    result = asyncio.run(graph.ainvoke(
        {"messages": [HumanMessage(content="Watch NIFTY above 20000")], "user_id": "u1", "tenant_id": "zerostic.com"},
        config={"configurable": {"user_id": "u1", "tenant_id": "zerostic.com"}},
    ))
    last_message = result["messages"][-1]
    assert isinstance(last_message, AIMessage)


def test_orchestrator_graph_compiles():
    from agents.orchestrator import build_orchestrator
    graph = build_orchestrator(
        llm=make_fake_llm(),
        analytics_graph=build_analytics_agent_stub(),
    )
    assert graph is not None


def test_orchestrator_routes_and_returns_response():
    from agents.orchestrator import build_orchestrator
    graph = build_orchestrator(
        llm=make_fake_llm("I'll help you with your request."),
        analytics_graph=build_analytics_agent_stub(),
    )
    result = graph.invoke(
        {"messages": [HumanMessage(content="Hello")], "user_id": "u1", "tenant_id": "zerostic.com"},
        config={"configurable": {"user_id": "u1", "tenant_id": "zerostic.com", "thread_id": "test-thread"}},
    )
    assert len(result["messages"]) >= 2


def build_analytics_agent_stub():
    from agents.analytics_agent import build_analytics_agent
    return build_analytics_agent(llm=make_fake_llm("Analytics handled it."))
