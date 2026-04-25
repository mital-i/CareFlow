const nodes = [
  { id: 'device',      label: 'Wearable / Device',     sub: 'Synthetic Vitals 1 Hz',    color: '#3b82f6', x: 60,  y: 120 },
  { id: 'detector',    label: 'Anomaly Detector',       sub: 'Heuristic scoring',         color: '#8b5cf6', x: 260, y: 120 },
  { id: 'monitor',     label: 'Monitor Agent',          sub: 'Fetch.ai uAgent',           color: '#06b6d4', x: 460, y: 120 },
  { id: 'coordinator', label: "Coordinator Agent",      sub: "Doctor's Assistant",        color: '#f59e0b', x: 460, y: 280 },
  { id: 'medgemma',    label: 'MedGemma (Ollama)',      sub: 'Risk classification',       color: '#22c55e', x: 260, y: 280 },
  { id: 'dashboard',   label: 'React Dashboard',        sub: 'Provider UI + Alerts',      color: '#ef4444', x: 60,  y: 280 },
]

const edges = [
  { from: 'device',      to: 'detector',    label: 'raw vitals' },
  { from: 'detector',    to: 'monitor',     label: 'AnomalyEvent' },
  { from: 'monitor',     to: 'coordinator', label: 'Chat Protocol' },
  { from: 'coordinator', to: 'medgemma',    label: 'classify_risk()' },
  { from: 'medgemma',    to: 'coordinator', label: 'RiskAssessment' },
  { from: 'coordinator', to: 'dashboard',   label: 'WebSocket' },
]

const CX = 80
const CY = 24

function nodeCenter(id) {
  const n = nodes.find((n) => n.id === id)
  return { x: n.x + CX, y: n.y + CY }
}

export default function SystemFlowDiagram({ onClose }) {
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-gray-950 border border-gray-700 rounded-2xl p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-sm uppercase tracking-widest text-gray-400">CareFlow System Flow</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 text-xl leading-none">×</button>
        </div>

        <svg width={700} height={380} className="overflow-visible">
          <defs>
            <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
              <path d="M0,0 L0,6 L8,3 z" fill="#6b7280" />
            </marker>
          </defs>

          {edges.map(({ from, to, label }) => {
            const a = nodeCenter(from)
            const b = nodeCenter(to)
            const mx = (a.x + b.x) / 2
            const my = (a.y + b.y) / 2
            return (
              <g key={`${from}-${to}`}>
                <line
                  x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                  stroke="#374151" strokeWidth={1.5} markerEnd="url(#arrow)"
                />
                <text x={mx} y={my - 6} fill="#9ca3af" fontSize={10} textAnchor="middle">
                  {label}
                </text>
              </g>
            )
          })}

          {nodes.map(({ id, label, sub, color, x, y }) => (
            <g key={id}>
              <rect
                x={x} y={y} width={CX * 2} height={CY * 2}
                rx={8} fill="#111827" stroke={color} strokeWidth={2}
              />
              <text x={x + CX} y={y + 16} fill={color} fontSize={11} textAnchor="middle" fontWeight="600">
                {label}
              </text>
              <text x={x + CX} y={y + 30} fill="#6b7280" fontSize={9} textAnchor="middle">
                {sub}
              </text>
            </g>
          ))}
        </svg>

        <p className="text-xs text-gray-600 text-center mt-2">
          Vitals streamed at 1 Hz · anomalies trigger MedGemma risk classification
        </p>
      </div>
    </div>
  )
}
