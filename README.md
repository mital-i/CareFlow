# CareFlow

CareFlow is a real-time patient monitoring pipeline: wearable vitals → heuristic anomaly detection → MedGemma risk classification → doctor-facing dashboard.

## Setup

### 1. Python backend

```bash
pip install -r requirements.txt
```

Copy `.env.example` → `.env` and fill in `MONGODB_URI`, `AGENT_MONITOR_SEED_PHRASE`, `AGENT_COORDINATOR_SEED_PHRASE`, and `AGENTVERSE_KEY`.

Seed the demo patient (run once):

```bash
python scripts/seed.py
```

### 2. React dashboard

```bash
cd careflow-ui
npm install
```

---

## Running the Full System

Open **5 terminals**. Terminals 1–3 require your Python venv active.

**Terminal 1 — Ollama (MedGemma)**
```bash
ollama serve
```
Pull the model once if you haven't already: `ollama pull medgemma`

**Terminal 2 — FastAPI gateway** *(venv)*
```bash
uvicorn api.main:app --reload --port 8000
```

**Terminal 3 — Agent 1: Vital Monitor** *(venv)*
```bash
python agents/agent1_monitor.py
```
Note the printed agent address and set `AGENT_MONITOR_ADDRESS` in `.env`.

**Terminal 4 — Agent 2: Coordinator** *(venv)*
```bash
python agents/agent2_coordinator.py
```
Note the printed agent address and set `AGENT_COORDINATOR_ADDRESS` in `.env`.

**Terminal 5 — React dashboard**
```bash
cd careflow-ui && npm run dev
```
Open `http://localhost:5173`.

---

## Triggering a Demo Anomaly

From the dashboard: press **D** to open Demo Controls, then click **Trigger AFib Anomaly**.

Or via curl:

```bash
curl -X POST http://localhost:8000/trigger-anomaly \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"patient-001","duration_seconds":30}'
```

Within 1–2 seconds, HR spikes, SpO2 dips, HRV drops → anomaly detected → MedGemma classifies risk → RiskPanel appears on dashboard.

### Dashboard key bindings
- **D** — Demo Controls overlay
- **F** — System Flow Diagram

---

## Vitals Stream

```bash
curl -N http://localhost:8000/vitals/stream/patient-001
```

Each event: `{"type":"vitals","data":{"patient_id":"patient-001","heart_rate":74,"spo2":98,"hrv":55}}`

By default uses the synthetic source (`VITALS_SOURCE=synthetic`).

### Replay BIDMC Vitals

CareFlow can also replay normalized CSV vitals through the same API and dashboard contract. The recommended public source is the [BIDMC PPG and Respiration Dataset](https://physionet.org/content/bidmc/1.0.0/), which provides 1 Hz HR and SpO2 numerics in CSV form. BIDMC contains realistic ICU vital patterns, but it does not provide clinical anomaly labels; CareFlow marks replay anomalies with the same demo thresholds used by the local detector.

Prepare a replay file from PhysioNet:

```bash
python scripts/prepare_bidmc_replay.py \
  --input https://physionet.org/files/bidmc/1.0.0/bidmc_csv/bidmc_25_Numerics.csv \
  --output vitals/replays/bidmc_25_careflow.csv
```

Run the API in replay mode:

```bash
VITALS_SOURCE=replay \
VITALS_REPLAY_PATH=vitals/replays/bidmc_25_careflow.csv \
VITALS_REPLAY_LOOP=true \
uvicorn api.main:app --reload --port 8000
```

Replay rows still emit the same `VitalsPayload` shape used by the React dashboard. The BIDMC converter derives a simple demo HRV proxy from rolling HR variability so the existing HR/SpO2/HRV charts and anomaly detector continue to work.

### Pitch

“CareFlow processes raw wearable vitals locally on-device using the ZETIC edge layer. The raw stream never needs to leave the device for initial detection. Once the local model detects a clinically relevant deviation, it sends only a compact anomaly event to the cloud AI pipeline for risk assessment and doctor-facing summarization.”
