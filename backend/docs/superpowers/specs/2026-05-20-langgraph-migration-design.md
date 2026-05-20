# LangGraph Migration Design
**Date:** 2026-05-20  
**Status:** Approved

## Summary

Replace the OpenAI Agents SDK (`openai-agents`) with LangChain + LangGraph as the full orchestration and RAG layer for JAI 2.0. The multi-agent handoff graph pattern is used: each sub-agent is a compiled `StateGraph`, and the orchestrator is a separate graph that routes to sub-agents via LangGraph `Command` edges.

---

## Architecture

```
backend/
├── config.py                        # ChatOpenAI(base_url=openrouter) — replaces AsyncOpenAI
├── rag/
│   ├── pipeline.py                  # Chroma + HuggingFaceEmbeddings + query_docs @tool
│   └── ingest.py                    # CLI: scan docs/, chunk, embed, persist ./chroma_db/
├── tools/
│   ├── pm_tools.py                  # @tool decorated (drop @function_tool + RunContextWrapper)
│   ├── dev_tools.py
│   └── analytics_tools.py
├── agents/
│   ├── pm_agent.py                  # Compiled StateGraph: ToolNode + pm tools + rag tool
│   ├── dev_agent.py
│   ├── analytics_agent.py
│   └── orchestrator.py              # Root graph with routing logic
├── main.py                          # orchestrator.graph.ainvoke(...)
└── evals/
    └── verify.py                    # Updated to call LangGraph orchestrator
```

### Data flow

```
User message
  → Orchestrator graph (ChatOpenAI decides route)
  → Command(goto="pm_agent" | "dev_agent" | "analytics_agent")
  → Sub-agent graph:
      agent_node → tools_node (if tool_calls) → agent_node → END
  → Control returns to orchestrator
  → Orchestrator emits final response
```

---

## State Schema

```python
class JAIState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    tenant_id: str
```

- `messages` uses LangGraph's `add_messages` reducer (append-only).
- `user_id` and `tenant_id` injected at graph entry, forwarded via `Command(update={...})` on every handoff.
- Tenant fields also passed as `RunnableConfig` configurable keys so tools receive them without exposing them in the LLM-visible tool schema (prevents prompt-injection bypass of tenant checks).

---

## Components

### `config.py`
- `ChatOpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY, model=OPENROUTER_MODEL)`
- Drop `AsyncOpenAI` and all `openai-agents` imports.
- LangSmith tracing: use `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY` env vars. LangGraph auto-instruments — no manual processor setup.

### `rag/pipeline.py`
- Embeddings: `HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")` (same model as `jai_rag.py`).
- Vectorstore: `Chroma(persist_directory="./chroma_db")`.
- Exposes `query_docs(question: str) -> str` decorated with `@tool`. Returns top-4 retrieved chunks as formatted string.
- Stateless — safe to call from any sub-agent.
- If Chroma DB missing: returns `"No documentation indexed. Run backend/rag/ingest.py first."` — never raises.

### `rag/ingest.py`
- CLI replacing `jai_rag.py ingest` and `setup_rag.sh`.
- Scans `backend/docs/**/*.md`, uses `RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)`.
- Embeds and persists to `./chroma_db/`.

### `tools/*.py`
- Drop `from agents import RunContextWrapper, function_tool`.
- Add `from langchain_core.tools import tool`.
- Replace `@function_tool` with `@tool`.
- Tenant fields (`user_id`, `tenant_id`) read from `RunnableConfig` via `config: RunnableConfig` parameter (LangChain tool injection pattern) — not from `RunContextWrapper`.

### `agents/pm_agent.py`, `dev_agent.py`, `analytics_agent.py`
Each follows identical structure:
```
StateGraph(JAIState)
  .add_node("agent", agent_node)    # ChatOpenAI.bind_tools([...domain_tools, query_docs])
  .add_node("tools", ToolNode([...]))
  .add_edge(START, "agent")
  .add_conditional_edges("agent", tools_condition)
  .add_edge("tools", "agent")
  .compile()
```
`ToolNode` catches tool exceptions and returns them as `ToolMessage` with error content — agent sees the error and can recover gracefully.

### `agents/orchestrator.py`
```
StateGraph(JAIState)
  .add_node("orchestrator", orchestrator_node)
  .add_node("pm_agent", pm_agent.graph)
  .add_node("dev_agent", dev_agent.graph)
  .add_node("analytics_agent", analytics_agent.graph)
  .add_edge(START, "orchestrator")
  .add_conditional_edges("orchestrator", route_to_agent)
  .compile()
```
`orchestrator_node` uses system prompt identical to current JAI 2.0 routing instructions. Routes via `Command(goto=<agent_name>, update={"user_id": ..., "tenant_id": ...})`.

---

## Error Handling

| Scenario | Handling |
|---|---|
| 429 rate limit | Caught in `verify.py` try/except, logged as `[ERROR]` |
| Tool raises exception | `ToolNode` catches, returns error as `ToolMessage`; agent surfaces to user |
| Chroma DB missing | `query_docs` returns informational string, never raises |
| Tenant violation in tool | Tool returns JSON error string; existing check logic preserved |
| Unknown route intent | Orchestrator falls back to direct response without sub-agent handoff |

---

## `evals/verify.py` Update

```python
result = await orchestrator.graph.ainvoke(
    {
        "messages": [HumanMessage(content=instruction)],
        "user_id": "eval_user_001",
        "tenant_id": "studio.zerostic.com"
    },
    config={"configurable": {
        "user_id": "eval_user_001",
        "tenant_id": "studio.zerostic.com"
    }}
)
final_output = result["messages"][-1].content
```
Cross-tenant leakage check logic unchanged.

---

## Files Deleted

| File | Reason |
|---|---|
| `jai_rag.py` (root) | Replaced by `backend/rag/` |
| `setup_rag.sh` (root) | Replaced by `backend/rag/ingest.py` |
| `run_jai_tests.py` (root) | Replaced by `backend/evals/verify.py` |
| `jai_test_results.json` (root) | Stale artifact |
| `requirements.txt` (root) | Duplicate — `backend/requirements.txt` is canonical |
| `backend/jai_agent.py` | Replaced by `backend/agents/` |
| `backend/core_agents.py` | Replaced by `backend/agents/orchestrator.py` |

---

## Dependencies (`backend/requirements.txt`)

Remove:
```
openai-agents
```

Add:
```
langchain
langgraph
langchain-openai
langchain-community
langchain-huggingface
chromadb
sentence-transformers
```

Keep:
```
openai>=1.0.0        # still needed by langchain-openai
python-dotenv>=1.0.0
langsmith
```
