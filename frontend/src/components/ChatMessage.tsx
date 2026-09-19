import { CaretDown, CaretRight, DownloadSimple, WarningCircle } from '@phosphor-icons/react'
import { useState } from 'react'
import type { ChatTurn } from '../types'
import { downloadCsv } from '../csv'
import { formatValue } from '../format'
import { ChartRenderer } from './ChartRenderer'
import { ResultTable } from './ResultTable'

export function ChatMessage({ turn }: { turn: ChatTurn }) {
  const [sqlOpen, setSqlOpen] = useState(false)
  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <div className="bg-blue-600 text-white rounded-2xl rounded-br-sm px-4 py-2 max-w-[80%] text-sm">
          {turn.question}
        </div>
      </div>

      <div className="flex justify-start">
        <div className="bg-white border border-neutral-200 rounded-2xl rounded-bl-sm px-4 py-3 max-w-[90%] w-full space-y-3">
          {turn.error ? (
            <p className="text-sm text-red-600 flex items-start gap-1.5">
              <WarningCircle size={16} weight="bold" className="shrink-0 mt-0.5" />
              <span>I couldn't answer that: {turn.error}</span>
            </p>
          ) : turn.is_scalar ? (
            <div>
              <p className="text-xs uppercase tracking-wide text-neutral-400">{turn.columns[0]}</p>
              <p className="text-3xl font-semibold text-neutral-900">{formatValue(turn.rows[0]?.[0])}</p>
            </div>
          ) : turn.rows.length === 0 ? (
            <p className="text-sm text-neutral-500">
              The query ran successfully but matched no rows. Try rephrasing, or check the loaded
              table's columns in the sidebar — the filter value may not match what's in the data.
            </p>
          ) : (
            <ResultTable columns={turn.columns} rows={turn.rows} />
          )}

          {turn.chart && <ChartRenderer chart={turn.chart} />}

          {!turn.error && turn.rows.length > 0 && (
            <button
              className="text-xs font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1"
              onClick={() => downloadCsv(turn.columns, turn.rows)}
            >
              <DownloadSimple size={14} weight="bold" /> Download result as CSV
            </button>
          )}

          {turn.sql && (
            <div className="text-xs">
              <button
                className="flex items-center gap-1 text-neutral-500 font-medium select-none"
                onClick={() => setSqlOpen((o) => !o)}
              >
                {sqlOpen ? <CaretDown size={12} /> : <CaretRight size={12} />}
                View generated SQL
              </button>
              {sqlOpen && (
                <pre className="mt-2 bg-neutral-50 border border-neutral-200 rounded-lg p-3 overflow-x-auto text-neutral-700">
                  {turn.sql}
                </pre>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
