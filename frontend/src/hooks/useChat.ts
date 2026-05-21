import { useState, useCallback } from 'react'
import { Message } from '../types'

function getOrCreateThreadId(): string {
  const key = 'jai_thread_id'
  let id = sessionStorage.getItem(key)
  if (!id) {
    id = crypto.randomUUID()
    sessionStorage.setItem(key, id)
  }
  return id
}

export function useChat(tenant: string, userId: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isStreaming) return

    setError(null)
    const userMsg: Message = { id: crypto.randomUUID(), role: 'user', content: text }
    const assistantMsg: Message = { id: crypto.randomUUID(), role: 'assistant', content: '' }
    setMessages(prev => [...prev, userMsg, assistantMsg])
    setIsStreaming(true)

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          user_id: userId,
          tenant_id: tenant,
          thread_id: getOrCreateThreadId(),
        }),
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail ?? 'Request failed')
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let isErrorEvent = false

      outer: while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const raw = decoder.decode(value, { stream: true })
        for (const line of raw.split('\n')) {
          if (line === 'event: error') {
            isErrorEvent = true
          } else if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') break outer
            if (isErrorEvent) {
              setError(data)
              setMessages(prev => {
                const updated = [...prev]
                updated[updated.length - 1] = { ...updated[updated.length - 1], content: `[Error: ${data}]` }
                return updated
              })
              break outer
            }
            if (data.trim()) {
              setMessages(prev => {
                const updated = [...prev]
                const last = updated[updated.length - 1]
                updated[updated.length - 1] = { ...last, content: last.content + data }
                return updated
              })
            }
          }
        }
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Unknown error'
      setError(msg)
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = { ...updated[updated.length - 1], content: `[Error: ${msg}]` }
        return updated
      })
    } finally {
      setIsStreaming(false)
    }
  }, [tenant, userId, isStreaming])

  return { messages, isStreaming, error, sendMessage }
}
