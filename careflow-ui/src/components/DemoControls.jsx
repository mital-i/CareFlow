import { useState } from 'react'

const API_BASE = 'http://localhost:8000'

export default function DemoControls({ onClose }) {
  const [loading, setLoading] = useState(false)
  const [duration, setDuration] = useState(30)
  const [countdown, setCountdown] = useState(null)

  const triggerAnomaly = async () => {
    setLoading(true)
    try {
      await fetch(`${API_BASE}/trigger-anomaly`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: 'patient-001', duration_seconds: duration }),
      })
      setCountdown(duration)
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) { clearInterval(timer); return null }
          return prev - 1
        })
      }, 1000)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-end justify-center pb-8 z-50" onClick={onClose}>
      <div
        className="slide-up bg-gray-900 border border-gray-700 rounded-2xl p-6 w-96 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-sm uppercase tracking-widest text-gray-400">Demo Controls</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 text-xl leading-none">×</button>
        </div>

        {countdown !== null ? (
          <div className="mb-4 bg-red-950 border border-red-800 rounded-xl p-4 text-center">
            <p className="text-xs text-red-400 uppercase tracking-widest mb-1">Anomaly Active</p>
            <p className="font-mono text-4xl font-bold text-red-300 animate-pulse">{countdown}s</p>
            <p className="text-xs text-gray-500 mt-1">Watch the dashboard…</p>
          </div>
        ) : (
          <div className="mb-4">
            <label className="text-xs text-gray-400 mb-2 block">Anomaly Duration</label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min={10}
                max={60}
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                className="flex-1 accent-red-500"
              />
              <span className="text-sm text-gray-300 font-mono w-10 text-right">{duration}s</span>
            </div>
          </div>
        )}

        <button
          onClick={triggerAnomaly}
          disabled={loading || countdown !== null}
          className="w-full bg-red-600 hover:bg-red-500 active:scale-95 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-bold py-3 rounded-lg transition-all text-sm"
        >
          {loading ? 'Injecting…' : countdown !== null ? '🚨 Anomaly Running…' : '🚨 Trigger AFib Anomaly'}
        </button>

        <p className="text-xs text-gray-600 mt-3 text-center">
          POST /trigger-anomaly → ZETIC detects → Gemini assesses → Dashboard alerts
        </p>
      </div>
    </div>
  )
}
