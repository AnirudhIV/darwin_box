import { useCallback, useState } from 'react'

const STORAGE_KEY = 'data-qa-session-id'

export function useSession() {
  const [sessionId, setSessionIdState] = useState<string | null>(() => {
    try {
      return localStorage.getItem(STORAGE_KEY)
    } catch {
      return null
    }
  })

  const setSessionId = useCallback((id: string) => {
    setSessionIdState(id)
    try {
      localStorage.setItem(STORAGE_KEY, id)
    } catch {
      // ignore storage failures (private browsing, etc.)
    }
  }, [])

  const clearSession = useCallback(() => {
    setSessionIdState(null)
    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch {
      // ignore
    }
  }, [])

  return { sessionId, setSessionId, clearSession }
}
