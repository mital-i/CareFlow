import { useEffect, useState } from 'react'

const API_BASE = 'http://localhost:8000'

const AGENTS = [
  { key: 'monitor_agent',      label: 'VitalMonitor',   icon: '🫀', desc: 'ZETIC on-device' },
  { key: 'coordinator_agent',  label: "Doctor's Asst",  icon: '🧠', desc: 'Gemini + Fetch.ai' },
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
        const agent = statuses[key]
        const alive = agent?.status === 'running'
        return (
          <div key={key} className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${alive ? 'bg-green-400' : 'bg-gray-600'}`} />
            <span className="text-sm font-medium">{icon} {label}</span>
            <span className="text-xs text-gray-500">{desc}</span>
          </div>
        )
      })}
      <div className="ml-auto flex items-center gap-2 text-xs text-gray-600">
        <span className="px-2 py-0.5 border border-gray-700 rounded">Fetch.ai Agentverse</span>
        <span className="px-2 py-0.5 border border-gray-700 rounded">ZETIC Melange</span>
        <span className="px-2 py-0.5 border border-gray-700 rounded">Vertex AI Gemini</span>
      </div>
    </div>
  )
}
