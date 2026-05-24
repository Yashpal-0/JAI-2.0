import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Message } from '../types'

interface Props {
  message: Message
  isLastAssistantMessage: boolean
  isStreaming: boolean
}

const STEP_RE = /\*{0,2}\[Step\s*(\d+)\/(\d+)\]\*{0,2}/i

function parseStep(content: string): { current: number; total: number; clean: string } | null {
  const m = content.match(STEP_RE)
  if (!m) return null
  return {
    current: parseInt(m[1], 10),
    total: parseInt(m[2], 10),
    clean: content.replace(STEP_RE, '').replace(/^\s*\n/, '').trim(),
  }
}

function StepProgress({ current, total }: { current: number; total: number }) {
  return (
    <div className="step-progress">
      <div className="step-bar">
        {Array.from({ length: total }, (_, i) => (
          <div
            key={i}
            className={`step-seg ${i < current ? 'step-done' : i === current - 1 ? 'step-active' : 'step-pending'}`}
          />
        ))}
      </div>
      <span className="step-label">Step {current} of {total}</span>
    </div>
  )
}

export default function MessageBubble({ message, isLastAssistantMessage, isStreaming }: Props) {
  const isUser = message.role === 'user'
  const showCursor = !isUser && isLastAssistantMessage && isStreaming

  // inline justifyContent required by tests (container.firstChild.style.justifyContent)
  const wrapperStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: isUser ? 'flex-end' : 'flex-start',
  }

  if (isUser) {
    return (
      <div style={wrapperStyle}>
        <div className="bubble-user">{message.content}</div>
      </div>
    )
  }

  const step = parseStep(message.content)
  const displayContent = step ? step.clean : message.content

  return (
    <div style={wrapperStyle}>
      <div className="bubble-ai-row">
        <div className="avatar">JAI</div>
        <div className="bubble-ai">
          {step && <StepProgress current={step.current} total={step.total} />}
          <div className="markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayContent}</ReactMarkdown>
            {showCursor && <span data-testid="cursor" className="streaming-cursor">▋</span>}
          </div>
        </div>
      </div>
    </div>
  )
}
