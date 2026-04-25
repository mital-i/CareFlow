import { useState } from 'react'
import { SEVERITY_COLORS } from '../lib/severity'

const TIER_COLORS = {
  LOG_ONLY: 'text-gray-400 bg-gray-800',
  PATIENT_ALERT: 'text-blue-300 bg-blue-900',
  PROVIDER_NOTIFY: 'text-orange-300 bg-orange-900',
  ER_DISPATCH: 'text-red-300 bg-red-900 animate-pulse',
}

export default function ActionLog({ entries }) {
  const [expanded, setExpanded] = useState(null)

  return (
    <div className="flex-1 flex flex-col overflow-hidden border-t border-gray-800">
      <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest px-3 pt-3 pb-2 shrink-0">
        Action Log
      </h3>
      <div className="flex-1 overflow-y-auto px-3 pb-3 flex flex-col gap-1.5">
        {entries.length === 0 ? (
          <p className="text-gray-600 text-xs">No actions yet</p>
        ) : (
          entries.map((e) => (
            <div
              key={e.action_id}
              className="bg-gray-900 rounded border border-gray-800 p-2 cursor-pointer hover:border-gray-600"
              onClick={() => setExpanded(expanded === e.action_id ? null : e.action_id)}
            >
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs text-gray-500">
                  {new Date(e.executed_at).toLocaleTimeString()}
                </span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${TIER_COLORS[e.action_tier] ?? ''}`}>
                  {e.action_tier}
                </span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${SEVERITY_COLORS[e.severity_level] ?? ''}`}>
                  {e.severity_level}
                </span>
              </div>
              {expanded === e.action_id && e.reasoning_context && (
                <p className="text-xs text-gray-300 mt-2 leading-relaxed">{e.reasoning_context}</p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
