"""
PyMOL Headless Runner for Project GENESIS Molecular Visualisation Engine.
Executes in an isolated subprocess with OSMesa software rendering to ensure
thread safety, stability, and zero leakage into the FastAPI server.
"""

import sys
import os
import json
import argparse
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Enable OSMesa software rendering for headless environments
os.environ["PYOPENGL_PLATFORM"] = "osmesa"

try:
    import pymol
    pymol.pymol_argv = ["pymol", "-cq"]
    pymol.finish_launching()
    from pymol import cmd, stored
except ImportError as e:
    sys.__stderr__.write(f"FATAL: Failed to import PyMOL: {e}\n")
    sys.__stderr__.flush()
    sys.exit(1)


def calculate_euclidean_distance(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)


def run_visualization(config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute PyMOL scene setup, measurements, PNG rendering, and PSE session export."""
    receptor_path = config.get("receptor_path")
    ligand_path = config.get("ligand_path")
    output_png = config.get("output_png")
    output_pse = config.get("output_pse")

    style = config.get("style", "cartoon")  # cartoon, surface, ribbon, sticks
    pocket_radius = float(config.get("pocket_radius", 4.5))
    contact_cutoff = float(config.get("contact_cutoff", 3.5))
    width = int(config.get("width", 1200))
    height = int(config.get("height", 900))
    dpi = int(config.get("dpi", 150))
    ray_trace = bool(config.get("ray_trace", True))
    title = config.get("title", "Project GENESIS Molecular Visualization")

    if not receptor_path or not os.path.exists(receptor_path):
        raise FileNotFoundError(f"Receptor file not found: {receptor_path}")

    # Re-initialize fresh scene
    cmd.reinitialize()
    cmd.set("ray_opaque_background", 1)
    cmd.set("antialias", 2)
    cmd.set("ambient", 0.25)
    cmd.set("reflect", 0.5)
    cmd.set("direct", 0.7)

    # 1. Load Receptor
    receptor_name = "receptor"
    cmd.load(receptor_path, receptor_name)
    receptor_atoms = cmd.count_atoms(receptor_name)
    if receptor_atoms == 0:
        raise ValueError(f"No atoms could be loaded from receptor file: {receptor_path}")

    # Style receptor
    cmd.hide("everything", receptor_name)
    if style in ("cartoon", "ribbon"):
        cmd.show("cartoon", receptor_name)
        cmd.color("marine", f"{receptor_name} and ss h")    # Alpha helices in marine blue
        cmd.color("salmon", f"{receptor_name} and ss s")    # Beta sheets in warm salmon
        cmd.color("grey80", f"{receptor_name} and ss l+''") # Loops in clean light grey
    elif style == "surface":
        cmd.show("cartoon", receptor_name)
        cmd.color("grey80", receptor_name)
        cmd.show("surface", receptor_name)
        cmd.set("transparency", 0.45, receptor_name)
        cmd.color("lightblue", f"surface and {receptor_name}")
    elif style == "sticks":
        cmd.show("sticks", receptor_name)
        cmd.color("grey80", f"{receptor_name} and elem C")
        cmd.util.cnc(receptor_name)

    # 2. Load Ligand / Docked Pose if provided
    ligand_name = "ligand"
    has_ligand = False
    ligand_atoms = 0
    pocket_residues = []
    contacts = []

    if ligand_path and os.path.exists(ligand_path):
        cmd.load(ligand_path, ligand_name)
        ligand_atoms = cmd.count_atoms(ligand_name)
        if ligand_atoms > 0:
            has_ligand = True
            cmd.hide("everything", ligand_name)
            cmd.show("sticks", ligand_name)
            cmd.set("stick_radius", 0.25, ligand_name)
            # High-visibility carbon coloring (warm amber/yellow for ligand)
            cmd.color("yellow", f"{ligand_name} and elem C")
            cmd.util.cnc(ligand_name)

            # 3. Select and style binding pocket residues
            pocket_sel = f"byres ({receptor_name} within {pocket_radius} of {ligand_name})"
            cmd.select("pocket", pocket_sel)
            cmd.show("sticks", "pocket")
            cmd.color("teal", "pocket and elem C")
            cmd.util.cnc("pocket")
            cmd.set("stick_radius", 0.18, "pocket")

            # Extract list of unique pocket residues
            stored.residues = []
            cmd.iterate("pocket and name CA", "stored.residues.append((chain, resn, resi))")
            for ch, resn, resi in stored.residues:
                pocket_residues.append({
                    "chain": ch,
                    "resname": resn,
                    "resnum": resi,
                    "label": f"{resn}{resi}",
                })

            # Add legible 3D labels to pocket CA atoms
            cmd.label("pocket and name CA", "\"%s%s\" % (resn, resi)")
            cmd.set("label_color", "wheat")
            cmd.set("label_size", 14)
            cmd.set("label_font_id", 7)  # Clean sans-serif font

            # 4. Geometric Distance & Contact Analysis
            # Geometrically detected contacts: distance between heteroatoms < contact_cutoff (typically 3.5 A)
            dist_obj = "geom_contacts"
            cmd.distance(
                dist_obj,
                f"{ligand_name} and (elem N,O,S,F,Cl,Br,I)",
                f"pocket and (elem N,O,S)",
                cutoff=contact_cutoff
            )
            cmd.set("dash_color", "yellow")
            cmd.set("dash_width", 2.2)
            cmd.set("dash_radius", 0.05)
            cmd.set("dash_gap", 0.25)
            cmd.set("dash_length", 0.2)

            # Extract exact coordinate distances
            stored.lig_atoms = []
            cmd.iterate_state(1, f"{ligand_name} and (elem N,O,S,F,Cl,Br,I)",
                              "stored.lig_atoms.append((name, elem, x, y, z))")

            stored.rec_atoms = []
            cmd.iterate_state(1, "pocket and (elem N,O,S)",
                              "stored.rec_atoms.append((resn, resi, chain, name, elem, x, y, z))")

            for l_name, l_elem, lx, ly, lz in stored.lig_atoms:
                for r_resn, r_resi, r_ch, r_name, r_elem, rx, ry, rz in stored.rec_atoms:
                    dist = calculate_euclidean_distance((lx, ly, lz), (rx, ry, rz))
                    if dist <= contact_cutoff:
                        contacts.append({
                            "ligand_atom": l_name,
                            "ligand_element": l_elem,
                            "receptor_residue": f"{r_resn}{r_resi}",
                            "receptor_chain": r_ch,
                            "receptor_atom": r_name,
                            "receptor_element": r_elem,
                            "distance_angstrom": round(dist, 2),
                            "contact_type": "polar_proximity (<3.5Å)" if dist <= 3.2 else "van_der_waals (<3.5Å)",
                            "validation_status": "geometrically_detected"
                        })

            # Sort contacts by ascending distance
            contacts.sort(key=lambda x: x["distance_angstrom"])

            # Focus camera on the binding pocket & ligand
            cmd.zoom("pocket or ligand", buffer=3.5)
        else:
            cmd.orient(receptor_name)
    else:
        cmd.orient(receptor_name)

    # 5. Render High-Resolution PNG
    os.makedirs(os.path.dirname(os.path.abspath(output_png)), exist_ok=True)
    if ray_trace:
        cmd.ray(width, height)
    cmd.png(output_png, width=width, height=height, dpi=dpi)

    # 6. Save Reusable PyMOL Session (.pse)
    os.makedirs(os.path.dirname(os.path.abspath(output_pse)), exist_ok=True)
    cmd.save(output_pse)

    cmd.quit()

    png_size = os.path.getsize(output_png) if os.path.exists(output_png) else 0
    pse_size = os.path.getsize(output_pse) if os.path.exists(output_pse) else 0

    return {
        "status": "success",
        "title": title,
        "style": style,
        "receptor_atoms": receptor_atoms,
        "has_ligand": has_ligand,
        "ligand_atoms": ligand_atoms,
        "pocket_radius_angstrom": pocket_radius,
        "contact_cutoff_angstrom": contact_cutoff,
        "pocket_residues_count": len(pocket_residues),
        "pocket_residues": pocket_residues,
        "geometric_contacts_count": len(contacts),
        "geometric_contacts": contacts,
        "png_path": output_png,
        "png_size_bytes": png_size,
        "pse_path": output_pse,
        "pse_size_bytes": pse_size,
        "resolution": f"{width}x{height} @ {dpi} DPI",
        "software_version": "PyMOL Open-Source 3.1.0"
    }


def main():
    parser = argparse.ArgumentParser(description="GENESIS PyMOL Visualisation Runner")
    parser.add_argument("--config", type=str, required=True, help="Path to JSON configuration file")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)

    try:
        result = run_visualization(config)
        # Write JSON response to pure standard output using sys.__stdout__
        sys.__stdout__.write("\n===PYMOL_RESULT_BEGIN===\n")
        sys.__stdout__.write(json.dumps(result))
        sys.__stdout__.write("\n===PYMOL_RESULT_END===\n")
        sys.__stdout__.flush()
    except Exception as e:
        err = {"status": "error", "error": str(e)}
        sys.__stdout__.write("\n===PYMOL_RESULT_BEGIN===\n")
        sys.__stdout__.write(json.dumps(err))
        sys.__stdout__.write("\n===PYMOL_RESULT_END===\n")
        sys.__stdout__.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()
