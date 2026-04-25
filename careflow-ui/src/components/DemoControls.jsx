import { useState } from 'react'
import { X } from 'lucide-react'
import toast from 'react-hot-toast'

export default function DemoControls({ onClose }) {
  const [patientId, setPatientId] = useState('P001')
  const [loading, setLoading] = useState(false)

  const triggerAnomaly = async () => {
    setLoading(true)
    try {
      await fetch(`/api/agents/trigger-anomaly?patient_id=${patientId}`, { method: 'POST' })
      toast.success(`Anomaly injected for ${patientId}`)
    } catch {
      toast.error('Trigger failed')
    } finally {
      setLoading(false)
    }
  }

  const resetPatient = async () => {
    toast('Re-seed not wired yet — run: python scripts/seed.py', { icon: 'ℹ️' })
  }

  return (
    <div className="fixed bottom-4 right-4 bg-gray-900 border border-yellow-700 rounded-lg p-4 w-72 z-50 shadow-xl">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-bold text-yellow-400 uppercase tracking-widest">Demo Controls</span>
        <button onClick={onClose} className="text-gray-500 hover:text-white"><X size={14} /></button>
      </div>

      <div className="flex flex-col gap-2">
        <select
          value={patientId}
          onChange={(e) => setPatientId(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-200"
        >
          <option value="P001">P001 — Margaret Chen</option>
          <option value="P002">P002 — Robert Okafor</option>
          <option value="P003">P003 — Amelia Torres</option>
        </select>

        <button
          onClick={triggerAnomaly}
          disabled={loading}
          className="bg-red-800 hover:bg-red-700 disabled:opacity-50 text-white text-xs py-1.5 px-3 rounded"
        >
          {loading ? 'Triggering…' : '🚨 Trigger Anomaly'}
        </button>

        <button
          onClick={resetPatient}
          className="bg-gray-700 hover:bg-gray-600 text-white text-xs py-1.5 px-3 rounded"
        >
          Reset / Re-seed
        </button>

        <p className="text-gray-600 text-xs mt-1">Press D to toggle · F for flow diagram</p>
      </div>
    </div>
  )
}
