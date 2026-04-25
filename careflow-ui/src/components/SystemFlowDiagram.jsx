import { X } from 'lucide-react'

const AGENTS = [
  { id: 'a1', label: 'Agent 1\nVital Monitor', sub: 'ZETIC Melange', x: 60, y: 180, color: '#1e40af' },
  { id: 'a2', label: 'Agent 2\nRisk Assessment', sub: 'Vertex AI + LangGraph', x: 220, y: 180, color: '#065f46' },
  { id: 'a3', label: 'Agent 3\nCoordinator', sub: 'Orchestrator', x: 380, y: 180, color: '#92400e' },
  { id: 'a4', label: 'Agent 4\nPatient', sub: 'Preferences', x: 300, y: 320, color: '#4c1d95' },
  { id: 'a5', label: 'Agent 5\nProvider', sub: 'Availability', x: 460, y: 320, color: '#7f1d1d' },
]

const ARROWS = [
  { x1: 160, y1: 200, x2: 210, y2: 200, label: 'AnomalyEvent' },
  { x1: 320, y1: 200, x2: 370, y2: 200, label: 'RiskAssessment' },
  { x1: 420, y1: 220, x2: 380, y2: 310, label: 'query prefs' },
  { x1: 440, y1: 220, x2: 490, y2: 310, label: 'check avail.' },
]

export default function SystemFlowDiagram({ onClose }) {
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-[620px]">
        <div className="flex items-center justify-between mb-4">
          <span className="font-bold text-sm tracking-widest text-gray-300">CAREFLOW AGENT NETWORK</span>
          <button onClick={onClose} className="text-gray-500 hover:text-white"><X size={16} /></button>
        </div>

        <svg width="580" height="420" viewBox="0 0 580 420" className="w-full">
          {/* Arrows */}
          <defs>
            <marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
              <path d="M0,0 L0,6 L6,3 z" fill="#60a5fa" />
            </marker>
          </defs>
          {ARROWS.map((a, i) => (
            <g key={i}>
              <line x1={a.x1} y1={a.y1} x2={a.x2} y2={a.y2} stroke="#60a5fa" strokeWidth={1.5} markerEnd="url(#arrow)" />
              <text x={(a.x1 + a.x2) / 2} y={(a.y1 + a.y2) / 2 - 6} textAnchor="middle" fill="#93c5fd" fontSize={9}>
                {a.label}
              </text>
            </g>
          ))}

          {/* Agent boxes */}
          {AGENTS.map((a) => (
            <g key={a.id} transform={`translate(${a.x}, ${a.y})`}>
              <rect x={-55} y={-30} width={110} height={60} rx={8} fill={a.color} fillOpacity={0.8} stroke="#374151" />
              {a.label.split('\n').map((line, i) => (
                <text key={i} x={0} y={-8 + i * 16} textAnchor="middle" fill="white" fontSize={11} fontWeight="bold">
                  {line}
                </text>
              ))}
              <text x={0} y={22} textAnchor="middle" fill="#d1d5db" fontSize={9}>{a.sub}</text>
            </g>
          ))}

          {/* Dashboard box */}
          <g transform="translate(520, 180)">
            <rect x={-45} y={-25} width={90} height={50} rx={8} fill="#1f2937" stroke="#4b5563" />
            <text x={0} y={-5} textAnchor="middle" fill="white" fontSize={10} fontWeight="bold">Dashboard</text>
            <text x={0} y={10} textAnchor="middle" fill="#9ca3af" fontSize={9}>React + WS</text>
          </g>
          <line x1={440} y1={180} x2={465} y2={180} stroke="#60a5fa" strokeWidth={1.5} markerEnd="url(#arrow)" />

          {/* MongoDB */}
          <g transform="translate(220, 340)">
            <rect x={-50} y={-20} width={100} height={40} rx={6} fill="#713f12" stroke="#92400e" />
            <text x={0} y={5} textAnchor="middle" fill="white" fontSize={10} fontWeight="bold">MongoDB Atlas</text>
          </g>
        </svg>
      </div>
    </div>
  )
}
