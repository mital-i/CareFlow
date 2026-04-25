import { useEffect, useRef, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceArea, Legend,
} from 'recharts'
import { useSSE } from '../hooks/useSSE'

const MAX_POINTS = 60

export default function VitalsChart({ patientId }) {
  const [data, setData] = useState([])
  const anomalyRef = useRef(null)

  useSSE(
    patientId ? `/vitals/stream/${patientId}` : null,
    (payload) => {
      setData((prev) => {
        const point = {
          t: new Date(payload.timestamp).toLocaleTimeString(),
          hr: payload.heart_rate,
          spo2: payload.spo2,
          hrv: payload.hrv,
          anomaly: payload.anomaly_flagged,
        }
        return [...prev.slice(-(MAX_POINTS - 1)), point]
      })
    }
  )

  const anomalyWindows = []
  let start = null
  data.forEach((d, i) => {
    if (d.anomaly && start === null) start = d.t
    if (!d.anomaly && start !== null) {
      anomalyWindows.push({ x1: start, x2: data[i - 1]?.t })
      start = null
    }
  })

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 p-4 flex-1">
      <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3">Live Vitals</h3>
      {data.length === 0 ? (
        <div className="flex items-center justify-center h-32 text-gray-600 text-sm">
          Connecting to vitals stream…
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <XAxis dataKey="t" tick={{ fontSize: 10, fill: '#6b7280' }} interval="preserveStartEnd" />
            <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} />
            <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', fontSize: 12 }} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {anomalyWindows.map((w, i) => (
              <ReferenceArea key={i} x1={w.x1} x2={w.x2} fill="#f9731620" />
            ))}
            <Line type="monotone" dataKey="hr" stroke="#60a5fa" dot={false} name="HR (bpm)" strokeWidth={1.5} />
            <Line type="monotone" dataKey="spo2" stroke="#34d399" dot={false} name="SpO2 (%)" strokeWidth={1.5} />
            <Line type="monotone" dataKey="hrv" stroke="#a78bfa" dot={false} name="HRV (ms)" strokeWidth={1.5} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
