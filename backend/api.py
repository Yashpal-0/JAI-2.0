import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager, suppress
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from config import SUPPORTED_TENANTS
from agents.orchestrator import build_orchestrator
from db import init_db, upsert_thread, list_threads, delete_thread, get_thread_owner

_REFRESH_INTERVAL = 24 * 3600
_DB_PATH = os.path.join(os.path.dirname(__file__), "checkpoints.db")


async def _company_refresh_loop() -> None:
    from rag.company_context import refresh_company_context
    while True:
        try:
            await refresh_company_context()
        except Exception as e:
            print(f"[api] Company context refresh error: {e}")
        await asyncio.sleep(_REFRESH_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    async with AsyncSqliteSaver.from_conn_string(_DB_PATH) as saver:
        app.state.graph = build_orchestrator(checkpointer=saver)
        task = asyncio.create_task(_company_refresh_loop())
        yield
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(lifespan=lifespan)

_CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


# ── Thread history endpoints ───────────────────────────────────────────────────

@app.get("/threads")
async def get_threads(user_id: str, tenant_id: str):
    if tenant_id not in SUPPORTED_TENANTS:
        raise HTTPException(status_code=400, detail=f"Invalid tenant_id: {tenant_id}")
    return list_threads(user_id, tenant_id)


@app.delete("/threads/{thread_id}")
async def remove_thread(thread_id: str, user_id: str, request: Request):
    owner = get_thread_owner(thread_id)
    if not owner:
        raise HTTPException(status_code=404, detail="Thread not found")
    if owner["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    delete_thread(thread_id)
    # Also delete LangGraph checkpoint state for this thread
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": thread_id, "user_id": owner["user_id"], "tenant_id": owner["tenant_id"]}}
    try:
        await graph.checkpointer.adelete_thread(config)
    except Exception:
        pass  # best-effort
    return {"deleted": thread_id}


@app.get("/threads/{thread_id}/messages")
async def get_thread_messages(thread_id: str, user_id: str, request: Request):
    owner = get_thread_owner(thread_id)
    if not owner:
        raise HTTPException(status_code=404, detail="Thread not found")
    if owner["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    graph = request.app.state.graph
    config = {"configurable": {
        "thread_id": thread_id,
        "user_id": owner["user_id"],
        "tenant_id": owner["tenant_id"],
    }}
    state = await graph.aget_state(config)
    if not state or not state.values:
        return []
    messages = []
    for msg in state.values.get("messages", []):
        if hasattr(msg, "type"):
            if msg.type == "human":
                messages.append({"role": "user", "content": msg.content})
            elif msg.type == "ai" and msg.content:
                messages.append({"role": "assistant", "content": msg.content})
    return messages


# ── Chat endpoint ──────────────────────────────────────────────────────────────

MAX_MESSAGE_LENGTH = 4000


class ChatRequest(BaseModel):
    message: str
    user_id: str
    tenant_id: str
    thread_id: str
    title: str = ""  # first user message used as thread title


@app.post("/chat")
async def chat(req: ChatRequest, request: Request):
    if req.tenant_id not in SUPPORTED_TENANTS:
        raise HTTPException(status_code=400, detail=f"Invalid tenant_id: {req.tenant_id}")

    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message cannot be empty")
    if len(message) > MAX_MESSAGE_LENGTH:
        raise HTTPException(status_code=400, detail=f"message exceeds {MAX_MESSAGE_LENGTH} characters")

    # Register / touch the thread in SQLite
    title = (req.title.strip() or message)[:60]
    upsert_thread(req.thread_id, req.user_id, req.tenant_id, title)

    graph = request.app.state.graph

    async def event_stream():
        try:
            config = {
                "configurable": {
                    "user_id": req.user_id,
                    "tenant_id": req.tenant_id,
                    "thread_id": req.thread_id,
                }
            }
            _STREAM_NODES = {"orchestrator", "analytics_agent", "input_guard", "output_guard"}
            async for chunk, metadata in graph.astream(
                {
                    "messages": [HumanMessage(content=message)],
                    "user_id": req.user_id,
                    "tenant_id": req.tenant_id,
                },
                config=config,
                stream_mode="messages",
            ):
                if metadata.get("langgraph_node") not in _STREAM_NODES:
                    continue
                if isinstance(chunk, (AIMessageChunk, AIMessage)) and chunk.content:
                    yield f"data: {chunk.content.replace(chr(10), chr(92) + 'n')}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"event: error\ndata: {str(e).replace(chr(10), ' ')}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
