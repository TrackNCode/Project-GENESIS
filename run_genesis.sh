#!/usr/bin/env bash
# =====================================================================
# PROJECT GENESIS: SCIENTIFIC AI DISCOVERY PLATFORM
# One-Click Linux Launcher
# =====================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================================================="
echo "       PROJECT GENESIS: SCIENTIFIC AI DISCOVERY PLATFORM"
echo "                     One-Click Linux Launcher"
echo "====================================================================="
echo ""

# 1. Detect Python environment
PY_CMD=""

if [ -f "venv/bin/python" ]; then
    PY_CMD="venv/bin/python"
    echo "[ENV] Using local virtual environment in ./venv"
elif command -v conda &> /dev/null && conda env list | grep -q "^genesis "; then
    PY_CMD="conda run --no-capture-output -n genesis python"
    echo "[ENV] Using Conda environment: genesis"
elif command -v python3 &> /dev/null; then
    PY_CMD="python3"
    echo "[ENV] Using System Python3"
else
    echo "[ERROR] No Python environment detected! Please run './install_genesis_linux.sh' first."
    exit 1
fi

echo ""
echo "====================================================================="
echo "[STARTING] Launching GENESIS Platform on http://127.0.0.1:8000 ..."
echo "[INFO] API Swagger Documentation: http://127.0.0.1:8000/docs"
echo "[INFO] Unified Interactive Portal: http://127.0.0.1:8000/"
echo "====================================================================="
echo ""

# Open browser in background after 3 seconds
(
    sleep 3
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://127.0.0.1:8000/" > /dev/null 2>&1 || true
    elif command -v sensible-browser &> /dev/null; then
        sensible-browser "http://127.0.0.1:8000/" > /dev/null 2>&1 || true
    fi
) &

# Start FastAPI server
exec $PY_CMD -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
