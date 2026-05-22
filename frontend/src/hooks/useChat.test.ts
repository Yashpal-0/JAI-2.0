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

    const { result } = renderHook(() => useChat('zerostic.com', 'test_user'))

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

    const { result } = renderHook(() => useChat('zerostic.com', 'test_user'))

    await act(async () => {
      await result.current.sendMessage('Hi')
    })

    expect(result.current.error).toBe('Invalid tenant_id: evil.com')
    expect(result.current.isStreaming).toBe(false)
  })
})
