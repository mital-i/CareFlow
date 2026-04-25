import { SEVERITY_COLORS } from '../lib/severity'

const RADIUS = 60
const STROKE = 10
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

export default function RiskGauge({ score, severity }) {
  const pct = Math.min(1, Math.max(0, score))
  const offset = CIRCUMFERENCE * (1 - pct)
  const color = severity === 'CRITICAL' ? '#ef4444'
    : severity === 'HIGH' ? '#f97316'
    : severity === 'MEDIUM' ? '#eab308'
    : '#22c55e'

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 p-4 flex flex-col items-center gap-2">
      <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest">Risk Score</h3>
      <svg width={150} height={150} viewBox="0 0 150 150">
        <circle cx={75} cy={75} r={RADIUS} fill="none" stroke="#1f2937" strokeWidth={STROKE} />
        <circle
          cx={75} cy={75} r={RADIUS}
          fill="none"
          stroke={color}
          strokeWidth={STROKE}
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 75 75)"
          style={{ transition: 'stroke-dashoffset 0.4s ease, stroke 0.4s ease' }}
        />
        <text x={75} y={72} textAnchor="middle" fill="white" fontSize={24} fontWeight="bold">
          {(pct * 100).toFixed(0)}
        </text>
        <text x={75} y={90} textAnchor="middle" fill="#9ca3af" fontSize={11}>
          {severity}
        </text>
      </svg>
    </div>
  )
}
