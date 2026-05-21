import { beforeAll, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import ChatWindow from './ChatWindow'
import { Message } from '../types'

beforeAll(() => {
  Element.prototype.scrollIntoView = vi.fn()
})

const userMsg = (id: string, content = 'Hello'): Message => ({
  id,
  role: 'user',
  content,
})

const assistantMsg = (id: string, content = 'Hi there'): Message => ({
  id,
  role: 'assistant',
  content,
})

describe('ChatWindow', () => {
  it('renders "Start the conversation..." when messages is empty', () => {
    render(<ChatWindow messages={[]} isStreaming={false} />)
    expect(screen.getByText('Start the conversation...')).toBeTruthy()
  })

  it('renders one MessageBubble per message', () => {
    const messages: Message[] = [
      userMsg('1', 'Hello'),
      assistantMsg('2', 'Hi'),
      userMsg('3', 'How are you?'),
    ]
    render(<ChatWindow messages={messages} isStreaming={false} />)
    expect(screen.getByText('Hello')).toBeTruthy()
    expect(screen.getByText('Hi')).toBeTruthy()
    expect(screen.getByText('How are you?')).toBeTruthy()
  })

  it('the last assistant message has isLastAssistantMessage true (shows cursor when streaming)', () => {
    const messages: Message[] = [
      userMsg('1'),
      assistantMsg('2', 'First assistant'),
      userMsg('3'),
      assistantMsg('4', 'Last assistant'),
    ]
    render(<ChatWindow messages={messages} isStreaming={true} />)
    // cursor should appear for the last assistant message only
    const cursors = screen.getAllByTestId('cursor')
    expect(cursors).toHaveLength(1)
  })

  it('a non-last assistant message does NOT have isLastAssistantMessage true (no cursor)', () => {
    const messages: Message[] = [
      assistantMsg('1', 'First assistant'),
      userMsg('2'),
      assistantMsg('3', 'Last assistant'),
    ]
    render(<ChatWindow messages={messages} isStreaming={true} />)
    // Only one cursor — on the last assistant, not on the first
    const cursors = screen.getAllByTestId('cursor')
    expect(cursors).toHaveLength(1)
    // Verify cursor is inside the same bubble as "Last assistant", not "First assistant"
    const cursor = cursors[0]
    // The cursor's parent is the bubble div; it should contain "Last assistant"
    expect(cursor.parentElement?.textContent).toContain('Last assistant')
    expect(cursor.parentElement?.textContent).not.toContain('First assistant')
  })

  it('renders successfully with messages (scrollIntoView does not crash)', () => {
    const messages: Message[] = [userMsg('1'), assistantMsg('2')]
    const { container } = render(<ChatWindow messages={messages} isStreaming={false} />)
    expect(container.firstChild).toBeTruthy()
  })
})
