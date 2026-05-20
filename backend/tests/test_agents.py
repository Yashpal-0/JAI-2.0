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


def test_pm_agent_graph_compiles():
    from agents.pm_agent import build_pm_agent
    graph = build_pm_agent(llm=make_fake_llm())
    assert graph is not None


def test_pm_agent_returns_ai_message():
    from agents.pm_agent import build_pm_agent
    graph = build_pm_agent(llm=make_fake_llm("I'll scope your project."))
    result = graph.invoke(
        {"messages": [HumanMessage(content="Scope a web project")], "user_id": "u1", "tenant_id": "studio.zerostic.com"},
        config={"configurable": {"user_id": "u1", "tenant_id": "studio.zerostic.com"}},
    )
    last_message = result["messages"][-1]
    assert isinstance(last_message, AIMessage)
    assert last_message.content != ""


def test_dev_agent_graph_compiles():
    from agents.dev_agent import build_dev_agent
    graph = build_dev_agent(llm=make_fake_llm())
    assert graph is not None


def test_dev_agent_returns_ai_message():
    from agents.dev_agent import build_dev_agent
    graph = build_dev_agent(llm=make_fake_llm("Here's a hint for your IDE error."))
    result = graph.invoke(
        {"messages": [HumanMessage(content="I have a missing semicolon error")], "user_id": "u1", "tenant_id": "dev.zerostic.com"},
        config={"configurable": {"user_id": "u1", "tenant_id": "dev.zerostic.com"}},
    )
    last_message = result["messages"][-1]
    assert isinstance(last_message, AIMessage)


def test_analytics_agent_graph_compiles():
    from agents.analytics_agent import build_analytics_agent
    graph = build_analytics_agent(llm=make_fake_llm())
    assert graph is not None


def test_analytics_agent_returns_ai_message():
    from agents.analytics_agent import build_analytics_agent
    graph = build_analytics_agent(llm=make_fake_llm("Market watcher set for NIFTY."))
    result = graph.invoke(
        {"messages": [HumanMessage(content="Watch NIFTY above 20000")], "user_id": "u1", "tenant_id": "studio.zerostic.com"},
        config={"configurable": {"user_id": "u1", "tenant_id": "studio.zerostic.com"}},
    )
    last_message = result["messages"][-1]
    assert isinstance(last_message, AIMessage)
