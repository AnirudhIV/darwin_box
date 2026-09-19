import { useEffect, useRef } from 'react'
import type { ChatTurn } from '../types'
import { ChatMessage } from './ChatMessage'

export function ChatThread({ history }: { history: ChatTurn[] }) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history.length])

  return (
    <div className="flex-1 overflow-y-auto space-y-6 px-1 py-4">
      {history.map((turn, i) => (
        <ChatMessage key={i} turn={turn} />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
