import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useTheme } from '../ThemeContext'
import type { ChartSpec } from '../types'
import { formatAxisLabel } from '../format'
import { chartColors } from '../theme'

export function ChartRenderer({ chart }: { chart: ChartSpec }) {
  const { theme } = useTheme()
  const { gridline, axis, muted, sequentialBlue, surface } = chartColors(theme)
  const { type, x_key, y_key, data } = chart

  const axisStyle = { fontSize: 12, fill: muted, fontFamily: 'system-ui, sans-serif' }
  const tooltipStyle = {
    background: surface,
    border: `1px solid ${gridline}`,
    borderRadius: 8,
    fontSize: 13,
  }

  if (type === 'line') {
    return (
      <LineChart width={560} height={280} data={data} margin={{ top: 10, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridline} vertical={false} />
        <XAxis dataKey={x_key} tick={axisStyle} stroke={axis} tickFormatter={formatAxisLabel} />
        <YAxis tick={axisStyle} stroke={axis} />
        <Tooltip contentStyle={tooltipStyle} labelFormatter={formatAxisLabel} />
        <Line type="monotone" dataKey={y_key} stroke={sequentialBlue} strokeWidth={2} dot={{ r: 4 }} />
      </LineChart>
    )
  }

  if (type === 'bar') {
    return (
      <BarChart width={560} height={280} data={data} margin={{ top: 10, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridline} vertical={false} />
        <XAxis dataKey={x_key} tick={axisStyle} stroke={axis} tickFormatter={formatAxisLabel} />
        <YAxis tick={axisStyle} stroke={axis} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: gridline }} labelFormatter={formatAxisLabel} />
        <Bar dataKey={y_key} fill={sequentialBlue} radius={[4, 4, 0, 0]} />
      </BarChart>
    )
  }

  // scatter
  return (
    <ScatterChart width={560} height={280} margin={{ top: 10, right: 20, bottom: 5, left: 0 }}>
      <CartesianGrid strokeDasharray="3 3" stroke={gridline} />
      <XAxis dataKey={x_key} name={x_key} tick={axisStyle} stroke={axis} type="number" />
      <YAxis dataKey={y_key} name={y_key} tick={axisStyle} stroke={axis} type="number" />
      <Tooltip contentStyle={tooltipStyle} cursor={{ strokeDasharray: '3 3' }} />
      <Scatter data={data} fill={sequentialBlue} />
    </ScatterChart>
  )
}
