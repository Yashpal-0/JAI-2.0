import { useState, useCallback, useRef, useEffect } from 'react'
import { Message } from '../types'

const msgKey = (id: string) => `jai_msgs_${id}`

function cacheMessages(threadId: string, messages: Message[]) {
  if (messages.length > 0) localStorage.setItem(msgKey(threadId), JSON.stringify(messages))
}

function getCached(threadId: string): Message[] | null {
  try {
    const raw = localStorage.getItem(msgKey(threadId))
    if (!raw) return null
    return JSON.parse(raw)
  } catch { return null }
}

async function fetchMessages(threadId: string, userId: string, tenantId: string): Promise<Message[]> {
  try {
    const res = await fetch(`/threads/${threadId}/messages?user_id=${encodeURIComponent(userId)}&tenant_id=${encodeURIComponent(tenantId)}`)
    if (!res.ok) return []
    const data: { role: string; content: string }[] = await res.json()
    return data.map(m => ({ id: crypto.randomUUID(), role: m.role as Message['role'], content: m.content }))
  } catch { return [] }
}

export function useChat(tenant: string, userId: string, threadId: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  // Switch thread: abort in-flight, load from cache or backend
  useEffect(() => {
    abortControllerRef.current?.abort()
    setIsStreaming(false)
    setError(null)

    const cached = getCached(threadId)
    if (cached) {
      setMessages(cached)
    } else {
      setMessages([])
      fetchMessages(threadId, userId, tenant).then(msgs => {
        if (msgs.length > 0) {
          setMessages(msgs)
          cacheMessages(threadId, msgs)
        }
      })
    }
  }, [threadId, userId])

  // Keep localStorage cache in sync
  useEffect(() => {
    cacheMessages(threadId, messages)
  }, [messages, threadId])

  useEffect(() => {
    return () => { abortControllerRef.current?.abort() }
  }, [])

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isStreaming) return

    setError(null)
    const userMsg: Message = { id: crypto.randomUUID(), role: 'user', content: text }
    const assistantMsg: Message = { id: crypto.randomUUID(), role: 'assistant', content: '' }
    setMessages(prev => [...prev, userMsg, assistantMsg])
    setIsStreaming(true)

    const abortController = new AbortController()
    abortControllerRef.current?.abort()
    abortControllerRef.current = abortController

    try {
      const isFirst = messages.length === 0
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          user_id: userId,
          tenant_id: tenant,
          thread_id: threadId,
          title: isFirst ? text.slice(0, 60) : '',
        }),
        signal: abortController.signal,
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail ?? 'Request failed')
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let isErrorEvent = false
      let buffer = ''

      outer: while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (line === 'event: error') {
            isErrorEvent = true
          } else if (line.startsWith('data: ')) {
            const data = line.slice(6).replace(/\\n/g, '\n')
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
            if (data) {
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
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return
      const msg = err instanceof Error ? err.message : 'Unknown error'
      setError(msg)
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = { ...updated[updated.length - 1], content: `[Error: ${msg}]` }
        return updated
      })
    } finally {
      setIsStreaming(false)
    }
  }, [tenant, userId, threadId, isStreaming, messages.length])

  return { messages, isStreaming, error, sendMessage }
}
