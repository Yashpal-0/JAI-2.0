from typing import Annotated, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class WorkflowStep(TypedDict):
    name: str        # e.g. "prd_quick", "quotation", "booking", "admin_msg"
    step: int        # current 1-based step index
    total: int       # total steps in this workflow
    data: dict       # collected answers so far


class JAIState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    tenant_id: str
    workflow: Optional[WorkflowStep]
    rag_context: Optional[str]  # chunks retrieved for the last query; used by output_guard
