import { useState } from 'react'

const SEVERITY_BADGE = {
  LOW:      'bg-green-900 text-green-300',
  MEDIUM:   'bg-yellow-900 text-yellow-300',
  HIGH:     'bg-orange-900 text-orange-300',
  CRITICAL: 'bg-red-900 text-red-300',
}

function LogEntry({ entry }) {
  const [expanded, setExpanded] = useState(false)
  const badge = SEVERITY_BADGE[entry.severity_level] || SEVERITY_BADGE.LOW
  const time = new Date(entry.generated_at).toLocaleTimeString()

  return (
    <button
      onClick={() => setExpanded((v) => !v)}
      className="w-full text-left border border-gray-800 rounded-lg p-3 hover:border-gray-600 transition-colors bg-gray-900"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-gray-500 text-xs font-mono">{time}</span>
        <span className={`text-xs px-1.5 py-0.5 rounded font-semibold ${badge}`}>
          {entry.severity_level}
        </span>
      </div>
      <p className="text-xs text-gray-400 mt-1 truncate">
        {entry.action_tier?.replace('_', ' ')} · score {Math.round(entry.risk_score * 100)}%
      </p>
      {expanded && (
        <p className="text-xs text-gray-300 mt-2 leading-relaxed text-left">
          {entry.reasoning_context}
        </p>
      )}
    </button>
  )
}

export default function ActionLog({ entries }) {
  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 h-full flex flex-col">
      <h2 className="font-semibold text-sm text-gray-300 mb-3">
        Action Log
        <span className="ml-2 text-xs text-gray-500 font-normal">click to expand</span>
      </h2>
      <div className="flex-1 overflow-y-auto space-y-2">
        {entries.length === 0 ? (
          <p className="text-gray-600 text-xs text-center py-8">Awaiting anomaly events…</p>
        ) : (
          entries.map((e, i) => <LogEntry key={i} entry={e} />)
        )}
      </div>
    </div>
  )
}
