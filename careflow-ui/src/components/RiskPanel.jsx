const SEVERITY_STYLES = {
  LOW:      { bar: 'bg-green-500',  text: 'text-green-400',  border: 'border-green-800',  badge: 'bg-green-900 text-green-300' },
  MEDIUM:   { bar: 'bg-yellow-400', text: 'text-yellow-400', border: 'border-yellow-700', badge: 'bg-yellow-900 text-yellow-300' },
  HIGH:     { bar: 'bg-orange-500', text: 'text-orange-400', border: 'border-orange-700', badge: 'bg-orange-900 text-orange-300' },
  CRITICAL: { bar: 'bg-red-600',    text: 'text-red-400',    border: 'border-red-600',    badge: 'bg-red-900 text-red-300' },
}

const ACTION_LABEL = {
  LOG_ONLY:        'Logged',
  PATIENT_ALERT:   'Patient Alerted',
  PROVIDER_NOTIFY: 'Provider Notified',
  ER_DISPATCH:     '🚨 ER Dispatch',
}

const SAFETY_STYLES = {
  PASS:      { text: 'text-cyan-400',   badge: 'bg-cyan-900 text-cyan-300 border-cyan-800',   icon: '🛡️', label: 'Safety Verified' },
  FAIL:      { text: 'text-red-400',    badge: 'bg-red-900 text-red-300 border-red-800',   icon: '⚠️', label: 'Safety Concern' },
  UNCERTAIN: { text: 'text-gray-400',   badge: 'bg-gray-800 text-gray-400 border-gray-700',   icon: '❓', label: 'Unverified' },
}

export default function RiskPanel({ assessment }) {
  if (!assessment) return null
  const s = SEVERITY_STYLES[assessment.severity_level] || SEVERITY_STYLES.LOW
  const safety = SAFETY_STYLES[assessment.safety_report?.status] || SAFETY_STYLES.UNCERTAIN
  
  const pct = Math.round(assessment.risk_score * 100)
  const isCritical = assessment.severity_level === 'CRITICAL'

  return (
    <div className={`fade-in-up bg-gray-900 rounded-xl border ${s.border} p-4 ${isCritical ? 'glow-red' : ''}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h2 className="font-semibold text-sm text-gray-300">Gemma Clinical Intelligence</h2>
          <span className={`text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border ${safety.badge} flex items-center gap-1`}>
            {safety.icon} {safety.label}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2 py-0.5 rounded font-bold ${s.badge} ${isCritical ? 'animate-pulse' : ''}`}>
            {assessment.severity_level}
          </span>
          <span className={`font-mono text-2xl font-bold ${s.text}`}>{pct}%</span>
        </div>
      </div>

      {/* Risk score bar */}
      <div className="h-2 bg-gray-800 rounded-full mb-3 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${s.bar}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <p className="text-sm text-gray-300 mb-2 leading-relaxed">{assessment.reasoning_context}</p>

      {assessment.safety_report?.status === 'FAIL' && (
        <div className="mb-3 p-2 rounded bg-red-950/50 border border-red-900/50">
          <p className="text-[11px] text-red-300 font-medium">
            <span className="font-bold">Safety Conflict:</span> {assessment.safety_report.concerns}
          </p>
        </div>
      )}

      <div className="border-t border-gray-800 pt-2 mt-2 flex items-start justify-between gap-3">
        <p className="text-xs text-gray-400 flex-1">
          <span className="font-semibold text-gray-300">Doctor note: </span>
          {assessment.doctor_note}
        </p>
        <span className={`text-xs shrink-0 font-semibold ${s.text}`}>
          {ACTION_LABEL[assessment.action_tier] ?? assessment.action_tier}
        </span>
      </div>
    </div>
  )
}
