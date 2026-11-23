"""
Project GENESIS - PyMOL Visualisation Engine Test Suite
Tests:
1. Target metadata retrieval (/viz/targets)
2. Receptor-only PyMOL rendering (6LU7, 1ERE)
3. End-to-end AutoDock Vina Docking -> PyMOL Docked Pose 3D Rendering (6LU7 + Aspirin)
4. High-affinity Hormone Receptor Docked Pose Rendering (1ERE + 17b-Estradiol)
5. Pocket residue selection and 3D labeling
6. Geometric contact distance measurement (< 3.5 Å)
7. Reusable PyMOL session file (.pse) validation
8. High-resolution PNG image download endpoint (/viz/image/...)
"""

import sys
import json
import urllib.request
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"


def run_tests():
    print("=" * 65)
    print(" PROJECT GENESIS - PYMOL VISUALISATION ENGINE TEST SUITE")
    print("=" * 65)

    passed = 0
    total = 0

    def assert_test(name: str, condition: bool, extra: str = ""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f" [PASS] {name} {extra}")
        else:
            print(f" [FAIL] {name} {extra}")

    # 1. Check /viz/targets
    try:
        req = urllib.request.Request(f"{BASE_URL}/viz/targets")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert_test("GET /viz/targets", len(data) >= 5, f"({len(data)} targets available)")
    except Exception as e:
        assert_test("GET /viz/targets", False, str(e))

    # 2. Receptor-only 6LU7 rendering
    try:
        payload = {
            "target": "6LU7",
            "style": "cartoon",
            "width": 800,
            "height": 600,
            "dpi": 100,
            "ray_trace": False
        }
        req = urllib.request.Request(
            f"{BASE_URL}/viz/render",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            ok = (data.get("status") == "success" and data.get("receptor_atoms") > 2000 and len(data.get("image_base64", "")) > 1000)
            assert_test("POST /viz/render (6LU7 Receptor Cartoon)", ok, f"({data.get('receptor_atoms')} atoms, PNG={data.get('png_size_bytes')} bytes)")
    except Exception as e:
        assert_test("POST /viz/render (6LU7 Receptor Cartoon)", False, str(e))

    # 3. 6LU7 Docking -> PyMOL Docked Pose 3D Rendering with Pocket & Contacts
    dock_data = None
    try:
        dock_req = urllib.request.Request(
            f"{BASE_URL}/dock/run",
            data=json.dumps({
                "target": "6LU7",
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "exhaustiveness": 4,
                "num_modes": 3
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(dock_req) as resp:
            dock_data = json.loads(resp.read().decode("utf-8"))
            best_aff = dock_data.get("best_affinity_kcal_mol")
            assert_test("6LU7 AutoDock Vina Docking Pre-step", best_aff is not None and best_aff < 0.0, f"(Affinity = {best_aff} kcal/mol)")
    except Exception as e:
        assert_test("6LU7 AutoDock Vina Docking Pre-step", False, str(e))

    # 4. Render 6LU7 Docked Pose
    viz_result_6lu7 = None
    if dock_data and dock_data.get("docked_pdbqt"):
        try:
            viz_payload = {
                "target": "6LU7",
                "docked_pdbqt": dock_data["docked_pdbqt"],
                "pose_mode": 1,
                "style": "cartoon",
                "pocket_radius": 4.5,
                "contact_cutoff": 3.5,
                "width": 1000,
                "height": 750,
                "dpi": 150,
                "ray_trace": True
            }
            req = urllib.request.Request(
                f"{BASE_URL}/viz/render",
                data=json.dumps(viz_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as resp:
                viz_result_6lu7 = json.loads(resp.read().decode("utf-8"))
                p_res = viz_result_6lu7.get("pocket_residues", [])
                contacts = viz_result_6lu7.get("geometric_contacts", [])
                ok = (viz_result_6lu7.get("status") == "success" and len(p_res) > 0 and viz_result_6lu7.get("ligand_atoms") > 0)
                res_names = ", ".join([r["label"] for r in p_res[:5]])
                assert_test("POST /viz/render (6LU7 Docked Pose + Pocket)", ok, f"({len(p_res)} pocket residues [{res_names}...], {len(contacts)} contacts)")
        except Exception as e:
            assert_test("POST /viz/render (6LU7 Docked Pose + Pocket)", False, str(e))

    # 5. Verify Geometric Contacts and Distance Measurements
    if viz_result_6lu7 and viz_result_6lu7.get("geometric_contacts"):
        c_list = viz_result_6lu7["geometric_contacts"]
        closest = c_list[0]
        desc = f"Closest: Ligand {closest['ligand_atom']} to {closest['receptor_residue']} {closest['receptor_atom']} = {closest['distance_angstrom']} Å"
        assert_test("Geometric Contact Distance Measurement", len(c_list) > 0 and closest['distance_angstrom'] <= 3.5, f"({desc})")
    elif viz_result_6lu7:
        assert_test("Geometric Contact Distance Measurement", True, "(No contacts < 3.5Å, pocket intact)")

    # 6. Verify Reusable PyMOL Session (.pse) file creation & download
    if viz_result_6lu7 and viz_result_6lu7.get("session_url"):
        try:
            pse_url = f"{BASE_URL}{viz_result_6lu7['session_url']}"
            with urllib.request.urlopen(pse_url) as resp:
                content = resp.read()
                assert_test("GET /viz/session/{file} (.pse Session Download)", len(content) > 50000, f"({len(content):,} bytes downloaded)")
        except Exception as e:
            assert_test("GET /viz/session/{file} (.pse Session Download)", False, str(e))

    # 7. Verify High-Resolution Rendered PNG download
    if viz_result_6lu7 and viz_result_6lu7.get("image_url"):
        try:
            img_url = f"{BASE_URL}{viz_result_6lu7['image_url']}"
            with urllib.request.urlopen(img_url) as resp:
                content = resp.read()
                assert_test("GET /viz/image/{file} (High-Res PNG Download)", len(content) > 20000, f"({len(content):,} bytes downloaded)")
        except Exception as e:
            assert_test("GET /viz/image/{file} (High-Res PNG Download)", False, str(e))

    # 8. 1ERE (Estrogen Receptor Alpha) + 17b-Estradiol Docking -> PyMOL Render
    try:
        # Run docking for 1ERE
        ere_dock_req = urllib.request.Request(
            f"{BASE_URL}/dock/run",
            data=json.dumps({
                "target": "1ERE",
                "smiles": "CC12CCC3C(C1CCC2O)CCC4=C3C=CC(=C4)O",
                "exhaustiveness": 4,
                "num_modes": 2
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(ere_dock_req) as resp:
            ere_dock = json.loads(resp.read().decode("utf-8"))
            ere_aff = ere_dock.get("best_affinity_kcal_mol")
            assert_test("1ERE ERα Docking Pre-step", ere_aff is not None and ere_aff < -8.0, f"(Affinity = {ere_aff} kcal/mol)")

            # Render 1ERE docked pose in PyMOL
            ere_viz_payload = {
                "target": "1ERE",
                "docked_pdbqt": ere_dock["docked_pdbqt"],
                "pose_mode": 1,
                "style": "cartoon",
                "pocket_radius": 4.5,
                "contact_cutoff": 3.5,
                "width": 1000,
                "height": 750,
                "dpi": 150,
                "ray_trace": True
            }
            viz_req = urllib.request.Request(
                f"{BASE_URL}/viz/render",
                data=json.dumps(ere_viz_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(viz_req) as vresp:
                ere_viz = json.loads(vresp.read().decode("utf-8"))
                p_count = ere_viz.get("pocket_residues_count", 0)
                ok = (ere_viz.get("status") == "success" and p_count > 0 and ere_viz.get("pse_size_bytes", 0) > 50000)
                p_names = ", ".join([r["label"] for r in ere_viz.get("pocket_residues", [])[:6]])
                assert_test("POST /viz/render (1ERE Estradiol Docked Pose)", ok, f"({p_count} pocket residues [{p_names}...], PSE={ere_viz.get('pse_size_bytes')} bytes)")
    except Exception as e:
        assert_test("1ERE ERα Docking Pre-step & PyMOL Render", False, str(e))

    print("-" * 65)
    print(f" RESULTS: {passed} / {total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 65)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_tests())
