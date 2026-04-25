# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Python backend
```bash
# Install dependencies (from repo root)
pip install -r requirements.txt

# Seed demo patients into MongoDB (required before first run)
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

CareFlow is a linear event pipeline: **Vitals → ZETIC Alert → Gemini Assessment → Dashboard**.

All Python modules run from the repo root and use `sys.path.insert(0, "..")` so imports are always relative to root (e.g. `from models.schemas import ...`, not relative imports).

### Data flow

```
vitals/generator.py  ──1 Hz──▶  zetic/melange_agent.py  ──AnomalyEvent──▶
agents/agent1_monitor.py  ──Fetch.ai Chat Protocol──▶  agents/agent2_coordinator.py
  ──risk/classifier.py (Gemini)──▶  POST /internal/broadcast  ──▶  WebSocket /ws
  ──▶  careflow-ui (React)
```

The demo trigger (`POST /trigger-anomaly`) mutates a module-level `_anomaly_until` float in `vitals/generator.py`; all subsequent calls to `generate_vitals()` read this flag and produce elevated values.

### Key design decisions

**Two Fetch.ai uAgents, not five.** Agent 1 (Monitor, port 8001) owns the ZETIC loop and publishes `AnomalyMessage`. Agent 2 (Coordinator, port 8002) owns Gemini classification and broadcasts results to the dashboard. Their Agentverse addresses live in `agents/addresses.py` and are loaded via env vars `AGENT_MONITOR_ADDRESS` / `AGENT_COORDINATOR_ADDRESS`.

**Coordinator-to-dashboard bridge.** The Coordinator agent is a separate process from FastAPI, so it cannot call `manager.broadcast()` directly. It POSTs to `POST /internal/broadcast` (FastAPI), which calls the WebSocket manager. This is the glue between the agent world and the UI world.

**Fallbacks everywhere.** `zetic/melange_agent.py` falls back to a z-score heuristic if the ZETIC SDK isn't installed. `risk/classifier.py` falls back to rule-based thresholds if the Gemini API fails. Both paths produce identical output types.

**Shared Pydantic models vs Fetch.ai models.** `models/schemas.py` holds Pydantic v2 models used throughout Python. `agents/message_types.py` holds separate `uagents.Model` subclasses required by the Fetch.ai Chat Protocol — the Coordinator manually converts between them.

### Environment setup

Copy `.env.example` → `.env` and fill in:
- `MONGODB_URI` — Atlas M0 connection string
- `OLLAMA_HOST` / `GEMMA_MODEL` — Ollama must be running locally (`ollama serve`); default model is `gemma2:2b`
- `AGENT_MONITOR_SEED` / `AGENT_COORDINATOR_SEED` — deterministic agent identity; print the generated address on first run and set `AGENT_MONITOR_ADDRESS` / `AGENT_COORDINATOR_ADDRESS`
- `ZETIC_MODEL_KEY` / `ZETIC_PERSONAL_KEY` — only needed if using real ZETIC SDK (heuristic fallback works without these)

### React dashboard key bindings
- **D** — toggle Demo Controls overlay (Trigger Anomaly button)
- **F** — toggle System Flow Diagram (for judge pitch)

WebSocket events from the backend all have shape `{ type: string, data: object }`. Currently the only event type is `"risk_assessment"`.
