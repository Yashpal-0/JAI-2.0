import { Message } from '../types'

interface Props {
  message: Message
  isLastAssistantMessage: boolean
  isStreaming: boolean
}

export default function MessageBubble({ message, isLastAssistantMessage, isStreaming }: Props) {
  const isUser = message.role === 'user'
  const showCursor = !isUser && isLastAssistantMessage && isStreaming

  const wrapperStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: isUser ? 'flex-end' : 'flex-start',
    marginBottom: '8px',
  }

  const bubbleStyle: React.CSSProperties = {
    maxWidth: '70%',
    padding: '10px 14px',
    borderRadius: '18px',
    backgroundColor: isUser ? '#0084ff' : '#f0f0f0',
    color: isUser ? '#ffffff' : '#1a1a1a',
    textAlign: isUser ? 'right' : 'left',
    wordBreak: 'break-word',
  }

  const cursorStyle: React.CSSProperties = {
    display: 'inline-block',
    animation: 'blink 1s step-end infinite',
    marginLeft: '1px',
  }

  return (
    <div style={wrapperStyle}>
      <div style={bubbleStyle}>
        {message.content}
        {showCursor && <span data-testid="cursor" style={cursorStyle}>▋</span>}
      </div>
    </div>
  )
}
