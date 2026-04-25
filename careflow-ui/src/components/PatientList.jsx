import { SEVERITY_DOT, scoreToSeverity } from '../lib/severity'

export default function PatientList({ patients, selected, onSelect }) {
  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">Patients</h2>
      {patients.map((p) => {
        const sev = p.current_severity ?? scoreToSeverity(p.current_risk_score ?? 0)
        const isSelected = selected?.patient_id === p.patient_id
        return (
          <button
            key={p.patient_id}
            onClick={() => onSelect(p)}
            className={`text-left p-3 rounded-lg border transition-colors ${
              isSelected ? 'border-blue-500 bg-gray-800' : 'border-gray-700 bg-gray-900 hover:bg-gray-800'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium">{p.name}</span>
              <span className={`w-2.5 h-2.5 rounded-full ${SEVERITY_DOT[sev] ?? 'bg-gray-400'}`} />
            </div>
            <div className="text-xs text-gray-400 truncate">{p.conditions?.[0] ?? 'No conditions'}</div>
            <div className="text-xs mt-1">
              <span className="text-gray-500">Risk: </span>
              <span className={sev === 'CRITICAL' ? 'text-red-400' : sev === 'HIGH' ? 'text-orange-400' : 'text-gray-300'}>
                {p.current_risk_score != null ? (p.current_risk_score * 100).toFixed(0) + '%' : '—'}
              </span>
            </div>
          </button>
        )
      })}
    </div>
  )
}
