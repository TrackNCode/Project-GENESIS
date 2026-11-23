"""
Cheminformatics helper utilities for Project GENESIS.
Provides chemical structure parsing, property computation, and 3D conformer generation using RDKit.
"""

from typing import Dict, List, Any

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Crippen, rdMolDescriptors, AllChem
    from rdkit.Chem.Draw import rdMolDraw2D
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "RDKit is not installed in the active environment. "
        "Activate genesis-cheminfo environment."
    ) from exc


def smiles_to_mol(smiles: str, add_hs: bool = False) -> Chem.Mol:
    """Convert a SMILES string to an RDKit Mol object.
    Raises ValueError if the SMILES is invalid.
    """
    if not smiles or not isinstance(smiles, str):
        raise ValueError("SMILES must be a non-empty string.")
    
    clean_smiles = smiles.strip()
    mol = Chem.MolFromSmiles(clean_smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES string: '{clean_smiles}'")
    
    if add_hs:
        mol = Chem.AddHs(mol)
    return mol


def mol_weight(smiles: str) -> float:
    """Return the exact molecular weight for a SMILES string."""
    mol = smiles_to_mol(smiles)
    return round(float(Descriptors.ExactMolWt(mol)), 4)


def mol_formula(smiles: str) -> str:
    """Return the Hill system molecular formula for a SMILES string (e.g., C2H6O)."""
    mol = smiles_to_mol(smiles)
    # Ensure formula accounts for implicit hydrogens
    mol_with_h = Chem.AddHs(mol)
    return rdMolDescriptors.CalcMolFormula(mol_with_h)


def mol_logp(smiles: str) -> float:
    """Return the calculated LogP (octanol-water partition coefficient) using Crippen's method."""
    mol = smiles_to_mol(smiles)
    return round(float(Crippen.MolLogP(mol)), 4)


def mol_properties(smiles: str) -> Dict[str, Any]:
    """Compute comprehensive physicochemical properties and Lipinski Rule of 5 descriptors."""
    mol = smiles_to_mol(smiles)
    mol_with_h = Chem.AddHs(mol)
    
    mw = round(float(Descriptors.ExactMolWt(mol)), 4)
    logp = round(float(Crippen.MolLogP(mol)), 4)
    hbd = int(Descriptors.NumHDonors(mol))
    hba = int(Descriptors.NumHAcceptors(mol))
    tpsa = round(float(Descriptors.TPSA(mol)), 2)
    rot_bonds = int(Descriptors.NumRotatableBonds(mol))
    formula = rdMolDescriptors.CalcMolFormula(mol_with_h)
    heavy_atoms = int(mol.GetNumHeavyAtoms())
    rings = int(rdMolDescriptors.CalcNumRings(mol))
    
    # Lipinski's Rule of 5 violations:
    # MW <= 500, LogP <= 5, HBD <= 5, HBA <= 10
    violations = 0
    if mw > 500:
        violations += 1
    if logp > 5:
        violations += 1
    if hbd > 5:
        violations += 1
    if hba > 10:
        violations += 1
        
    lipinski_pass = violations <= 1

    return {
        "smiles": smiles,
        "formula": formula,
        "molecular_weight": mw,
        "logp": logp,
        "tpsa": tpsa,
        "hbd": hbd,
        "hba": hba,
        "rotatable_bonds": rot_bonds,
        "heavy_atom_count": heavy_atoms,
        "ring_count": rings,
        "lipinski_violations": violations,
        "lipinski_pass": lipinski_pass,
    }


def mol_conformer_3d(smiles: str, optimize: bool = True) -> Dict[str, Any]:
    """Generate a 3D conformer with 3D atomic coordinates and MMFF force field optimization."""
    mol = smiles_to_mol(smiles, add_hs=True)
    
    # Embed 3D coordinates using ETKDG algorithm
    res = AllChem.EmbedMolecule(mol, randomSeed=42)
    if res != 0:
        # Fallback to random coordinates if standard embedding fails
        AllChem.EmbedMolecule(mol, useRandomCoords=True, randomSeed=42)
    
    energy = None
    if optimize:
        try:
            mmff_props = AllChem.MMFFGetMoleculeProperties(mol)
            if mmff_props:
                ff = AllChem.MMFFGetMoleculeForceField(mol, mmff_props)
                ff.Minimize(maxIts=500)
                energy = round(ff.CalcEnergy(), 4)
            else:
                AllChem.UFFOptimizeMolecule(mol, maxIters=500)
        except Exception:
            # If force field optimization encounters issues, retain embedded conformer
            pass

    conformer = mol.GetConformer()
    atoms: List[Dict[str, Any]] = []
    for i, atom in enumerate(mol.GetAtoms()):
        pos = conformer.GetAtomPosition(i)
        atoms.append({
            "index": i,
            "symbol": atom.GetSymbol(),
            "atomic_num": atom.GetAtomicNum(),
            "x": round(pos.x, 4),
            "y": round(pos.y, 4),
            "z": round(pos.z, 4),
        })

    bonds: List[Dict[str, Any]] = []
    for bond in mol.GetBonds():
        bonds.append({
            "begin_atom": bond.GetBeginAtomIdx(),
            "end_atom": bond.GetEndAtomIdx(),
            "order": float(bond.GetBondTypeAsDouble()),
        })

    mol_block = Chem.MolToMolBlock(mol)

    return {
        "smiles": smiles,
        "atom_count": len(atoms),
        "energy_kcal_mol": energy,
        "atoms": atoms,
        "bonds": bonds,
        "mol_block": mol_block,
    }


def mol_svg(smiles: str, width: int = 350, height: int = 300) -> str:
    """Generate a 2D depiction of the molecule as an SVG XML string."""
    mol = smiles_to_mol(smiles)
    AllChem.Compute2DCoords(mol)
    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    return drawer.GetDrawingText()
