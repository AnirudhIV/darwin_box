export interface ColumnMeta {
  name: string
  type: string
}

export interface TablePreview {
  columns: string[]
  rows: unknown[][]
}

export interface TableSummary {
  name: string
  source_filename: string
  sheet: string | null
  n_rows: number
  columns: ColumnMeta[]
  preview?: TablePreview
}

export interface UploadResponse {
  session_id: string
  tables: TableSummary[]
  errors: { filename: string; error: string }[]
}

export interface ChartSpec {
  type: 'line' | 'bar' | 'scatter'
  x_key: string
  y_key: string
  data: Record<string, unknown>[]
}

export interface AskResponse {
  sql: string | null
  columns: string[]
  rows: unknown[][]
  is_scalar: boolean
  chart: ChartSpec | null
  error: string | null
  attempts: number
}

export interface ChatTurn extends AskResponse {
  question: string
}
