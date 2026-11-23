import React, { useState, useEffect, useRef } from 'react';
import MolecularViewer3D from '@/components/MolecularViewer3D';

const API_BASE = 'http://127.0.0.1:8000';

interface LibrarySummary {
  id: string;
  name: string;
  category: string;
  description: string;
  compound_count: number;
  sample_compounds: string[];
}

interface PreFilterResult {
  name: string;
  smiles: string;
  class: string;
  passed: boolean;
  violations: string[];
  mw: number;
  logp: number;
  hbd: number;
  hba: number;
  rotatable_bonds: number;
  tpsa: number;
  pains_alerts: string[];
}

interface PreFilterResponse {
  total_compounds: number;
  passed_count: number;
  pass_rate_pct: number;
  results: PreFilterResult[];
}

interface ScreenedHit {
  rank: number;
  name: string;
  smiles: string;
  class: string;
  prefilter_passed: boolean;
  violations: string[];
  docking_status: string;
  binding_affinity: number;
  heavy_atoms: number;
  ligand_efficiency: number;
  pki_estimate: number;
  clogp: number;
  lipophilic_efficiency: number;
  composite_score: number;
  docked_pdb?: string;
  docked_pdbqt?: string;
  error?: string;
}

interface JobProgress {
  total?: number;
  current?: number;
  total_compounds?: number;
  processed_compounds?: number;
  current_compound?: string;
  pct: number;
}

interface JobStatusResponse {
  job_id: string;
  target: string;
  status: string;
  progress: JobProgress;
  total_hits?: number;
  docked_count?: number;
  filtered_count?: number;
  failed_count?: number;
  error?: string;
}

const TARGET_PRESETS = [
  { id: '6LU7', name: 'SARS-CoV-2 Main Protease (Mpro)', indication: 'COVID-19 / Antiviral', res: '2.16 Å' },
  { id: '1ERE', name: 'Estrogen Receptor Alpha (ERα)', indication: 'Breast Cancer / Oncology', res: '3.10 Å' },
  { id: '1IEP', name: 'Abl Tyrosine Kinase', indication: 'Chronic Myeloid Leukemia', res: '2.10 Å' },
  { id: '1M17', name: 'EGFR Kinase Domain', indication: 'Non-Small Cell Lung Cancer', res: '2.60 Å' },
  { id: '1CX2', name: 'Cyclooxygenase-2 (COX-2)', indication: 'Inflammation & Pain', res: '3.00 Å' },
];

const ScreeningConsole: React.FC = () => {
  // Config state
  const [target, setTarget] = useState('6LU7');
  const [libraries, setLibraries] = useState<LibrarySummary[]>([]);
  const [selectedLibraryId, setSelectedLibraryId] = useState('fda_diversity');
  const [libraryMode, setLibraryMode] = useState<'curated' | 'custom'>('curated');
  const [customSmilesText, setCustomSmilesText] = useState(
    'CC(=O)Oc1ccccc1C(=O)O Aspirin\nCC(C)Cc1ccc(cc1)C(C)C(=O)O Ibuprofen\nCC(=O)Nc1ccc(O)cc1 Acetaminophen\nO=C(O)c1cn(C2CC2)c3cc(N4CCNCC4)c(F)cc3c1=O Ciprofloxacin'
  );

  // Filters state
  const [applyLipinski, setApplyLipinski] = useState(true);
  const [applyVeber, setApplyVeber] = useState(true);
  const [applyPains, setApplyPains] = useState(true);
  const [strictFilter, setStrictFilter] = useState(true);
  const [minMw, setMinMw] = useState(100);
  const [maxMw, setMaxMw] = useState(650);
  const [exhaustiveness, setExhaustiveness] = useState(4);

  // Pre-filter state
  const [prefilterLoading, setPrefilterLoading] = useState(false);
  const [prefilterData, setPrefilterData] = useState<PreFilterResponse | null>(null);

  // Virtual Screening Execution state
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [isScreening, setIsScreening] = useState(false);
  const [results, setResults] = useState<ScreenedHit[]>([]);
  const [sortBy, setSortBy] = useState<'affinity' | 'ligand_efficiency' | 'composite_score'>('affinity');
  const [savedCandidates, setSavedCandidates] = useState<Record<string, boolean>>({});
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // 3D Pose Inspection Modal
  const [viewingHit, setViewingHit] = useState<ScreenedHit | null>(null);
  const [proteinPdbData, setProteinPdbData] = useState<string>('');
  const [modalLoading, setModalLoading] = useState(false);

  // PyMOL High-Res Render Modal
  const [pymolHit, setPymolHit] = useState<ScreenedHit | null>(null);
  const [pymolImageUrl, setPymolImageUrl] = useState<string | null>(null);
  const [pymolRendering, setPymolRendering] = useState(false);

  const pollIntervalRef = useRef<any>(null);

  // Fetch libraries on mount
  useEffect(() => {
    fetch(`${API_BASE}/screening/libraries`)
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setLibraries(data);
          if (data.length > 0) setSelectedLibraryId(data[0].id);
        }
      })
      .catch((err) => console.error('Failed to load libraries:', err));
  }, []);

  // Polling for screening progress
  useEffect(() => {
    if (!activeJobId || !isScreening) return;

    pollIntervalRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/screening/status/${activeJobId}`);
        if (!res.ok) throw new Error('Status poll failed');
        const data: JobStatusResponse = await res.json();
        setJobStatus(data);

        const normalizedStatus = (data.status || '').toLowerCase();
        if (normalizedStatus === 'completed') {
          setIsScreening(false);
          clearInterval(pollIntervalRef.current);
          fetchResults(activeJobId, sortBy);
        } else if (normalizedStatus === 'failed') {
          setIsScreening(false);
          clearInterval(pollIntervalRef.current);
          setErrorMsg(data.error || 'Virtual screening execution failed.');
        }
      } catch (err: any) {
        console.error('Polling error:', err);
      }
    }, 1500);

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [activeJobId, isScreening, sortBy]);

  const fetchResults = async (jobId: string, sort: string) => {
    try {
      const res = await fetch(`${API_BASE}/screening/results/${jobId}?sort_by=${sort}`);
      if (!res.ok) throw new Error('Failed to fetch results');
      const data = await res.json();
      setResults(data.ranked_hits || []);
    } catch (err: any) {
      setErrorMsg(err.message);
    }
  };

  const handleSortChange = (newSort: 'affinity' | 'ligand_efficiency' | 'composite_score') => {
    setSortBy(newSort);
    if (activeJobId && !isScreening) {
      fetchResults(activeJobId, newSort);
    }
  };

  // Run Pre-Filter
  const handleRunPrefilter = async () => {
    setPrefilterLoading(true);
    setErrorMsg(null);
    try {
      const payload: any = {
        apply_lipinski: applyLipinski,
        apply_veber: applyVeber,
        apply_pains: applyPains,
        min_mw: Number(minMw),
        max_mw: Number(maxMw),
      };
      if (libraryMode === 'curated') {
        payload.library_id = selectedLibraryId;
      } else {
        payload.custom_smiles = customSmilesText;
      }

      const res = await fetch(`${API_BASE}/screening/prefilter`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Prefilter request failed');
      }

      const data: PreFilterResponse = await res.json();
      setPrefilterData(data);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setPrefilterLoading(false);
    }
  };

  // Start Virtual Screening
  const handleStartScreening = async () => {
    setIsScreening(true);
    setErrorMsg(null);
    setResults([]);
    setJobStatus(null);

    try {
      const payload: any = {
        target,
        exhaustiveness: Number(exhaustiveness),
        apply_lipinski: applyLipinski,
        apply_veber: applyVeber,
        apply_pains: applyPains,
        strict_filter: strictFilter,
      };

      if (libraryMode === 'curated') {
        payload.library_id = selectedLibraryId;
      } else {
        payload.custom_compounds = customSmilesText;
      }

      const res = await fetch(`${API_BASE}/screening/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to start screening job');
      }

      const data = await res.json();
      setActiveJobId(data.job_id);
    } catch (err: any) {
      setIsScreening(false);
      setErrorMsg(err.message);
    }
  };

  // Save Candidate to SQLite
  const handleSaveCandidate = async (hit: ScreenedHit) => {
    try {
      const payload = {
        project_id: 1,
        name: hit.name,
        smiles: hit.smiles,
        binding_affinity: hit.binding_affinity,
        ligand_efficiency: hit.ligand_efficiency,
        target: target,
      };

      const res = await fetch(`${API_BASE}/screening/save_candidate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error('Save candidate failed');
      setSavedCandidates((prev) => ({ ...prev, [hit.name]: true }));
    } catch (err: any) {
      alert(`Could not save candidate: ${err.message}`);
    }
  };

  // Open 3D Pose Modal
  const handleInspectPose = async (hit: ScreenedHit) => {
    setViewingHit(hit);
    setModalLoading(true);
    try {
      // Fetch clean target protein PDB for 3Dmol viewer overlay
      const res = await fetch(`${API_BASE}/docking/targets`);
      if (res.ok) {
        // Fallback or read PDB via standard route
        const targetRes = await fetch(`${API_BASE}/viz/targets`);
        const targets = await targetRes.json();
        const found = targets.find((t: any) => t.pdb_id === target);
        if (found) {
          // If available from server
        }
      }
    } catch (e) {
      console.warn(e);
    } finally {
      setModalLoading(false);
    }
  };

  // Render PyMOL Publication Quality View
  const handleRenderPyMOL = async (hit: ScreenedHit) => {
    setPymolHit(hit);
    setPymolRendering(true);
    setPymolImageUrl(null);

    try {
      const res = await fetch(`${API_BASE}/viz/render`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target: target,
          smiles: hit.smiles,
          style: 'cartoon',
          color_by: 'chain',
          pocket_residues_highlight: true,
          distance_cutoff: 4.5,
          ray_trace: true,
          width: 1280,
          height: 960,
        }),
      });

      if (!res.ok) throw new Error('PyMOL render failed');
      const data = await res.json();
      setPymolImageUrl(`${API_BASE}${data.image_url}`);
    } catch (err: any) {
      alert(`PyMOL Rendering Error: ${err.message}`);
    } finally {
      setPymolRendering(false);
    }
  };

  const getAffinityBadgeColor = (aff: number) => {
    if (aff <= -8.0) return 'bg-purple-900/40 text-purple-300 border-purple-500/50 shadow-purple-500/20';
    if (aff <= -7.0) return 'bg-emerald-900/40 text-emerald-300 border-emerald-500/50 shadow-emerald-500/20';
    if (aff <= -6.0) return 'bg-cyan-900/40 text-cyan-300 border-cyan-500/50 shadow-cyan-500/20';
    return 'bg-amber-900/40 text-amber-300 border-amber-500/50 shadow-amber-500/20';
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Title & Engine Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-900/80 border border-cyan-500/30 backdrop-blur shadow-xl shadow-cyan-950/20">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-cyan-400 animate-ping" />
            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-400 bg-clip-text text-transparent">
              High-Throughput Virtual Screening Console
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              Phase 5
            </span>
          </div>
          <p className="text-slate-400 text-sm mt-1">
            Multithreaded AutoDock Vina Docking Engine • RDKit Cheminformatics Filters • Multi-Parametric Hit Ranking (ΔG, LE, LLE)
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="px-3 py-1.5 rounded-lg bg-slate-800/90 border border-slate-700/60 text-xs text-slate-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Vina 1.2.5 Multithreaded</span>
          </div>
          <div className="px-3 py-1.5 rounded-lg bg-slate-800/90 border border-slate-700/60 text-xs text-slate-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span>Meeko 0.5.1 Ligand Prep</span>
          </div>
          <div className="px-3 py-1.5 rounded-lg bg-slate-800/90 border border-slate-700/60 text-xs text-slate-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-purple-400" />
            <span>PyMOL 3.1.0 Ray Tracer</span>
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/50 text-red-200 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">⚠️</span>
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg(null)} className="text-red-400 hover:text-red-200 font-bold">
            ✕
          </button>
        </div>
      )}

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Target & Library Selection */}
        <div className="lg:col-span-2 space-y-6">
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur shadow-lg space-y-5">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <span className="text-cyan-400">1.</span> Select Biological Target & Compound Library
            </h2>

            {/* Target Selection */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Biological Target Receptor (PDB)
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                {TARGET_PRESETS.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setTarget(t.id)}
                    className={`text-left p-3 rounded-xl border transition-all ${
                      target === t.id
                        ? 'bg-cyan-950/40 border-cyan-400/80 shadow-md shadow-cyan-900/20 text-white'
                        : 'bg-slate-800/40 border-slate-700/60 hover:bg-slate-800/80 text-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm tracking-wide text-cyan-300">{t.id}</span>
                      <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                        {t.res}
                      </span>
                    </div>
                    <div className="text-xs font-medium text-slate-200 mt-1 truncate">{t.name}</div>
                    <div className="text-[11px] text-slate-400 truncate">{t.indication}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Library Mode Selector */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Screening Compound Library
                </label>
                <div className="flex rounded-lg bg-slate-800 p-0.5 border border-slate-700/60 text-xs">
                  <button
                    onClick={() => setLibraryMode('curated')}
                    className={`px-3 py-1 rounded-md transition-all ${
                      libraryMode === 'curated' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Curated Libraries
                  </button>
                  <button
                    onClick={() => setLibraryMode('custom')}
                    className={`px-3 py-1 rounded-md transition-all ${
                      libraryMode === 'custom' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Custom SMILES
                  </button>
                </div>
              </div>

              {libraryMode === 'curated' ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {libraries.map((lib) => (
                    <div
                      key={lib.id}
                      onClick={() => setSelectedLibraryId(lib.id)}
                      className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                        selectedLibraryId === lib.id
                          ? 'bg-teal-950/40 border-teal-400/80 shadow-md shadow-teal-900/20 text-white'
                          : 'bg-slate-800/40 border-slate-700/60 hover:bg-slate-800/80 text-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-sm text-teal-300">{lib.name}</span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-teal-500/20 text-teal-300 font-mono">
                          {lib.compound_count} cmpds
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 line-clamp-2 mb-2">{lib.description}</p>
                      <div className="text-[11px] text-slate-500 flex items-center gap-1">
                        <span>Includes:</span>
                        <span className="text-slate-400 italic truncate">{lib.sample_compounds.join(', ')}...</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-2">
                  <textarea
                    rows={4}
                    value={customSmilesText}
                    onChange={(e) => setCustomSmilesText(e.target.value)}
                    placeholder="Enter SMILES [space] Compound Name (one per line)..."
                    className="w-full rounded-xl bg-slate-950 border border-slate-700 p-3 font-mono text-xs text-cyan-300 focus:outline-none focus:border-cyan-400"
                  />
                  <p className="text-[11px] text-slate-400">
                    Format: <code className="text-cyan-400">SMILES [optional name]</code> on each line. Example:{' '}
                    <code className="text-slate-300">CC(=O)Oc1ccccc1C(=O)O Aspirin</code>
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Physicochemical & Pre-Filtering Settings */}
        <div className="space-y-6">
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur shadow-lg space-y-4">
            <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
              <span className="text-cyan-400">2.</span> Cheminformatics Filters
            </h2>

            <div className="space-y-3">
              <label className="flex items-center justify-between p-2.5 rounded-xl bg-slate-800/40 border border-slate-700/50 cursor-pointer hover:bg-slate-800/70">
                <div className="text-xs">
                  <div className="font-semibold text-slate-200">Lipinski Rule of 5</div>
                  <div className="text-[11px] text-slate-400">MW ≤ 500, LogP ≤ 5, HBD ≤ 5, HBA ≤ 10</div>
                </div>
                <input
                  type="checkbox"
                  checked={applyLipinski}
                  onChange={(e) => setApplyLipinski(e.target.checked)}
                  className="w-4 h-4 rounded text-cyan-500 bg-slate-900 border-slate-700 focus:ring-0"
                />
              </label>

              <label className="flex items-center justify-between p-2.5 rounded-xl bg-slate-800/40 border border-slate-700/50 cursor-pointer hover:bg-slate-800/70">
                <div className="text-xs">
                  <div className="font-semibold text-slate-200">Veber Bioavailability</div>
                  <div className="text-[11px] text-slate-400">Rotatable Bonds ≤ 10, TPSA ≤ 140 Å²</div>
                </div>
                <input
                  type="checkbox"
                  checked={applyVeber}
                  onChange={(e) => setApplyVeber(e.target.checked)}
                  className="w-4 h-4 rounded text-cyan-500 bg-slate-900 border-slate-700 focus:ring-0"
                />
              </label>

              <label className="flex items-center justify-between p-2.5 rounded-xl bg-slate-800/40 border border-slate-700/50 cursor-pointer hover:bg-slate-800/70">
                <div className="text-xs">
                  <div className="font-semibold text-slate-200">PAINS Structural Filter</div>
                  <div className="text-[11px] text-slate-400">Filter Pan-Assay Interference Motifs</div>
                </div>
                <input
                  type="checkbox"
                  checked={applyPains}
                  onChange={(e) => setApplyPains(e.target.checked)}
                  className="w-4 h-4 rounded text-cyan-500 bg-slate-900 border-slate-700 focus:ring-0"
                />
              </label>

              <label className="flex items-center justify-between p-2.5 rounded-xl bg-slate-800/40 border border-cyan-500/30 cursor-pointer hover:bg-slate-800/70">
                <div className="text-xs">
                  <div className="font-semibold text-cyan-300">Strict Docking Gate</div>
                  <div className="text-[11px] text-slate-400">Skip docking for compounds failing filters</div>
                </div>
                <input
                  type="checkbox"
                  checked={strictFilter}
                  onChange={(e) => setStrictFilter(e.target.checked)}
                  className="w-4 h-4 rounded text-cyan-500 bg-slate-900 border-slate-700 focus:ring-0"
                />
              </label>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <div>
                <label className="text-[11px] font-semibold text-slate-400 block mb-1">Min MW (Da)</label>
                <input
                  type="number"
                  value={minMw}
                  onChange={(e) => setMinMw(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs text-white"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-slate-400 block mb-1">Max MW (Da)</label>
                <input
                  type="number"
                  value={maxMw}
                  onChange={(e) => setMaxMw(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs text-white"
                />
              </div>
            </div>

            <div className="pt-2">
              <label className="text-[11px] font-semibold text-slate-400 block mb-1">
                Vina Exhaustiveness ({exhaustiveness})
              </label>
              <select
                value={exhaustiveness}
                onChange={(e) => setExhaustiveness(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs text-white"
              >
                <option value={2}>2 - Rapid Screen (Ultra Fast)</option>
                <option value={4}>4 - High-Throughput Screen (Recommended)</option>
                <option value={8}>8 - Standard Exhaustive Search</option>
                <option value={12}>12 - High-Precision Lead Docking</option>
              </select>
            </div>

            {/* Action Buttons */}
            <div className="pt-3 space-y-2">
              <button
                onClick={handleRunPrefilter}
                disabled={prefilterLoading || isScreening}
                className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-600 font-semibold text-xs text-slate-200 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {prefilterLoading ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
                    <span>Evaluating Descriptors...</span>
                  </>
                ) : (
                  <>
                    <span>⚡ Rapid Pre-Filter Library</span>
                  </>
                )}
              </button>

              <button
                onClick={handleStartScreening}
                disabled={isScreening}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 via-teal-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 font-bold text-xs uppercase tracking-wider text-slate-950 shadow-lg shadow-cyan-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isScreening ? (
                  <>
                    <span className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                    <span>Screening In Progress...</span>
                  </>
                ) : (
                  <>
                    <span>🚀 Launch Virtual Screening</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Pre-Filter Results Card */}
      {prefilterData && (
        <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <span>Cheminformatics Pre-Filter Report</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-cyan-300 font-mono">
                {prefilterData.passed_count} / {prefilterData.total_compounds} Passed ({prefilterData.pass_rate_pct}%)
              </span>
            </h3>
            <button onClick={() => setPrefilterData(null)} className="text-xs text-slate-500 hover:text-slate-300">
              Dismiss
            </button>
          </div>

          {/* Pass Rate Progress Bar */}
          <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-400 to-emerald-400 transition-all duration-500"
              style={{ width: `${prefilterData.pass_rate_pct}%` }}
            />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {prefilterData.results.slice(0, 8).map((r, idx) => (
              <div
                key={idx}
                className={`p-2.5 rounded-xl border text-xs ${
                  r.passed
                    ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-200'
                    : 'bg-red-950/20 border-red-500/40 text-red-200'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold truncate">{r.name}</span>
                  <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-900/80">
                    {r.passed ? '✓ Pass' : '✗ Fail'}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 flex justify-between">
                  <span>MW: {r.mw?.toFixed(1)}</span>
                  <span>LogP: {r.logp?.toFixed(2)}</span>
                </div>
                {!r.passed && r.violations && r.violations.length > 0 && (
                  <div className="text-[10px] text-red-400 mt-1 truncate">
                    Violations: {r.violations.join(', ')}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Real-time Job Progress Monitor */}
      {jobStatus && (
        <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900/90 to-slate-950/90 border border-cyan-500/40 shadow-xl shadow-cyan-950/30 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {(jobStatus.status.toLowerCase() === 'running' || jobStatus.status.toLowerCase() === 'pending') && (
                <span className="w-3 h-3 rounded-full bg-cyan-400 animate-ping" />
              )}
              {jobStatus.status.toLowerCase() === 'completed' && (
                <span className="w-3 h-3 rounded-full bg-emerald-400" />
              )}
              {jobStatus.status.toLowerCase() === 'failed' && (
                <span className="w-3 h-3 rounded-full bg-red-400" />
              )}
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span>Virtual Screening Job:</span>
                  <span className="text-cyan-400 font-mono">{jobStatus.job_id}</span>
                </h3>
                <p className="text-xs text-slate-400">
                  Target: <span className="text-slate-200 font-semibold">{jobStatus.target}</span> • Status:{' '}
                  <span
                    className={`font-bold uppercase ${
                      jobStatus.status.toLowerCase() === 'completed'
                        ? 'text-emerald-400'
                        : jobStatus.status.toLowerCase() === 'failed'
                        ? 'text-red-400'
                        : 'text-cyan-400'
                    }`}
                  >
                    {jobStatus.status}
                  </span>
                </p>
              </div>
            </div>

            <div className="text-right">
              <span className="text-2xl font-black text-cyan-300 font-mono">
                {jobStatus.progress?.pct?.toFixed(0)}%
              </span>
              <div className="text-xs text-slate-400">
                {jobStatus.progress?.current ?? jobStatus.progress?.processed_compounds ?? 0} of{' '}
                {jobStatus.progress?.total ?? jobStatus.progress?.total_compounds ?? 0} screened
              </div>
            </div>
          </div>

          {/* Animated Progress Bar */}
          <div className="w-full h-3 rounded-full bg-slate-800/80 overflow-hidden p-0.5 border border-slate-700/60">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                jobStatus.status === 'COMPLETED'
                  ? 'bg-gradient-to-r from-emerald-500 to-teal-400'
                  : 'bg-gradient-to-r from-cyan-500 via-teal-400 to-emerald-400 animate-pulse'
              }`}
              style={{ width: `${jobStatus.progress?.pct || 0}%` }}
            />
          </div>

          {jobStatus.status === 'RUNNING' && jobStatus.progress?.current_compound && (
            <div className="text-xs text-slate-400 flex items-center justify-between">
              <span>
                Currently Docking:{' '}
                <span className="text-cyan-300 font-semibold">{jobStatus.progress.current_compound}</span>
              </span>
              <span className="font-mono text-slate-500">AutoDock Vina Engine Active</span>
            </div>
          )}
        </div>
      )}

      {/* Virtual Screening Results & Hit Table */}
      {results.length > 0 && (
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-5">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-black text-white flex items-center gap-2">
                <span>Ranked Hit Candidates</span>
                <span className="text-xs font-normal px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800">
                  {results.length} Compounds
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Multi-parametric ranking considering ΔG binding affinity, ligand efficiency, and lipophilicity.
              </p>
            </div>

            {/* Sort & Export Controls */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-1 bg-slate-800 p-1 rounded-xl border border-slate-700 text-xs">
                <span className="text-slate-400 px-2">Sort:</span>
                <button
                  onClick={() => handleSortChange('affinity')}
                  className={`px-2.5 py-1 rounded-lg transition-all ${
                    sortBy === 'affinity' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-slate-300'
                  }`}
                >
                  ΔG (Affinity)
                </button>
                <button
                  onClick={() => handleSortChange('ligand_efficiency')}
                  className={`px-2.5 py-1 rounded-lg transition-all ${
                    sortBy === 'ligand_efficiency' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-slate-300'
                  }`}
                >
                  Ligand Eff (LE)
                </button>
                <button
                  onClick={() => handleSortChange('composite_score')}
                  className={`px-2.5 py-1 rounded-lg transition-all ${
                    sortBy === 'composite_score' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-slate-300'
                  }`}
                >
                  Composite Rank
                </button>
              </div>

              {activeJobId && (
                <div className="flex items-center gap-2">
                  <a
                    href={`${API_BASE}/screening/export/${activeJobId}?format=csv`}
                    download
                    className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs text-slate-200 font-semibold transition-all flex items-center gap-1.5"
                  >
                    <span>📥 Export CSV</span>
                  </a>
                  <a
                    href={`${API_BASE}/screening/export/${activeJobId}?format=json`}
                    download
                    className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs text-slate-200 font-semibold transition-all flex items-center gap-1.5"
                  >
                    <span>📥 JSON</span>
                  </a>
                </div>
              )}
            </div>
          </div>

          {/* Interactive Hit Table */}
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/70 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-3">Rank</th>
                  <th className="py-3 px-3">Compound Name</th>
                  <th className="py-3 px-3">Class</th>
                  <th className="py-3 px-3 text-right">Affinity (ΔG)</th>
                  <th className="py-3 px-3 text-right">Ligand Eff (LE)</th>
                  <th className="py-3 px-3 text-right">LLE</th>
                  <th className="py-3 px-3 text-center">Lipinski</th>
                  <th className="py-3 px-3 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {results.map((hit) => (
                  <tr key={hit.rank} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-3 font-mono font-bold text-cyan-400">#{hit.rank}</td>
                    <td className="py-3 px-3">
                      <div className="font-bold text-slate-100">{hit.name}</div>
                      <div className="text-[10px] text-slate-500 font-mono truncate max-w-xs">{hit.smiles}</div>
                    </td>
                    <td className="py-3 px-3 text-slate-400">{hit.class || 'Unclassified'}</td>
                    <td className="py-3 px-3 text-right">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full border text-xs font-mono font-bold ${getAffinityBadgeColor(
                          hit.binding_affinity
                        )}`}
                      >
                        {hit.binding_affinity.toFixed(2)} kcal/mol
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-slate-200">
                      {hit.ligand_efficiency > 0 ? hit.ligand_efficiency.toFixed(3) : '—'}
                    </td>
                    <td className="py-3 px-3 text-right font-mono text-slate-200">
                      {hit.lipophilic_efficiency !== 0 ? hit.lipophilic_efficiency.toFixed(2) : '—'}
                    </td>
                    <td className="py-3 px-3 text-center">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          hit.prefilter_passed
                            ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/60'
                            : 'bg-red-950/60 text-red-400 border border-red-800/60'
                        }`}
                      >
                        {hit.prefilter_passed ? '✓ Compliant' : '✗ Flagged'}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex items-center justify-center gap-1.5">
                        {hit.docked_pdb && (
                          <button
                            onClick={() => handleInspectPose(hit)}
                            title="View 3D Docked Conformation"
                            className="px-2 py-1 rounded-lg bg-cyan-950/60 hover:bg-cyan-900 border border-cyan-800 text-[11px] text-cyan-300 transition-all"
                          >
                            👁 3D Pose
                          </button>
                        )}
                        <button
                          onClick={() => handleRenderPyMOL(hit)}
                          title="Generate Ray-Traced PyMOL Rendering"
                          className="px-2 py-1 rounded-lg bg-purple-950/60 hover:bg-purple-900 border border-purple-800 text-[11px] text-purple-300 transition-all"
                        >
                          🧪 PyMOL
                        </button>
                        <button
                          onClick={() => handleSaveCandidate(hit)}
                          disabled={savedCandidates[hit.name]}
                          title="Save to Candidates Database"
                          className={`px-2 py-1 rounded-lg text-[11px] transition-all border ${
                            savedCandidates[hit.name]
                              ? 'bg-emerald-900/40 border-emerald-700 text-emerald-300'
                              : 'bg-slate-800 hover:bg-slate-700 border-slate-600 text-slate-200'
                          }`}
                        >
                          {savedCandidates[hit.name] ? '✓ Saved' : '💾 Save'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 3D Pose Inspection Modal */}
      {viewingHit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-4xl bg-slate-900 border border-cyan-500/40 rounded-2xl overflow-hidden shadow-2xl space-y-4 p-5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>3D Docked Complex:</span>
                  <span className="text-cyan-400">{viewingHit.name}</span>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                    {target}
                  </span>
                </h3>
                <p className="text-xs text-slate-400">
                  Affinity: <span className="text-cyan-300 font-bold">{viewingHit.binding_affinity} kcal/mol</span> • LE:{' '}
                  <span className="text-emerald-300 font-bold">{viewingHit.ligand_efficiency} kcal/mol/atom</span>
                </p>
              </div>
              <button
                onClick={() => setViewingHit(null)}
                className="w-8 h-8 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center font-bold"
              >
                ✕
              </button>
            </div>

            <div className="h-[460px] rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
              <MolecularViewer3D
                proteinPdb={proteinPdbData}
                ligandPdb={viewingHit.docked_pdb}
                styleMode="cartoon"
                height="460px"
              />
            </div>

            <div className="flex items-center justify-between text-xs text-slate-400">
              <div className="font-mono truncate max-w-md">SMILES: {viewingHit.smiles}</div>
              <button
                onClick={() => setViewingHit(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold"
              >
                Close Viewer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PyMOL Publication Render Modal */}
      {pymolHit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-3xl bg-slate-900 border border-purple-500/40 rounded-2xl overflow-hidden shadow-2xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <span className="text-purple-400">PyMOL 3.1.0 High-Res Render:</span>
                  <span>{pymolHit.name}</span>
                </h3>
                <p className="text-xs text-slate-400">
                  Receptor: {target} • Ray-Traced Publication Quality View (1280x960)
                </p>
              </div>
              <button
                onClick={() => setPymolHit(null)}
                className="w-8 h-8 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center font-bold"
              >
                ✕
              </button>
            </div>

            <div className="min-h-[380px] rounded-xl border border-slate-800 bg-slate-950 flex items-center justify-center overflow-hidden">
              {pymolRendering ? (
                <div className="text-center space-y-3">
                  <span className="w-8 h-8 border-3 border-purple-400 border-t-transparent rounded-full animate-spin inline-block" />
                  <p className="text-xs text-purple-300 font-mono">Running Schrödinger PyMOL Subprocess Ray-Trace...</p>
                </div>
              ) : pymolImageUrl ? (
                <img
                  src={pymolImageUrl}
                  alt="PyMOL High Res Render"
                  className="max-h-[500px] w-auto object-contain rounded-lg"
                />
              ) : (
                <div className="text-xs text-slate-500">No image available</div>
              )}
            </div>

            <div className="flex items-center justify-between">
              {pymolImageUrl ? (
                <a
                  href={pymolImageUrl}
                  download={`PyMOL_${target}_${pymolHit.name}.png`}
                  className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-purple-600/30"
                >
                  <span>💾 Download High-Res PNG</span>
                </a>
              ) : <div />}

              <button
                onClick={() => setPymolHit(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScreeningConsole;
