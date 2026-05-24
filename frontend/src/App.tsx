import { useState, useCallback, useEffect } from 'react'
import { TENANTS, Tenant, Thread } from './types'
import { useChat } from './hooks/useChat'
import { TenantSelector } from './components/TenantSelector'
import ChatWindow from './components/ChatWindow'
import Sidebar from './components/Sidebar'

const USER_ID = 'ui_user'

async function apiFetchThreads(userId: string, tenantId: string): Promise<Thread[]> {
  try {
    const res = await fetch(`/threads?user_id=${encodeURIComponent(userId)}&tenant_id=${encodeURIComponent(tenantId)}`)
    if (!res.ok) return []
    return res.json()
  } catch { return [] }
}

async function apiDeleteThread(threadId: string, userId: string): Promise<void> {
  await fetch(`/threads/${threadId}?user_id=${encodeURIComponent(userId)}`, { method: 'DELETE' })
}

export default function App() {
  const [tenant, setTenant] = useState<Tenant>(TENANTS[0])
  const [inputText, setInputText] = useState('')
  const [threads, setThreads] = useState<Thread[]>([])
  const [currentId, setCurrentId] = useState<string>(() => crypto.randomUUID())

  const { messages, isStreaming, error, sendMessage } = useChat(tenant, USER_ID, currentId)

  // Load thread list from backend on mount and when tenant changes
  useEffect(() => {
    apiFetchThreads(USER_ID, tenant).then(data => {
      setThreads(data)
      if (data.length > 0 && !data.find(t => t.id === currentId)) {
        setCurrentId(data[0].id)
      }
    })
  }, [tenant])

  const handleSend = () => {
    const trimmed = inputText.trim()
    if (!trimmed || isStreaming) return

    // Optimistically add thread to sidebar on first message
    if (messages.length === 0) {
      const title = trimmed.length > 60 ? trimmed.slice(0, 60) + '…' : trimmed
      const newThread: Thread = { id: currentId, title, createdAt: Date.now(), updatedAt: Date.now() }
      setThreads(prev => [newThread, ...prev.filter(t => t.id !== currentId)])
    }

    sendMessage(trimmed)
    setInputText('')
  }

  const handleNewChat = useCallback(() => {
    setCurrentId(crypto.randomUUID())
    setInputText('')
  }, [])

  const handleSwitchThread = useCallback((id: string) => {
    setCurrentId(id)
    setInputText('')
  }, [])

  const handleDeleteThread = useCallback(async (id: string) => {
    await apiDeleteThread(id, USER_ID)
    localStorage.removeItem(`jai_msgs_${id}`)
    const remaining = threads.filter(t => t.id !== id)
    setThreads(remaining)
    if (id === currentId) {
      setCurrentId(remaining[0]?.id ?? crypto.randomUUID())
    }
  }, [currentId, threads])

  const isDisabled = isStreaming || inputText.trim() === ''

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <>
      <div className="aurora-bg" aria-hidden="true">
        <div className="aurora-orb aurora-orb-1" />
        <div className="aurora-orb aurora-orb-2" />
        <div className="aurora-orb aurora-orb-3" />
      </div>

      <div className="app-root">
        <Sidebar
          threads={threads}
          currentId={currentId}
          onSelect={handleSwitchThread}
          onNewChat={handleNewChat}
          onDelete={handleDeleteThread}
        />

        <div className="main-area">
          <header className="app-header">
            <h1 className="app-title">JAI 2.0</h1>
            <TenantSelector value={tenant} onChange={setTenant} disabled={isStreaming} />
          </header>

          {error !== null && (
            <div role="alert" className="error-banner">
              {error}
            </div>
          )}

          <div className="chat-panel">
            <ChatWindow messages={messages} isStreaming={isStreaming} />

            <div className="input-area">
              <div className="input-row">
                <div className="textarea-shell">
                  <textarea
                    rows={2}
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Type a message…"
                    className="chat-textarea"
                  />
                </div>
                <button onClick={handleSend} disabled={isDisabled} className="send-btn">
                  Send
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
