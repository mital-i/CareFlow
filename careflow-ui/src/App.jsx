import { useEffect, useReducer, useState } from 'react'
import toast from 'react-hot-toast'
import AgentStatusBar from './components/AgentStatusBar'
import PatientList from './components/PatientList'
import VitalsChart from './components/VitalsChart'
import RiskGauge from './components/RiskGauge'
import ActionLog from './components/ActionLog'
import ProviderPanel from './components/ProviderPanel'
import DemoControls from './components/DemoControls'
import SystemFlowDiagram from './components/SystemFlowDiagram'
import { useWebSocket } from './hooks/useWebSocket'

const initialState = {
  patients: [],
  selectedPatient: null,
  riskScore: 0,
  severityLevel: 'LOW',
  actionLog: [],
  providerAlerts: [],
  agentStatuses: [],
}

function reducer(state, action) {
  switch (action.type) {
    case 'SET_PATIENTS':
      return { ...state, patients: action.payload, selectedPatient: action.payload[0] ?? null }
    case 'SELECT_PATIENT':
      return { ...state, selectedPatient: action.payload }
    case 'RISK_UPDATE':
      return { ...state, riskScore: action.payload.risk_score, severityLevel: action.payload.severity_level }
    case 'ACTION_DECISION': {
      const entry = action.payload
      const newLog = [entry, ...state.actionLog].slice(0, 50)
      const isHigh = ['HIGH', 'CRITICAL'].includes(entry.severity_level)
      const alerts = isHigh ? [entry, ...state.providerAlerts].slice(0, 10) : state.providerAlerts
      return { ...state, actionLog: newLog, providerAlerts: alerts }
    }
    case 'SET_AGENTS':
      return { ...state, agentStatuses: action.payload }
    default:
      return state
  }
}

export default function App() {
  const [state, dispatch] = useReducer(reducer, initialState)
  const [showDemo, setShowDemo] = useState(false)
  const [showFlow, setShowFlow] = useState(false)

  const { connected } = useWebSocket('ws://localhost:8000/ws', (event) => {
    const msg = JSON.parse(event.data)
    if (msg.type === 'action_decision') {
      dispatch({ type: 'ACTION_DECISION', payload: msg.data })
      dispatch({ type: 'RISK_UPDATE', payload: msg.data })
      toast(`${msg.data.severity_level} — ${msg.data.action_tier}`, {
        icon: msg.data.severity_level === 'CRITICAL' ? '🚨' : '⚠️',
      })
    }
  })

  useEffect(() => {
    fetch('/api/patients')
      .then((r) => r.json())
      .then((data) => dispatch({ type: 'SET_PATIENTS', payload: data }))
      .catch(console.error)

    fetch('/api/agents/status')
      .then((r) => r.json())
      .then((data) => dispatch({ type: 'SET_AGENTS', payload: data }))
      .catch(console.error)
  }, [])

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'd' || e.key === 'D') setShowDemo((v) => !v)
      if (e.key === 'f' || e.key === 'F') setShowFlow((v) => !v)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <AgentStatusBar agents={state.agentStatuses} connected={connected} />

      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar — patient list */}
        <aside className="w-64 border-r border-gray-800 overflow-y-auto p-3 shrink-0">
          <PatientList
            patients={state.patients}
            selected={state.selectedPatient}
            onSelect={(p) => dispatch({ type: 'SELECT_PATIENT', payload: p })}
          />
        </aside>

        {/* Main panel */}
        <main className="flex-1 flex flex-col overflow-hidden p-4 gap-4">
          <div className="flex gap-4 flex-1 overflow-hidden">
            <div className="flex-1 flex flex-col gap-4 overflow-hidden">
              {state.selectedPatient && (
                <VitalsChart patientId={state.selectedPatient.patient_id} />
              )}
            </div>
            <div className="w-48 flex flex-col gap-4">
              <RiskGauge score={state.riskScore} severity={state.severityLevel} />
            </div>
          </div>
        </main>

        {/* Right panel — action log + provider */}
        <aside className="w-80 border-l border-gray-800 flex flex-col overflow-hidden">
          <ProviderPanel alerts={state.providerAlerts} />
          <ActionLog entries={state.actionLog} />
        </aside>
      </div>

      {showDemo && <DemoControls onClose={() => setShowDemo(false)} />}
      {showFlow && <SystemFlowDiagram onClose={() => setShowFlow(false)} />}
    </div>
  )
}
