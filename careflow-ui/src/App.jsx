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
  const [criticalBanner, setCriticalBanner] = useState(null)
  const [showFlowDiagram, setShowFlowDiagram] = useState(false)
  const [showDemoControls, setShowDemoControls] = useState(false)
  const wsRef = useRef(null)
  const bannerTimerRef = useRef(null)

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
          setTimeout(() => setFlashRed(false), 2400)

          setCriticalBanner(data)
          clearTimeout(bannerTimerRef.current)
          bannerTimerRef.current = setTimeout(() => setCriticalBanner(null), 8000)
        }
        const showToast = SEVERITY_TOAST[severity]
        if (showToast) showToast(data.doctor_note)
      }
    }
  }, [])

  useEffect(() => {
    connectWs()
    return () => {
      wsRef.current?.close()
      clearTimeout(bannerTimerRef.current)
    }
  }, [connectWs])

  useEffect(() => {
    const es = new EventSource(`${API_BASE}/vitals/stream/${SELECTED_PATIENT}`)
    es.onmessage = (e) => {
      const event = JSON.parse(e.data)
      const payload = event.type === 'vitals' ? event.data : event
      setVitals((prev) => [...prev.slice(-59), { ...payload, time: new Date(payload.timestamp).toLocaleTimeString() }])
    }
    es.addEventListener('anomaly', (e) => {
      const event = JSON.parse(e.data)
      if (event.type === 'anomaly') {
        setFlashRed(true)
        setTimeout(() => setFlashRed(false), 2400)
      }
    })
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

  const isCritical = criticalBanner?.severity_level === 'CRITICAL'

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
          <span className={`flex items-center gap-1.5 ${wsConnected ? 'text-green-400' : 'text-red-400'}`}>
            <span className="relative flex h-1.5 w-1.5">
              {wsConnected && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />}
              <span className={`relative inline-flex rounded-full h-1.5 w-1.5 ${wsConnected ? 'bg-green-400' : 'bg-red-400'}`} />
            </span>
            {wsConnected ? 'Live' : 'Reconnecting…'}
          </span>
          <span>F = flow diagram · D = demo controls</span>
        </div>
      </header>

      <AgentStatusBar />

      {/* Critical alert banner */}
      {criticalBanner && (
        <div className={`slide-up border-b px-6 py-3 flex items-center justify-between ${isCritical ? 'bg-red-950 border-red-800' : 'bg-orange-950 border-orange-800'}`}>
          <div className="flex items-center gap-3">
            <span className="animate-pulse text-xl">{isCritical ? '🚨' : '⚠️'}</span>
            <div>
              <p className={`font-bold text-sm ${isCritical ? 'text-red-300' : 'text-orange-300'}`}>
                {criticalBanner.severity_level} ALERT — Margaret Chen (patient-001)
              </p>
              <p className="text-xs text-gray-400 mt-0.5">{criticalBanner.doctor_note}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-xs font-mono px-2 py-1 rounded font-bold ${isCritical ? 'bg-red-900 text-red-200' : 'bg-orange-900 text-orange-200'}`}>
              Risk {Math.round(criticalBanner.risk_score * 100)}%
            </span>
            <span className={`text-xs px-2 py-1 rounded font-semibold ${isCritical ? 'bg-red-900 text-red-200' : 'bg-orange-900 text-orange-200'}`}>
              {criticalBanner.action_tier?.replace(/_/g, ' ')}
            </span>
            <button onClick={() => setCriticalBanner(null)} className="text-gray-500 hover:text-gray-300 text-xl ml-2 leading-none">×</button>
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="flex-1 grid grid-cols-12 gap-4 p-4">
        {/* Left: Vitals Chart */}
        <section className="col-span-8 flex flex-col gap-4">
          <VitalsChart vitals={vitals} hasAnomaly={flashRed} />
          {latestAssessment && (
            <RiskPanel key={latestAssessment.assessment_id} assessment={latestAssessment} />
          )}
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
