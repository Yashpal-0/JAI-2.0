import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import MessageBubble from './MessageBubble'
import type { Message } from '../types'

const userMessage: Message = { id: '1', role: 'user', content: 'Hello!' }
const assistantMessage: Message = { id: '2', role: 'assistant', content: 'Hi there!' }

describe('MessageBubble', () => {
  it('renders user message right-aligned', () => {
    const { container } = render(
      <MessageBubble message={userMessage} isLastAssistantMessage={false} isStreaming={false} />
    )
    const wrapper = container.firstChild as HTMLElement
    expect(wrapper.style.justifyContent).toBe('flex-end')
  })

  it('renders assistant message left-aligned', () => {
    const { container } = render(
      <MessageBubble message={assistantMessage} isLastAssistantMessage={false} isStreaming={false} />
    )
    const wrapper = container.firstChild as HTMLElement
    expect(wrapper.style.justifyContent).toBe('flex-start')
  })

  it('shows blinking cursor when isLastAssistantMessage and isStreaming', () => {
    render(
      <MessageBubble message={assistantMessage} isLastAssistantMessage={true} isStreaming={true} />
    )
    expect(screen.getByTestId('cursor')).toBeInTheDocument()
  })

  it('does not show cursor when isStreaming is false', () => {
    render(
      <MessageBubble message={assistantMessage} isLastAssistantMessage={true} isStreaming={false} />
    )
    expect(screen.queryByTestId('cursor')).not.toBeInTheDocument()
  })

  it('does not show cursor on user messages even when isStreaming is true', () => {
    render(
      <MessageBubble message={userMessage} isLastAssistantMessage={false} isStreaming={true} />
    )
    expect(screen.queryByTestId('cursor')).not.toBeInTheDocument()
  })
})
