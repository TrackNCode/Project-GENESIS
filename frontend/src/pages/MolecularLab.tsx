import React, { useState, useEffect } from 'react';
import MolecularViewer3D from '@/components/MolecularViewer3D';

const API_BASE = 'http://127.0.0.1:8000';

interface PresetMolecule {
  name: string;
  smiles: string;
  description: string;
  category: string;
}

interface DockingTarget {
  pdb_id: string;
  name: string;
  organism: string;
  indication: string;
  description: string;
  resolution_angstrom: number;
  center: { x: number; y: number; z: number };
  box_size: { x: number; y: number; z: number };
  co_ligand: string;
}

interface DockingPose {
  mode: number;
  affinity_kcal_mol: number;
  rmsd_lower_bound: number;
  rmsd_upper_bound: number;
  atom_count: number;
  pdb_block: string;
}

interface DockingResult {
  target: string;
  target_name: string;
  smiles: string;
  grid_center: { x: number; y: number; z: number };
  grid_size: { x: number; y: number; z: number };
  exhaustiveness: number;
  total_modes: number;
  best_affinity_kcal_mol: number;
  poses: DockingPose[];
  docked_pdbqt: string;
}

interface GeometricContact {
  ligand_atom: string;
  ligand_element: string;
  receptor_residue: string;
  receptor_chain: string;
  receptor_atom: string;
  receptor_element: string;
  distance_angstrom: number;
  contact_type: string;
  validation_status: string;
}

interface PocketResidue {
  chain: string;
  resname: string;
  resnum: string;
  label: string;
}

interface PyMOLResult {
  status: string;
  title: string;
  style: string;
  target: string;
  receptor_atoms: number;
  has_ligand: boolean;
  ligand_atoms: number;
  pocket_radius_angstrom: number;
  contact_cutoff_angstrom: number;
  pocket_residues_count: number;
  pocket_residues: PocketResidue[];
  geometric_contacts_count: number;
  geometric_contacts: GeometricContact[];
  image_base64: string;
  image_url: string;
  session_url: string;
  resolution: string;
  software_version: string;
  png_size_bytes?: number;
  pse_size_bytes?: number;
}

interface MolecularProperties {
  smiles: string;
  formula: string;
  molecular_weight: number;
  logp: number;
  tpsa: number;
  hbd: number;
  hba: number;
  rotatable_bonds: number;
  heavy_atom_count: number;
  ring_count: number;
  lipinski_violations: number;
  lipinski_pass: boolean;
}

interface ConformerAtom {
  index: number;
  symbol: string;
  atomic_num: number;
  x: number;
  y: number;
  z: number;
}

interface ConformerData {
  smiles: string;
  atom_count: number;
  energy_kcal_mol?: number;
  atoms: ConformerAtom[];
  mol_block: string;
}

const MolecularLab: React.FC = () => {
  // Navigation / Engine Mode
  const [engineMode, setEngineMode] = useState<'docking' | 'visualization' | 'cheminformatics'>('docking');

  // Shared State
  const [smiles, setSmiles] = useState<string>('CC(=O)Oc1ccccc1C(=O)O'); // Default Aspirin
  const [serverOnline, setServerOnline] = useState<boolean | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Cheminformatics State
  const [presets, setPresets] = useState<PresetMolecule[]>([]);
  const [properties, setProperties] = useState<MolecularProperties | null>(null);
  const [conformer, setConformer] = useState<ConformerData | null>(null);
  const [svgUrl, setSvgUrl] = useState<string>('');
  const [activeChemTab, setActiveChemTab] = useState<'properties' | '3d' | 'molblock'>('properties');

  // Docking State (Phase 4)
  const [targets, setTargets] = useState<DockingTarget[]>([]);
  const [selectedTarget, setSelectedTarget] = useState<string>('6LU7');
  const [exhaustiveness, setExhaustiveness] = useState<number>(4);
  const [numModes, setNumModes] = useState<number>(5);
  const [dockingResult, setDockingResult] = useState<DockingResult | null>(null);
  const [selectedPoseIdx, setSelectedPoseIdx] = useState<number>(0);
  const [proteinPdb, setProteinPdb] = useState<string>('');
  const [viewerStyle, setViewerStyle] = useState<'cartoon' | 'surface' | 'stick'>('cartoon');
  const [dockingViewTab, setDockingViewTab] = useState<'3dmol' | 'pymol'>('3dmol');

  // PyMOL Visualisation Engine State
  const [pymolStyle, setPymolStyle] = useState<'cartoon' | 'surface' | 'ribbon' | 'sticks'>('cartoon');
  const [pocketRadius, setPocketRadius] = useState<number>(4.5);
  const [contactCutoff, setContactCutoff] = useState<number>(3.5);
  const [rayTrace, setRayTrace] = useState<boolean>(true);
  const [pymolResult, setPymolResult] = useState<PyMOLResult | null>(null);
  const [dockingPymolResult, setDockingPymolResult] = useState<PyMOLResult | null>(null);

  // Instant Ligand Rendering State
  const [instantSvg, setInstantSvg] = useState<string>('');
  const [instantProps, setInstantProps] = useState<MolecularProperties | null>(null);
  const [instantConformer, setInstantConformer] = useState<ConformerData | null>(null);
  const [instantLoading, setInstantLoading] = useState<boolean>(false);
  const [instantPreviewMode, setInstantPreviewMode] = useState<'2d' | '3d'>('2d');

  // Instant Ligand Rendering Function
  const fetchInstantLigand = async (targetSmiles: string) => {
    const trimmed = targetSmiles.trim();
    if (!trimmed) {
      setInstantSvg('');
      setInstantProps(null);
      setInstantConformer(null);
      return;
    }

    setInstantLoading(true);
    try {
      const svgPromise = fetch(`${API_BASE}/chem/structure_2d`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ smiles: trimmed }),
      })
        .then((res) => (res.ok ? res.text() : ''))
        .then((svgText) => setInstantSvg(svgText))
        .catch(() => setInstantSvg(''));

      const propsPromise = fetch(`${API_BASE}/chem/properties`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ smiles: trimmed }),
      })
        .then((res) => (res.ok ? res.json() : null))
        .then((p) => {
          if (p) {
            setInstantProps(p);
            setProperties(p);
          }
        })
        .catch(() => {});

      const confPromise = fetch(`${API_BASE}/chem/conformer_3d`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ smiles: trimmed, optimize: true }),
      })
        .then((res) => (res.ok ? res.json() : null))
        .then((c) => {
          if (c) {
            setInstantConformer(c);
            setConformer(c);
          }
        })
        .catch(() => {});

      await Promise.all([svgPromise, propsPromise, confPromise]);
    } catch {
      // Silent catch
    } finally {
      setInstantLoading(false);
    }
  };

  // Instant Debounce on smiles change
  useEffect(() => {
    const timer = setTimeout(() => {
      if (smiles && smiles.trim().length > 0) {
        fetchInstantLigand(smiles);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [smiles]);

  useEffect(() => {
    // Check health
    fetch(`${API_BASE}/health`)
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'ok') setServerOnline(true);
      })
      .catch(() => setServerOnline(false));

    // Fetch chemical presets
    fetch(`${API_BASE}/chem/presets`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setPresets(data))
      .catch(() => {});

    // Fetch docking / viz targets
    fetch(`${API_BASE}/dock/targets`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: DockingTarget[]) => {
        setTargets(data);
        if (data.length > 0) setSelectedTarget(data[0].pdb_id);
      })
      .catch(() => {});
  }, []);

  // Fetch protein PDB when target changes
  useEffect(() => {
    if (!selectedTarget) return;
    fetch(`${API_BASE}/dock/receptor_pdb/${selectedTarget}`)
      .then((res) => (res.ok ? res.text() : ''))
      .then((pdbText) => setProteinPdb(pdbText))
      .catch(() => setProteinPdb(''));
  }, [selectedTarget]);

  // Run Cheminformatics Analysis
  const handleAnalyzeChem = async (inputSmiles?: string) => {
    const targetSmiles = (inputSmiles || smiles).trim();
    if (!targetSmiles) return;

    setLoading(true);
    setError(null);

    try {
      const propRes = await fetch(`${API_BASE}/chem/properties`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ smiles: targetSmiles }),
      });
      if (!propRes.ok) {
        const errData = await propRes.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP ${propRes.status}`);
      }
      const propData = await propRes.json();
      setProperties(propData);

      const confRes = await fetch(`${API_BASE}/chem/conformer_3d`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ smiles: targetSmiles, optimize: true }),
      });
      if (confRes.ok) {
        setConformer(await confRes.json());
      }

      const svgRes = await fetch(`${API_BASE}/chem/structure_2d`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ smiles: targetSmiles }),
      });
      if (svgRes.ok) {
        const svgBlob = await svgRes.blob();
        setSvgUrl(URL.createObjectURL(svgBlob));
      }
    } catch (err: any) {
      setError(err.message || 'Cheminformatics computation failed');
    } finally {
      setLoading(false);
    }
  };

  // Run AutoDock Vina Simulation (Phase 4)
  const handleRunDocking = async () => {
    if (!smiles.trim()) {
      setError('Please provide a valid ligand SMILES string.');
      return;
    }

    setLoading(true);
    setError(null);
    setSelectedPoseIdx(0);
    setDockingPymolResult(null);

    try {
      const res = await fetch(`${API_BASE}/dock/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          smiles: smiles.trim(),
          target: selectedTarget,
          exhaustiveness: Number(exhaustiveness),
          num_modes: Number(numModes),
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Docking failed with HTTP ${res.status}`);
      }

      const data: DockingResult = await res.json();
      setDockingResult(data);
    } catch (err: any) {
      setError(err.message || 'AutoDock Vina simulation failed.');
    } finally {
      setLoading(false);
    }
  };

  // Render Docked Pose with PyMOL
  const handleRenderDockedPoseWithPyMOL = async () => {
    if (!dockingResult || !dockingResult.docked_pdbqt) return;
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/viz/render`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target: dockingResult.target,
          docked_pdbqt: dockingResult.docked_pdbqt,
          pose_mode: selectedPoseIdx + 1,
          style: pymolStyle,
          pocket_radius: Number(pocketRadius),
          contact_cutoff: Number(contactCutoff),
          width: 1200,
          height: 900,
          dpi: 150,
          ray_trace: rayTrace,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `PyMOL rendering failed with HTTP ${res.status}`);
      }

      const data: PyMOLResult = await res.json();
      setDockingPymolResult(data);
      setDockingViewTab('pymol');
    } catch (err: any) {
      setError(err.message || 'PyMOL rendering failed.');
    } finally {
      setLoading(false);
    }
  };

  // Render Standalone Target / Ligand with PyMOL
  const handleRenderPyMOLStandalone = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/viz/render`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target: selectedTarget,
          smiles: smiles.trim() || undefined,
          style: pymolStyle,
          pocket_radius: Number(pocketRadius),
          contact_cutoff: Number(contactCutoff),
          width: 1200,
          height: 900,
          dpi: 150,
          ray_trace: rayTrace,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `PyMOL rendering failed with HTTP ${res.status}`);
      }

      const data: PyMOLResult = await res.json();
      setPymolResult(data);
    } catch (err: any) {
      setError(err.message || 'PyMOL rendering failed.');
    } finally {
      setLoading(false);
    }
  };

  const currentTargetObj = targets.find((t) => t.pdb_id === selectedTarget);
  const activePose = dockingResult?.poses[selectedPoseIdx];

  // Estimate Ki = exp(deltaG / (RT))
  const estimateKi = (deltaG: number) => {
    const RT = 0.592; // kcal/mol at 298.15 K
    const molar = Math.exp(deltaG / RT);
    if (molar < 1e-6) {
      return `${(molar * 1e9).toFixed(2)} nM`;
    } else if (molar < 1e-3) {
      return `${(molar * 1e6).toFixed(2)} µM`;
    } else {
      return `${(molar * 1e3).toFixed(2)} mM`;
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', color: '#e0e0e0', fontFamily: 'system-ui, sans-serif' }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #30363d', paddingBottom: '14px', marginBottom: '20px' }}>
        <div>
          <h2 style={{ color: '#00ffff', margin: 0, fontSize: '24px' }}>Molecular Lab & Visualisation Engine</h2>
          <p style={{ margin: '4px 0 0', color: '#8b949e', fontSize: '14px' }}>
            AutoDock Vina multithreaded docking, Schrödinger PyMOL 3.1.0 open-source engine, and 3Dmol.js viewer.
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              display: 'inline-block',
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: serverOnline ? '#00ff88' : '#ff4444',
            }}
          />
          <span style={{ fontSize: '13px', color: serverOnline ? '#00ff88' : '#ff8888', fontWeight: 500 }}>
            {serverOnline ? 'Backend Online (127.0.0.1:8000)' : 'Backend Offline'}
          </span>
        </div>
      </div>

      {/* Engine Switcher */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
        <button
          onClick={() => setEngineMode('docking')}
          style={{
            flex: 1,
            padding: '12px',
            backgroundColor: engineMode === 'docking' ? '#00ffff22' : '#161b22',
            color: engineMode === 'docking' ? '#00ffff' : '#8b949e',
            border: engineMode === 'docking' ? '2px solid #00ffff' : '1px solid #30363d',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: 'bold',
            fontSize: '14px',
          }}
        >
          🧬 AutoDock Vina Docking Engine
        </button>
        <button
          onClick={() => {
            setEngineMode('visualization');
            if (!pymolResult) handleRenderPyMOLStandalone();
          }}
          style={{
            flex: 1,
            padding: '12px',
            backgroundColor: engineMode === 'visualization' ? '#00ffff22' : '#161b22',
            color: engineMode === 'visualization' ? '#00ffff' : '#8b949e',
            border: engineMode === 'visualization' ? '2px solid #00ffff' : '1px solid #30363d',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: 'bold',
            fontSize: '14px',
          }}
        >
          🔬 PyMOL 3D Visualisation Engine
        </button>
        <button
          onClick={() => {
            setEngineMode('cheminformatics');
            if (!properties) handleAnalyzeChem();
          }}
          style={{
            flex: 1,
            padding: '12px',
            backgroundColor: engineMode === 'cheminformatics' ? '#00ffff22' : '#161b22',
            color: engineMode === 'cheminformatics' ? '#00ffff' : '#8b949e',
            border: engineMode === 'cheminformatics' ? '2px solid #00ffff' : '1px solid #30363d',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: 'bold',
            fontSize: '14px',
          }}
        >
          🧪 Cheminformatics & Lipinski Profiler
        </button>
      </div>

      {/* Ligand Input & Presets Bar */}
      <div style={{ backgroundColor: '#161b22', padding: '16px', borderRadius: '8px', border: '1px solid #30363d', marginBottom: '20px' }}>
        <div style={{ marginBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <label style={{ fontSize: '13px', color: '#8b949e', fontWeight: 'bold' }}>Ligand SMILES String:</label>
            <span style={{ fontSize: '11px', color: '#00ffff', backgroundColor: '#00ffff22', padding: '2px 6px', borderRadius: '4px' }}>
              ⚡ Instant Live Render
            </span>
          </div>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {presets.slice(0, 7).map((p) => (
              <button
                key={p.name}
                onClick={() => {
                  setSmiles(p.smiles);
                  fetchInstantLigand(p.smiles);
                  if (engineMode === 'cheminformatics') handleAnalyzeChem(p.smiles);
                }}
                style={{
                  backgroundColor: smiles === p.smiles ? '#00ffff33' : '#21262d',
                  color: smiles === p.smiles ? '#00ffff' : '#c9d1d9',
                  border: smiles === p.smiles ? '1px solid #00ffff' : '1px solid #30363d',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '11px',
                  cursor: 'pointer',
                  fontWeight: smiles === p.smiles ? 'bold' : 'normal',
                }}
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            value={smiles}
            onChange={(e) => {
              setSmiles(e.target.value);
            }}
            placeholder="e.g. CC(=O)Oc1ccccc1C(=O)O"
            style={{
              flex: 1,
              padding: '10px 14px',
              backgroundColor: '#0d1117',
              border: '1px solid #30363d',
              borderRadius: '6px',
              color: '#fff',
              fontSize: '14px',
              fontFamily: 'monospace',
            }}
          />
          {engineMode === 'cheminformatics' && (
            <button
              onClick={() => handleAnalyzeChem()}
              disabled={loading}
              style={{
                padding: '10px 20px',
                backgroundColor: '#00ffff',
                color: '#000',
                fontWeight: 'bold',
                border: 'none',
                borderRadius: '6px',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? 'Computing...' : 'Calculate Properties'}
            </button>
          )}
        </div>

        {/* Instant Ligand Live Rendering Panel */}
        {smiles.trim().length > 0 && (
          <div
            style={{
              backgroundColor: '#0d1117',
              border: '1px solid #30363d',
              borderRadius: '8px',
              padding: '14px 16px',
              marginTop: '14px',
              display: 'flex',
              gap: '20px',
              alignItems: 'center',
              flexWrap: 'wrap',
            }}
          >
            {/* Left: 2D Vector / 3D WebGL Toggle & Visualizer */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: '4px', marginBottom: '8px' }}>
                <button
                  onClick={() => setInstantPreviewMode('2d')}
                  style={{
                    padding: '3px 8px',
                    fontSize: '11px',
                    borderRadius: '4px',
                    border: 'none',
                    cursor: 'pointer',
                    backgroundColor: instantPreviewMode === '2d' ? '#00ffff' : '#21262d',
                    color: instantPreviewMode === '2d' ? '#000' : '#8b949e',
                    fontWeight: 'bold',
                  }}
                >
                  2D Structure
                </button>
                <button
                  onClick={() => setInstantPreviewMode('3d')}
                  style={{
                    padding: '3px 8px',
                    fontSize: '11px',
                    borderRadius: '4px',
                    border: 'none',
                    cursor: 'pointer',
                    backgroundColor: instantPreviewMode === '3d' ? '#00ffff' : '#21262d',
                    color: instantPreviewMode === '3d' ? '#000' : '#8b949e',
                    fontWeight: 'bold',
                  }}
                >
                  3D Conformer
                </button>
              </div>

              <div
                style={{
                  width: '200px',
                  height: '150px',
                  backgroundColor: '#161b22',
                  borderRadius: '6px',
                  border: '1px solid #30363d',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  overflow: 'hidden',
                  position: 'relative',
                }}
              >
                {instantLoading ? (
                  <div style={{ fontSize: '11px', color: '#00ffff' }}>Rendering Live...</div>
                ) : instantPreviewMode === '2d' ? (
                  instantSvg ? (
                    <div
                      dangerouslySetInnerHTML={{ __html: instantSvg }}
                      style={{
                        width: '100%',
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        filter: 'invert(0.9) hue-rotate(180deg)',
                      }}
                    />
                  ) : (
                    <span style={{ fontSize: '11px', color: '#8b949e' }}>Generating 2D...</span>
                  )
                ) : instantConformer?.mol_block ? (
                  <MolecularViewer3D ligandPdb={instantConformer.mol_block} height="150px" />
                ) : (
                  <span style={{ fontSize: '11px', color: '#8b949e' }}>Generating 3D...</span>
                )}
              </div>
            </div>

            {/* Right: Instant Physicochemical Properties */}
            <div style={{ flex: 1, minWidth: '300px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '6px' }}>
                <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#00ffff' }}>
                  ⚡ Instant Molecular Properties
                </span>
                {instantProps && (
                  <span
                    style={{
                      fontSize: '11px',
                      padding: '2px 8px',
                      borderRadius: '10px',
                      backgroundColor: instantProps.lipinski_pass ? '#00ff8822' : '#ff444422',
                      color: instantProps.lipinski_pass ? '#00ff88' : '#ff4444',
                      border: `1px solid ${instantProps.lipinski_pass ? '#00ff88' : '#ff4444'}`,
                      fontWeight: 500,
                    }}
                  >
                    {instantProps.lipinski_pass ? '✓ Lipinski Pass (Drug-Like)' : `⚠ ${instantProps.lipinski_violations} Lipinski Violations`}
                  </span>
                )}
              </div>

              {instantProps ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(115px, 1fr))', gap: '8px' }}>
                  <div style={{ backgroundColor: '#161b22', padding: '6px 10px', borderRadius: '4px', border: '1px solid #30363d' }}>
                    <div style={{ fontSize: '10px', color: '#8b949e' }}>Formula</div>
                    <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#fff' }}>{instantProps.formula}</div>
                  </div>
                  <div style={{ backgroundColor: '#161b22', padding: '6px 10px', borderRadius: '4px', border: '1px solid #30363d' }}>
                    <div style={{ fontSize: '10px', color: '#8b949e' }}>Molecular Weight</div>
                    <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#00ffff' }}>{instantProps.molecular_weight.toFixed(1)} g/mol</div>
                  </div>
                  <div style={{ backgroundColor: '#161b22', padding: '6px 10px', borderRadius: '4px', border: '1px solid #30363d' }}>
                    <div style={{ fontSize: '10px', color: '#8b949e' }}>Crippen LogP</div>
                    <div style={{ fontSize: '13px', fontWeight: 'bold', color: instantProps.logp <= 5 ? '#00ff88' : '#ff8888' }}>{instantProps.logp.toFixed(2)}</div>
                  </div>
                  <div style={{ backgroundColor: '#161b22', padding: '6px 10px', borderRadius: '4px', border: '1px solid #30363d' }}>
                    <div style={{ fontSize: '10px', color: '#8b949e' }}>Polar Surface (TPSA)</div>
                    <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#fff' }}>{instantProps.tpsa.toFixed(1)} Å²</div>
                  </div>
                  <div style={{ backgroundColor: '#161b22', padding: '6px 10px', borderRadius: '4px', border: '1px solid #30363d' }}>
                    <div style={{ fontSize: '10px', color: '#8b949e' }}>HBD / HBA</div>
                    <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#fff' }}>{instantProps.hbd} / {instantProps.hba}</div>
                  </div>
                  <div style={{ backgroundColor: '#161b22', padding: '6px 10px', borderRadius: '4px', border: '1px solid #30363d' }}>
                    <div style={{ fontSize: '10px', color: '#8b949e' }}>Rotatable Bonds</div>
                    <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#fff' }}>{instantProps.rotatable_bonds}</div>
                  </div>
                </div>
              ) : (
                <div style={{ fontSize: '12px', color: '#8b949e' }}>
                  {instantLoading ? 'Calculating properties...' : 'Type a valid SMILES string above to render.'}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {error && (
        <div style={{ backgroundColor: '#ff444422', border: '1px solid #ff4444', color: '#ff8888', padding: '12px', borderRadius: '6px', marginBottom: '20px', fontSize: '13px' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* ======================= DOCKING ENGINE VIEW ======================= */}
      {engineMode === 'docking' && (
        <div>
          {/* Target Selector & Docking Parameters */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '20px', marginBottom: '20px' }}>
            {/* Target Card */}
            <div style={{ backgroundColor: '#161b22', padding: '16px', borderRadius: '8px', border: '1px solid #30363d' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h3 style={{ margin: 0, color: '#00ffff', fontSize: '16px' }}>Select Therapeutic Target Receptor</h3>
                <span style={{ fontSize: '12px', color: '#8b949e' }}>PDB Archive Validated</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '8px', marginBottom: '14px' }}>
                {targets.map((t) => (
                  <button
                    key={t.pdb_id}
                    onClick={() => setSelectedTarget(t.pdb_id)}
                    style={{
                      padding: '8px 4px',
                      backgroundColor: selectedTarget === t.pdb_id ? '#00ffff22' : '#21262d',
                      color: selectedTarget === t.pdb_id ? '#00ffff' : '#c9d1d9',
                      border: selectedTarget === t.pdb_id ? '2px solid #00ffff' : '1px solid #30363d',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      textAlign: 'center',
                    }}
                  >
                    <div style={{ fontWeight: 'bold', fontSize: '13px' }}>{t.pdb_id}</div>
                    <div style={{ fontSize: '10px', color: '#8b949e', marginTop: '2px' }}>{t.indication.split('/')[0].trim()}</div>
                  </button>
                ))}
              </div>

              {currentTargetObj && (
                <div style={{ backgroundColor: '#0d1117', padding: '12px', borderRadius: '6px', fontSize: '13px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <strong style={{ color: '#fff' }}>{currentTargetObj.name}</strong>
                    <span style={{ color: '#00ff88' }}>{currentTargetObj.resolution_angstrom} Å Resolution</span>
                  </div>
                  <div style={{ color: '#8b949e', marginBottom: '6px' }}>{currentTargetObj.organism} • Indication: {currentTargetObj.indication}</div>
                  <p style={{ margin: 0, color: '#c9d1d9', fontSize: '12px' }}>{currentTargetObj.description}</p>
                </div>
              )}
            </div>

            {/* Run Docking Action Card */}
            <div style={{ backgroundColor: '#161b22', padding: '16px', borderRadius: '8px', border: '1px solid #30363d', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <h4 style={{ margin: '0 0 10px', color: '#fff', fontSize: '15px' }}>Docking Parameters</h4>
                <div style={{ marginBottom: '10px' }}>
                  <label style={{ fontSize: '12px', color: '#8b949e', display: 'block', marginBottom: '4px' }}>
                    Search Exhaustiveness:
                  </label>
                  <select
                    value={exhaustiveness}
                    onChange={(e) => setExhaustiveness(Number(e.target.value))}
                    style={{ width: '100%', padding: '6px', backgroundColor: '#0d1117', color: '#fff', border: '1px solid #30363d', borderRadius: '4px' }}
                  >
                    <option value={4}>Fast Screening (Exhaustiveness: 4)</option>
                    <option value={8}>Standard Precision (Exhaustiveness: 8)</option>
                    <option value={16}>High Precision (Exhaustiveness: 16)</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '12px', color: '#8b949e', display: 'block', marginBottom: '4px' }}>
                    Binding Modes to Keep:
                  </label>
                  <select
                    value={numModes}
                    onChange={(e) => setNumModes(Number(e.target.value))}
                    style={{ width: '100%', padding: '6px', backgroundColor: '#0d1117', color: '#fff', border: '1px solid #30363d', borderRadius: '4px' }}
                  >
                    <option value={3}>Top 3 Modes</option>
                    <option value={5}>Top 5 Modes</option>
                    <option value={9}>Top 9 Modes</option>
                  </select>
                </div>
              </div>

              <button
                onClick={handleRunDocking}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '12px',
                  backgroundColor: '#00ffff',
                  color: '#000',
                  fontWeight: 'bold',
                  fontSize: '15px',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.7 : 1,
                  marginTop: '14px',
                }}
              >
                {loading ? 'Running Vina Simulation...' : '🚀 Execute Vina Docking'}
              </button>
            </div>
          </div>

          {/* Pre-Dock Target & Ligand 3D Preview (Shown before docking execution) */}
          {!dockingResult && (
            <div style={{ backgroundColor: '#161b22', padding: '16px', borderRadius: '8px', border: '1px solid #30363d', marginBottom: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                <div>
                  <h4 style={{ margin: 0, color: '#00ffff', fontSize: '15px' }}>
                    🌐 Target Receptor & Ligand 3D Preview ({selectedTarget} - {currentTargetObj?.name})
                  </h4>
                  <p style={{ margin: '2px 0 0', color: '#8b949e', fontSize: '12px' }}>
                    Pre-docking preview of active site receptor pocket with live ligand conformer. Click &apos;🚀 Execute Vina Docking&apos; to run conformational simulation.
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '6px' }}>
                  {(['cartoon', 'surface', 'stick'] as const).map((style) => (
                    <button
                      key={style}
                      onClick={() => setViewerStyle(style)}
                      style={{
                        padding: '4px 8px',
                        borderRadius: '4px',
                        border: 'none',
                        fontSize: '11px',
                        cursor: 'pointer',
                        backgroundColor: viewerStyle === style ? '#00ffff' : '#21262d',
                        color: viewerStyle === style ? '#000' : '#c9d1d9',
                        fontWeight: viewerStyle === style ? 'bold' : 'normal',
                        textTransform: 'capitalize',
                      }}
                    >
                      {style}
                    </button>
                  ))}
                </div>
              </div>
              <MolecularViewer3D
                proteinPdb={proteinPdb}
                ligandPdb={instantConformer?.mol_block}
                styleMode={viewerStyle}
                height="450px"
              />
              <div style={{ marginTop: '10px', display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#8b949e', flexWrap: 'wrap', gap: '6px' }}>
                <span>🎨 Spectrum: Target Receptor ({selectedTarget})</span>
                <span>🟢 Green Sticks: Live Ligand Conformer ({instantProps?.formula || 'Ligand'})</span>
              </div>
            </div>
          )}

          {/* Results: 3D Visualization & Binding Poses */}
          {dockingResult && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px' }}>
              {/* Dual Viewer: 3Dmol.js WebGL & PyMOL High-Res Render */}
              <div style={{ backgroundColor: '#161b22', padding: '16px', borderRadius: '8px', border: '1px solid #30363d' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button
                      onClick={() => setDockingViewTab('3dmol')}
                      style={{
                        padding: '6px 12px',
                        borderRadius: '6px',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        backgroundColor: dockingViewTab === '3dmol' ? '#00ffff' : '#21262d',
                        color: dockingViewTab === '3dmol' ? '#000' : '#c9d1d9',
                      }}
                    >
                      🌐 3Dmol.js WebGL View
                    </button>
                    <button
                      onClick={() => {
                        if (!dockingPymolResult) handleRenderDockedPoseWithPyMOL();
                        else setDockingViewTab('pymol');
                      }}
                      style={{
                        padding: '6px 12px',
                        borderRadius: '6px',
                        border: 'none',
                        cursor: 'pointer',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        backgroundColor: dockingViewTab === 'pymol' ? '#00ffff' : '#21262d',
                        color: dockingViewTab === 'pymol' ? '#000' : '#c9d1d9',
                      }}
                    >
                      🔬 PyMOL Ray-Traced Render
                    </button>
                  </div>

                  {dockingViewTab === '3dmol' && (
                    <div style={{ display: 'flex', gap: '4px' }}>
                      {(['cartoon', 'surface', 'stick'] as const).map((style) => (
                        <button
                          key={style}
                          onClick={() => setViewerStyle(style)}
                          style={{
                            padding: '4px 8px',
                            borderRadius: '4px',
                            border: 'none',
                            fontSize: '11px',
                            cursor: 'pointer',
                            backgroundColor: viewerStyle === style ? '#00ffff' : '#21262d',
                            color: viewerStyle === style ? '#000' : '#c9d1d9',
                            fontWeight: viewerStyle === style ? 'bold' : 'normal',
                            textTransform: 'capitalize',
                          }}
                        >
                          {style}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {dockingViewTab === '3dmol' ? (
                  <>
                    <MolecularViewer3D
                      proteinPdb={proteinPdb}
                      ligandPdb={activePose?.pdb_block}
                      styleMode={viewerStyle}
                      height="450px"
                    />
                    <div style={{ marginTop: '10px', display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#8b949e' }}>
                      <span>🎨 Spectrum Cartoon: Target Protein ({dockingResult.target})</span>
                      <span>🟢 Green Sticks: Docked Ligand Pose #{selectedPoseIdx + 1} ({activePose?.affinity_kcal_mol} kcal/mol)</span>
                    </div>
                  </>
                ) : (
                  <div>
                    {dockingPymolResult ? (
                      <div>
                        <div style={{ position: 'relative', borderRadius: '8px', overflow: 'hidden', border: '1px solid #30363d', backgroundColor: '#0d1117' }}>
                          <img
                            src={`data:image/png;base64,${dockingPymolResult.image_base64}`}
                            alt="PyMOL Docked Pose Render"
                            style={{ width: '100%', height: 'auto', display: 'block' }}
                          />
                          <div style={{ position: 'absolute', top: '10px', right: '10px', display: 'flex', gap: '8px' }}>
                            <a
                              href={`${API_BASE}${dockingPymolResult.session_url}`}
                              download
                              style={{
                                padding: '6px 12px',
                                backgroundColor: '#1f6feb',
                                color: '#fff',
                                borderRadius: '4px',
                                textDecoration: 'none',
                                fontSize: '12px',
                                fontWeight: 'bold',
                              }}
                            >
                              ⬇️ Download .PSE Session
                            </a>
                            <a
                              href={`${API_BASE}${dockingPymolResult.image_url}`}
                              download
                              style={{
                                padding: '6px 12px',
                                backgroundColor: '#238636',
                                color: '#fff',
                                borderRadius: '4px',
                                textDecoration: 'none',
                                fontSize: '12px',
                                fontWeight: 'bold',
                              }}
                            >
                              🖼️ Download PNG
                            </a>
                          </div>
                        </div>

                        {/* PyMOL Geometric Contacts & Pocket Residues */}
                        <div style={{ marginTop: '14px', backgroundColor: '#0d1117', padding: '12px', borderRadius: '6px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
                            <strong style={{ color: '#00ffff' }}>Binding Pocket Residues ({dockingPymolResult.pocket_residues_count})</strong>
                            <span style={{ color: '#8b949e' }}>Radius: {dockingPymolResult.pocket_radius_angstrom} Å</span>
                          </div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '12px' }}>
                            {dockingPymolResult.pocket_residues.map((r) => (
                              <span
                                key={r.label}
                                style={{
                                  backgroundColor: '#21262d',
                                  padding: '2px 8px',
                                  borderRadius: '4px',
                                  fontSize: '11px',
                                  fontFamily: 'monospace',
                                  color: '#79c0ff',
                                }}
                              >
                                {r.label}
                              </span>
                            ))}
                          </div>

                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '13px' }}>
                            <strong style={{ color: '#00ff88' }}>Geometric Distance Contacts ({dockingPymolResult.geometric_contacts_count})</strong>
                            <span style={{ fontSize: '11px', color: '#ffaa00' }}>Spatial cutoff &lt; {dockingPymolResult.contact_cutoff_angstrom} Å</span>
                          </div>
                          {dockingPymolResult.geometric_contacts.length > 0 ? (
                            <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse', fontFamily: 'monospace' }}>
                              <thead>
                                <tr style={{ color: '#8b949e', borderBottom: '1px solid #30363d', textAlign: 'left' }}>
                                  <th style={{ padding: '4px' }}>Ligand Atom</th>
                                  <th style={{ padding: '4px' }}>Pocket Residue</th>
                                  <th style={{ padding: '4px' }}>Receptor Atom</th>
                                  <th style={{ padding: '4px' }}>Distance (Å)</th>
                                  <th style={{ padding: '4px' }}>Contact Type</th>
                                </tr>
                              </thead>
                              <tbody>
                                {dockingPymolResult.geometric_contacts.slice(0, 6).map((c, i) => (
                                  <tr key={i} style={{ borderBottom: '1px solid #21262d' }}>
                                    <td style={{ padding: '4px', color: '#ffff00' }}>{c.ligand_atom} ({c.ligand_element})</td>
                                    <td style={{ padding: '4px', color: '#79c0ff' }}>{c.receptor_residue}</td>
                                    <td style={{ padding: '4px', color: '#c9d1d9' }}>{c.receptor_atom} ({c.receptor_element})</td>
                                    <td style={{ padding: '4px', color: '#00ff88', fontWeight: 'bold' }}>{c.distance_angstrom} Å</td>
                                    <td style={{ padding: '4px', color: '#8b949e' }}>{c.contact_type}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          ) : (
                            <div style={{ fontSize: '12px', color: '#8b949e' }}>No polar heteroatom contacts detected under {dockingPymolResult.contact_cutoff_angstrom} Å.</div>
                          )}
                          <div style={{ marginTop: '8px', fontSize: '11px', color: '#8b949e', fontStyle: 'italic' }}>
                            * Note: Geometrically detected proximity distances. Does not imply chemically validated bonding.
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div style={{ textAlign: 'center', padding: '40px', color: '#8b949e' }}>
                        <p>Generate high-resolution PyMOL ray-trace and session for Mode #{selectedPoseIdx + 1}:</p>
                        <button
                          onClick={handleRenderDockedPoseWithPyMOL}
                          disabled={loading}
                          style={{
                            padding: '10px 20px',
                            backgroundColor: '#00ffff',
                            color: '#000',
                            border: 'none',
                            borderRadius: '6px',
                            fontWeight: 'bold',
                            cursor: 'pointer',
                          }}
                        >
                          {loading ? 'Rendering with PyMOL...' : '🔬 Render Mode with PyMOL'}
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Poses Table & Binding Affinity */}
              <div style={{ backgroundColor: '#161b22', padding: '16px', borderRadius: '8px', border: '1px solid #30363d', display: 'flex', flexDirection: 'column' }}>
                <div style={{ marginBottom: '14px', backgroundColor: '#0d1117', padding: '12px', borderRadius: '6px', textAlign: 'center', borderLeft: '4px solid #00ffff' }}>
                  <div style={{ fontSize: '12px', color: '#8b949e' }}>Best Predicted Binding Affinity</div>
                  <div style={{ fontSize: '24px', color: '#00ffff', fontWeight: 'bold' }}>
                    {dockingResult.best_affinity_kcal_mol} <span style={{ fontSize: '14px', color: '#8b949e' }}>kcal/mol</span>
                  </div>
                  <div style={{ fontSize: '12px', color: '#00ff88', marginTop: '2px' }}>
                    Est. Affinity ($K_i$): ~{estimateKi(dockingResult.best_affinity_kcal_mol)}
                  </div>
                </div>

                <h4 style={{ margin: '0 0 8px', fontSize: '14px', color: '#fff' }}>Docked Conformation Modes</h4>
                <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #30363d', borderRadius: '4px' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#21262d', textAlign: 'left', color: '#8b949e' }}>
                        <th style={{ padding: '6px' }}>Mode</th>
                        <th style={{ padding: '6px' }}>Affinity</th>
                        <th style={{ padding: '6px' }}>RMSD l.b.</th>
                        <th style={{ padding: '6px' }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dockingResult.poses.map((p, idx) => (
                        <tr
                          key={p.mode}
                          style={{
                            borderBottom: '1px solid #21262d',
                            backgroundColor: selectedPoseIdx === idx ? '#00ffff18' : 'transparent',
                          }}
                        >
                          <td style={{ padding: '6px', fontWeight: 'bold' }}>#{p.mode}</td>
                          <td style={{ padding: '6px', color: '#00ffff', fontWeight: 'bold' }}>
                            {p.affinity_kcal_mol}
                          </td>
                          <td style={{ padding: '6px', color: '#8b949e' }}>{p.rmsd_lower_bound} Å</td>
                          <td style={{ padding: '6px' }}>
                            <button
                              onClick={() => {
                                setSelectedPoseIdx(idx);
                                setDockingPymolResult(null);
                              }}
                              style={{
                                padding: '2px 8px',
                                backgroundColor: selectedPoseIdx === idx ? '#00ffff' : '#30363d',
                                color: selectedPoseIdx === idx ? '#000' : '#fff',
                                border: 'none',
                                borderRadius: '3px',
                                cursor: 'pointer',
                                fontSize: '11px',
                              }}
                            >
                              {selectedPoseIdx === idx ? 'Viewing' : 'Select'}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <button
                  onClick={handleRenderDockedPoseWithPyMOL}
                  disabled={loading}
                  style={{
                    marginTop: '12px',
                    padding: '8px',
                    backgroundColor: '#1f6feb',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    fontSize: '12px',
                    fontWeight: 'bold',
                  }}
                >
                  🔬 Render Selected Mode in PyMOL
                </button>

                <button
                  onClick={() => {
                    const blob = new Blob([dockingResult.docked_pdbqt], { type: 'text/plain' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `${dockingResult.target}_docked_${dockingResult.smiles.slice(0, 8)}.pdbqt`;
                    a.click();
                  }}
                  style={{
                    marginTop: '8px',
                    padding: '8px',
                    backgroundColor: '#21262d',
                    color: '#c9d1d9',
                    border: '1px solid #30363d',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px',
                  }}
                >
                  💾 Download Docked PDBQT
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ======================= DEDICATED PYMOL VISUALISATION ENGINE ======================= */}
      {engineMode === 'visualization' && (
        <div>
          {/* Controls Bar */}
          <div style={{ backgroundColor: '#161b22', padding: '16px', borderRadius: '8px', border: '1px solid #30363d', marginBottom: '20px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '14px', alignItems: 'end' }}>
              <div>
                <label style={{ fontSize: '12px', color: '#8b949e', display: 'block', marginBottom: '4px' }}>Target Receptor:</label>
                <select
                  value={selectedTarget}
                  onChange={(e) => setSelectedTarget(e.target.value)}
                  style={{ width: '100%', padding: '8px', backgroundColor: '#0d1117', color: '#fff', border: '1px solid #30363d', borderRadius: '4px' }}
                >
                  {targets.map((t) => (
                    <option key={t.pdb_id} value={t.pdb_id}>{t.pdb_id} - {t.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: '12px', color: '#8b949e', display: 'block', marginBottom: '4px' }}>Rendering Style:</label>
                <select
                  value={pymolStyle}
                  onChange={(e) => setPymolStyle(e.target.value as any)}
                  style={{ width: '100%', padding: '8px', backgroundColor: '#0d1117', color: '#fff', border: '1px solid #30363d', borderRadius: '4px' }}
                >
                  <option value="cartoon">Cartoon (Secondary Structure)</option>
                  <option value="surface">Transparent Surface</option>
                  <option value="ribbon">Ribbon Wireframe</option>
                  <option value="sticks">All-Atom Sticks</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '12px', color: '#8b949e', display: 'block', marginBottom: '4px' }}>Pocket Radius (Å):</label>
                <input
                  type="number"
                  step="0.5"
                  value={pocketRadius}
                  onChange={(e) => setPocketRadius(Number(e.target.value))}
                  style={{ width: '100%', padding: '8px', backgroundColor: '#0d1117', color: '#fff', border: '1px solid #30363d', borderRadius: '4px' }}
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', color: '#8b949e', display: 'block', marginBottom: '4px' }}>Contact Cutoff (Å):</label>
                <input
                  type="number"
                  step="0.5"
                  value={contactCutoff}
                  onChange={(e) => setContactCutoff(Number(e.target.value))}
                  style={{ width: '100%', padding: '8px', backgroundColor: '#0d1117', color: '#fff', border: '1px solid #30363d', borderRadius: '4px' }}
                />
              </div>

              <button
                onClick={handleRenderPyMOLStandalone}
                disabled={loading}
                style={{
                  padding: '10px',
                  backgroundColor: '#00ffff',
                  color: '#000',
                  fontWeight: 'bold',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.7 : 1,
                }}
              >
                {loading ? 'Rendering PyMOL...' : '📸 Render Scene'}
              </button>
            </div>
          </div>

          {/* Render Result Card */}
          {pymolResult && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px' }}>
              {/* Main Image View */}
              <div style={{ backgroundColor: '#161b22', padding: '16px', borderRadius: '8px', border: '1px solid #30363d' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <h3 style={{ margin: 0, color: '#00ffff', fontSize: '16px' }}>
                    {pymolResult.target} High-Resolution 3D Render ({pymolResult.style})
                  </h3>
                  <span style={{ fontSize: '12px', color: '#8b949e' }}>{pymolResult.resolution} • {pymolResult.software_version}</span>
                </div>

                <div style={{ borderRadius: '8px', overflow: 'hidden', border: '1px solid #30363d', backgroundColor: '#0d1117' }}>
                  <img
                    src={`data:image/png;base64,${pymolResult.image_base64}`}
                    alt="PyMOL Rendering"
                    style={{ width: '100%', height: 'auto', display: 'block' }}
                  />
                </div>

                <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '12px', color: '#8b949e' }}>
                    Receptor Atoms: <strong>{pymolResult.receptor_atoms}</strong> | Ligand Atoms: <strong>{pymolResult.ligand_atoms}</strong>
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <a
                      href={`${API_BASE}${pymolResult.session_url}`}
                      download
                      style={{
                        padding: '6px 12px',
                        backgroundColor: '#1f6feb',
                        color: '#fff',
                        borderRadius: '4px',
                        textDecoration: 'none',
                        fontSize: '12px',
                        fontWeight: 'bold',
                      }}
                    >
                      ⬇️ Download .PSE Session
                    </a>
                    <a
                      href={`${API_BASE}${pymolResult.image_url}`}
                      download
                      style={{
                        padding: '6px 12px',
                        backgroundColor: '#238636',
                        color: '#fff',
                        borderRadius: '4px',
                        textDecoration: 'none',
                        fontSize: '12px',
                        fontWeight: 'bold',
                      }}
                    >
                      🖼️ Download PNG
                    </a>
                  </div>
                </div>
              </div>

              {/* Side Panel: Pocket Residues & Geometric Contacts */}
              <div style={{ backgroundColor: '#161b22', padding: '16px', borderRadius: '8px', border: '1px solid #30363d', display: 'flex', flexDirection: 'column' }}>
                <h4 style={{ margin: '0 0 10px', color: '#00ffff', fontSize: '14px' }}>
                  Binding Pocket Residues ({pymolResult.pocket_residues_count})
                </h4>
                <div style={{ maxHeight: '160px', overflowY: 'auto', marginBottom: '14px', border: '1px solid #30363d', borderRadius: '4px', padding: '8px', backgroundColor: '#0d1117' }}>
                  {pymolResult.pocket_residues.length > 0 ? (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                      {pymolResult.pocket_residues.map((r) => (
                        <span key={r.label} style={{ backgroundColor: '#21262d', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', color: '#79c0ff' }}>
                          {r.label}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: '12px', color: '#8b949e' }}>No localized pocket residues. (Receptor-only view)</div>
                  )}
                </div>

                <h4 style={{ margin: '0 0 8px', color: '#00ff88', fontSize: '14px' }}>
                  Geometric Distance Contacts ({pymolResult.geometric_contacts_count})
                </h4>
                <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #30363d', borderRadius: '4px', padding: '6px', backgroundColor: '#0d1117' }}>
                  {pymolResult.geometric_contacts.length > 0 ? (
                    <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse', fontFamily: 'monospace' }}>
                      <thead>
                        <tr style={{ color: '#8b949e', borderBottom: '1px solid #30363d', textAlign: 'left' }}>
                          <th style={{ padding: '4px' }}>Residue</th>
                          <th style={{ padding: '4px' }}>Dist (Å)</th>
                          <th style={{ padding: '4px' }}>Pair</th>
                        </tr>
                      </thead>
                      <tbody>
                        {pymolResult.geometric_contacts.map((c, i) => (
                          <tr key={i} style={{ borderBottom: '1px solid #21262d' }}>
                            <td style={{ padding: '4px', color: '#79c0ff' }}>{c.receptor_residue}</td>
                            <td style={{ padding: '4px', color: '#00ff88', fontWeight: 'bold' }}>{c.distance_angstrom}</td>
                            <td style={{ padding: '4px', color: '#8b949e' }}>{c.ligand_atom}-{c.receptor_atom}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <div style={{ fontSize: '12px', color: '#8b949e' }}>No geometric contacts detected within {pymolResult.contact_cutoff_angstrom} Å.</div>
                  )}
                </div>
                <div style={{ marginTop: '10px', fontSize: '11px', color: '#8b949e', fontStyle: 'italic' }}>
                  * Geometrically detected spatial proximity. Not chemically validated bonding.
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ======================= PHASE 3: CHEMINFORMATICS VIEW ======================= */}
      {engineMode === 'cheminformatics' && properties && (
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px' }}>
          {/* 2D Structure Card */}
          <div style={{ backgroundColor: '#161b22', padding: '16px', borderRadius: '8px', border: '1px solid #30363d', textAlign: 'center' }}>
            <h3 style={{ color: '#00ffff', margin: '0 0 12px', fontSize: '16px' }}>2D Chemical Depiction</h3>
            {svgUrl ? (
              <div style={{ backgroundColor: '#ffffff', padding: '10px', borderRadius: '6px', display: 'flex', justifyContent: 'center' }}>
                <img src={svgUrl} alt="Molecule Depiction" style={{ maxWidth: '100%', height: 'auto' }} />
              </div>
            ) : (
              <p style={{ color: '#666' }}>Structure preview</p>
            )}

            <div style={{ marginTop: '14px', textAlign: 'left', fontSize: '13px', color: '#aaa' }}>
              <div><strong>SMILES:</strong> <code style={{ color: '#79c0ff' }}>{properties.smiles}</code></div>
              <div style={{ marginTop: '4px' }}><strong>Hill Formula:</strong> <span style={{ color: '#fff' }}>{properties.formula}</span></div>
              <div style={{ marginTop: '4px' }}><strong>Exact MW:</strong> <span style={{ color: '#fff' }}>{properties.molecular_weight} g/mol</span></div>
            </div>
          </div>

          {/* Properties & Conformer Detail */}
          <div style={{ backgroundColor: '#161b22', padding: '16px', borderRadius: '8px', border: '1px solid #30363d' }}>
            <div style={{ display: 'flex', borderBottom: '1px solid #30363d', marginBottom: '16px', gap: '10px' }}>
              <button
                onClick={() => setActiveChemTab('properties')}
                style={{
                  padding: '8px 16px',
                  background: 'none',
                  border: 'none',
                  borderBottom: activeChemTab === 'properties' ? '2px solid #00ffff' : '2px solid transparent',
                  color: activeChemTab === 'properties' ? '#00ffff' : '#888',
                  cursor: 'pointer',
                  fontWeight: activeChemTab === 'properties' ? 'bold' : 'normal',
                }}
              >
                Physicochemical & Lipinski
              </button>
              <button
                onClick={() => setActiveChemTab('3d')}
                style={{
                  padding: '8px 16px',
                  background: 'none',
                  border: 'none',
                  borderBottom: activeChemTab === '3d' ? '2px solid #00ffff' : '2px solid transparent',
                  color: activeChemTab === '3d' ? '#00ffff' : '#888',
                  cursor: 'pointer',
                  fontWeight: activeChemTab === '3d' ? 'bold' : 'normal',
                }}
              >
                3D Conformer Coordinates
              </button>
              <button
                onClick={() => setActiveChemTab('molblock')}
                style={{
                  padding: '8px 16px',
                  background: 'none',
                  border: 'none',
                  borderBottom: activeChemTab === 'molblock' ? '2px solid #00ffff' : '2px solid transparent',
                  color: activeChemTab === 'molblock' ? '#00ffff' : '#888',
                  cursor: 'pointer',
                  fontWeight: activeChemTab === 'molblock' ? 'bold' : 'normal',
                }}
              >
                MolBlock (SDF)
              </button>
            </div>

            {activeChemTab === 'properties' && (
              <div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '20px' }}>
                  <div style={{ backgroundColor: '#0d1117', padding: '12px', borderRadius: '6px' }}>
                    <div style={{ fontSize: '12px', color: '#888' }}>Molecular Weight</div>
                    <div style={{ fontSize: '20px', color: '#00ffff', fontWeight: 'bold' }}>{properties.molecular_weight} <span style={{ fontSize: '13px', color: '#aaa' }}>g/mol</span></div>
                  </div>
                  <div style={{ backgroundColor: '#0d1117', padding: '12px', borderRadius: '6px' }}>
                    <div style={{ fontSize: '12px', color: '#888' }}>Calculated LogP</div>
                    <div style={{ fontSize: '20px', color: properties.logp <= 5 ? '#00ff88' : '#ffaa00', fontWeight: 'bold' }}>{properties.logp}</div>
                  </div>
                  <div style={{ backgroundColor: '#0d1117', padding: '12px', borderRadius: '6px' }}>
                    <div style={{ fontSize: '12px', color: '#888' }}>TPSA</div>
                    <div style={{ fontSize: '20px', color: '#fff', fontWeight: 'bold' }}>{properties.tpsa} <span style={{ fontSize: '13px', color: '#aaa' }}>Å²</span></div>
                  </div>
                  <div style={{ backgroundColor: '#0d1117', padding: '12px', borderRadius: '6px' }}>
                    <div style={{ fontSize: '12px', color: '#888' }}>H-Bond Donors (HBD)</div>
                    <div style={{ fontSize: '18px', color: '#fff' }}>{properties.hbd}</div>
                  </div>
                  <div style={{ backgroundColor: '#0d1117', padding: '12px', borderRadius: '6px' }}>
                    <div style={{ fontSize: '12px', color: '#888' }}>H-Bond Acceptors (HBA)</div>
                    <div style={{ fontSize: '18px', color: '#fff' }}>{properties.hba}</div>
                  </div>
                  <div style={{ backgroundColor: '#0d1117', padding: '12px', borderRadius: '6px' }}>
                    <div style={{ fontSize: '12px', color: '#888' }}>Rotatable Bonds</div>
                    <div style={{ fontSize: '18px', color: '#fff' }}>{properties.rotatable_bonds}</div>
                  </div>
                </div>

                <div style={{ backgroundColor: '#0d1117', padding: '14px', borderRadius: '6px', borderLeft: properties.lipinski_pass ? '4px solid #00ff88' : '4px solid #ff4444' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h4 style={{ margin: 0, color: '#fff' }}>Lipinski Rule of 5 (Drug-likeness)</h4>
                    <span
                      style={{
                        padding: '4px 10px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        backgroundColor: properties.lipinski_pass ? '#00ff8822' : '#ff444422',
                        color: properties.lipinski_pass ? '#00ff88' : '#ff4444',
                      }}
                    >
                      {properties.lipinski_pass ? 'PASSED (Drug-like)' : 'FAILED (>1 Violation)'}
                    </span>
                  </div>
                  <p style={{ margin: '8px 0 0', fontSize: '13px', color: '#aaa' }}>
                    Violations: <strong>{properties.lipinski_violations}</strong> / 4. Criteria: MW ≤ 500 ({properties.molecular_weight}), LogP ≤ 5 ({properties.logp}), HBD ≤ 5 ({properties.hbd}), HBA ≤ 10 ({properties.hba}).
                  </p>
                </div>
              </div>
            )}

            {activeChemTab === '3d' && conformer && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px', fontSize: '13px' }}>
                  <span>Total Atoms with Explicit H: <strong>{conformer.atom_count}</strong></span>
                  {conformer.energy_kcal_mol !== undefined && (
                    <span style={{ color: '#00ffff' }}>Force Field Energy: <strong>{conformer.energy_kcal_mol} kcal/mol</strong></span>
                  )}
                </div>
                <div style={{ maxHeight: '280px', overflowY: 'auto', border: '1px solid #30363d', borderRadius: '4px' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', fontFamily: 'monospace' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#21262d', textAlign: 'left' }}>
                        <th style={{ padding: '6px 10px' }}>#</th>
                        <th style={{ padding: '6px 10px' }}>Element</th>
                        <th style={{ padding: '6px 10px' }}>X (Å)</th>
                        <th style={{ padding: '6px 10px' }}>Y (Å)</th>
                        <th style={{ padding: '6px 10px' }}>Z (Å)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {conformer.atoms.map((a) => (
                        <tr key={a.index} style={{ borderBottom: '1px solid #21262d' }}>
                          <td style={{ padding: '5px 10px', color: '#888' }}>{a.index}</td>
                          <td style={{ padding: '5px 10px', color: '#00ffff', fontWeight: 'bold' }}>{a.symbol}</td>
                          <td style={{ padding: '5px 10px' }}>{a.x.toFixed(4)}</td>
                          <td style={{ padding: '5px 10px' }}>{a.y.toFixed(4)}</td>
                          <td style={{ padding: '5px 10px' }}>{a.z.toFixed(4)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeChemTab === 'molblock' && conformer && (
              <pre
                style={{
                  backgroundColor: '#0d1117',
                  padding: '12px',
                  borderRadius: '6px',
                  fontSize: '11px',
                  fontFamily: 'monospace',
                  maxHeight: '300px',
                  overflowY: 'auto',
                  color: '#c9d1d9',
                  margin: 0,
                }}
              >
                {conformer.mol_block}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MolecularLab;
