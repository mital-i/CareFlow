import { SEVERITY_COLORS } from '../lib/severity'

export default function ProviderPanel({ alerts }) {
  const handleAcknowledge = async (alertId) => {
    await fetch('/api/agents/acknowledge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alert_id: alertId, acknowledged_at: new Date().toISOString() }),
    }).catch(console.error)
  }

  if (alerts.length === 0) return null

  return (
    <div className="border-b border-gray-800 p-3 flex flex-col gap-2 shrink-0 max-h-48 overflow-y-auto">
      <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest shrink-0">Provider Alerts</h3>
      {alerts.map((a) => (
        <div key={a.action_id} className="bg-gray-900 border border-red-800 rounded p-2">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium">{a.patient_id}</span>
            <span className={`text-xs px-1.5 py-0.5 rounded ${SEVERITY_COLORS[a.severity_level] ?? ''}`}>
              {a.severity_level}
            </span>
          </div>
          {a.reasoning_context && (
            <p className="text-xs text-gray-400 mb-2 leading-relaxed line-clamp-2">{a.reasoning_context}</p>
          )}
          <button
            onClick={() => handleAcknowledge(a.action_id)}
            className="text-xs bg-blue-800 hover:bg-blue-700 text-blue-100 px-2 py-1 rounded"
          >
            Acknowledge
          </button>
        </div>
      ))}
    </div>
  )
}
