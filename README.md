# CareFlow

## Person 1: Data & Edge Layer

This layer generates synthetic wearable vitals, runs local anomaly detection through a ZETIC Melange-compatible wrapper, stores demo data in MongoDB Atlas, and streams live vitals to the dashboard with Server-Sent Events.

### Install

```bash
pip install -r requirements.txt
```

Create `.env` from `.env.example` and set `MONGODB_URI`.

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

### Pitch

“CareFlow processes raw wearable vitals locally on-device using the ZETIC edge layer. The raw stream never needs to leave the device for initial detection. Once the local model detects a clinically relevant deviation, it sends only a compact anomaly event to the cloud AI pipeline for risk assessment and doctor-facing summarization.”
