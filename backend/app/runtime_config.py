"""
runtime_config.py
Dynamic cross-platform runtime resolution for Project GENESIS.
Automatically resolves Python interpreters, model weights, and data directories across Windows and Linux.
"""

import os
import sys
from pathlib import Path

# Base Paths (Computed dynamically relative to this file)
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
BIN_DIR = BACKEND_DIR / "bin"
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

# Ensure data directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "models_weights").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "ingestion" / "chembl").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "ingestion" / "opentargets").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "ingestion" / "tdc").mkdir(parents=True, exist_ok=True)


def get_gpu_python() -> str:
    """
    Dynamically locate the GPU-enabled Python interpreter (for Chemprop, GNINA, REINVENT).
    Priority order:
    1. GENESIS_GPU_PYTHON environment variable
    2. Check if current interpreter has torch
    3. Candidate Conda / virtualenv locations on Windows and Linux
    4. Fallback to sys.executable (graceful CPU fallback)
    """
    # 1. Environment variable
    env_py = os.environ.get("GENESIS_GPU_PYTHON")
    if env_py and Path(env_py).exists():
        return env_py

    # 2. Check if current interpreter has both torch and chemprop
    try:
        import torch  # type: ignore
        import chemprop  # type: ignore
        return sys.executable
    except ImportError:
        pass

    # 3. Candidate Conda paths (Windows & Linux)
    home = Path.home()
    candidate_paths = [
        # Windows candidates
        r"C:\Users\MINICO~1\envs\genesis-gpu\python.exe",
        home / "miniconda3" / "envs" / "genesis-gpu" / "python.exe",
        home / "anaconda3" / "envs" / "genesis-gpu" / "python.exe",
        home / "miniforge3" / "envs" / "genesis-gpu" / "python.exe",
        home / ".conda" / "envs" / "genesis-gpu" / "python.exe",
        # Linux / Unix candidates
        home / "miniconda3" / "envs" / "genesis-gpu" / "bin" / "python",
        home / "anaconda3" / "envs" / "genesis-gpu" / "bin" / "python",
        home / "miniforge3" / "envs" / "genesis-gpu" / "bin" / "python",
        home / ".conda" / "envs" / "genesis-gpu" / "bin" / "python",
        Path("/opt/conda/envs/genesis-gpu/bin/python"),
        Path("/opt/venv/bin/python"),
    ]

    for candidate in candidate_paths:
        if Path(candidate).exists():
            return str(candidate)

    # 4. Fallback to sys.executable
    return sys.executable
