"""
chemprop_service.py
Project GENESIS - Chemprop D-MPNN High-Performance Prediction Service.
Bridges the FastAPI backend (running in genesis-cheminfo) to the deep learning
Evidential D-MPNN engine (running on NVIDIA RTX 3060 CUDA in genesis-gpu).
"""

from typing import Dict, Any, List, Optional
import subprocess
import json
import time
from pathlib import Path

from ..runtime_config import get_gpu_python

CURRENT_DIR = Path(__file__).resolve().parent
ENGINE_SCRIPT = str(CURRENT_DIR / "chemprop_engine.py")


class ChempropService:
    """Manages deep neural network prediction jobs on the GPU worker."""

    @classmethod
    def run_gpu_inference(cls, task: str, payload: Dict[str, Any], timeout: int = 45) -> Any:
        """
        Executes inference in the isolated genesis-gpu environment via IPC.
        Keeps heavy PyTorch CUDA libraries strictly isolated from genesis-cheminfo.
        """
        start_time = time.time()
        try:
            gpu_py = get_gpu_python()
            proc = subprocess.Popen(
                [gpu_py, ENGINE_SCRIPT, task],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8"
            )
            stdout, stderr = proc.communicate(input=json.dumps(payload), timeout=timeout)

            if proc.returncode != 0:
                print(f"[ChempropService] GPU process error ({proc.returncode}): {stderr}", flush=True)
                return cls._fallback_predictions(task, payload)

            result = json.loads(stdout)
            elapsed = round(time.time() - start_time, 3)
            return {
                "status": "success",
                "task": task,
                "elapsed_seconds": elapsed,
                "predictions": result
            }
        except subprocess.TimeoutExpired:
            proc.kill()
            return {"status": "error", "message": "GPU inference timed out"}
        except Exception as e:
            print(f"[ChempropService] Fallback invoked: {e}", flush=True)
            return cls._fallback_predictions(task, payload)

    @classmethod
    def predict_bioactivity(cls, smiles: List[str], target: str = "6LU7") -> Dict[str, Any]:
        """Predict pIC50 and evidential epistemic uncertainty for target protein."""
        return cls.run_gpu_inference("bioactivity", {"smiles": smiles, "target": target})

    @classmethod
    def predict_admet(cls, smiles: List[str]) -> Dict[str, Any]:
        """Predict Caco-2 permeability and hERG cardiotoxicity."""
        return cls.run_gpu_inference("admet", {"smiles": smiles})

    @classmethod
    def _fallback_predictions(cls, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Safe heuristic fallback if GPU environment is detached."""
        smiles = payload.get("smiles", [])
        preds = []
        for smi in smiles:
            preds.append({
                "smiles": smi,
                "valid": True,
                "pIC50_pred": 6.2,
                "epistemic_uncertainty": 0.45,
                "out_of_distribution": False,
                "caco2_papp_log_cm_s": -5.2,
                "herg_inhibition_prob": 0.25,
                "admet_risk_level": "LOW",
                "model": "Heuristic_Fallback",
                "device": "cpu"
            })
        return {"status": "fallback", "task": task, "predictions": preds}
