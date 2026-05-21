import { useEffect, useRef } from 'react'
import { Message } from '../types'
import MessageBubble from './MessageBubble'

interface Props {
  messages: Message[]
  isStreaming: boolean
}

export default function ChatWindow({ messages, isStreaming }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const lastAssistantIndex = (() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'assistant') return i
    }
    return -1
  })()

  const containerStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    overflowY: 'auto',
    flex: 1,
    padding: '16px',
  }

  const emptyStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    flex: 1,
    color: '#888',
    fontSize: '16px',
  }

  if (messages.length === 0) {
    return (
      <div style={containerStyle}>
        <div style={emptyStyle}>Start the conversation...</div>
      </div>
    )
  }

  return (
    <div style={containerStyle}>
      {messages.map((message, index) => (
        <MessageBubble
          key={message.id}
          message={message}
          isStreaming={isStreaming}
          isLastAssistantMessage={index === lastAssistantIndex}
        />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
