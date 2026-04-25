import { useEffect, useState } from 'react'

const API_BASE = 'http://localhost:8000'

const AGENTS = [
  { key: 'monitor_agent',     label: 'VitalMonitor',  icon: '🫀', desc: 'ZETIC on-device' },
  { key: 'coordinator_agent', label: "Doctor's Asst", icon: '🧠', desc: 'Gemini + Fetch.ai' },
]

const TECH_BADGES = [
  { label: 'Fetch.ai Agentverse', color: 'border-blue-800 text-blue-400' },
  { label: 'ZETIC Melange',       color: 'border-purple-800 text-purple-400' },
  { label: 'Vertex AI Gemini',    color: 'border-emerald-800 text-emerald-400' },
]

export default function AgentStatusBar() {
  const [statuses, setStatuses] = useState({})

  useEffect(() => {
    const poll = async () => {
      try {
        const res = await fetch(`${API_BASE}/agents/status`)
        const data = await res.json()
        setStatuses(data)
      } catch {
        setStatuses({})
      }
    }
    poll()
    const id = setInterval(poll, 10000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="bg-gray-900 border-b border-gray-800 px-6 py-2 flex items-center gap-6">
      <span className="text-xs text-gray-500 uppercase tracking-widest mr-2">Agents</span>
      {AGENTS.map(({ key, label, icon, desc }) => {
        const alive = statuses[key]?.status === 'running'
        return (
          <div key={key} className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              {alive && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />}
              <span className={`relative inline-flex rounded-full h-2 w-2 ${alive ? 'bg-green-400' : 'bg-gray-600'}`} />
            </span>
            <span className="text-sm font-medium">{icon} {label}</span>
            <span className="text-xs text-gray-500">{desc}</span>
          </div>
        )
      })}
      <div className="ml-auto flex items-center gap-2 text-xs">
        {TECH_BADGES.map(({ label, color }) => (
          <span key={label} className={`px-2 py-0.5 border rounded font-medium ${color}`}>{label}</span>
        ))}
      </div>
    </div>
  )
}
