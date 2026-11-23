import React, { useState, useEffect } from 'react';

const API_BASE = 'http://127.0.0.1:8000';

interface TargetOption {
  pdb_id: string;
  name: string;
  indication: string;
  defaultLead: string;
}

const TARGETS: TargetOption[] = [
  { pdb_id: '6LU7', name: 'SARS-CoV-2 Main Protease (Mpro)', indication: 'COVID-19 Antiviral', defaultLead: 'Cc1cc(nc(n1)N)C(=O)NCc2ccccc2' },
  { pdb_id: '1ERE', name: 'Estrogen Receptor Alpha (ERα)', indication: 'Breast Cancer Oncology', defaultLead: 'Oc1ccc2c(c1)OC(c3ccccc3)C2' },
  { pdb_id: '1IEP', name: 'Abl Tyrosine Kinase', indication: 'Chronic Myeloid Leukemia', defaultLead: 'Cc1ccc(cc1Nc2nccc(n2)c3cccnc3)NC(=O)c4ccc(cc4)CN5CCNCC5' },
  { pdb_id: '1M17', name: 'EGFR Kinase Domain', indication: 'Non-Small Cell Lung Cancer', defaultLead: 'COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OC' },
  { pdb_id: '1CX2', name: 'Cyclooxygenase-2 (COX-2)', indication: 'Inflammation & Pain Management', defaultLead: 'Cc1ccc(cc1)c2cc(nn2c3ccc(cc3)S(=O)(=O)N)C(F)(F)F' },
];

const IterativeDiscovery: React.FC = () => {
  const [selectedTarget, setSelectedTarget] = useState<TargetOption>(TARGETS[0]);
  const [campaignName, setCampaignName] = useState('Mpro Autonomous Optimization Campaign');
  const [totalIterations, setTotalIterations] = useState(2);
  const [candidatesPerIter, setCandidatesPerIter] = useState(3);
  const [leadSmiles, setLeadSmiles] = useState(TARGETS[0].defaultLead);
  
  const [running, setRunning] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [campaignsList, setCampaignsList] = useState<any[]>([]);
  const [activeCampaignId, setActiveCampaignId] = useState<string | null>(null);
  const [campaignDetails, setCampaignDetails] = useState<any>(null);
  const [lineageGraph, setLineageGraph] = useState<any>(null);
  const [failureTaxonomy, setFailureTaxonomy] = useState<any>(null);

  // Load campaigns on mount
  useEffect(() => {
    fetchCampaigns();
    fetchTaxonomy();
  }, []);

  // When activeCampaignId changes, load details & lineage
  useEffect(() => {
    if (activeCampaignId) {
      fetchCampaignDetails(activeCampaignId);
      fetchCampaignLineage(activeCampaignId);
    }
  }, [activeCampaignId]);

  const fetchCampaigns = async () => {
    try {
      const res = await fetch(`${API_BASE}/iterative_loop/campaigns`);
      if (res.ok) {
        const data = await res.json();
        setCampaignsList(data);
        if (data.length > 0 && !activeCampaignId) {
          setActiveCampaignId(data[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to fetch campaigns', err);
    }
  };

  const fetchTaxonomy = async () => {
    try {
      const res = await fetch(`${API_BASE}/iterative_loop/failure_taxonomy`);
      if (res.ok) {
        const data = await res.json();
        setFailureTaxonomy(data);
      }
    } catch (err) {
      console.error('Failed to fetch failure taxonomy', err);
    }
  };

  const fetchCampaignDetails = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/iterative_loop/campaign/${id}`);
      if (res.ok) {
        const data = await res.json();
        setCampaignDetails(data);
      }
    } catch (err) {
      console.error('Failed to fetch campaign details', err);
    }
  };

  const fetchCampaignLineage = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/iterative_loop/campaign/${id}/lineage`);
      if (res.ok) {
        const data = await res.json();
        setLineageGraph(data);
      }
    } catch (err) {
      console.error('Failed to fetch campaign lineage', err);
    }
  };

  const handleLaunchCampaign = async () => {
    setRunning(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE}/iterative_loop/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_name: campaignName,
          target: selectedTarget.pdb_id,
          total_iterations: totalIterations,
          candidates_per_iter: candidatesPerIter,
          initial_lead_smiles: leadSmiles.trim() || null,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Campaign execution failed');
      }

      const result = await res.json();
      setActiveCampaignId(result.campaign_id);
      await fetchCampaigns();
      await fetchTaxonomy();
    } catch (err: any) {
      setErrorMsg(err.message || 'An error occurred during campaign run');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-gradient-to-r from-gray-900 via-indigo-950 to-gray-900 border border-indigo-700/50 rounded-xl p-6 shadow-2xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 bg-cyan-500/20 text-cyan-300 text-xs font-mono font-bold rounded-full border border-cyan-500/40">
                MILESTONE 5 & 6
              </span>
              <h1 className="text-2xl font-black tracking-wide text-white">
                Closed-Loop Iterative Discovery & Lineage Studio
              </h1>
            </div>
            <p className="text-gray-300 text-sm mt-1">
              Autonomous multi-objective drug discovery: <code className="text-cyan-400">GENERATE → SCREEN → DOCK → PREDICT → EVALUATE → ANALYSE → LEARN → OPTIMISE</code>
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-3 py-1 rounded-md text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <span className="w-2 h-2 rounded-full bg-emerald-400 mr-2 animate-pulse" />
              RTX 3060 CUDA Active
            </span>
          </div>
        </div>
      </div>

      {/* Main Grid: Launcher + Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Launcher Config Card */}
        <div className="bg-gray-800/90 border border-gray-700 rounded-xl p-5 shadow-lg space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="text-indigo-400">🚀</span> Campaign Configuration
          </h2>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase mb-1">Target Receptor</label>
            <select
              value={selectedTarget.pdb_id}
              onChange={(e) => {
                const t = TARGETS.find((x) => x.pdb_id === e.target.value) || TARGETS[0];
                setSelectedTarget(t);
                setLeadSmiles(t.defaultLead);
                setCampaignName(`${t.name} Optimization Campaign`);
              }}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
            >
              {TARGETS.map((t) => (
                <option key={t.pdb_id} value={t.pdb_id}>
                  {t.name} ({t.pdb_id})
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-400 mt-1 italic">{selectedTarget.indication}</p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase mb-1">Campaign Name</label>
            <input
              type="text"
              value={campaignName}
              onChange={(e) => setCampaignName(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1">Rounds (Iterations)</label>
              <input
                type="number"
                min={1}
                max={5}
                value={totalIterations}
                onChange={(e) => setTotalIterations(parseInt(e.target.value) || 2)}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-1">Per Round</label>
              <input
                type="number"
                min={1}
                max={6}
                value={candidatesPerIter}
                onChange={(e) => setCandidatesPerIter(parseInt(e.target.value) || 3)}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase mb-1">Initial Lead SMILES</label>
            <textarea
              rows={2}
              value={leadSmiles}
              onChange={(e) => setLeadSmiles(e.target.value)}
              placeholder="Leave blank for pure de novo generation"
              className="w-full bg-gray-900 border border-gray-700 rounded-lg p-2 font-mono text-xs text-gray-200 focus:outline-none focus:border-indigo-500"
            />
          </div>

          {errorMsg && (
            <div className="p-3 bg-red-950/60 border border-red-700 rounded-lg text-xs text-red-300">
              {errorMsg}
            </div>
          )}

          <button
            onClick={handleLaunchCampaign}
            disabled={running}
            className={`w-full py-3 px-4 rounded-xl font-bold text-sm tracking-wide transition-all shadow-md flex items-center justify-center gap-2 ${
              running
                ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/30'
            }`}
          >
            {running ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                Executing 9-Stage Loop on CUDA...
              </>
            ) : (
              '⚡ Launch Autonomous Campaign'
            )}
          </button>
        </div>

        {/* Campaign Metrics & System Health */}
        <div className="lg:col-span-2 space-y-6">
          {/* Historical Campaigns Dropdown & Overview */}
          <div className="bg-gray-800/90 border border-gray-700 rounded-xl p-5 shadow-lg">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span className="text-cyan-400">📊</span> Active Campaign Lineage & Metrics
              </h2>
              {campaignsList.length > 0 && (
                <select
                  value={activeCampaignId || ''}
                  onChange={(e) => setActiveCampaignId(e.target.value)}
                  className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-cyan-300 font-mono focus:outline-none"
                >
                  {campaignsList.map((c) => (
                    <option key={c.id} value={c.id}>
                      [{c.target}] {c.name} ({c.id})
                    </option>
                  ))}
                </select>
              )}
            </div>

            {campaignDetails ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-gray-900/80 border border-gray-800 rounded-lg p-3 text-center">
                  <span className="text-xs text-gray-400 uppercase font-semibold">Status</span>
                  <div className="text-sm font-bold mt-1 text-emerald-400">{campaignDetails.status}</div>
                </div>
                <div className="bg-gray-900/80 border border-gray-800 rounded-lg p-3 text-center">
                  <span className="text-xs text-gray-400 uppercase font-semibold">Total Evaluated</span>
                  <div className="text-sm font-bold mt-1 text-white">{campaignDetails.candidates?.length || 0} candidates</div>
                </div>
                <div className="bg-gray-900/80 border border-gray-800 rounded-lg p-3 text-center">
                  <span className="text-xs text-gray-400 uppercase font-semibold">Best Reward</span>
                  <div className="text-sm font-bold mt-1 text-cyan-300">
                    {campaignDetails.summary_metrics?.best_candidate_reward || 0.0}
                  </div>
                </div>
                <div className="bg-gray-900/80 border border-gray-800 rounded-lg p-3 text-center">
                  <span className="text-xs text-gray-400 uppercase font-semibold">Total Runtime</span>
                  <div className="text-sm font-bold mt-1 text-purple-300">
                    {campaignDetails.summary_metrics?.total_elapsed_seconds || 0}s
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-sm text-gray-400 py-6 text-center">No campaign selected or active.</div>
            )}

            {/* Failure Taxonomy Quick Bar */}
            {failureTaxonomy && (
              <div className="mt-5 pt-4 border-t border-gray-700/60">
                <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide block mb-2">
                  System-Wide Failure Taxonomy & Acceptance Rate
                </span>
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="bg-emerald-950/40 border border-emerald-800/50 rounded p-2">
                    <span className="text-emerald-400 font-bold">{failureTaxonomy.totals?.accepted || 0}</span>
                    <span className="block text-gray-400 text-[10px]">ACCEPTED</span>
                  </div>
                  <div className="bg-cyan-950/40 border border-cyan-800/50 rounded p-2">
                    <span className="text-cyan-400 font-bold">{failureTaxonomy.totals?.active_learning_candidates || 0}</span>
                    <span className="block text-gray-400 text-[10px]">ACTIVE LEARNING</span>
                  </div>
                  <div className="bg-rose-950/40 border border-rose-800/50 rounded p-2">
                    <span className="text-rose-400 font-bold">{failureTaxonomy.totals?.rejected || 0}</span>
                    <span className="block text-gray-400 text-[10px]">REJECTED</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Candidate Lineage Tree & Evolutionary Comparison */}
      {campaignDetails && campaignDetails.candidates && (
        <div className="bg-gray-800/90 border border-gray-700 rounded-xl p-6 shadow-lg space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-700/80 pb-4">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span className="text-amber-400">🧬</span> Molecular Lineage & Pareto Frontier
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Evolutionary lineage showing parent-child derivation across iterations
              </p>
            </div>
            <div className="flex gap-2">
              <span className="px-2.5 py-1 bg-emerald-900/50 text-emerald-300 border border-emerald-700/60 rounded text-xs">
                Accepted Lead
              </span>
              <span className="px-2.5 py-1 bg-cyan-900/50 text-cyan-300 border border-cyan-700/60 rounded text-xs">
                Active Learning (High Uncertainty)
              </span>
              <span className="px-2.5 py-1 bg-rose-900/50 text-rose-300 border border-rose-700/60 rounded text-xs">
                Classified Failure
              </span>
            </div>
          </div>

          {/* Iteration-by-Iteration Cards */}
          <div className="space-y-6">
            {campaignDetails.iterations?.map((iter: any) => {
              const iterCandidates = campaignDetails.candidates.filter(
                (c: any) => c.iteration === iter.iteration
              );
              return (
                <div key={iter.iteration} className="border border-gray-700/60 bg-gray-900/60 rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="px-3 py-1 bg-indigo-900/60 border border-indigo-700 text-indigo-300 font-bold text-xs rounded-full">
                      Iteration {iter.iteration}
                    </span>
                    <div className="text-xs text-gray-400 flex gap-4">
                      <span>Mean Reward: <strong className="text-cyan-300">{iter.mean_reward}</strong></span>
                      <span>Best Reward: <strong className="text-amber-300">{iter.best_reward}</strong></span>
                      <span>Funnel: {iter.screened_count} screened → {iter.accepted_count} accepted</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {iterCandidates.map((cand: any) => (
                      <div
                        key={cand.id}
                        className={`border rounded-lg p-3 space-y-2 transition-all ${
                          cand.decision === 'ACCEPTED'
                            ? 'bg-gray-800/90 border-emerald-700/70'
                            : cand.decision === 'ACTIVE_LEARNING_CANDIDATE'
                            ? 'bg-gray-800/90 border-cyan-700/70'
                            : 'bg-gray-800/50 border-rose-900/60 opacity-80'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <span className="text-[10px] font-mono text-gray-400 truncate">{cand.id}</span>
                          <span
                            className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                              cand.decision === 'ACCEPTED'
                                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                : cand.decision === 'ACTIVE_LEARNING_CANDIDATE'
                                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                                : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                            }`}
                          >
                            {cand.decision}
                          </span>
                        </div>

                        {cand.parent_id && (
                          <div className="text-[10px] text-amber-400/90 flex items-center gap-1 font-mono">
                            <span>↳ Derived from:</span>
                            <span className="underline">{cand.parent_id}</span>
                          </div>
                        )}

                        <div className="bg-gray-900 p-2 rounded text-[11px] font-mono text-gray-200 break-all select-all">
                          {cand.smiles}
                        </div>

                        {cand.failure_reason && (
                          <div className="text-[10px] text-rose-400 font-semibold">
                            ⚠️ Failure: {cand.failure_reason}
                          </div>
                        )}

                        <div className="grid grid-cols-2 gap-1.5 pt-1 text-[11px] border-t border-gray-700/50">
                          <div>
                            <span className="text-gray-400">Composite:</span>{' '}
                            <strong className="text-cyan-300">{cand.composite_reward}</strong>
                          </div>
                          <div>
                            <span className="text-gray-400">Vina Affinity:</span>{' '}
                            <strong className="text-gray-200">{cand.vina_affinity_kcal_mol} kcal</strong>
                          </div>
                          <div>
                            <span className="text-gray-400">GNINA CNN:</span>{' '}
                            <strong className="text-gray-200">{cand.cnn_score}</strong>
                          </div>
                          <div>
                            <span className="text-gray-400">pIC50:</span>{' '}
                            <strong className="text-gray-200">{cand.chemprop_pIC50}</strong>
                          </div>
                          <div>
                            <span className="text-gray-400">Uncertainty (u):</span>{' '}
                            <strong className={cand.epistemic_uncertainty > 0.65 ? 'text-amber-400' : 'text-gray-200'}>
                              {cand.epistemic_uncertainty}
                            </strong>
                          </div>
                          <div>
                            <span className="text-gray-400">QED / SA:</span>{' '}
                            <strong className="text-gray-200">{cand.qed} / {cand.sa_score}</strong>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default IterativeDiscovery;
