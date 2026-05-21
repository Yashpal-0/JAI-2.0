import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'
import { useChat } from './hooks/useChat'

vi.mock('./hooks/useChat', () => ({
  useChat: vi.fn(() => ({
    messages: [],
    isStreaming: false,
    error: null,
    sendMessage: vi.fn(),
  })),
}))

const mockUseChat = vi.mocked(useChat)

beforeEach(() => {
  mockUseChat.mockReturnValue({
    messages: [],
    isStreaming: false,
    error: null,
    sendMessage: vi.fn(),
  })
})

describe('App', () => {
  it('renders the "JAI 2.0" heading', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /JAI 2\.0/i })).toBeInTheDocument()
  })

  it('renders TenantSelector', () => {
    render(<App />)
    expect(screen.getByText('Tenant:')).toBeInTheDocument()
    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })

  it('renders ChatWindow', () => {
    render(<App />)
    // ChatWindow renders an empty-state message when there are no messages
    expect(screen.getByText('Start the conversation...')).toBeInTheDocument()
  })

  it('Send button is disabled when input is empty', () => {
    render(<App />)
    const sendBtn = screen.getByRole('button', { name: /send/i })
    expect(sendBtn).toBeDisabled()
  })

  it('typing in textarea and pressing Enter triggers sendMessage with trimmed text', async () => {
    const sendMessage = vi.fn()
    mockUseChat.mockReturnValue({
      messages: [],
      isStreaming: false,
      error: null,
      sendMessage,
    })

    render(<App />)
    const textarea = screen.getByPlaceholderText(/type a message/i)

    await userEvent.type(textarea, '  hello world  ')
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })

    expect(sendMessage).toHaveBeenCalledWith('hello world')
  })
})
