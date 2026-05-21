import { useState } from 'react'
import { TENANTS, Tenant } from './types'
import { useChat } from './hooks/useChat'
import { TenantSelector } from './components/TenantSelector'
import ChatWindow from './components/ChatWindow'

const USER_ID = 'ui_user'

export default function App() {
  const [tenant, setTenant] = useState<Tenant>(TENANTS[0])
  const [inputText, setInputText] = useState('')
  const { messages, isStreaming, error, sendMessage } = useChat(tenant, USER_ID)

  const handleSend = () => {
    const trimmed = inputText.trim()
    if (!trimmed || isStreaming) return
    sendMessage(trimmed)
    setInputText('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        fontFamily: 'sans-serif',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.75rem 1rem',
          borderBottom: '1px solid #ddd',
          background: '#fff',
          flexShrink: 0,
        }}
      >
        <h1 style={{ margin: 0, fontSize: '1.25rem' }}>JAI 2.0</h1>
        <TenantSelector
          value={tenant}
          onChange={setTenant}
          disabled={isStreaming}
        />
      </div>

      {/* Chat area */}
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <ChatWindow messages={messages} isStreaming={isStreaming} />
      </div>

      {/* Error banner */}
      {error !== null && (
        <div
          role="alert"
          style={{
            background: '#ffeeee',
            color: '#cc0000',
            padding: '0.5rem 1rem',
            flexShrink: 0,
          }}
        >
          {error}
        </div>
      )}

      {/* Input row */}
      <div
        style={{
          display: 'flex',
          gap: '0.5rem',
          padding: '0.75rem 1rem',
          borderTop: '1px solid #ddd',
          background: '#fff',
          flexShrink: 0,
        }}
      >
        <textarea
          rows={2}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message…"
          style={{
            flex: 1,
            resize: 'horizontal',
            padding: '0.5rem',
            borderRadius: '4px',
            border: '1px solid #ccc',
            fontSize: '1rem',
            fontFamily: 'inherit',
          }}
        />
        <button
          onClick={handleSend}
          disabled={isStreaming || inputText.trim() === ''}
          style={{
            padding: '0.5rem 1.25rem',
            borderRadius: '4px',
            border: 'none',
            background: '#0066cc',
            color: '#fff',
            fontSize: '1rem',
            cursor: isStreaming || inputText.trim() === '' ? 'not-allowed' : 'pointer',
            opacity: isStreaming || inputText.trim() === '' ? 0.6 : 1,
          }}
        >
          Send
        </button>
      </div>
    </div>
  )
}
