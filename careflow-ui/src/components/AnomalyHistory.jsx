import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const SEVERITY_COLOR = {
  LOW: '#22c55e',
  MEDIUM: '#facc15',
  HIGH: '#f97316',
  CRITICAL: '#dc2626',
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="bg-gray-800 border border-gray-700 rounded p-2 text-xs">
      <p className="text-gray-400">{new Date(d.detected_at).toLocaleTimeString()}</p>
      <p className="text-white font-semibold mt-0.5">{d.signal_type}</p>
      <p style={{ color: SEVERITY_COLOR[d.severity_level] ?? '#9ca3af' }}>
        Score: {Math.round(d.deviation_score * 100)}%
      </p>
    </div>
  )
}

export default function AnomalyHistory({ entries }) {
  if (!entries || entries.length === 0) {
    return (
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
        <h2 className="font-semibold text-sm text-gray-300 mb-3">Anomaly History</h2>
        <p className="text-xs text-gray-600 text-center py-4">No anomalies recorded yet</p>
      </div>
    )
  }

  const chartData = [...entries].reverse().map((e, i) => ({
    ...e,
    index: i,
    score_pct: Math.round(e.deviation_score * 100),
  }))

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-sm text-gray-300">Anomaly History</h2>
        <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full font-mono">
          {entries.length}
        </span>
      </div>

      <ResponsiveContainer width="100%" height={70}>
        <BarChart data={chartData} margin={{ top: 2, right: 4, left: -28, bottom: 0 }}>
          <XAxis dataKey="index" hide />
          <YAxis domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 9 }} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="score_pct" radius={[2, 2, 0, 0]}>
            {chartData.map((entry) => (
              <Cell
                key={entry.anomaly_id ?? entry.index}
                fill={SEVERITY_COLOR[entry.severity_level] ?? '#6b7280'}
                fillOpacity={0.8}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-2 space-y-1 max-h-32 overflow-y-auto">
        {entries.map((e) => (
          <div
            key={e.anomaly_id ?? e.detected_at}
            className="flex items-center justify-between text-xs text-gray-500 py-0.5"
          >
            <span className="font-mono">{new Date(e.detected_at).toLocaleTimeString()}</span>
            <span className="text-gray-400">{e.signal_type}</span>
            <span style={{ color: SEVERITY_COLOR[e.severity_level] ?? '#9ca3af' }} className="font-semibold">
              {Math.round(e.deviation_score * 100)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
