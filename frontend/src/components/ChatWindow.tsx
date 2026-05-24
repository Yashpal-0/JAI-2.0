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

  return (
    <div className="chat-scroll">
      {messages.length === 0 ? (
        <div className="chat-empty">Start the conversation...</div>
      ) : (
        messages.map((message, index) => (
          <div key={message.id} data-testid="message-bubble" className="message-wrapper">
            <MessageBubble
              message={message}
              isStreaming={isStreaming}
              isLastAssistantMessage={index === lastAssistantIndex}
            />
          </div>
        ))
      )}
      <div ref={bottomRef} />
    </div>
  )
}
