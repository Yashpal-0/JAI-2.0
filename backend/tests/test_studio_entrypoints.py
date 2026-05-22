import json
from pathlib import Path

from langgraph.graph.state import CompiledStateGraph


def test_orchestrator_graph_entrypoint():
    from agents.orchestrator import graph
    assert graph is not None
    assert isinstance(graph, CompiledStateGraph)


def test_analytics_graph_entrypoint():
    from agents.analytics_agent import graph
    assert graph is not None
    assert isinstance(graph, CompiledStateGraph)


def test_langgraph_json_valid():
    config_path = Path(__file__).parent.parent / "langgraph.json"
    assert config_path.exists(), "langgraph.json not found in backend/"
    config = json.loads(config_path.read_text())
    assert "graphs" in config
    assert "orchestrator" in config["graphs"]
    assert "analytics" in config["graphs"]
    assert "dependencies" in config
    assert "env" in config


def test_langgraph_json_graph_paths_resolvable():
    """Graph module paths in langgraph.json must point to importable symbols."""
    config_path = Path(__file__).parent.parent / "langgraph.json"
    config = json.loads(config_path.read_text())
    for graph_name, graph_ref in config["graphs"].items():
        # graph_ref format: "./path/to/module.py:variable"
        assert ":" in graph_ref, f"{graph_name}: missing ':' separator in '{graph_ref}'"
        module_path, symbol = graph_ref.rsplit(":", 1)
        # Strip leading "./"
        module_file = Path(__file__).parent.parent / module_path.lstrip("./")
        assert module_file.exists(), f"{graph_name}: module file not found at {module_file}"
