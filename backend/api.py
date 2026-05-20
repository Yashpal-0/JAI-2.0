import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from functools import lru_cache
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessageChunk

from config import SUPPORTED_TENANTS
from agents.orchestrator import build_orchestrator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@lru_cache(maxsize=1)
def get_graph():
    return build_orchestrator()


class ChatRequest(BaseModel):
    message: str
    user_id: str
    tenant_id: str
    thread_id: str


@app.post("/chat")
async def chat(req: ChatRequest, graph=Depends(get_graph)):
    if req.tenant_id not in SUPPORTED_TENANTS:
        raise HTTPException(status_code=400, detail=f"Invalid tenant_id: {req.tenant_id}")

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
                    "messages": [HumanMessage(content=req.message)],
                    "user_id": req.user_id,
                    "tenant_id": req.tenant_id,
                },
                config=config,
                stream_mode="messages",
            ):
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    yield f"data: {chunk.content}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
