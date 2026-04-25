# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Python backend
```bash
# Install dependencies (from repo root)
pip install -r requirements.txt

# Seed the demo patient into MongoDB (required before first run)
python scripts/seed.py

# Start everything at once
./start.sh

# Run individual services
uvicorn api.main:app --reload --port 8000   # FastAPI gateway
python agents/agent1_monitor.py             # Vital Monitor Agent (port 8001)
python agents/agent2_coordinator.py         # Coordinator Agent (port 8002)
```

### React dashboard
```bash
cd careflow-ui
npm install
npm run dev      # dev server at http://localhost:5173
npm run build
```

### Trigger a demo anomaly
```bash
curl -X POST http://localhost:8000/trigger-anomaly \
     -H "Content-Type: application/json" \
     -d '{"patient_id":"patient-001","duration_seconds":30}'
```

## Architecture

CareFlow is a linear event pipeline: **Vitals Generator → Heuristic Anomaly Detection → AnomalyEvent → MedGemma/Agent Assessment → Dashboard**.

All Python modules run from the repo root and use `sys.path.insert(0, "..")` so imports are always relative to root (e.g. `from models.schemas import ...`, not relative imports).

### Data flow

```
vitals/generator.py  ──1 Hz──▶  vitals/api.py SSE /vitals/stream/{patient_id}
  └──▶  vitals/anomaly.py (AnomalyDetector)  ──AnomalyEvent──▶  Mongo anomaly_events

Agent path:
agents/agent1_monitor.py  ──process_vitals──▶  Fetch.ai Chat Protocol
  ──▶ agents/agent2_coordinator.py ──▶ risk/classifier.py (MedGemma via Ollama)
  ──▶ POST /internal/broadcast ──▶ WebSocket /ws ──▶ careflow-ui (React)
```

The demo trigger (`POST /trigger-anomaly`) updates per-patient in-memory state in `vitals/generator.py`. The next vitals reading for that patient immediately spikes HR, dips SpO2, and drops HRV for the demo window before smoothly recovering.

### Key design decisions

**Two Fetch.ai uAgents, not five.** Agent 1 (Monitor, port 8001) owns the anomaly detection loop and publishes `AnomalyMessage`. Agent 2 (Coordinator, port 8002) owns MedGemma classification and broadcasts results to the dashboard. Their Agentverse addresses live in `agents/addresses.py` and are loaded via env vars `AGENT_MONITOR_ADDRESS` / `AGENT_COORDINATOR_ADDRESS`.

**Coordinator-to-dashboard bridge.** The Coordinator agent is a separate process from FastAPI, so it cannot call `manager.broadcast()` directly. It POSTs to `POST /internal/broadcast` (FastAPI), which calls the WebSocket manager. This is the glue between the agent world and the UI world.

**Fallback in risk classifier.** `risk/classifier.py` falls back to rule-based thresholds if Ollama/MedGemma is unavailable. Both paths produce identical output types.

**Mongo collections stay simple.** Person 1's data layer uses only `patients`, `vitals_history`, and `anomaly_events`. The seeded demo patient is `patient-001` / Margaret Chen.

### Environment setup

Copy `.env.example` → `.env` and fill in:
- `MONGODB_URI` — Atlas M0 connection string
- `OLLAMA_HOST` / `GEMMA_MODEL` — Ollama must be running locally (`ollama serve`); pull MedGemma with `ollama pull medgemma`
- `AGENT_MONITOR_SEED_PHRASE` / `AGENT_COORDINATOR_SEED_PHRASE` — deterministic agent identity; address is printed to console on first run, then set `AGENT_MONITOR_ADDRESS` / `AGENT_COORDINATOR_ADDRESS`
- `AGENTVERSE_KEY` — Fetch.ai Agentverse API key for mailbox messaging

### React dashboard key bindings
- **D** — toggle Demo Controls overlay (Trigger Anomaly button)
- **F** — toggle System Flow Diagram (for judge pitch)

SSE vitals events from `/vitals/stream/{patient_id}` have shape `{ type: "vitals", data: VitalsPayload }`, with named `"anomaly"` SSE events carrying `{ type: "anomaly", data: AnomalyEvent }`. WebSocket events from the backend all have shape `{ type: string, data: object }`; the main dashboard WebSocket event type remains `"risk_assessment"`.
