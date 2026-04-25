"""
Benchmarks ZETIC Melange inference across CPU and NPU profiles.
Run: python zetic/benchmark.py
Records latency per inference and prints a summary for the pitch.

TODO: Replace stub timing with real Melange SDK profiling once SDK is installed.
"""
import statistics
import time
from datetime import datetime, timezone

from models.vitals import VitalsPayload
from zetic.melange_agent import MelangeAgent


def _make_payload(patient_id: str, hr: float = 75.0) -> VitalsPayload:
    return VitalsPayload(
        patient_id=patient_id,
        heart_rate=hr,
        spo2=97.5,
        hrv=55.0,
        timestamp=datetime.now(timezone.utc),
        device_id="benchmark-device",
    )


def run_benchmark(n: int = 100):
    agent = MelangeAgent(patient_id="BENCH")
    latencies_ms = []

    # Prime the buffer
    for _ in range(10):
        agent.push_vitals(_make_payload("BENCH"))

    print(f"Running {n} inference iterations...")
    for i in range(n):
        payload = _make_payload("BENCH", hr=72 + (i % 30))
        t0 = time.perf_counter()
        agent._run_inference()
        t1 = time.perf_counter()
        latencies_ms.append((t1 - t0) * 1000)

    print("\n── ZETIC Melange Benchmark Results ──────────────────")
    print(f"  Iterations  : {n}")
    print(f"  Mean latency: {statistics.mean(latencies_ms):.2f} ms")
    print(f"  P50 latency : {statistics.median(latencies_ms):.2f} ms")
    print(f"  P99 latency : {sorted(latencies_ms)[int(n * 0.99)]:.2f} ms")
    print(f"  Max latency : {max(latencies_ms):.2f} ms")
    print(f"  Target      : <100ms per inference")
    target_met = statistics.mean(latencies_ms) < 100
    print(f"  Target met  : {'YES ✓' if target_met else 'NO ✗'}")
    print("─────────────────────────────────────────────────────")


if __name__ == "__main__":
    run_benchmark()
