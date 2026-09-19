import type { ChatTurn } from '../types'
import { downloadCsv } from '../csv'
import { formatValue } from '../format'
import { ChartRenderer } from './ChartRenderer'
import { ResultTable } from './ResultTable'

export function ChatMessage({ turn }: { turn: ChatTurn }) {
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
            <p className="text-sm text-red-600">I couldn't answer that: {turn.error}</p>
          ) : turn.is_scalar ? (
            <div>
              <p className="text-xs uppercase tracking-wide text-neutral-400">{turn.columns[0]}</p>
              <p className="text-3xl font-semibold text-neutral-900">{formatValue(turn.rows[0]?.[0])}</p>
            </div>
          ) : (
            <ResultTable columns={turn.columns} rows={turn.rows} />
          )}

          {turn.chart && <ChartRenderer chart={turn.chart} />}

          {!turn.error && turn.rows.length > 0 && (
            <button
              className="text-xs font-medium text-blue-600 hover:text-blue-700"
              onClick={() => downloadCsv(turn.columns, turn.rows)}
            >
              Download result as CSV
            </button>
          )}

          {turn.sql && (
            <details className="text-xs">
              <summary className="cursor-pointer text-neutral-500 font-medium select-none">
                View generated SQL
              </summary>
              <pre className="mt-2 bg-neutral-50 border border-neutral-200 rounded-lg p-3 overflow-x-auto text-neutral-700">
                {turn.sql}
              </pre>
            </details>
          )}
        </div>
      </div>
    </div>
  )
}
