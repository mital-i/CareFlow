# CareFlow

## Person 1: Data & Edge Layer

This layer streams configurable wearable vitals, runs local heuristic anomaly detection, stores demo data in MongoDB Atlas, and streams live vitals to the dashboard with Server-Sent Events.

### Install

```bash
pip install -r requirements.txt
```

Create `.env` from `.env.example` and set `MONGODB_URI`.

By default CareFlow uses the synthetic source:

```bash
VITALS_SOURCE=synthetic
```

### Seed Demo Data

```bash
python scripts/seed.py
```

This resets the demo data for `patient-001`, inserts Margaret Chen, and adds 20 normal vitals readings.

### Start The API

```bash
uvicorn api.main:app --reload --port 8000
```

Startup logs should show Mongo, demo patient, vitals stream, and trigger endpoint readiness.

### Open The SSE Stream

```bash
curl -N http://localhost:8000/vitals/stream/patient-001
```

Each vitals event is shaped as:

```json
{"type":"vitals","data":{"patient_id":"patient-001","heart_rate":74,"spo2":98,"hrv":55}}
```

### Trigger Anomaly

```bash
curl -X POST http://localhost:8000/trigger-anomaly \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"patient-001"}'
```

Within 1-2 seconds, heart rate spikes, SpO2 dips, HRV drops, and the local detector emits an `AnomalyEvent`.

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

“CareFlow streams wearable vitals through a heuristic anomaly detector. Once a clinically relevant deviation is detected, a compact anomaly event is forwarded to the agent pipeline where MedGemma classifies risk and surfaces a doctor-facing assessment to the dashboard in real time.”
