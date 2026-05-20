# Frontend Chat UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a React (Vite) chat UI at `frontend/` and a FastAPI SSE server at `backend/api.py` that bridges the LangGraph orchestrator to the browser.

**Architecture:** FastAPI on :8000 exposes `POST /chat` which streams LangGraph `astream` output as Server-Sent Events. React (Vite) app on :5173 proxies `/chat` to the backend, renders a scrollable chat window with a tenant selector, and appends AI tokens into message bubbles as they arrive via `fetch` + `ReadableStream`.

**Tech Stack:** FastAPI, uvicorn, httpx (backend); React 18, Vite 5, TypeScript, Vitest, @testing-library/react (frontend)

---

## File Map

**Backend:**
- Modify: `backend/requirements.txt` — add fastapi, uvicorn[standard], httpx
- Create: `backend/api.py` — FastAPI app, CORS, `POST /chat` SSE endpoint
- Create: `backend/tests/test_api.py` — test invalid tenant → 400

**Frontend (all new under `frontend/`):**
- `package.json`
- `vite.config.ts` — proxy `/chat` → localhost:8000; vitest config
- `tsconfig.json`
- `index.html`
- `src/main.tsx`
- `src/index.css`
- `src/types.ts` — `Message` interface, `TENANTS` constant, `Tenant` type
- `src/hooks/useChat.ts` — message state, SSE fetch stream, thread_id
- `src/hooks/useChat.test.ts` — vitest hook test with mocked fetch
- `src/components/TenantSelector.tsx`
- `src/components/MessageBubble.tsx`
- `src/components/ChatWindow.tsx`
- `src/App.tsx`

---

### Task 1: Backend API server

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/api.py`
- Create: `backend/tests/test_api.py`

- [ ] **Step 1: Add new dependencies to backend/requirements.txt**

Append these three lines to the existing `backend/requirements.txt`:
```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
httpx>=0.27.0
```

- [ ] **Step 2: Install new dependencies**

```bash
cd backend && pip install fastapi "uvicorn[standard]" httpx
```
Expected: packages install without error.

- [ ] **Step 3: Write the failing test**

Create `backend/tests/test_api.py`:
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock
from fastapi.testclient import TestClient


def test_chat_invalid_tenant():
    import api
    api.app.dependency_overrides[api.get_graph] = lambda: MagicMock()
    client = TestClient(api.app)
    response = client.post("/chat", json={
        "message": "hello",
        "user_id": "test_user",
        "tenant_id": "evil.com",
        "thread_id": "test-thread-001",
    })
    api.app.dependency_overrides.clear()
    assert response.status_code == 400
    assert "Invalid tenant_id" in response.json()["detail"]
```

- [ ] **Step 4: Run test to confirm it fails**

```bash
cd backend && pytest tests/test_api.py -v
```
Expected: `ModuleNotFoundError: No module named 'api'` — `api.py` does not exist yet.

- [ ] **Step 5: Create backend/api.py**

```python
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
```

- [ ] **Step 6: Run test to confirm it passes**

```bash
cd backend && pytest tests/test_api.py -v
```
Expected: `test_chat_invalid_tenant` PASS.

- [ ] **Step 7: Smoke test the server starts**

```bash
cd backend && uvicorn api:app --port 8000
```
Expected: logs `Application startup complete.` (Ctrl+C to stop).

- [ ] **Step 8: Commit**

```bash
git add backend/requirements.txt backend/api.py backend/tests/test_api.py
git commit -m "feat: add fastapi sse chat endpoint"
```

---

### Task 2: Frontend scaffold

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/index.css`
- Create: `frontend/src/App.tsx` (placeholder)

- [ ] **Step 1: Create frontend/package.json**

```json
{
  "name": "jai-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.1",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.1",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.5.2",
    "jsdom": "^24.1.1",
    "typescript": "^5.5.3",
    "vite": "^5.4.2",
    "vitest": "^2.0.5"
  }
}
```

- [ ] **Step 2: Create frontend/vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/chat': 'http://localhost:8000',
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
```

- [ ] **Step 3: Create frontend/tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true
  },
  "include": ["src"]
}
```

- [ ] **Step 4: Create frontend/index.html**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>JAI 2.0</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 5: Create frontend/src/index.css**

```css
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f5f5;
  color: #1a1a1a;
  height: 100vh;
}

#root {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
```

- [ ] **Step 6: Create frontend/src/main.tsx**

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

- [ ] **Step 7: Create placeholder frontend/src/App.tsx**

```tsx
export default function App() {
  return <div style={{ padding: 24 }}>JAI 2.0 loading…</div>
}
```

- [ ] **Step 8: Install and verify dev server**

```bash
cd frontend && npm install && npm run dev
```
Expected: Vite starts at `http://localhost:5173`. Browser shows "JAI 2.0 loading…".

- [ ] **Step 9: Commit**

```bash
cd .. && git add frontend/
git commit -m "feat: scaffold react vite frontend"
```

---

### Task 3: types.ts and useChat hook

**Files:**
- Create: `frontend/src/types.ts`
- Create: `frontend/src/hooks/useChat.ts`
- Create: `frontend/src/hooks/useChat.test.ts`

- [ ] **Step 1: Create frontend/src/types.ts**

```typescript
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export const TENANTS = [
  'studio.zerostic.com',
  'pm.zerostic.com',
  'dev.zerostic.com',
] as const

export type Tenant = typeof TENANTS[number]
```

- [ ] **Step 2: Write the failing test**

Create `frontend/src/hooks/useChat.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useChat } from './useChat'

function mockFetchStream(lines: string[]) {
  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    start(controller) {
      for (const line of lines) {
        controller.enqueue(encoder.encode(line))
      }
      controller.close()
    },
  })
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, body: stream }))
}

beforeEach(() => {
  vi.unstubAllGlobals()
  sessionStorage.clear()
})

describe('useChat', () => {
  it('appends user message and streams assistant tokens', async () => {
    mockFetchStream([
      'data: Hello\n\n',
      'data:  world\n\n',
      'data: [DONE]\n\n',
    ])

    const { result } = renderHook(() => useChat('studio.zerostic.com', 'test_user'))

    await act(async () => {
      await result.current.sendMessage('Hi')
    })

    expect(result.current.messages).toHaveLength(2)
    expect(result.current.messages[0]).toMatchObject({ role: 'user', content: 'Hi' })
    expect(result.current.messages[1]).toMatchObject({ role: 'assistant', content: 'Hello world' })
    expect(result.current.isStreaming).toBe(false)
  })

  it('sets error on non-ok response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Invalid tenant_id: evil.com' }),
    }))

    const { result } = renderHook(() => useChat('studio.zerostic.com', 'test_user'))

    await act(async () => {
      await result.current.sendMessage('Hi')
    })

    expect(result.current.error).toBe('Invalid tenant_id: evil.com')
    expect(result.current.isStreaming).toBe(false)
  })
})
```

- [ ] **Step 3: Run test to confirm it fails**

```bash
cd frontend && npm test
```
Expected: `Cannot find module './useChat'`.

- [ ] **Step 4: Create frontend/src/hooks/useChat.ts**

```typescript
import { useState, useCallback } from 'react'
import { Message } from '../types'

function getOrCreateThreadId(): string {
  const key = 'jai_thread_id'
  let id = sessionStorage.getItem(key)
  if (!id) {
    id = crypto.randomUUID()
    sessionStorage.setItem(key, id)
  }
  return id
}

export function useChat(tenant: string, userId: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isStreaming) return

    setError(null)
    const userMsg: Message = { id: crypto.randomUUID(), role: 'user', content: text }
    const assistantMsg: Message = { id: crypto.randomUUID(), role: 'assistant', content: '' }
    setMessages(prev => [...prev, userMsg, assistantMsg])
    setIsStreaming(true)

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          user_id: userId,
          tenant_id: tenant,
          thread_id: getOrCreateThreadId(),
        }),
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail ?? 'Request failed')
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let isErrorEvent = false

      outer: while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const raw = decoder.decode(value, { stream: true })
        for (const line of raw.split('\n')) {
          if (line === 'event: error') {
            isErrorEvent = true
          } else if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') break outer
            if (isErrorEvent) {
              setError(data)
              setMessages(prev => {
                const updated = [...prev]
                updated[updated.length - 1] = { ...updated[updated.length - 1], content: `[Error: ${data}]` }
                return updated
              })
              break outer
            }
            if (data.trim()) {
              setMessages(prev => {
                const updated = [...prev]
                const last = updated[updated.length - 1]
                updated[updated.length - 1] = { ...last, content: last.content + data }
                return updated
              })
            }
          }
        }
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Unknown error'
      setError(msg)
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = { ...updated[updated.length - 1], content: `[Error: ${msg}]` }
        return updated
      })
    } finally {
      setIsStreaming(false)
    }
  }, [tenant, userId, isStreaming])

  return { messages, isStreaming, error, sendMessage }
}
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
cd frontend && npm test
```
Expected: both `useChat` tests PASS.

- [ ] **Step 6: Commit**

```bash
cd .. && git add frontend/src/types.ts frontend/src/hooks/
git commit -m "feat: add Message types and useChat SSE hook"
```

---

### Task 4: TenantSelector component

**Files:**
- Create: `frontend/src/components/TenantSelector.tsx`

- [ ] **Step 1: Create frontend/src/components/TenantSelector.tsx**

```tsx
import { TENANTS, Tenant } from '../types'

interface Props {
  value: Tenant
  onChange: (tenant: Tenant) => void
  disabled: boolean
}

export function TenantSelector({ value, onChange, disabled }: Props) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <label htmlFor="tenant-select" style={{ fontSize: '13px', color: '#666', fontWeight: 500 }}>
        Tenant:
      </label>
      <select
        id="tenant-select"
        value={value}
        onChange={e => onChange(e.target.value as Tenant)}
        disabled={disabled}
        style={{
          padding: '4px 8px',
          borderRadius: '6px',
          border: '1px solid #ddd',
          fontSize: '13px',
          background: disabled ? '#f9f9f9' : 'white',
          cursor: disabled ? 'not-allowed' : 'pointer',
        }}
      >
        {TENANTS.map(t => (
          <option key={t} value={t}>{t}</option>
        ))}
      </select>
    </div>
  )
}
```

- [ ] **Step 2: Verify no TypeScript errors**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
cd .. && git add frontend/src/components/TenantSelector.tsx
git commit -m "feat: add TenantSelector component"
```

---

### Task 5: MessageBubble component

**Files:**
- Create: `frontend/src/components/MessageBubble.tsx`

- [ ] **Step 1: Create frontend/src/components/MessageBubble.tsx**

```tsx
import { Message } from '../types'

interface Props {
  message: Message
  isLast: boolean
  isStreaming: boolean
}

export function MessageBubble({ message, isLast, isStreaming }: Props) {
  const isUser = message.role === 'user'
  const showCursor = isLast && !isUser && isStreaming

  return (
    <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', marginBottom: '12px' }}>
      <div
        style={{
          maxWidth: '72%',
          padding: '10px 14px',
          borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
          background: isUser ? '#0070f3' : 'white',
          color: isUser ? 'white' : '#1a1a1a',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          fontSize: '14px',
          lineHeight: '1.5',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {message.content || (showCursor ? '' : '…')}
        {showCursor && (
          <span style={{ animation: 'blink 1s step-end infinite' }}>▋</span>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify no TypeScript errors**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
cd .. && git add frontend/src/components/MessageBubble.tsx
git commit -m "feat: add MessageBubble component"
```

---

### Task 6: ChatWindow component

**Files:**
- Create: `frontend/src/components/ChatWindow.tsx`

- [ ] **Step 1: Create frontend/src/components/ChatWindow.tsx**

```tsx
import { useEffect, useRef } from 'react'
import { Message } from '../types'
import { MessageBubble } from './MessageBubble'

interface Props {
  messages: Message[]
  isStreaming: boolean
}

export function ChatWindow({ messages, isStreaming }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#aaa',
        fontSize: '14px',
      }}>
        Send a message to start the conversation.
      </div>
    )
  }

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
      {messages.map((msg, i) => (
        <MessageBubble
          key={msg.id}
          message={msg}
          isLast={i === messages.length - 1}
          isStreaming={isStreaming}
        />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
```

- [ ] **Step 2: Verify no TypeScript errors**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 3: Commit**

```bash
cd .. && git add frontend/src/components/ChatWindow.tsx
git commit -m "feat: add ChatWindow with auto-scroll"
```

---

### Task 7: App.tsx — wire everything together

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Rewrite frontend/src/App.tsx**

```tsx
import { useState, useRef, KeyboardEvent } from 'react'
import { Tenant, TENANTS } from './types'
import { useChat } from './hooks/useChat'
import { TenantSelector } from './components/TenantSelector'
import { ChatWindow } from './components/ChatWindow'

const USER_ID = 'ui_user'

export default function App() {
  const [tenant, setTenant] = useState<Tenant>(TENANTS[0])
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const { messages, isStreaming, error, sendMessage } = useChat(tenant, USER_ID)

  const handleSend = () => {
    const text = input.trim()
    if (!text || isStreaming) return
    setInput('')
    sendMessage(text)
    textareaRef.current?.focus()
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{
        padding: '12px 16px',
        borderBottom: '1px solid #e5e5e5',
        background: 'white',
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        flexShrink: 0,
      }}>
        <span style={{ fontWeight: 700, fontSize: '16px' }}>JAI 2.0</span>
        <TenantSelector value={tenant} onChange={setTenant} disabled={isStreaming} />
      </div>

      {/* Messages */}
      <ChatWindow messages={messages} isStreaming={isStreaming} />

      {/* Error banner */}
      {error && (
        <div style={{
          padding: '8px 16px',
          background: '#fff0f0',
          color: '#c00',
          fontSize: '13px',
          borderTop: '1px solid #fcc',
          flexShrink: 0,
        }}>
          {error}
        </div>
      )}

      {/* Input row */}
      <div style={{
        padding: '12px 16px',
        borderTop: '1px solid #e5e5e5',
        background: 'white',
        display: 'flex',
        gap: '8px',
        alignItems: 'flex-end',
        flexShrink: 0,
      }}>
        <textarea
          ref={textareaRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Message JAI… (Enter to send, Shift+Enter for newline)"
          disabled={isStreaming}
          rows={1}
          style={{
            flex: 1,
            resize: 'none',
            padding: '10px 14px',
            borderRadius: '12px',
            border: '1px solid #ddd',
            fontSize: '14px',
            lineHeight: '1.5',
            outline: 'none',
            fontFamily: 'inherit',
          }}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || isStreaming}
          style={{
            padding: '10px 20px',
            borderRadius: '12px',
            border: 'none',
            background: (!input.trim() || isStreaming) ? '#ccc' : '#0070f3',
            color: 'white',
            fontWeight: 600,
            fontSize: '14px',
            cursor: (!input.trim() || isStreaming) ? 'not-allowed' : 'pointer',
            flexShrink: 0,
          }}
        >
          {isStreaming ? '…' : 'Send'}
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Run TypeScript check**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 3: Run all frontend tests**

```bash
npm test
```
Expected: 2 tests PASS.

- [ ] **Step 4: Verify UI in browser**

With `npm run dev` running: open `http://localhost:5173`.
Expected: header with "JAI 2.0" + tenant selector, empty state showing "Send a message…", input box and Send button.

- [ ] **Step 5: Commit**

```bash
cd .. && git add frontend/src/App.tsx
git commit -m "feat: add App layout, wire TenantSelector and ChatWindow"
```

---

### Task 8: Manual integration test

**Files:** None — manual verification only.

- [ ] **Step 1: Start the backend**

Terminal 1, from repo root:
```bash
cd backend && uvicorn api:app --reload --port 8000
```
Expected: `Application startup complete.` (model loads on first request).

- [ ] **Step 2: Start the frontend**

Terminal 2, from repo root:
```bash
cd frontend && npm run dev
```
Expected: Vite at `http://localhost:5173`.

- [ ] **Step 3: Send first message**

Open `http://localhost:5173`. Type "Hello, what can you help me with?" and press Enter.
Expected: user bubble appears right-aligned, assistant bubble appears left-aligned, tokens stream in as they arrive, blinking cursor visible during streaming.

- [ ] **Step 4: Verify multi-turn memory**

Send a follow-up: "What did I just ask you?"
Expected: assistant references the previous message content (MemorySaver thread active).

- [ ] **Step 5: Verify PM routing**

Select `pm.zerostic.com` from the tenant dropdown. Send "Scope a web project with a 5000 budget."
Expected: orchestrator routes to PM agent, response includes scoping content.

- [ ] **Step 6: Verify error display**

Stop the backend (Ctrl+C). Send another message.
Expected: error banner shows a connection error, input re-enabled.

- [ ] **Step 7: Commit any fixes needed**

If any issues were fixed during testing:
```bash
git add -p
git commit -m "fix: integration test corrections"
```
