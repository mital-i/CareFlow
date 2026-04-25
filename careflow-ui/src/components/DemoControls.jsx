import { useState } from 'react'

const API_BASE = 'http://localhost:8000'

export default function DemoControls({ onClose }) {
  const [loading, setLoading] = useState(false)
  const [duration, setDuration] = useState(30)

  const triggerAnomaly = async () => {
    setLoading(true)
    try {
      await fetch(`${API_BASE}/trigger-anomaly`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: 'patient-001', duration_seconds: duration }),
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-end justify-center pb-8 z-50" onClick={onClose}>
      <div
        className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-96 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-sm uppercase tracking-widest text-gray-400">Demo Controls</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 text-xl leading-none">×</button>
        </div>

        <div className="mb-4">
          <label className="text-xs text-gray-400 mb-1 block">Anomaly Duration (seconds)</label>
          <input
            type="range"
            min={10}
            max={60}
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
            className="w-full accent-red-500"
          />
          <span className="text-xs text-gray-400 font-mono">{duration}s</span>
        </div>

        <button
          onClick={triggerAnomaly}
          disabled={loading}
          className="w-full bg-red-600 hover:bg-red-500 disabled:bg-gray-700 text-white font-bold py-3 rounded-lg transition-colors text-sm"
        >
          {loading ? 'Injecting…' : '🚨 Trigger AFib Anomaly'}
        </button>

        <p className="text-xs text-gray-600 mt-3 text-center">
          POST /trigger-anomaly → ZETIC detects → Gemini assesses → Dashboard alerts
        </p>
      </div>
    </div>
  )
}
