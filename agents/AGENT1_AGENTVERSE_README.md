# CareFlow Vital Monitoring Agent

## Name
CareFlow-VitalMonitor

## Description
CareFlow Vital Monitoring Agent streams synthetic patient vitals, runs a ZETIC Melange anomaly detector, and publishes AnomalyEvent messages when elevated heart rate, suppressed HRV, or SpO2 deviation patterns cross the configured threshold.

## Keywords
healthcare, vitals, anomaly detection, ZETIC Melange, on-device AI, patient monitoring

## Endpoint
Set `AGENT1_PUBLIC_ENDPOINT` to the public `/submit` endpoint used by Agentverse.

Example:

```text
AGENT1_PUBLIC_ENDPOINT=https://your-tunnel.example/submit
```

Local development uses:

```text
AGENT1_ENDPOINT=http://localhost:8001/submit
```

## Exposed Capabilities
- Publishes `AnomalyEventMessage` to Agent 2 when the ZETIC detector crosses `ANOMALY_THRESHOLD`.
- Handles `VitalsQueryMessage` and returns the latest vitals snapshot for a patient.
- Handles `DetectAnomalyRequestMessage` and returns a one-off anomaly detection result.
- Publishes an Agent Chat Protocol manifest so Agentverse/ASI clients can ask for latest vitals in natural language.

## Registration Steps
1. Fill `.env` with `AGENT1_SEED`, `AGENT1_PUBLIC_ENDPOINT`, and `AGENTVERSE_API_KEY`.
2. Start the agent with `python3 agents/agent1_vital_monitor.py`.
3. Copy the printed agent address into `AGENT1_ADDRESS`.
4. In Agentverse, choose Connect Agent, Chat Protocol, and enter the public endpoint.
5. Run the generated Agentverse registration script if prompted, then evaluate registration.

## Privacy Note
The demo database stores raw vitals for dashboard and history views. The inter-agent/Agentverse path publishes only anomaly summaries through `AnomalyEventMessage`; raw vitals are not pushed upstream to Agent 2.
