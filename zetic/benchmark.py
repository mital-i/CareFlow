"""
Benchmarks anomaly inference across local CPU fallback and the mobile Melange bridge.
Run: python3 zetic/benchmark.py --profile cpu --iterations 100
Run: python3 zetic/benchmark.py --profile npu --bridge-url http://<device>:8765/infer
"""
import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.vitals import VitalsPayload
from zetic.melange_agent import HeuristicBackend, MelangeAgent, MelangeBridgeBackend


def _make_payload(patient_id: str, hr: float = 75.0) -> VitalsPayload:
    return VitalsPayload(
        patient_id=patient_id,
        heart_rate=hr,
        spo2=97.5,
        hrv=55.0,
        timestamp=datetime.now(timezone.utc),
        device_id="benchmark-device",
    )


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    idx = min(len(values) - 1, int(round((len(values) - 1) * percentile)))
    return sorted(values)[idx]


def run_benchmark(n: int = 100, profile: str = "cpu", bridge_url: str | None = None) -> dict:
    backend = MelangeBridgeBackend(bridge_url=bridge_url) if profile == "npu" else HeuristicBackend()
    agent = MelangeAgent(patient_id="BENCH", backend=backend, cooldown_seconds=0)
    latencies_ms = []

    # Prime the buffer
    for _ in range(10):
        agent.push_vitals(_make_payload("BENCH"))

    print(f"Running {n} inference iterations...")
    for i in range(n):
        payload = _make_payload("BENCH", hr=72 + (i % 45))
        agent.push_vitals(payload)
        t0 = time.perf_counter()
        agent._run_inference()
        t1 = time.perf_counter()
        latencies_ms.append((t1 - t0) * 1000)

    summary = {
        "profile": profile,
        "backend": backend.name,
        "iterations": n,
        "mean_latency_ms": round(statistics.mean(latencies_ms), 3),
        "p50_latency_ms": round(statistics.median(latencies_ms), 3),
        "p99_latency_ms": round(_percentile(latencies_ms, 0.99), 3),
        "max_latency_ms": round(max(latencies_ms), 3),
        "target_latency_ms": 100.0,
        "target_met": statistics.mean(latencies_ms) < 100,
        "measured_at": datetime.now(timezone.utc).isoformat(),
    }

    print("\n── ZETIC Melange Benchmark Results ──────────────────")
    print(f"  Profile     : {summary['profile']}")
    print(f"  Backend     : {summary['backend']}")
    print(f"  Iterations  : {summary['iterations']}")
    print(f"  Mean latency: {summary['mean_latency_ms']:.2f} ms")
    print(f"  P50 latency : {summary['p50_latency_ms']:.2f} ms")
    print(f"  P99 latency : {summary['p99_latency_ms']:.2f} ms")
    print(f"  Max latency : {summary['max_latency_ms']:.2f} ms")
    print(f"  Target      : <100ms per inference")
    print(f"  Target met  : {'YES' if summary['target_met'] else 'NO'}")
    print("─────────────────────────────────────────────────────")
    return summary


def write_results(summary: dict, output_path: str = "zetic/benchmark_results.json") -> None:
    path = Path(output_path)
    existing = []
    if path.exists():
        existing = json.loads(path.read_text())
        if not isinstance(existing, list):
            existing = [existing]
    existing.append(summary)
    path.write_text(json.dumps(existing, indent=2) + "\n")
    print(f"Saved benchmark summary to {path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark CareFlow ZETIC inference latency.")
    parser.add_argument("--profile", choices=["cpu", "npu"], default="cpu")
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--bridge-url", default=None)
    parser.add_argument("--output", default="zetic/benchmark_results.json")
    parser.add_argument("--no-write", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = run_benchmark(n=args.iterations, profile=args.profile, bridge_url=args.bridge_url)
    if not args.no_write:
        write_results(result, output_path=args.output)
