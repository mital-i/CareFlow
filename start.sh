#!/usr/bin/env bash
# CareFlow — one-command launch
# Usage: ./start.sh
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# Load env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo "=== CareFlow Startup ==="

# 1. Seed DB if needed (skip if already seeded)
echo "[1/5] Checking DB seed..."
python3 scripts/seed.py

# 2. Start FastAPI gateway in background
echo "[2/5] Starting FastAPI gateway on :8000"
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# 3. Start all 5 agents in background
echo "[3/5] Starting agents..."
python3 agents/agent1_vital_monitor.py &
AGENT1_PID=$!
python3 agents/agent2_risk_assessment.py &
AGENT2_PID=$!
python3 agents/agent3_coordinator.py &
AGENT3_PID=$!
python3 agents/agent4_patient.py &
AGENT4_PID=$!
python3 agents/agent5_provider.py &
AGENT5_PID=$!

# 4. Start React dev server
echo "[4/5] Starting React dashboard on :5173"
cd careflow-ui && npm run dev &
UI_PID=$!
cd "$ROOT"

echo ""
echo "=== CareFlow Running ==="
echo "  Dashboard  : http://localhost:5173"
echo "  API        : http://localhost:8000"
echo "  API docs   : http://localhost:8000/docs"
echo ""
echo "  Press D in the dashboard to open Demo Controls"
echo "  Press F to show the System Flow diagram"
echo "  Ctrl+C to stop all services"

# Cleanup on exit
trap "kill $API_PID $AGENT1_PID $AGENT2_PID $AGENT3_PID $AGENT4_PID $AGENT5_PID $UI_PID 2>/dev/null; echo 'Stopped.'" EXIT

wait
