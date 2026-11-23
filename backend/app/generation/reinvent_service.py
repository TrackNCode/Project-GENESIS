"""
reinvent_service.py
Project GENESIS - REINVENT 4 Multi-Objective Generative RL Service Bridge.
Bridges the FastAPI backend (running in genesis-cheminfo) to the deep generative
reinforcement learning engine (running on NVIDIA GeForce RTX 3060 CUDA in genesis-gpu).
"""

from typing import Dict, Any, List, Optional
import subprocess
import json
import time
from pathlib import Path

from ..runtime_config import get_gpu_python

CURRENT_DIR = Path(__file__).resolve().parent
REINVENT_ENGINE_SCRIPT = str(CURRENT_DIR / "reinvent_engine.py")


class REINVENTService:
    """Manages multi-objective molecular generation and RL optimization."""

    @classmethod
    def run_gpu_generation(cls, task: str, payload: Dict[str, Any], timeout: int = 45) -> Any:
        """Executes molecular generation in the genesis-gpu environment."""
        start_time = time.time()
        try:
            gpu_py = get_gpu_python()
            proc = subprocess.Popen(
                [gpu_py, REINVENT_ENGINE_SCRIPT, task],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8"
            )
            stdout, stderr = proc.communicate(input=json.dumps(payload), timeout=timeout)

            if proc.returncode != 0:
                print(f"[REINVENTService] Warning: GPU process error ({proc.returncode}): {stderr}", flush=True)
                return cls._fallback_generation(task, payload)

            result = json.loads(stdout)
            elapsed = round(time.time() - start_time, 3)
            return {
                "status": "success",
                "task": task,
                "elapsed_seconds": elapsed,
                "candidates": result
            }
        except subprocess.TimeoutExpired:
            proc.kill()
            return {"status": "error", "message": "Molecular generation timed out"}
        except Exception as e:
            print(f"[REINVENTService] Fallback invoked: {e}", flush=True)
            return cls._fallback_generation(task, payload)

    @classmethod
    def generate_de_novo(cls, target: str = "6LU7", num_candidates: int = 8) -> Dict[str, Any]:
        """Generate diverse de novo drug candidates tailored to target."""
        return cls.run_gpu_generation("de_novo", {"target": target, "num_candidates": num_candidates})

    @classmethod
    def scaffold_hop(cls, lead_smiles: str, target: str = "6LU7", num_candidates: int = 5) -> Dict[str, Any]:
        """Perform bioisosteric scaffold hopping around a lead molecule."""
        return cls.run_gpu_generation("scaffold_hop", {
            "lead_smiles": lead_smiles,
            "target": target,
            "num_candidates": num_candidates
        })

    @classmethod
    def score_candidate(
        cls,
        smiles: str,
        target: str = "6LU7",
        predicted_pIC50: float = 6.5,
        epistemic_uncertainty: float = 0.25,
        herg_prob: float = 0.20
    ) -> Dict[str, Any]:
        """Evaluate multi-objective composite reward breakdown for a candidate."""
        res = cls.run_gpu_generation("evaluate", {
            "smiles": smiles,
            "target": target,
            "predicted_pIC50": predicted_pIC50,
            "epistemic_uncertainty": epistemic_uncertainty,
            "herg_prob": herg_prob
        })
        if res.get("status") == "success":
            return res.get("candidates", {})
        return res

    @classmethod
    def _fallback_generation(cls, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based candidate generation if GPU environment is detached."""
        target = payload.get("target", "6LU7")
        num = payload.get("num_candidates", 5)
        
        candidates = []
        samples = [
            ("O=C1NCc2ccccc2N1C(=O)c3ccccc3", 7.2, 0.78, 2.8),
            ("Cc1cc(nc(n1)N)C(=O)NCc2ccccc2", 6.8, 0.82, 2.5),
            ("O=C(Cc1ccccc1)NC(Cc2c[nH]c3ccccc23)C(=O)N", 7.6, 0.65, 3.4),
            ("c1ccc(cc1)CNC(=O)c2cnccn2", 6.5, 0.85, 2.2),
            ("COc1ccc(cc1)C(=O)NC2CCNCC2", 6.9, 0.79, 2.7)
        ]
        
        for i in range(min(num, len(samples))):
            smi, pIC50, qed, sa = samples[i]
            comp_reward = round(0.35 * ((pIC50 - 5.0) / 4.0) + 0.25 * qed + 0.20 * ((6.0 - sa) / 5.0) - 0.03, 3)
            candidates.append({
                "smiles": smi,
                "valid": True,
                "composite_reward": comp_reward,
                "components": {
                    "predicted_pIC50": pIC50,
                    "affinity_reward": round((pIC50 - 5.0) / 4.0, 3),
                    "qed": qed,
                    "synthetic_accessibility": sa,
                    "sa_reward": round((6.0 - sa) / 5.0, 3),
                    "herg_cardiotox_prob": 0.15,
                    "tox_penalty": 0.15,
                    "epistemic_uncertainty": 0.28,
                    "uncertainty_penalty": 0.28
                },
                "target": target,
                "generation_engine": "Heuristic_Fallback"
            })
        
        return {"status": "fallback", "task": task, "candidates": candidates}
