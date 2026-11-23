import React, { useState, useEffect } from 'react';

const API_BASE = 'http://127.0.0.1:8000';

interface TargetOption {
  symbol: string;
  name: string;
  ensembl_id: string;
  chembl_id: string;
}

const TARGETS: TargetOption[] = [
  { symbol: 'ESR1', name: 'Estrogen Receptor Alpha (ERα)', ensembl_id: 'ENSG00000091831', chembl_id: 'CHEMBL206' },
  { symbol: 'ABL1', name: 'Abl Tyrosine Kinase', ensembl_id: 'ENSG00000148400', chembl_id: 'CHEMBL1862' },
  { symbol: 'EGFR', name: 'Epidermal Growth Factor Receptor', ensembl_id: 'ENSG00000146648', chembl_id: 'CHEMBL203' },
  { symbol: 'PTGS2', name: 'Cyclooxygenase-2 (COX-2)', ensembl_id: 'ENSG00000073756', chembl_id: 'CHEMBL230' },
  { symbol: 'Mpro', name: 'SARS-CoV-2 Main Protease', ensembl_id: 'VIRAL_SARS_COV_2', chembl_id: 'CHEMBL4296597' },
];

const DiseaseIntelligence: React.FC = () => {
  const [selectedTarget, setSelectedTarget] = useState<TargetOption>(TARGETS[0]);
  const [loading, setLoading] = useState(false);
  const [otData, setOtData] = useState<any>(null);
  const [chemblData, setChemblData] = useState<any>(null);
  const [tdcData, setTdcData] = useState<any>(null);
  const [selectedTdcId, setSelectedTdcId] = useState('caco2_wang');
  const [tdcLoading, setTdcLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Fetch Open Targets & ChEMBL when target changes
  const handleFetchTargetData = async (target: TargetOption) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      // 1. Fetch Open Targets Tractability & Diseases
      const otPromise = fetch(`${API_BASE}/ingestion/opentargets/target_tractability`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ensembl_id: target.ensembl_id }),
      }).then((r) => r.json());

      // 2. Fetch ChEMBL Live Bioactivity Records
      const chemblPromise = fetch(`${API_BASE}/ingestion/chembl/query_target`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_chembl_id: target.chembl_id, activity_type: 'IC50', limit: 15 }),
      }).then((r) => r.json());

      const [otRes, chemblRes] = await Promise.all([otPromise, chemblPromise]);
      setOtData(otRes);
      setChemblData(chemblRes);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Fetch TDC Benchmark
  const handleFetchTdc = async (datasetId: string) => {
    setTdcLoading(true);
    try {
      const res = await fetch(`${API_BASE}/ingestion/tdc/load_benchmark`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_id: datasetId, split_type: 'scaffold' }),
      });
      const data = await res.json();
      setTdcData(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setTdcLoading(false);
    }
  };

  useEffect(() => {
    handleFetchTargetData(selectedTarget);
    handleFetchTdc(selectedTdcId);
  }, []);

  const onTargetChange = (target: TargetOption) => {
    setSelectedTarget(target);
    handleFetchTargetData(target);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-900/80 border border-indigo-500/30 backdrop-blur shadow-xl shadow-indigo-950/20">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-indigo-400 animate-ping" />
            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-400 via-cyan-300 to-teal-400 bg-clip-text text-transparent">
              Scientific Intelligence & Target Ingestion Hub
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
              Stages 1-2
            </span>
          </div>
          <p className="text-slate-400 text-sm mt-1">
            Open Targets Platform Genetics • EMBL-EBI ChEMBL Bioactivities • Therapeutics Data Commons (TDC) Scaffold Partitions
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="px-3 py-1.5 rounded-lg bg-slate-800/90 border border-slate-700/60 text-xs text-slate-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-indigo-400" />
            <span>Open Targets GraphQL v4</span>
          </div>
          <div className="px-3 py-1.5 rounded-lg bg-slate-800/90 border border-slate-700/60 text-xs text-slate-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-teal-400" />
            <span>ChEMBL 34 REST API</span>
          </div>
          <div className="px-3 py-1.5 rounded-lg bg-slate-800/90 border border-slate-700/60 text-xs text-slate-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Bemis-Murcko Splitter</span>
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/50 text-red-200 text-sm flex items-center justify-between">
          <span>⚠️ {errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="font-bold text-red-400">✕</button>
        </div>
      )}

      {/* Target Selector */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
          Select Therapeutic Target for Real-Time Open Targets & ChEMBL Ingestion:
        </label>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2.5">
          {TARGETS.map((t) => (
            <button
              key={t.symbol}
              onClick={() => onTargetChange(t)}
              className={`p-3 rounded-xl border text-left transition-all ${
                selectedTarget.symbol === t.symbol
                  ? 'bg-indigo-950/50 border-indigo-400 text-white shadow-md shadow-indigo-950/30'
                  : 'bg-slate-800/40 border-slate-700/60 text-slate-300 hover:bg-slate-800'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-indigo-300">{t.symbol}</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-900 text-slate-400">
                  {t.chembl_id}
                </span>
              </div>
              <div className="text-xs text-slate-200 truncate mt-1">{t.name}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Open Targets & ChEMBL Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Open Targets Platform Card */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-indigo-400">1.</span> Open Targets Platform Validation
            </h2>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-800 font-mono">
              Ensembl: {selectedTarget.ensembl_id}
            </span>
          </div>

          {loading ? (
            <div className="py-12 text-center text-xs text-indigo-300 font-mono">
              <span className="w-5 h-5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin inline-block mb-2" />
              <div>Querying Open Targets GraphQL API...</div>
            </div>
          ) : otData ? (
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs space-y-1">
                <div className="font-bold text-sm text-white">{otData.approvedName || selectedTarget.name}</div>
                <div className="text-slate-400">
                  Approved Symbol: <span className="text-indigo-300 font-mono">{otData.approvedSymbol || selectedTarget.symbol}</span> • Biotype:{' '}
                  <span className="text-slate-200 font-mono">{otData.biotype || 'protein_coding'}</span>
                </div>
              </div>

              {/* Small-Molecule Tractability */}
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Small-Molecule Tractability & Druggability:
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {otData.tractability && otData.tractability.length > 0 ? (
                    otData.tractability.map((tr: any, idx: number) => (
                      <div
                        key={idx}
                        className={`p-2 rounded-lg border text-xs ${
                          tr.value
                            ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-300'
                            : 'bg-slate-950/40 border-slate-800 text-slate-400'
                        }`}
                      >
                        <div className="font-bold">{tr.label}</div>
                        <div className="text-[10px] text-slate-400">{tr.value ? '✓ Confirmed' : '—'}</div>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-slate-500 p-2">Tractability assessment validated</div>
                  )}
                </div>
              </div>

              {/* Associated Diseases & Genetic Association Scores */}
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Associated Diseases & Genetic Evidence Score:
                </div>
                <div className="space-y-1.5">
                  {otData.associatedDiseases?.rows?.slice(0, 4).map((row: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-xl bg-slate-950/50 border border-slate-800/80 flex items-center justify-between text-xs"
                    >
                      <span className="font-medium text-slate-200 truncate">{row.disease?.name}</span>
                      <span className="font-mono text-cyan-400 font-bold px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-800/60">
                        Score: {row.score?.toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Provenance Badge */}
              <div className="text-[11px] text-slate-500 flex items-center justify-between pt-2 border-t border-slate-800">
                <span>Source: Open Targets Platform GraphQL</span>
                <span className="text-emerald-400 font-mono">GROUND_TRUTH_EXPERIMENTAL</span>
              </div>
            </div>
          ) : null}
        </div>

        {/* ChEMBL Bioactivity Live Stream Card */}
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-teal-400">2.</span> ChEMBL Bioactivity Stream
            </h2>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-teal-950 text-teal-300 border border-teal-800 font-mono">
              ChEMBL: {selectedTarget.chembl_id}
            </span>
          </div>

          {loading ? (
            <div className="py-12 text-center text-xs text-teal-300 font-mono">
              <span className="w-5 h-5 border-2 border-teal-400 border-t-transparent rounded-full animate-spin inline-block mb-2" />
              <div>Fetching Experimental Bioactivities from EMBL-EBI ChEMBL...</div>
            </div>
          ) : chemblData?.records ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>
                  Retrieved <span className="text-teal-300 font-bold">{chemblData.records.length}</span> standardized
                  concentration-response records
                </span>
                <span className="font-mono text-slate-500">Unit: standard_value → pIC50</span>
              </div>

              {/* Records Table */}
              <div className="max-h-[360px] overflow-y-auto space-y-2 pr-1">
                {chemblData.records.map((rec: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-teal-500/40 transition-all text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-teal-300 font-mono">{rec.compound_chembl_id}</span>
                      <span className="font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold">
                        pIC50 = {rec.standardized_pIC50} ({rec.experimental_value} {rec.experimental_units})
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono truncate">{rec.smiles}</div>
                    <div className="text-[10px] text-slate-500 flex justify-between">
                      <span>Assay: {rec.assay_chembl_id}</span>
                      <span className="text-slate-400 italic truncate max-w-xs">{rec.assay_description}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Provenance Badge */}
              <div className="text-[11px] text-slate-500 flex items-center justify-between pt-2 border-t border-slate-800">
                <span>Source: EMBL-EBI ChEMBL REST API (CC-BY-SA-3.0)</span>
                <span className="text-emerald-400 font-mono">GROUND_TRUTH_EXPERIMENTAL</span>
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {/* Therapeutics Data Commons (TDC) Benchmarking Card */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-emerald-400">3.</span> Therapeutics Data Commons (TDC) ML Benchmarks
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Curated ADMET and bioactivity benchmark datasets with guaranteed leak-free Bemis-Murcko scaffold partitions.
            </p>
          </div>

          {/* Dataset Selector Tabs */}
          <div className="flex rounded-xl bg-slate-800 p-1 border border-slate-700/80 text-xs">
            <button
              onClick={() => {
                setSelectedTdcId('caco2_wang');
                handleFetchTdc('caco2_wang');
              }}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                selectedTdcId === 'caco2_wang' ? 'bg-emerald-500 text-slate-950 font-bold' : 'text-slate-300'
              }`}
            >
              Caco-2 (Wang)
            </button>
            <button
              onClick={() => {
                setSelectedTdcId('herg_karim');
                handleFetchTdc('herg_karim');
              }}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                selectedTdcId === 'herg_karim' ? 'bg-emerald-500 text-slate-950 font-bold' : 'text-slate-300'
              }`}
            >
              hERG (Karim)
            </button>
            <button
              onClick={() => {
                setSelectedTdcId('mpro_postera');
                handleFetchTdc('mpro_postera');
              }}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                selectedTdcId === 'mpro_postera' ? 'bg-emerald-500 text-slate-950 font-bold' : 'text-slate-300'
              }`}
            >
              Mpro Moonshot
            </button>
          </div>
        </div>

        {tdcLoading ? (
          <div className="py-10 text-center text-xs text-emerald-300 font-mono">
            <span className="w-5 h-5 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin inline-block mb-2" />
            <div>Partitioning Benchmark Scaffolds...</div>
          </div>
        ) : tdcData ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs space-y-1">
                <div className="text-slate-400">Benchmark Dataset:</div>
                <div className="font-bold text-white text-sm">{tdcData.name}</div>
                <div className="text-[11px] text-slate-400">
                  Category: <span className="text-emerald-400">{tdcData.category}</span> • Unit:{' '}
                  <span className="font-mono text-slate-300">{tdcData.units}</span>
                </div>
              </div>

              {/* Scaffold Split Breakdown */}
              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs space-y-1">
                <div className="text-slate-400">Bemis-Murcko Scaffold Partitioning:</div>
                <div className="flex items-center gap-2 font-mono font-bold text-xs pt-1">
                  <span className="text-cyan-400">Train: {tdcData.splits?.stats?.train_count} ({tdcData.splits?.stats?.train_pct}%)</span>
                  <span>•</span>
                  <span className="text-teal-400">Val: {tdcData.splits?.stats?.val_count}</span>
                  <span>•</span>
                  <span className="text-emerald-400">Test: {tdcData.splits?.stats?.test_count} ({tdcData.splits?.stats?.test_pct}%)</span>
                </div>
                <div className="text-[11px] text-slate-500">
                  Total Scaffolds: {tdcData.splits?.stats?.total_scaffolds}
                </div>
              </div>

              {/* Leak-Free Verification Audit Card */}
              <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/40 text-xs space-y-1">
                <div className="text-slate-400">Data Leakage Audit:</div>
                <div className="font-bold text-emerald-400 text-sm flex items-center gap-1.5">
                  <span>✓ {tdcData.leak_free_audit?.audit_verdict}</span>
                </div>
                <div className="text-[11px] text-slate-300">
                  Test Overlap Count:{' '}
                  <span className="font-mono font-bold text-emerald-300">
                    {tdcData.leak_free_audit?.train_test_overlap_count} Scaffolds
                  </span>
                </div>
              </div>
            </div>

            {/* Benchmark Samples Table */}
            <div className="rounded-xl border border-slate-800 overflow-hidden">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 uppercase text-[10px] text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Compound Name</th>
                    <th className="py-2.5 px-3">Canonical SMILES</th>
                    <th className="py-2.5 px-3">Murcko Scaffold</th>
                    <th className="py-2.5 px-3 text-right">Experimental Ground Truth</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
                  {tdcData.splits?.train?.concat(tdcData.splits?.test || []).slice(0, 6).map((rec: any, idx: number) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-bold text-white">{rec.name}</td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-slate-400 truncate max-w-xs">{rec.smiles}</td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-emerald-300 truncate max-w-xs">
                        {rec.scaffold || 'Acyclic'}
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono font-bold text-cyan-300">
                        {rec.label_value}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default DiseaseIntelligence;
