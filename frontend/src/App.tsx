import { ChartBar } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { askQuestion, getTables, removeTable, uploadFiles } from './api'
import { ChatInput } from './components/ChatInput'
import { ChatThread } from './components/ChatThread'
import { FileUploader } from './components/FileUploader'
import { TableList } from './components/TableList'
import { useSession } from './hooks/useSession'
import type { ChatTurn, TableSummary } from './types'

export default function App() {
  const { sessionId, setSessionId, clearSession } = useSession()
  const [tables, setTables] = useState<TableSummary[]>([])
  const [history, setHistory] = useState<ChatTurn[]>([])
  const [uploading, setUploading] = useState(false)
  const [asking, setAsking] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) return
    getTables(sessionId)
      .then((res) => setTables(res.tables))
      .catch(() => {
        // session expired server-side (e.g. backend restarted) - reset silently
        clearSession()
        setTables([])
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleFiles = async (files: File[]) => {
    setUploading(true)
    setError(null)
    try {
      const res = await uploadFiles(files, sessionId)
      setSessionId(res.session_id)
      setTables(res.tables)
      if (res.errors.length > 0) {
        setError(res.errors.map((e) => `${e.filename}: ${e.error}`).join('; '))
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  const handleAsk = async (question: string) => {
    if (!sessionId) return
    setAsking(true)
    try {
      const res = await askQuestion(sessionId, question)
      setHistory((h) => [...h, { question, ...res }])
    } catch (e) {
      setHistory((h) => [
        ...h,
        {
          question,
          sql: null,
          columns: [],
          rows: [],
          is_scalar: false,
          chart: null,
          error: e instanceof Error ? e.message : 'Something went wrong.',
          attempts: 0,
        },
      ])
    } finally {
      setAsking(false)
    }
  }

  const handleRemoveTable = async (tableName: string) => {
    if (!sessionId) return
    try {
      const res = await removeTable(sessionId, tableName)
      setTables(res.tables)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to remove table.')
    }
  }

  const handleClear = () => {
    clearSession()
    setTables([])
    setHistory([])
    setError(null)
  }

  return (
    <div className="h-screen flex bg-neutral-50">
      <aside className="w-80 shrink-0 border-r border-neutral-200 bg-white p-4 flex flex-col gap-4 overflow-y-auto">
        <div>
          <h1 className="text-lg font-semibold text-neutral-900 flex items-center gap-2">
            <ChartBar size={20} weight="bold" className="text-blue-600" /> Data Q&A
          </h1>
          <p className="text-xs text-neutral-500 mt-1">Upload CSV/Excel files, then ask questions.</p>
        </div>

        <FileUploader onFiles={handleFiles} disabled={uploading} />
        {uploading && <p className="text-xs text-neutral-400">Uploading...</p>}
        {error && <p className="text-xs text-red-600">{error}</p>}

        <TableList tables={tables} onRemove={handleRemoveTable} />

        {tables.length > 0 && (
          <button
            className="mt-auto text-xs font-medium text-neutral-500 hover:text-neutral-700 border border-neutral-200 rounded-lg py-2"
            onClick={handleClear}
          >
            Clear session
          </button>
        )}
      </aside>

      <main className="flex-1 flex flex-col p-6 max-w-4xl mx-auto w-full">
        {history.length === 0 ? (
          <div className="flex-1 flex items-center justify-center text-center">
            <p className="text-sm text-neutral-400">
              {tables.length === 0
                ? 'Upload at least one CSV or Excel file to get started.'
                : 'Ask a question about your data below.'}
            </p>
          </div>
        ) : (
          <ChatThread history={history} />
        )}

        <div className="pt-4">
          <ChatInput disabled={tables.length === 0} loading={asking} onSubmit={handleAsk} />
        </div>
      </main>
    </div>
  )
}
