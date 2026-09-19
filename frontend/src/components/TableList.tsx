import { CaretDown, CaretRight } from '@phosphor-icons/react'
import { useState } from 'react'
import type { TableSummary } from '../types'

function TableItem({ table }: { table: TableSummary }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="rounded-lg border border-neutral-200 bg-white">
      <button
        className="w-full flex items-center justify-between px-3 py-2 text-left"
        onClick={() => setOpen((o) => !o)}
      >
        <span className="text-sm font-medium text-neutral-800 truncate">
          {table.name} <span className="text-neutral-400 font-normal">({table.n_rows} rows)</span>
        </span>
        <span className="text-neutral-400">
          {open ? <CaretDown size={14} /> : <CaretRight size={14} />}
        </span>
      </button>
      {open && (
        <div className="px-3 pb-3 text-xs text-neutral-500 space-y-1">
          <p>
            Source: {table.source_filename}
            {table.sheet ? ` / sheet '${table.sheet}'` : ''}
          </p>
          <p className="truncate">Columns: {table.columns.map((c) => c.name).join(', ')}</p>
        </div>
      )}
    </div>
  )
}

export function TableList({ tables }: { tables: TableSummary[] }) {
  if (tables.length === 0) return null
  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-neutral-400">Loaded tables</h3>
      {tables.map((t) => (
        <TableItem key={t.name} table={t} />
      ))}
    </div>
  )
}
