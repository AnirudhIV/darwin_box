import type { AskResponse, UploadResponse } from './types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function parseOrThrow(res: Response) {
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(body.detail ?? body.error ?? `Request failed (${res.status})`)
  }
  return body
}

export async function uploadFiles(
  files: File[],
  sessionId: string | null,
): Promise<UploadResponse> {
  const form = new FormData()
  for (const file of files) form.append('files', file)
  if (sessionId) form.append('session_id', sessionId)

  const res = await fetch(`${BASE_URL}/api/upload`, { method: 'POST', body: form })
  return parseOrThrow(res)
}

export async function getTables(sessionId: string): Promise<{ tables: UploadResponse['tables'] }> {
  const res = await fetch(`${BASE_URL}/api/tables?session_id=${encodeURIComponent(sessionId)}`)
  return parseOrThrow(res)
}

export async function askQuestion(sessionId: string, question: string): Promise<AskResponse> {
  const res = await fetch(`${BASE_URL}/api/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, question }),
  })
  return parseOrThrow(res)
}
