# CareFlow — Claude Context

CareFlow is a 36-hour hackathon project for LA Hacks 2026. Full monorepo boilerplate was scaffolded on 2026-04-24.

## Project Overview

An autonomous network of healthcare agents that detects patient health risks on-device and coordinates personalized interventions before emergencies happen.

**Prize targets:** Fetch.ai Agentverse ($2,500), ZETIC On-Device AI ($1,000), Catalyst for Care (Healthcare), MongoDB Atlas, Arista Networks.

**Note:** ElevenLabs is explicitly excluded from this implementation despite appearing in the PRD. The WBS PDF is the source of truth and overrides the PRD where they conflict.

## Monorepo Structure

```
/agents          — All 5 Fetch.ai uAgents + shared protocols
/api             — FastAPI gateway + WebSocket hub (Part 4)
/careflow-ui     — React + Tailwind + Recharts dashboard (Part 4)
/db              — Shared MongoDB utility (Part 1 owns)
/models          — All Pydantic models — shared contract (Part 1 owns)
/risk            — LangGraph pipeline + Vertex AI Gemini classifier (Part 2)
/scripts         — Database seed script
/tests           — Integration tests
/vitals          — Synthetic vitals generator + SSE endpoint (Part 1)
/zetic           — ZETIC Melange on-device anomaly detection (Part 1)
```

## Shared Contracts

These files are imported by multiple parts. Do not change field names or signatures without notifying all teammates.

| File | Owner | Consumers |
|------|-------|-----------|
| `models/schemas.py` | Part 1 | All parts |
| `db/db.py` | Part 1 | Parts 1, 2, 3 |
| `agents/addresses.py` | Part 1 | Parts 1, 2, 3, 4 |
| `agents/message_types.py` | Part 3 | Parts 1, 2, 3 |
| `agents/ws_broadcaster.py` | Parts 3 & 4 | Parts 3, 4 |
| `vitals/api.py` | Part 1 | Part 4 |
| `tests/network_test.py` | Part 3 | Part 4 |
| `scripts/seed.py` | Part 1 | Part 4 |
| `start.sh` | Part 4 | All parts |
| `.env.example` | Parts 1, 2 | Parts 1, 2, 4 |

## Team Parts

### Part 1 — Data + ZETIC
Owns: `models/`, `db/`, `vitals/`, `zetic/`, `scripts/`

Key files:
- `models/schemas.py` — all Pydantic models for MongoDB collections
- `db/db.py` — `get_patient()`, `save_vitals()`, `save_risk_assessment()`, `save_action_log()`
- `vitals/generator.py` — 1 Hz synthetic vitals stream with `trigger_anomaly()` demo mode
- `vitals/api.py` — SSE endpoint at `/vitals/stream/{patient_id}`
- `zetic/melange_agent.py` — ZETIC Melange wrapper; real SDK calls are stubbed with `TODO` comments
- `zetic/benchmark.py` — latency benchmark for the pitch (target: <100ms per inference)
- `scripts/seed.py` — seeds 3 demo patients + 30 days of vitals; run with `python scripts/seed.py`
- `agents/agent1_vital_monitor.py` — Fetch.ai uAgent wrapping the ZETIC detector

**TODO (Part 1):** Replace the stub inference in `zetic/melange_agent.py` (lines marked `TODO`) with real ZETIC Melange SDK calls once the SDK is installed.

### Part 2 — Risk Intelligence
Owns: `risk/`, `agents/agent2_risk_assessment.py`

Key files:
- `risk/classifier.py` — Vertex AI Gemini call with exponential backoff + rule-based fallback
- `risk/pipeline.py` — LangGraph `StateGraph`: fetch_history → classify → emergency_flag → save → publish
- `risk/nodes.py` — node functions for the graph
- `risk/history.py` — builds `PatientHistory` from MongoDB for the Gemini prompt
- `risk/prompt_templates.py` — structured prompt template for risk classification
- `risk/cache.py` — in-memory cache of last 5 assessments per patient

**TODO (Part 2):** Set `GCP_PROJECT_ID` in `.env` and point `GOOGLE_APPLICATION_CREDENTIALS` at your service account key. The Vertex AI integration in `risk/classifier.py` is otherwise complete.

### Part 3 — Agent Network
Owns: `agents/agent3_coordinator.py`, `agents/agent4_patient.py`, `agents/agent5_provider.py`, `agents/protocols/`, `agents/message_types.py`, `agents/ws_broadcaster.py`

Key files:
- `agents/agent3_coordinator.py` — Core Orchestrator; receives `RiskAssessment`, queries Agents 4 & 5, applies routing logic, saves to MongoDB, broadcasts to dashboard
- `agents/agent4_patient.py` — Patient Agent; loads notification preferences from MongoDB, answers `can_receive_alert()` queries
- `agents/agent5_provider.py` — Provider Agent; simulates Mon–Fri 9–5 PT availability + on-call slot for CRITICAL
- `agents/message_types.py` — all Fetch.ai Chat Protocol message models
- `agents/addresses.py` — **fill in after Agentverse registration**

Routing logic in Agent 3:
- `score < 0.4` → `LOG_ONLY`
- `0.4–0.6` → `PATIENT_ALERT`
- `0.6–0.8` → `PATIENT_ALERT` + `PROVIDER_NOTIFY`
- `> 0.8` → `PROVIDER_NOTIFY` + `ER_DISPATCH` flag

**TODO (Parts 1–3):** Register each agent on Agentverse (run each `agentN_*.py` once to get its address) and update `agents/addresses.py`.

### Part 4 — Frontend + Glue
Owns: `api/`, `careflow-ui/`, `start.sh`

Key files:
- `api/main.py` — FastAPI app with CORS, WebSocket hub at `/ws`, health check at `/health`
- `api/routers/patients.py` — `GET /patients`, `GET /patients/{id}/history`, `GET /patients/{id}/actions`
- `api/routers/agents.py` — `GET /agents/status`, `POST /agents/trigger-anomaly`
- `api/ws_manager.py` — wraps `ws_broadcaster` for FastAPI WebSocket connections
- `careflow-ui/src/App.jsx` — root layout with reducer, WebSocket dispatch, keyboard shortcuts
- `careflow-ui/src/components/` — all 8 React components (see below)

React components:
- `AgentStatusBar` — top bar showing all 5 agents + heartbeat dots
- `PatientList` — sidebar with risk-score badges
- `VitalsChart` — real-time Recharts line chart fed from SSE; highlights anomaly windows in orange
- `RiskGauge` — SVG circular gauge 0.0–1.0 with color gradient
- `ActionLog` — scrollable reverse-chronological action log; expandable rows
- `ProviderPanel` — HIGH/CRITICAL alert cards with Acknowledge button
- `DemoControls` — dev overlay (toggle with `D` key): trigger anomaly, reset patient
- `SystemFlowDiagram` — SVG agent flow diagram (toggle with `F` key)

**TODO (Part 4):** Run `cd careflow-ui && npm install` before first dev run.

## Getting Started

```bash
# 1. Copy and fill in credentials
cp .env.example .env

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install frontend dependencies
cd careflow-ui && npm install && cd ..

# 4. Seed the database
python scripts/seed.py

# 5. Launch everything
./start.sh
```

Services after launch:
- Dashboard: http://localhost:5173
- API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Environment Variables

See `.env.example` for the full list. Minimum required to run:

```
MONGODB_URI=          # MongoDB Atlas connection string
GCP_PROJECT_ID=       # Google Cloud project ID (Part 2)
GOOGLE_APPLICATION_CREDENTIALS=  # Path to GCP service account JSON (Part 2)
AGENT1_SEED=          # Seed phrase for each agent (Parts 1–3)
...
```

## Running Tests

```bash
pytest tests/network_test.py -v
```

The integration test mocks Vertex AI and MongoDB so it can run offline.

## Demo Script (4 min)

1. **Normal state (30s)** — show dashboard with all 5 agents green, vitals streaming, risk at ~0.1
2. **Trigger anomaly (45s)** — press `D`, click "Trigger Anomaly" for P001; Agent 1 detects within 2s
3. **Risk assessment (45s)** — Agent 2 calls Vertex AI; watch `reasoning_context` populate in the action log
4. **Coordinated action (60s)** — Agent 3 routes to `PATIENT_ALERT + PROVIDER_NOTIFY`; provider panel lights up
5. **Closing (30s)** — "From anomaly to coordinated intervention: ~6 seconds"
