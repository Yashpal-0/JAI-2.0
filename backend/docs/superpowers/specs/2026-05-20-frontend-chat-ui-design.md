# Frontend Chat UI Design
**Date:** 2026-05-20
**Status:** Approved

## Summary

Add a React (Vite) chat UI at `frontend/` and a FastAPI HTTP server at `backend/api.py` that bridges the existing LangGraph orchestrator to the browser via Server-Sent Events (SSE).

---

## Architecture

Two independent servers during development:

```
frontend/ (Vite :5173)              backend/ (FastAPI :8000)
  src/
    App.tsx              POST /chat  →  graph.astream()
    hooks/useChat.ts  ←─ SSE stream ←─ LangGraph orchestrator
    components/
      ChatWindow.tsx
      MessageBubble.tsx
      TenantSelector.tsx
    types.ts
  vite.config.ts (proxy /chat → :8000 in dev)
```

Vite proxies `/chat` to `:8000` in dev — no CORS headers needed. For production, build React with `npm run build` and serve `dist/` as FastAPI static files.

---

## File Map

**Created:**
- `backend/api.py` — FastAPI app, SSE `/chat` endpoint
- `frontend/package.json`
- `frontend/vite.config.ts` — proxy `/chat` → `http://localhost:8000`
- `frontend/tsconfig.json`
- `frontend/index.html`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx` — root layout: tenant selector + chat window + input
- `frontend/src/types.ts` — `Message` type (`id`, `role`, `content`)
- `frontend/src/hooks/useChat.ts` — message state, SSE fetch logic, thread_id
- `frontend/src/components/ChatWindow.tsx` — scrollable message list
- `frontend/src/components/MessageBubble.tsx` — user/assistant styled bubbles
- `frontend/src/components/TenantSelector.tsx` — tenant dropdown

**Modified:**
- `backend/requirements.txt` — add `fastapi`, `uvicorn[standard]`, `sse-starlette`

---

## Backend: `api.py`

FastAPI app with a single endpoint:

```
POST /chat
Body: { message: str, user_id: str, tenant_id: str, thread_id: str }
Response: text/event-stream
```

Validation: `tenant_id` must be in `SUPPORTED_TENANTS` from `config.py` — returns 400 otherwise.

Streaming: calls `graph.astream(..., stream_mode="messages")` which yields `(AIMessageChunk, metadata)` tuples. Each chunk's `.content` is sent as:
```
data: <token>\n\n
```
When the stream ends:
```
data: [DONE]\n\n
```
On exception mid-stream:
```
event: error\ndata: <message>\n\n
```

CORS: allows `http://localhost:5173` (Vite dev origin).

---

## Frontend: `useChat.ts`

Hook interface:
```ts
const { messages, isStreaming, error, sendMessage } = useChat(tenant, userId)
```

- `messages: Message[]` — full conversation history including in-progress streaming message
- `isStreaming: boolean` — true while response is arriving
- `error: string | null` — last error, cleared on next send
- `sendMessage(text: string): void` — appends user message, opens SSE fetch stream

`thread_id`: UUID generated once per browser session, stored in `sessionStorage`. Same tab = same thread (conversation history preserved across page refresh). New tab = new thread.

Streaming implementation uses `fetch()` + `response.body.getReader()` — not `EventSource`, because `EventSource` does not support POST bodies. Reads the response body as a `ReadableStream`, splits on `data: `, strips `[DONE]`, appends tokens to the last message in state.

---

## Frontend: Components

**`TenantSelector.tsx`**
Controlled `<select>` with options for `studio.zerostic.com`, `pm.zerostic.com`, `dev.zerostic.com`. Disabled while `isStreaming`. Changing tenant does NOT clear conversation — thread continues with new tenant context (allows cross-tenant exploration in dev).

**`ChatWindow.tsx`**
Scrollable `<div>` containing a `MessageBubble` per message. Auto-scrolls to bottom whenever `messages` changes using `useEffect` + `scrollIntoView`.

**`MessageBubble.tsx`**
Renders a single message. User messages right-aligned, assistant messages left-aligned. Shows a blinking cursor `▋` at the end of the last assistant message while `isStreaming`.

**`App.tsx`**
- State: `tenant` (string), `userId` (hardcoded `"ui_user"`)
- Renders: `TenantSelector` → `ChatWindow` → input row (textarea + send button)
- Send button disabled when `isStreaming` or input is empty
- Enter key (without Shift) submits

---

## Error Handling

| Scenario | Backend | Frontend |
|---|---|---|
| Invalid `tenant_id` | HTTP 400 JSON before stream | Error shown in chat, input re-enabled |
| LangGraph exception mid-stream | `event: error` SSE then stream closes | Error appended as system message |
| Network drop | — | `fetch` rejects, error shown, `isStreaming` reset |
| Empty message | 422 FastAPI validation | Prevented client-side (button disabled) |

`isStreaming` always resets to `false` on any error path — UI never gets stuck.

---

## Running

```bash
# Terminal 1 — backend API
cd backend
uvicorn api:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev   # → http://localhost:5173
```
