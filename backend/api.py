import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager, suppress
from dotenv import load_dotenv
load_dotenv()

from functools import lru_cache
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk

from config import SUPPORTED_TENANTS
# Note: importing orchestrator triggers module-level `graph = build_orchestrator()` (for langgraph dev).
# get_graph() below builds a second independent instance for this server — both share no state.
from agents.orchestrator import build_orchestrator

_REFRESH_INTERVAL = 24 * 3600  # seconds


async def _company_refresh_loop() -> None:
    """Scrape zerostic.com on startup and refresh every 24 h."""
    from rag.company_context import refresh_company_context
    while True:
        try:
            await refresh_company_context()
        except Exception as e:
            print(f"[api] Company context refresh error: {e}")
        await asyncio.sleep(_REFRESH_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@lru_cache(maxsize=1)
def get_graph():
    return build_orchestrator()


MAX_MESSAGE_LENGTH = 4000


class ChatRequest(BaseModel):
    message: str
    user_id: str
    tenant_id: str
    thread_id: str


@app.post("/chat")
async def chat(req: ChatRequest, graph=Depends(get_graph)):
    if req.tenant_id not in SUPPORTED_TENANTS:
        raise HTTPException(status_code=400, detail=f"Invalid tenant_id: {req.tenant_id}")

    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message cannot be empty")
    if len(message) > MAX_MESSAGE_LENGTH:
        raise HTTPException(status_code=400, detail=f"message exceeds {MAX_MESSAGE_LENGTH} characters")

    async def event_stream():
        try:
            config = {
                "configurable": {
                    "user_id": req.user_id,
                    "tenant_id": req.tenant_id,
                    "thread_id": req.thread_id,
                }
            }
            async for chunk, metadata in graph.astream(
                {
                    "messages": [HumanMessage(content=message)],
                    "user_id": req.user_id,
                    "tenant_id": req.tenant_id,
                },
                config=config,
                stream_mode="messages",
            ):
                if isinstance(chunk, (AIMessageChunk, AIMessage)) and chunk.content:
                    yield f"data: {chunk.content.replace(chr(10), chr(92) + 'n')}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"event: error\ndata: {str(e).replace(chr(10), ' ')}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
