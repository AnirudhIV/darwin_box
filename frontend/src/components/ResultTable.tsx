import { formatValue } from '../format'

export function ResultTable({ columns, rows }: { columns: string[]; rows: unknown[][] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-neutral-200 dark:border-neutral-800">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="bg-neutral-50 dark:bg-neutral-950">
            {columns.map((col) => (
              <th
                key={col}
                className="px-3 py-2 text-left font-medium text-neutral-500 dark:text-neutral-400 border-b border-neutral-200 dark:border-neutral-800"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="odd:bg-white even:bg-neutral-50/50 dark:odd:bg-neutral-900 dark:even:bg-neutral-900/50">
              {row.map((cell, j) => (
                <td
                  key={j}
                  className="px-3 py-2 text-neutral-800 dark:text-neutral-200 border-b border-neutral-100 dark:border-neutral-800 whitespace-nowrap"
                >
                  {cell === null ? (
                    <span className="text-neutral-300 dark:text-neutral-600">—</span>
                  ) : (
                    formatValue(cell)
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
