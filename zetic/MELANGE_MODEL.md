# CareFlow ZETIC Melange Model Contract

## Input
The anomaly model consumes the last 10 seconds of vitals as a `[10, 3]` float matrix:

```text
[
  [normalized_hr, normalized_spo2, normalized_hrv],
  ...
]
```

Normalization is implemented in `zetic.melange_agent.build_feature_matrix`:

```text
normalized_hr = (heart_rate - baseline_hr) / 40
normalized_spo2 = (spo2 - baseline_spo2) / 10
normalized_hrv = (hrv - baseline_hrv) / 40
```

## Output
The model or bridge must return JSON with either:

```json
{"deviation_score": 0.72}
```

or:

```json
{"score": 0.72}
```

Scores are clamped to `0.0..1.0`; Agent 1 emits an `AnomalyEvent` when the score is at least `ANOMALY_THRESHOLD` (default `0.65`).

## Melange Deployment
1. Export or prepare a compact LSTM/CNN/MLP time-series anomaly model as ONNX or PyTorch Exported Program (`.pt2`).
2. Upload it to the ZETIC Melange dashboard or CLI.
3. Store the returned model identifier in `ZETIC_MODEL_KEY`.
4. Store the Melange personal key in `ZETIC_PERSONAL_KEY`.
5. Run the physical-device bridge and set:

```text
ZETIC_BACKEND=melange_bridge
ZETIC_BRIDGE_URL=http://<device-or-tunnel>:8765/infer
```

The Python backend publishes only `AnomalyEventMessage` to other agents. Raw vitals are kept in MongoDB for the local demo dashboard and history contract.
