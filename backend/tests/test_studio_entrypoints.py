from langgraph.graph.state import CompiledStateGraph


def test_orchestrator_graph_entrypoint():
    from agents.orchestrator import graph
    assert graph is not None
    assert isinstance(graph, CompiledStateGraph)


def test_analytics_graph_entrypoint():
    from agents.analytics_agent import graph
    assert graph is not None
    assert isinstance(graph, CompiledStateGraph)
