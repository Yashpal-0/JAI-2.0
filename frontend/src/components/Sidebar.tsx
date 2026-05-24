import { Thread } from '../types'

interface Props {
  threads: Thread[]
  currentId: string
  onSelect: (id: string) => void
  onNewChat: () => void
  onDelete: (id: string) => void
}

function timeAgo(ts: number): string {
  const diff = Date.now() - ts
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

export default function Sidebar({ threads, currentId, onSelect, onNewChat, onDelete }: Props) {
  return (
    <aside className="sidebar">
      <button className="new-chat-btn" onClick={onNewChat}>+ New Chat</button>
      <div className="thread-list">
        {threads.map(t => (
          <div
            key={t.id}
            className={`thread-item${t.id === currentId ? ' thread-item-active' : ''}`}
            onClick={() => onSelect(t.id)}
          >
            <div className="thread-info">
              <span className="thread-title">{t.title}</span>
              <span className="thread-time">{timeAgo(t.updatedAt)}</span>
            </div>
            <button
              className="thread-delete"
              onClick={e => { e.stopPropagation(); onDelete(t.id) }}
              aria-label="Delete conversation"
            >×</button>
          </div>
        ))}
        {threads.length === 0 && (
          <p className="sidebar-empty">No conversations yet</p>
        )}
      </div>
    </aside>
  )
}
