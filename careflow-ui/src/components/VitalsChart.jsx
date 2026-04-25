import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-gray-800 border border-gray-700 rounded p-2 text-xs">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: <span className="font-mono font-bold">{p.value}</span>
        </p>
      ))}
    </div>
  )
}

export default function VitalsChart({ vitals, hasAnomaly }) {
  return (
    <div className={`bg-gray-900 rounded-xl border p-4 transition-colors ${hasAnomaly ? 'border-red-500' : 'border-gray-800'}`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-sm text-gray-300">Live Vitals — Margaret Chen (patient-001)</h2>
        {hasAnomaly && (
          <span className="text-red-400 text-xs font-bold animate-pulse uppercase tracking-widest">
            ⚠ Anomaly Detected
          </span>
        )}
      </div>

      {/* Heart Rate */}
      <div className="mb-4">
        <p className="text-xs text-gray-500 mb-1">Heart Rate (BPM)</p>
        <ResponsiveContainer width="100%" height={100}>
          <LineChart data={vitals} margin={{ top: 2, right: 4, left: -28, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="time" tick={{ fill: '#6b7280', fontSize: 9 }} interval="preserveStartEnd" />
            <YAxis domain={[40, 180]} tick={{ fill: '#6b7280', fontSize: 9 }} />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={100} stroke="#f59e0b" strokeDasharray="4 2" strokeWidth={1} />
            <Line type="monotone" dataKey="heart_rate" stroke="#f87171" strokeWidth={2} dot={false} name="HR" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* SpO2 */}
      <div className="mb-4">
        <p className="text-xs text-gray-500 mb-1">SpO2 (%)</p>
        <ResponsiveContainer width="100%" height={80}>
          <LineChart data={vitals} margin={{ top: 2, right: 4, left: -28, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="time" tick={{ fill: '#6b7280', fontSize: 9 }} interval="preserveStartEnd" />
            <YAxis domain={[88, 101]} tick={{ fill: '#6b7280', fontSize: 9 }} />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={95} stroke="#f59e0b" strokeDasharray="4 2" strokeWidth={1} />
            <Line type="monotone" dataKey="spo2" stroke="#60a5fa" strokeWidth={2} dot={false} name="SpO2" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* HRV */}
      <div>
        <p className="text-xs text-gray-500 mb-1">HRV (ms)</p>
        <ResponsiveContainer width="100%" height={80}>
          <LineChart data={vitals} margin={{ top: 2, right: 4, left: -28, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="time" tick={{ fill: '#6b7280', fontSize: 9 }} interval="preserveStartEnd" />
            <YAxis domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 9 }} />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={25} stroke="#f59e0b" strokeDasharray="4 2" strokeWidth={1} />
            <Line type="monotone" dataKey="hrv" stroke="#34d399" strokeWidth={2} dot={false} name="HRV" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <p className="text-xs text-gray-600 mt-2 text-right">
        ZETIC Melange · on-device inference · raw vitals never leave device
      </p>
    </div>
  )
}
