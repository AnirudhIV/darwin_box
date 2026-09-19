export function formatValue(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'number' && !Number.isInteger(value)) {
    return value.toLocaleString(undefined, { maximumFractionDigits: 2 })
  }
  return String(value)
}

const ISO_DATE_RE = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})$/
const MONTH_NAMES = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]

// Parses the date components directly rather than via `new Date(...)`, since
// these strings carry no timezone and Date() would interpret them as local
// time - shifting the displayed day depending on the viewer's timezone.
export function formatAxisLabel(value: unknown): string {
  if (typeof value !== 'string') return String(value)
  const match = ISO_DATE_RE.exec(value)
  if (!match) return value
  const [, year, month, day] = match
  const monthName = MONTH_NAMES[Number(month) - 1]
  return day === '01' ? `${monthName} ${year}` : `${monthName} ${Number(day)}, ${year}`
}
