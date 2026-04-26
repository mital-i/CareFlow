import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import AgentStatusBar from './components/AgentStatusBar'
import VitalsChart from './components/VitalsChart'
import RiskPanel from './components/RiskPanel'
import ActionLog from './components/ActionLog'
import AnomalyHistory from './components/AnomalyHistory'
import DemoControls from './components/DemoControls'
import SystemFlowDiagram from './components/SystemFlowDiagram'

const WS_URL = 'ws://localhost:8000/ws'
const API_BASE = 'http://localhost:8000'

const SEVERITY_TOAST = {
  LOW: null,
  MEDIUM: (note) => toast(note, { icon: '⚠️' }),
  HIGH: (note) => toast.error(`HIGH RISK: ${note}`),
  CRITICAL: (note) => toast.error(`🚨 CRITICAL: ${note}`, { duration: 10000 }),
}

export default function App() {
  const [patients, setPatients] = useState([])
  const [selectedPatient, setSelectedPatient] = useState('patient-001')
  const [vitals, setVitals] = useState([])
  const [assessmentsByPatient, setAssessmentsByPatient] = useState({})
  const [actionLogByPatient, setActionLogByPatient] = useState({})
  const [anomalyHistory, setAnomalyHistory] = useState([])
  const [wsConnected, setWsConnected] = useState(false)
  const [flashRed, setFlashRed] = useState(false)
  const [criticalBanner, setCriticalBanner] = useState(null)
  const [showFlowDiagram, setShowFlowDiagram] = useState(false)
  const [showDemoControls, setShowDemoControls] = useState(false)
  const wsRef = useRef(null)
  const bannerTimerRef = useRef(null)
  const reconnectTimerRef = useRef(null)
  const shouldReconnectRef = useRef(false)
  const esRef = useRef(null)

  // Fetch patient list on mount
  useEffect(() => {
    fetch(`${API_BASE}/patients`)
      .then((r) => r.json())
      .then(setPatients)
      .catch(() => {})
  }, [])

  // Fetch anomaly history whenever patient changes or new assessment arrives
  const fetchAnomalyHistory = useCallback(() => {
    fetch(`${API_BASE}/anomalies/${selectedPatient}`)
      .then((r) => r.json())
      .then(setAnomalyHistory)
      .catch(() => {})
  }, [selectedPatient])

  useEffect(() => {
    fetchAnomalyHistory()
  }, [fetchAnomalyHistory])

  // WebSocket for risk assessments and acknowledgments
  const connectWs = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return
    }

    shouldReconnectRef.current = true
    clearTimeout(reconnectTimerRef.current)
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => setWsConnected(true)
    ws.onclose = () => {
      if (wsRef.current !== ws) return
      wsRef.current = null
      setWsConnected(false)
      if (shouldReconnectRef.current) {
        reconnectTimerRef.current = setTimeout(connectWs, 2000)
      }
    }
    ws.onerror = () => ws.close()

    ws.onmessage = (e) => {
      const { type, data } = JSON.parse(e.data)

      if (type === 'risk_assessment') {
        const pid = data.patient_id
        setAssessmentsByPatient((prev) => ({ ...prev, [pid]: data }))
        setActionLogByPatient((prev) => {
          const existing = prev[pid] ?? []
          if (data.assessment_id && existing.some((e) => e.assessment_id === data.assessment_id)) {
            return prev
          }
          return { ...prev, [pid]: [data, ...existing].slice(0, 50) }
        })
        fetchAnomalyHistory()

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

      if (type === 'acknowledged') {
        setActionLogByPatient((prev) => {
          const updated = {}
          for (const [pid, entries] of Object.entries(prev)) {
            updated[pid] = entries.map((e) =>
              e.assessment_id === data.assessment_id ? { ...e, acknowledged: true } : e
            )
          }
          return updated
        })
        setAssessmentsByPatient((prev) => {
          const updated = { ...prev }
          for (const pid of Object.keys(updated)) {
            if (updated[pid]?.assessment_id === data.assessment_id) {
              updated[pid] = { ...updated[pid], acknowledged: true }
            }
          }
          return updated
        })
      }
    }
  }, [fetchAnomalyHistory])

  useEffect(() => {
    connectWs()
    return () => {
      shouldReconnectRef.current = false
      clearTimeout(reconnectTimerRef.current)
      wsRef.current?.close()
      wsRef.current = null
      clearTimeout(bannerTimerRef.current)
    }
  }, [connectWs])

  // SSE vitals stream — reconnects when patient changes
  useEffect(() => {
    esRef.current?.close()
    setVitals([])

    const es = new EventSource(`${API_BASE}/vitals/stream/${selectedPatient}`)
    esRef.current = es

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
  }, [selectedPatient])

  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'f' || e.key === 'F') setShowFlowDiagram((v) => !v)
      if (e.key === 'd' || e.key === 'D') setShowDemoControls((v) => !v)
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [])

  const selectedPatientData = patients.find((p) => p.patient_id === selectedPatient)
  const latestAssessment = assessmentsByPatient[selectedPatient] ?? null
  const actionLog = actionLogByPatient[selectedPatient] ?? []
  const isCritical = criticalBanner?.severity_level === 'CRITICAL'

  const handleAcknowledge = async (assessmentId) => {
    await fetch(`${API_BASE}/acknowledge/${assessmentId}`, { method: 'POST' })
  }

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

      {/* Patient selector */}
      {patients.length > 0 && (
        <div className="bg-gray-900 border-b border-gray-800 px-6 py-2 flex items-center gap-2">
          <span className="text-xs text-gray-500 mr-2">PATIENT</span>
          {patients.map((p) => (
            <button
              key={p.patient_id}
              onClick={() => setSelectedPatient(p.patient_id)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                selectedPatient === p.patient_id
                  ? 'bg-blue-900 border-blue-600 text-blue-200'
                  : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500'
              }`}
            >
              <span className="font-semibold">{p.name}</span>
              <span className="text-gray-500 ml-1.5">{p.conditions[0]}</span>
            </button>
          ))}
        </div>
      )}

      {/* Critical alert banner */}
      {criticalBanner && (
        <div className={`slide-up border-b px-6 py-3 flex items-center justify-between ${isCritical ? 'bg-red-950 border-red-800' : 'bg-orange-950 border-orange-800'}`}>
          <div className="flex items-center gap-3">
            <span className="animate-pulse text-xl">{isCritical ? '🚨' : '⚠️'}</span>
            <div>
              <p className={`font-bold text-sm ${isCritical ? 'text-red-300' : 'text-orange-300'}`}>
                {criticalBanner.severity_level} ALERT — {selectedPatientData?.name ?? criticalBanner.patient_id}
              </p>
              <p className="text-xs text-gray-400 mt-0.5">{criticalBanner.doctor_note}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-xs font-mono px-2 py-1 rounded font-bold ${isCritical ? 'bg-red-900 text-red-200' : 'bg-orange-900 text-orange-200'}`}>
              Risk {Math.round(criticalBanner.risk_score * 100)}%
            </span>
            {!criticalBanner.acknowledged && (
              <button
                onClick={() => handleAcknowledge(criticalBanner.assessment_id)}
                className="text-xs px-3 py-1 rounded bg-green-800 hover:bg-green-700 text-green-200 font-semibold transition-colors"
              >
                Acknowledge
              </button>
            )}
            <button onClick={() => setCriticalBanner(null)} className="text-gray-500 hover:text-gray-300 text-xl ml-2 leading-none">×</button>
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="flex-1 grid grid-cols-12 gap-4 p-4">
        {/* Left: Vitals + Risk */}
        <section className="col-span-8 flex flex-col gap-4">
          <VitalsChart
            vitals={vitals}
            hasAnomaly={flashRed}
            patientName={selectedPatientData ? `${selectedPatientData.name} (${selectedPatient})` : selectedPatient}
          />
          {latestAssessment && (
            <RiskPanel
              key={latestAssessment.assessment_id}
              assessment={latestAssessment}
              onAcknowledge={handleAcknowledge}
            />
          )}
        </section>

        {/* Right: Action Log + Anomaly History */}
        <section className="col-span-4 flex flex-col gap-4">
          <ActionLog entries={actionLog} />
          <AnomalyHistory entries={anomalyHistory} />
        </section>
      </main>

      {showDemoControls && (
        <DemoControls
          onClose={() => setShowDemoControls(false)}
          selectedPatient={selectedPatient}
          patientName={selectedPatientData?.name ?? selectedPatient}
        />
      )}
      {showFlowDiagram && <SystemFlowDiagram onClose={() => setShowFlowDiagram(false)} />}
    </div>
  )
}
