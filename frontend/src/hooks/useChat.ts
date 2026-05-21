import { useState, useCallback, useRef, useEffect } from 'react'
import { Message } from '../types'

function getOrCreateThreadId(tenant: string): string {
  const threadKey = `jai_thread_id_${tenant}`
  let id = sessionStorage.getItem(threadKey)
  if (!id) {
    id = crypto.randomUUID()
    sessionStorage.setItem(threadKey, id)
  }
  return id
}

export function useChat(tenant: string, userId: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

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
    abortControllerRef.current?.abort()  // cancel any in-flight request
    abortControllerRef.current = abortController

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          user_id: userId,
          tenant_id: tenant,
          thread_id: getOrCreateThreadId(tenant),
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
        buffer = lines.pop() ?? ''  // keep the last incomplete line

        for (const line of lines) {
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
  }, [tenant, userId, isStreaming])

  return { messages, isStreaming, error, sendMessage }
}
