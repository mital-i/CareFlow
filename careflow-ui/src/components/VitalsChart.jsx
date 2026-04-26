import {
  CartesianGrid,
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

function StatCard({ label, value, unit, warn, danger }) {
  const textColor = danger ? 'text-red-400' : warn ? 'text-yellow-400' : 'text-emerald-400'
  const bg = danger
    ? 'bg-red-950/40 border-red-800/60'
    : warn
    ? 'bg-yellow-950/40 border-yellow-800/60'
    : 'bg-gray-800/60 border-gray-700'
  return (
    <div className={`flex-1 rounded-lg border px-4 py-3 transition-colors duration-500 ${bg}`}>
      <p className="text-xs text-gray-500 uppercase tracking-widest mb-1">{label}</p>
      <p className={`font-mono font-bold text-3xl leading-none ${textColor}`}>
        {value ?? '—'}
        <span className="text-xs font-normal text-gray-500 ml-1">{unit}</span>
      </p>
    </div>
  )
}

export default function VitalsChart({ vitals, hasAnomaly, patientName }) {
  const latest = vitals[vitals.length - 1]

  return (
    <div className={`bg-gray-900 rounded-xl border p-4 transition-colors duration-300 ${hasAnomaly ? 'border-red-500' : 'border-gray-800'}`}>
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-sm text-gray-300">Live Vitals — {patientName ?? 'patient-001'}</h2>
        <div className="flex items-center gap-3">
          {hasAnomaly && (
            <span className="text-red-400 text-xs font-bold animate-pulse uppercase tracking-widest">
              ⚠ Anomaly Detected
            </span>
          )}
          <span className="flex items-center gap-1.5 text-xs text-emerald-400">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-400" />
            </span>
            LIVE
          </span>
        </div>
      </div>

      {/* Live stat cards */}
      <div className="flex gap-3 mb-4">
        <StatCard
          label="Heart Rate" value={latest?.heart_rate} unit="BPM"
          warn={latest?.heart_rate > 100} danger={latest?.heart_rate > 120}
        />
        <StatCard
          label="SpO₂" value={latest?.spo2} unit="%"
          warn={latest?.spo2 < 97} danger={latest?.spo2 < 95}
        />
        <StatCard
          label="HRV" value={latest?.hrv} unit="ms"
          warn={latest?.hrv < 40} danger={latest?.hrv < 25}
        />
      </div>

      {vitals.length === 0 ? (
        <div className="flex items-center justify-center h-40 text-gray-600 text-sm">
          <span className="animate-pulse">Connecting to vitals stream…</span>
        </div>
      ) : (
        <>
          {/* Heart Rate */}
          <div className="mb-3">
            <p className="text-xs text-gray-500 mb-1">Heart Rate (BPM)</p>
            <ResponsiveContainer width="100%" height={90}>
              <LineChart data={vitals} margin={{ top: 2, right: 4, left: -28, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="time" tick={{ fill: '#6b7280', fontSize: 9 }} interval="preserveStartEnd" />
                <YAxis domain={[40, 180]} tick={{ fill: '#6b7280', fontSize: 9 }} />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={100} stroke="#f59e0b" strokeDasharray="4 2" strokeWidth={1} />
                <Line type="monotone" dataKey="heart_rate" stroke="#f87171" strokeWidth={2} dot={false} name="HR" isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* SpO2 */}
          <div className="mb-3">
            <p className="text-xs text-gray-500 mb-1">SpO₂ (%)</p>
            <ResponsiveContainer width="100%" height={70}>
              <LineChart data={vitals} margin={{ top: 2, right: 4, left: -28, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="time" tick={{ fill: '#6b7280', fontSize: 9 }} interval="preserveStartEnd" />
                <YAxis domain={[88, 101]} tick={{ fill: '#6b7280', fontSize: 9 }} />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={95} stroke="#f59e0b" strokeDasharray="4 2" strokeWidth={1} />
                <Line type="monotone" dataKey="spo2" stroke="#60a5fa" strokeWidth={2} dot={false} name="SpO₂" isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* HRV */}
          <div>
            <p className="text-xs text-gray-500 mb-1">HRV (ms)</p>
            <ResponsiveContainer width="100%" height={70}>
              <LineChart data={vitals} margin={{ top: 2, right: 4, left: -28, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="time" tick={{ fill: '#6b7280', fontSize: 9 }} interval="preserveStartEnd" />
                <YAxis domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 9 }} />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={25} stroke="#f59e0b" strokeDasharray="4 2" strokeWidth={1} />
                <Line type="monotone" dataKey="hrv" stroke="#34d399" strokeWidth={2} dot={false} name="HRV" isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      <p className="text-xs text-gray-600 mt-2 text-right">
        Heuristic anomaly detection · MedGemma risk classification
      </p>
    </div>
  )
}
