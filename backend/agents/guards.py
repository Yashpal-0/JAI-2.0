"""
LangGraph guard nodes driven by agents/guardrails.yaml.

To add or change a rule: edit guardrails.yaml — no Python changes needed.

Graph position:
    START → input_guard → orchestrator → ... → output_guard → END
"""
import json
import logging
import re
from pathlib import Path
from typing import Any, Literal

import yaml
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END
from langgraph.types import Command

from agents.state import JAIState
from config import get_llm

log = logging.getLogger(__name__)

_RULES_PATH = Path(__file__).parent / "guardrails.yaml"
_rules_cache: dict[str, Any] | None = None


def _load_rules() -> dict[str, Any]:
    global _rules_cache
    if _rules_cache is None:
        try:
            _rules_cache = yaml.safe_load(_RULES_PATH.read_text()) or {}
        except Exception as e:
            log.error(f"[guards] Failed to load guardrails.yaml: {e}")
            _rules_cache = {}
    return _rules_cache


def reload_rules() -> None:
    """Force rules to reload from disk on next request (useful after editing guardrails.yaml)."""
    global _rules_cache
    _rules_cache = None


# ── Rule runners ───────────────────────────────────────────────────────────────

def _match_regex(rule: dict, text: str) -> bool:
    for pattern in rule.get("patterns", []):
        if re.search(pattern, text):
            return True
    return False


def _run_llm_input_classifier(rule: dict, query: str) -> bool:
    """Returns True if the LLM flags the input as jailbreak or harmful."""
    llm = get_llm()
    prompt = rule["prompt"].replace("{query}", query)
    try:
        result = llm.invoke(prompt)
        content = result.content if hasattr(result, "content") else str(result)
        match = re.search(r"\{[^{}]+\}", content, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return bool(data.get("is_jailbreak")) or bool(data.get("is_harmful"))
    except Exception as e:
        log.warning(f"[guards] LLM input classifier error (rule={rule['id']}): {e}")
    return False


def _run_llm_output_checker(rule: dict, response: str, rag_context: str) -> bool:
    """Returns True if the LLM flags the output as containing hallucinations."""
    if not rag_context:
        return False
    llm = get_llm()
    prompt = (
        rule["prompt"]
        .replace("{rag_context}", rag_context)
        .replace("{response}", response)
    )
    try:
        result = llm.invoke(prompt)
        content = result.content if hasattr(result, "content") else str(result)
        match = re.search(r"\{[^{}]+\}", content, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return bool(data.get("contains_hallucination"))
    except Exception as e:
        log.warning(f"[guards] LLM output checker error (rule={rule['id']}): {e}")
    return False


# ── LangGraph nodes ────────────────────────────────────────────────────────────

def input_guard_node(state: JAIState, config: RunnableConfig) -> Command[Literal["orchestrator", "__end__"]]:
    """
    Runs before the orchestrator. Evaluates input_rules from guardrails.yaml.
    Regex rules run first (no latency); LLM rules run only if all regex rules pass.
    """
    user_messages = [
        m for m in state["messages"]
        if hasattr(m, "type") and m.type == "human"
    ]
    if not user_messages:
        return Command(goto="orchestrator")

    query = user_messages[-1].content
    rules = _load_rules()

    for rule in rules.get("input_rules", []):
        if not rule.get("enabled", True):
            continue

        triggered = False
        rule_type = rule.get("type")

        if rule_type == "regex":
            triggered = _match_regex(rule, query)
        elif rule_type == "llm":
            triggered = _run_llm_input_classifier(rule, query)

        if triggered:
            log.info(f"[guards] Input blocked — rule='{rule['id']}'  query={query[:80]!r}")
            return Command(
                goto=END,
                update={"messages": [AIMessage(content=rule["response"])]},
            )

    return Command(goto="orchestrator")


def output_guard_node(state: JAIState, config: RunnableConfig) -> dict:
    """
    Runs after the orchestrator/analytics agent. Evaluates output_rules from
    guardrails.yaml before the response reaches the client.
    Always terminates — the graph has an explicit edge output_guard → END.
    """
    ai_messages = [m for m in state["messages"] if isinstance(m, AIMessage)]
    if not ai_messages:
        return {}

    last_response = ai_messages[-1].content
    rag_context = state.get("rag_context") or ""
    rules = _load_rules()

    for rule in rules.get("output_rules", []):
        if not rule.get("enabled", True):
            continue

        triggered = False
        rule_type = rule.get("type")

        if rule_type == "regex":
            triggered = _match_regex(rule, last_response)
        elif rule_type == "llm":
            triggered = _run_llm_output_checker(rule, last_response, rag_context)

        if triggered:
            log.warning(
                f"[guards] Output blocked — rule='{rule['id']}'  "
                f"response={last_response[:80]!r}"
            )
            return {"messages": [AIMessage(content=rule["response"])]}

    return {}
