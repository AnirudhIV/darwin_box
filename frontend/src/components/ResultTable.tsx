import { formatValue } from '../format'

export function ResultTable({ columns, rows }: { columns: string[]; rows: unknown[][] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-neutral-200">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="bg-neutral-50">
            {columns.map((col) => (
              <th
                key={col}
                className="px-3 py-2 text-left font-medium text-neutral-500 border-b border-neutral-200"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="odd:bg-white even:bg-neutral-50/50">
              {row.map((cell, j) => (
                <td key={j} className="px-3 py-2 text-neutral-800 border-b border-neutral-100 whitespace-nowrap">
                  {cell === null ? <span className="text-neutral-300">—</span> : formatValue(cell)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
