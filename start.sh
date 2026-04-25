#!/usr/bin/env bash
# CareFlow — one-command launch
# Usage: ./start.sh
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ ! -f .env ]; then
  echo "❌  .env not found. Copy .env.example → .env and fill in credentials."
  exit 1
fi

export $(grep -v '^#' .env | xargs)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CareFlow  ·  LA Hacks 2026"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Ollama is reachable
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
if ! curl -sf "$OLLAMA_HOST" > /dev/null 2>&1; then
  echo "⚠️   Ollama not detected at $OLLAMA_HOST"
  echo "    Run in a separate terminal:  ollama serve"
  echo "    (risk classifier will use rule-based fallback until Ollama is up)"
  echo ""
fi

# Seed DB (idempotent — safe to re-run)
echo "▶ Seeding demo patients…"
python scripts/seed.py

echo "▶ Starting FastAPI gateway on :8000…"
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
PID_API=$!

sleep 1

echo "▶ Starting Monitor Agent on :8001…"
python agents/agent1_monitor.py &
PID_AGENT1=$!

echo "▶ Starting Coordinator Agent on :8002…"
python agents/agent2_coordinator.py &
PID_AGENT2=$!

echo ""
echo "✅  All services running:"
echo "   API Gateway  →  http://localhost:8000"
echo "   API Docs     →  http://localhost:8000/docs"
echo "   Monitor      →  http://localhost:8001"
echo "   Coordinator  →  http://localhost:8002"
echo ""
echo "📊  Start the React dashboard:"
echo "   cd careflow-ui && npm install && npm run dev"
echo "   then open  http://localhost:5173"
echo ""
echo "🚨  Trigger anomaly:  press D in the dashboard, or:"
echo "   curl -X POST http://localhost:8000/trigger-anomaly \\"
echo '        -H "Content-Type: application/json" \'
echo '        -d '"'"'{"patient_id":"patient-001","duration_seconds":30}'"'"

trap "kill $PID_API $PID_AGENT1 $PID_AGENT2 2>/dev/null; echo 'Stopped.'" EXIT INT TERM
wait
