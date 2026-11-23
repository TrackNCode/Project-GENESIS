#!/usr/bin/env bash
# =====================================================================
# PROJECT GENESIS: SCIENTIFIC AI DISCOVERY PLATFORM
# Linux Automated Installer (Ubuntu, Debian, Fedora, CentOS, Arch)
# =====================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================================================="
echo "       PROJECT GENESIS: SCIENTIFIC AI DISCOVERY PLATFORM"
echo "                   Linux Automated Installer"
echo "====================================================================="
echo ""

# 1. System packages check (for Debian/Ubuntu)
if command -v apt-get &> /dev/null; then
    echo "[1/4] Checking required Linux system graphics & GL packages..."
    if ! dpkg -s libgl1 libglib2.0-0 &> /dev/null; then
        echo "Installing libgl1 and libglib2.0-0 via sudo apt-get..."
        sudo apt-get update -y && sudo apt-get install -y libgl1 libglib2.0-0 curl wget build-essential || true
    else
        echo "[OK] System GL libraries already present."
    fi
fi

# 2. Python Environment Setup
echo ""
echo "[2/4] Setting up Python scientific environment..."
if command -v conda &> /dev/null; then
    echo "[FOUND] Conda package manager detected."
    conda env create -f environment_genesis.yml || conda env update -f environment_genesis.yml --prune
    echo "[SUCCESS] Conda environment 'genesis' created."
elif command -v python3 &> /dev/null; then
    echo "[FOUND] System python3 detected."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements_full.txt
    echo "[SUCCESS] Virtual environment in ./venv created."
else
    echo "[ERROR] Neither conda nor python3 found! Please install Conda or Python 3.11."
    exit 1
fi

# 3. AutoDock Vina Linux Binary
echo ""
echo "[3/4] Ensuring AutoDock Vina Linux 64-bit binary is present..."
mkdir -p backend/bin
if [ ! -f "backend/bin/vina" ]; then
    echo "Downloading AutoDock Vina v1.2.5 (Linux x86_64)..."
    wget -q https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.5/vina_1.2.5_linux_x86_64 -O backend/bin/vina
    chmod +x backend/bin/vina
    echo "[OK] AutoDock Vina binary installed to backend/bin/vina."
else
    chmod +x backend/bin/vina
    echo "[OK] AutoDock Vina binary confirmed."
fi

# 4. Make scripts executable
echo ""
echo "[4/4] Setting execution permissions..."
chmod +x run_genesis.sh || true

echo ""
echo "====================================================================="
echo "  INSTALLATION COMPLETE!"
echo "  Execute './run_genesis.sh' to launch the entire platform."
echo "====================================================================="
