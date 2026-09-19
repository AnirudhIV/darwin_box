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
import type { ChartSpec } from '../types'
import { formatAxisLabel } from '../format'
import { AXIS, GRIDLINE, MUTED, SEQUENTIAL_BLUE, SURFACE } from '../theme'

const axisStyle = { fontSize: 12, fill: MUTED, fontFamily: 'system-ui, sans-serif' }
const tooltipStyle = {
  background: SURFACE,
  border: `1px solid ${GRIDLINE}`,
  borderRadius: 8,
  fontSize: 13,
}

export function ChartRenderer({ chart }: { chart: ChartSpec }) {
  const { type, x_key, y_key, data } = chart

  if (type === 'line') {
    return (
      <LineChart width={560} height={280} data={data} margin={{ top: 10, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRIDLINE} vertical={false} />
        <XAxis dataKey={x_key} tick={axisStyle} stroke={AXIS} tickFormatter={formatAxisLabel} />
        <YAxis tick={axisStyle} stroke={AXIS} />
        <Tooltip contentStyle={tooltipStyle} labelFormatter={formatAxisLabel} />
        <Line type="monotone" dataKey={y_key} stroke={SEQUENTIAL_BLUE} strokeWidth={2} dot={{ r: 4 }} />
      </LineChart>
    )
  }

  if (type === 'bar') {
    return (
      <BarChart width={560} height={280} data={data} margin={{ top: 10, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRIDLINE} vertical={false} />
        <XAxis dataKey={x_key} tick={axisStyle} stroke={AXIS} tickFormatter={formatAxisLabel} />
        <YAxis tick={axisStyle} stroke={AXIS} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: GRIDLINE }} labelFormatter={formatAxisLabel} />
        <Bar dataKey={y_key} fill={SEQUENTIAL_BLUE} radius={[4, 4, 0, 0]} />
      </BarChart>
    )
  }

  // scatter
  return (
    <ScatterChart width={560} height={280} margin={{ top: 10, right: 20, bottom: 5, left: 0 }}>
      <CartesianGrid strokeDasharray="3 3" stroke={GRIDLINE} />
      <XAxis dataKey={x_key} name={x_key} tick={axisStyle} stroke={AXIS} type="number" />
      <YAxis dataKey={y_key} name={y_key} tick={axisStyle} stroke={AXIS} type="number" />
      <Tooltip contentStyle={tooltipStyle} cursor={{ strokeDasharray: '3 3' }} />
      <Scatter data={data} fill={SEQUENTIAL_BLUE} />
    </ScatterChart>
  )
}
