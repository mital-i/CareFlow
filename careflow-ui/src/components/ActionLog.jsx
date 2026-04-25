import { useState } from 'react'

const SEVERITY_BADGE = {
  LOW:      'bg-green-900 text-green-300',
  MEDIUM:   'bg-yellow-900 text-yellow-300',
  HIGH:     'bg-orange-900 text-orange-300',
  CRITICAL: 'bg-red-900 text-red-300',
}

function LogEntry({ entry, isNew }) {
  const [expanded, setExpanded] = useState(false)
  const badge = SEVERITY_BADGE[entry.severity_level] || SEVERITY_BADGE.LOW
  const time = new Date(entry.generated_at).toLocaleTimeString()

  return (
    <button
      onClick={() => setExpanded((v) => !v)}
      className={`w-full text-left border rounded-lg p-3 hover:border-gray-600 transition-colors bg-gray-900 ${
        isNew ? 'border-gray-500 fade-in-up' : 'border-gray-800'
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-gray-500 text-xs font-mono">{time}</span>
        <span className={`text-xs px-1.5 py-0.5 rounded font-semibold ${badge}`}>
          {entry.severity_level}
        </span>
      </div>
      <p className="text-xs text-gray-400 mt-1 truncate">
        {entry.action_tier?.replace(/_/g, ' ')} · score {Math.round(entry.risk_score * 100)}%
      </p>
      {expanded && (
        <p className="text-xs text-gray-300 mt-2 leading-relaxed text-left border-t border-gray-800 pt-2">
          {entry.reasoning_context}
        </p>
      )}
    </button>
  )
}

export default function ActionLog({ entries }) {
  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-sm text-gray-300">Action Log</h2>
        <div className="flex items-center gap-2">
          {entries.length > 0 && (
            <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full font-mono">
              {entries.length}
            </span>
          )}
          <span className="text-xs text-gray-500">click to expand</span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto space-y-2">
        {entries.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 gap-2 text-gray-600">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <circle cx="12" cy="12" r="9" />
              <path d="M12 8v4l3 3" />
            </svg>
            <p className="text-xs text-center leading-relaxed">
              Awaiting anomaly events…
              <br />
              <span className="text-gray-700">Press D to trigger a demo</span>
            </p>
          </div>
        ) : (
          entries.map((e) => (
            <LogEntry key={e.assessment_id ?? e.generated_at} entry={e} isNew={entries[0] === e} />
          ))
        )}
      </div>
    </div>
  )
}
