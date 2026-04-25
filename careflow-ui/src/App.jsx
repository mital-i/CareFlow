import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import AgentStatusBar from './components/AgentStatusBar'
import VitalsChart from './components/VitalsChart'
import RiskPanel from './components/RiskPanel'
import ActionLog from './components/ActionLog'
import DemoControls from './components/DemoControls'
import SystemFlowDiagram from './components/SystemFlowDiagram'

const WS_URL = 'ws://localhost:8000/ws'
const API_BASE = 'http://localhost:8000'
const SELECTED_PATIENT = 'patient-001'

const SEVERITY_TOAST = {
  LOW: null,
  MEDIUM: (note) => toast(note, { icon: '⚠️' }),
  HIGH: (note) => toast.error(`HIGH RISK: ${note}`),
  CRITICAL: (note) => toast.error(`🚨 CRITICAL: ${note}`, { duration: 10000 }),
}

export default function App() {
  const [vitals, setVitals] = useState([])
  const [latestAssessment, setLatestAssessment] = useState(null)
  const [actionLog, setActionLog] = useState([])
  const [wsConnected, setWsConnected] = useState(false)
  const [flashRed, setFlashRed] = useState(false)
  const [showFlowDiagram, setShowFlowDiagram] = useState(false)
  const [showDemoControls, setShowDemoControls] = useState(false)
  const wsRef = useRef(null)

  const connectWs = useCallback(() => {
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => setWsConnected(true)
    ws.onclose = () => {
      setWsConnected(false)
      setTimeout(connectWs, 2000)
    }
    ws.onerror = () => ws.close()

    ws.onmessage = (e) => {
      const { type, data } = JSON.parse(e.data)
      if (type === 'risk_assessment') {
        setLatestAssessment(data)
        setActionLog((prev) => [data, ...prev].slice(0, 50))

        const severity = data.severity_level
        if (['HIGH', 'CRITICAL'].includes(severity)) {
          setFlashRed(true)
          setTimeout(() => setFlashRed(false), 1600)
        }
        const showToast = SEVERITY_TOAST[severity]
        if (showToast) showToast(data.doctor_note)
      }
    }
  }, [])

  useEffect(() => {
    connectWs()
    return () => wsRef.current?.close()
  }, [connectWs])

  useEffect(() => {
    const es = new EventSource(`${API_BASE}/vitals/stream/${SELECTED_PATIENT}`)
    es.onmessage = (e) => {
      const payload = JSON.parse(e.data)
      setVitals((prev) => [...prev.slice(-59), { ...payload, time: new Date(payload.timestamp).toLocaleTimeString() }])
    }
    return () => es.close()
  }, [])

  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'f' || e.key === 'F') setShowFlowDiagram((v) => !v)
      if (e.key === 'd' || e.key === 'D') setShowDemoControls((v) => !v)
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [])

  return (
    <div className={`min-h-screen flex flex-col transition-colors duration-300 ${flashRed ? 'flash-critical' : ''}`}>
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          <span className="font-bold text-lg tracking-tight">CareFlow</span>
          <span className="text-gray-500 text-sm">Autonomous Patient Monitoring</span>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span className={`flex items-center gap-1 ${wsConnected ? 'text-green-400' : 'text-red-400'}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-green-400' : 'bg-red-400'}`} />
            {wsConnected ? 'Live' : 'Reconnecting…'}
          </span>
          <span>F = flow diagram · D = demo controls</span>
        </div>
      </header>

      <AgentStatusBar />

      {/* Main content */}
      <main className="flex-1 grid grid-cols-12 gap-4 p-4">
        {/* Left: Vitals Chart */}
        <section className="col-span-8 flex flex-col gap-4">
          <VitalsChart vitals={vitals} hasAnomaly={flashRed} />
          {latestAssessment && <RiskPanel assessment={latestAssessment} />}
        </section>

        {/* Right: Action Log */}
        <section className="col-span-4">
          <ActionLog entries={actionLog} />
        </section>
      </main>

      {showDemoControls && <DemoControls onClose={() => setShowDemoControls(false)} />}
      {showFlowDiagram && <SystemFlowDiagram onClose={() => setShowFlowDiagram(false)} />}
    </div>
  )
}
