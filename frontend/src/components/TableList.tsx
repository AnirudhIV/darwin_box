import { CaretDown, CaretRight, TrashSimple } from '@phosphor-icons/react'
import { useState } from 'react'
import type { TableSummary } from '../types'

function TableItem({
  table,
  onRemove,
}: {
  table: TableSummary
  onRemove: (name: string) => void
}) {
  const [open, setOpen] = useState(false)
  return (
    <div className="rounded-lg border border-neutral-200 bg-white group">
      <div className="flex items-center gap-1 px-3 py-2">
        <button
          className="flex-1 flex items-center justify-between text-left min-w-0"
          onClick={() => setOpen((o) => !o)}
        >
          <span className="text-sm font-medium text-neutral-800 truncate">
            {table.name} <span className="text-neutral-400 font-normal">({table.n_rows} rows)</span>
          </span>
          <span className="text-neutral-400 shrink-0 ml-2">
            {open ? <CaretDown size={14} /> : <CaretRight size={14} />}
          </span>
        </button>
        <button
          className="shrink-0 p-1 text-neutral-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
          title={`Remove ${table.name}`}
          onClick={() => onRemove(table.name)}
        >
          <TrashSimple size={14} />
        </button>
      </div>
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

export function TableList({
  tables,
  onRemove,
}: {
  tables: TableSummary[]
  onRemove: (name: string) => void
}) {
  if (tables.length === 0) return null
  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-neutral-400">Loaded tables</h3>
      {tables.map((t) => (
        <TableItem key={t.name} table={t} onRemove={onRemove} />
      ))}
    </div>
  )
}
