from pathlib import Path
from typing import Literal
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from agents.guards import input_guard_node, output_guard_node
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from dotenv import load_dotenv

load_dotenv()

from agents.state import JAIState
from config import get_llm
from rag.pipeline import build_rag_context

MAX_HISTORY_MESSAGES = 20

_INSTRUCTIONS_PATH = Path(__file__).parent.parent / "jai_instructions.md"
_JAI_INSTRUCTIONS: str = _INSTRUCTIONS_PATH.read_text(encoding="utf-8")

_COMING_SOON = (
    "This feature isn't live yet. You can email support@zerostic.com "
    "or call +91 8076376175 for assistance."
)


def _build_system_prompt() -> str:
    from rag.company_context import get_company_context_str
    return _JAI_INSTRUCTIONS.replace("{about}", get_company_context_str())


# ── Sub-agent routing ──────────────────────────────────────────────────────────

@tool
def transfer_to_analytics_agent() -> str:
    """Transfer to Analytics Agent for market triggers, FnO Bazar signals, telemetry, and frustration analytics."""
    return "Transferring to Analytics Agent"


# ── Client data tools ──────────────────────────────────────────────────────────

@tool
def get_client_projects(user_id: str, tenant_id: str) -> str:
    """Fetch the client's projects from Zerostic — active, completed, and in-review projects with status details."""
    return _COMING_SOON


@tool
def get_payment_history(user_id: str, tenant_id: str) -> str:
    """Fetch the client's payment records from Zerostic — all payments, statuses (confirmed/pending/rejected), and amounts."""
    return _COMING_SOON


@tool
def get_invoices(user_id: str, tenant_id: str) -> str:
    """Fetch the client's invoices from Zerostic — invoice list with amounts, statuses, and download links."""
    return _COMING_SOON


@tool
def get_contracts(user_id: str, tenant_id: str) -> str:
    """Fetch the client's contracts from Zerostic — contract list with signing status (pending/signed)."""
    return _COMING_SOON


@tool
def get_account_status(user_id: str, tenant_id: str) -> str:
    """Fetch the client's account status — verification status, active/completed project counts, account tier (lead/active)."""
    return _COMING_SOON


@tool
def get_notifications(user_id: str, tenant_id: str) -> str:
    """Fetch the client's unread notifications from Zerostic — account activity, project updates, payment status changes."""
    return _COMING_SOON


# ── Action tools ───────────────────────────────────────────────────────────────

@tool
def submit_quotation_request(user_id: str, tenant_id: str, project_title: str, description: str, budget_range: str = "", timeline: str = "") -> str:
    """Submit a new project quotation request to the Zerostic team."""
    return _COMING_SOON


@tool
def book_scheduler_call(user_id: str, tenant_id: str, call_type: str, preferred_datetime: str, notes: str = "") -> str:
    """Book a call with the Zerostic team via the Zerostic Scheduler.
    call_type: one of 'Project Consultation' (60min), 'Technical Discussion' (45min),
    'Demo/Presentation' (30min), 'Support Session' (30min), 'Other' (30min).
    preferred_datetime: ISO 8601 format. Available Mon-Fri 9AM-6PM IST, up to 30 days ahead."""
    return _COMING_SOON


@tool
def send_admin_message(user_id: str, tenant_id: str, subject: str, message: str) -> str:
    """Send a message thread to the Zerostic admin team."""
    return _COMING_SOON


# ── Tool groups ────────────────────────────────────────────────────────────────

TRANSFER_TOOLS = [transfer_to_analytics_agent]

ACTION_TOOLS = [
    get_client_projects,
    get_payment_history,
    get_invoices,
    get_contracts,
    get_account_status,
    get_notifications,
    submit_quotation_request,
    book_scheduler_call,
    send_admin_message,
]

ALL_TOOLS = TRANSFER_TOOLS + ACTION_TOOLS

TOOL_TO_NODE = {
    "transfer_to_analytics_agent": "analytics_agent",
}


def build_orchestrator(
    llm: BaseChatModel | None = None,
    analytics_graph=None,
    checkpointer=None,
):
    if llm is None:
        llm = get_llm()

    if analytics_graph is None:
        from agents.analytics_agent import build_analytics_agent
        analytics_graph = build_analytics_agent()

    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    def orchestrator_node(state: JAIState, config: RunnableConfig) -> Command[Literal["analytics_agent", "tools", "output_guard"]]:
        all_messages = list(state["messages"])

        user_messages = [m for m in all_messages if hasattr(m, "type") and m.type == "human"]
        last_query = user_messages[-1].content if user_messages else ""

        rag_context = build_rag_context(last_query) if last_query else ""
        base_prompt = _build_system_prompt()
        system_content = base_prompt if not rag_context else f"{base_prompt}\n\n{rag_context}"

        history = all_messages[-MAX_HISTORY_MESSAGES:] if len(all_messages) > MAX_HISTORY_MESSAGES else all_messages
        messages = [SystemMessage(content=system_content)] + history
        response = llm_with_tools.invoke(messages, config=config)

        if not response.tool_calls:
            return Command(
                goto="output_guard",
                update={"messages": [response], "rag_context": rag_context},
            )

        tool_name = response.tool_calls[0]["name"]

        if tool_name in TOOL_TO_NODE:
            return Command(
                goto=TOOL_TO_NODE[tool_name],
                update={
                    "messages": [response],
                    "user_id": state.get("user_id", ""),
                    "tenant_id": state.get("tenant_id", ""),
                    "rag_context": rag_context,
                },
            )

        return Command(goto="tools", update={"messages": [response], "rag_context": rag_context})

    workflow = StateGraph(JAIState)
    workflow.add_node("input_guard", input_guard_node)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("tools", ToolNode(ACTION_TOOLS))
    workflow.add_node("analytics_agent", analytics_graph)
    workflow.add_node("output_guard", output_guard_node)
    workflow.add_edge(START, "input_guard")
    workflow.add_edge("tools", "orchestrator")
    workflow.add_edge("analytics_agent", "output_guard")
    workflow.add_edge("output_guard", END)

    return workflow.compile(checkpointer=checkpointer)


graph = build_orchestrator()
