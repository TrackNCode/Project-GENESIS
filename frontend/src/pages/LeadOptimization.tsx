import React, { useState, useEffect } from 'react';
import { API_BASE } from '@/api/config';

interface PresetLead {
  name: string;
  smiles: string;
  target: string;
  indication: string;
}

const PRESET_LEADS: PresetLead[] = [
  {
    name: 'Nirmatrelvir (Paxlovid)',
    smiles: 'CC1(C2C1C(N(C2)C(=O)C(C(C)(C)C)NC(=O)C(F)(F)F)C(=O)NC(CC3CCNC3=O)C#N)C',
    target: '6LU7',
    indication: 'SARS-CoV-2 Protease Inhibitor',
  },
  {
    name: 'Imatinib (Gleevec)',
    smiles: 'Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc4nccc(n4)c5cccnc5',
    target: '1IEP',
    indication: 'Abl Tyrosine Kinase Inhibitor',
  },
  {
    name: '17beta-Estradiol',
    smiles: 'CC12CCC3C(C1CCC2O)CCC4=C3C=CC(=C4)O',
    target: '1ERE',
    indication: 'Estrogen Receptor Agonist',
  },
  {
    name: 'Erlotinib (Tarceva)',
    smiles: 'COCCOC1=C(OCCOC)C=C2C(=C1)C(=NC=N2)NC3=CC=CC(=C3)C#C',
    target: '1M17',
    indication: 'EGFR Tyrosine Kinase Inhibitor',
  },
  {
    name: 'Celecoxib (Celebrex)',
    smiles: 'Cc1ccc(-c2cc(C(F)(F)F)nn2-c2ccc(S(N)(=O)=O)cc2)cc1',
    target: '1CX2',
    indication: 'Selective COX-2 Inhibitor',
  },
  {
    name: 'Ibuprofen',
    smiles: 'CC(C)Cc1ccc(cc1)C(C)C(=O)O',
    target: '6LU7',
    indication: 'NSAID / Weak Protease Binder',
  },
];

const TARGET_OPTIONS = [
  { id: '6LU7', name: 'SARS-CoV-2 Main Protease (Mpro)' },
  { id: '1IEP', name: 'Abl Tyrosine Kinase' },
  { id: '1ERE', name: 'Estrogen Receptor Alpha (ERα)' },
  { id: '1M17', name: 'EGFR Kinase Domain' },
  { id: '1CX2', name: 'Cyclooxygenase-2 (COX-2)' },
];

const LeadOptimization: React.FC = () => {
  const [smiles, setSmiles] = useState(PRESET_LEADS[0].smiles);
  const [target, setTarget] = useState(PRESET_LEADS[0].target);
  const [selectedLeadName, setSelectedLeadName] = useState(PRESET_LEADS[0].name);

  const [loading, setLoading] = useState(false);
  const [leadProfile, setLeadProfile] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [candidateSaveStatus, setCandidateSaveStatus] = useState<string | null>(null);

  // Analyze lead on mount or button click
  const handleAnalyzeLead = async (inputSmiles = smiles, inputTarget = target) => {
    setLoading(true);
    setErrorMsg(null);
    setCandidateSaveStatus(null);

    try {
      const res = await fetch(`${API_BASE}/ai_models/lead_opt/comprehensive_lead_profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ smiles: inputSmiles, target: inputTarget }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Lead profiling failed');
      }

      const data = await res.json();
      setLeadProfile(data);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleAnalyzeLead();
  }, []);

  const selectPreset = (preset: PresetLead) => {
    setSelectedLeadName(preset.name);
    setSmiles(preset.smiles);
    setTarget(preset.target);
    handleAnalyzeLead(preset.smiles, preset.target);
  };

  const handleApplyAnalog = (analogSmiles: string, ruleName: string) => {
    setSelectedLeadName(`Optimized Analog (${ruleName})`);
    setSmiles(analogSmiles);
    handleAnalyzeLead(analogSmiles, target);
  };

  const handleSaveToCandidates = async (saveSmiles: string, name: string, pIC50: number) => {
    try {
      const res = await fetch(`${API_BASE}/screening/save_candidate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: 1,
          name: name,
          smiles: saveSmiles,
          binding_affinity: -pIC50,
          target: target,
        }),
      });

      if (!res.ok) throw new Error('Save to database failed');
      const data = await res.json();

      // Trigger automatic AI model scoring in DB
      await fetch(`${API_BASE}/ai_models/candidates/${data.candidate_id}/evaluate_all?target=${target}`, {
        method: 'POST',
      });

      setCandidateSaveStatus(`Successfully saved '${name}' to Candidate Database!`);
    } catch (err: any) {
      alert(`Error saving candidate: ${err.message}`);
    }
  };

  const qsar = leadProfile?.qsar;
  const adme = leadProfile?.adme;
  const tox = leadProfile?.toxicity;
  const mpo = leadProfile?.mpo_desirability;
  const bioisosteres = leadProfile?.bioisosteric_optimizations || [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-teal-600" />
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
              Lead Optimisation & AI Prediction Studio
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider rounded-full bg-teal-50 text-teal-800 border border-teal-200 font-bold">
              Phase 6
            </span>
          </div>
          <p className="text-slate-500 text-sm mt-1">
            Target-Specific QSAR Modeling (pIC50) • Comprehensive ADME Pharmacokinetics • In Silico Toxicity & Bioisosteric Design
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-teal-400" />
            <span>QSAR Ridge + RF Ensemble</span>
          </div>
          <div className="px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span>5-CYP450 Metabolism Matrix</span>
          </div>
          <div className="px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-purple-400" />
            <span>hERG & Ames Toxicity Engine</span>
          </div>
        </div>
      </div>

      {candidateSaveStatus && (
        <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/50 text-emerald-200 text-sm flex items-center justify-between">
          <span>✓ {candidateSaveStatus}</span>
          <button onClick={() => setCandidateSaveStatus(null)} className="font-bold text-emerald-400">✕</button>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/50 text-red-200 text-sm flex items-center justify-between">
          <span>⚠️ {errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="font-bold text-red-400">✕</button>
        </div>
      )}

      {/* Preset Leads Selector */}
      <div className="p-4 rounded-2xl bg-white border border-slate-200">
        <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-2">
          Select Benchmark Therapeutic Lead or Inspect Custom SMILES:
        </label>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
          {PRESET_LEADS.map((p) => (
            <button
              key={p.name}
              onClick={() => selectPreset(p)}
              className={`p-2.5 rounded-xl border text-left transition-all ${
                selectedLeadName === p.name
                  ? 'bg-teal-50 border-teal-600 text-teal-900 font-bold shadow-sm'
                  : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
              }`}
            >
              <div className="font-bold text-xs truncate text-teal-300">{p.name}</div>
              <div className="text-[10px] text-slate-500 truncate">{p.indication}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Input Form */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 p-5 rounded-2xl bg-white border border-slate-200">
        <div className="lg:col-span-3">
          <label className="text-xs font-semibold text-slate-500 block mb-1">Lead Molecule SMILES String</label>
          <input
            type="text"
            value={smiles}
            onChange={(e) => setSmiles(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs font-mono text-teal-700 focus:outline-none focus:border-teal-400"
          />
        </div>
        <div>
          <label className="text-xs font-semibold text-slate-500 block mb-1">Target Receptor</label>
          <div className="flex gap-2">
            <select
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-white focus:outline-none"
            >
              {TARGET_OPTIONS.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.id} - {t.name}
                </option>
              ))}
            </select>
            <button
              onClick={() => handleAnalyzeLead(smiles, target)}
              disabled={loading}
              className="px-5 py-3 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold shadow-sm"
            >
              {loading ? (
                <span className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
              ) : (
                <span>⚡ Run AI Models</span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Lead Profile Cards Grid */}
      {leadProfile && (
        <div className="space-y-6">
          {/* Top Row: MPO Desirability & QSAR Bioactivity */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Multi-Property Objective (MPO) Desirability Card */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span>MPO Desirability Score</span>
                </h3>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-teal-500/20 text-teal-300 border border-teal-500/30">
                  {mpo?.rating}
                </span>
              </div>

              {/* Big Circular/Radial Visual Gauge */}
              <div className="text-center py-2">
                <div className="text-5xl font-black font-mono tracking-tight bg-gradient-to-r from-teal-400 to-emerald-400 bg-clip-text text-transparent">
                  {mpo?.mpo_score}
                </div>
                <div className="text-xs text-slate-500 mt-1">Composite Desirability (0.00 - 1.00)</div>
              </div>

              {/* 5-Dimensional Desirability Breakdown */}
              <div className="space-y-2 text-xs">
                <div>
                  <div className="flex justify-between text-[11px] text-slate-700 mb-0.5">
                    <span>Target Potency</span>
                    <span className="font-mono text-teal-700">{(mpo?.potency_desirability * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                    <div className="h-full bg-cyan-400" style={{ width: `${mpo?.potency_desirability * 100}%` }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-[11px] text-slate-700 mb-0.5">
                    <span>Lipophilicity (cLogP)</span>
                    <span className="font-mono text-teal-300">{(mpo?.lipophilicity_desirability * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                    <div className="h-full bg-teal-400" style={{ width: `${mpo?.lipophilicity_desirability * 100}%` }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-[11px] text-slate-700 mb-0.5">
                    <span>Polar Surface Area (TPSA)</span>
                    <span className="font-mono text-emerald-300">{(mpo?.polar_surface_desirability * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                    <div className="h-full bg-emerald-400" style={{ width: `${mpo?.polar_surface_desirability * 100}%` }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-[11px] text-slate-700 mb-0.5">
                    <span>Cardio & Genetic Safety</span>
                    <span className="font-mono text-slate-700">{(mpo?.safety_desirability * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                    <div className="h-full bg-purple-400" style={{ width: `${mpo?.safety_desirability * 100}%` }} />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-[11px] text-slate-700 mb-0.5">
                    <span>ADME Permeability & Metabolic Stability</span>
                    <span className="font-mono text-amber-300">{(mpo?.adme_desirability * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                    <div className="h-full bg-amber-400" style={{ width: `${mpo?.adme_desirability * 100}%` }} />
                  </div>
                </div>
              </div>

              <button
                onClick={() => handleSaveToCandidates(smiles, selectedLeadName, qsar?.predicted_pIC50 || 7.0)}
                className="w-full py-2.5 rounded-xl bg-slate-100 hover:bg-slate-700 border border-slate-200 text-xs font-semibold text-slate-800 transition-all flex items-center justify-center gap-2"
              >
                <span>💾 Save Lead to Project Candidates DB</span>
              </button>
            </div>

            {/* QSAR Bioactivity Prediction Card */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span>QSAR Bioactivity Engine</span>
                </h3>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-950 text-teal-700 border border-cyan-800 font-mono">
                  {target}
                </span>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">Predicted pIC50 (-log₁₀[IC50]):</span>
                  <span className="text-2xl font-black font-mono text-teal-700">{qsar?.predicted_pIC50}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">Estimated IC50:</span>
                  <span className="text-sm font-bold font-mono text-white">
                    {qsar?.predicted_IC50_nM < 1000
                      ? `${qsar?.predicted_IC50_nM} nM`
                      : `${qsar?.predicted_IC50_uM} µM`}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">Activity Classification:</span>
                  <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                    {qsar?.activity_class}
                  </span>
                </div>
              </div>

              {/* Applicability Domain (AD) Check */}
              <div className="p-3.5 rounded-xl bg-slate-50/40 border border-slate-200 text-xs space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-700">Applicability Domain (AD)</span>
                  <span
                    className={`font-mono text-[11px] px-2 py-0.5 rounded ${
                      qsar?.applicability_domain?.in_domain
                        ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800'
                        : 'bg-amber-950/80 text-amber-400 border border-amber-800'
                    }`}
                  >
                    {qsar?.applicability_domain?.in_domain ? '✓ In Domain' : '⚠ Out of Domain'}
                  </span>
                </div>
                <div className="text-[11px] text-slate-500">
                  Nearest Neighbor Tanimoto:{' '}
                  <span className="text-slate-800 font-mono font-bold">
                    {qsar?.applicability_domain?.max_tanimoto_similarity}
                  </span>
                </div>
                <div className="text-[11px] text-slate-500">
                  Confidence: <span className="text-teal-700">{qsar?.applicability_domain?.confidence_level}</span>
                </div>
              </div>

              {/* Target Multi-Selectivity Comparison */}
              <div className="space-y-1.5 text-xs">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Multi-Target Bioactivity Selectivity:
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {leadProfile?.multi_target_profile?.targets &&
                    Object.entries(leadProfile.multi_target_profile.targets).map(([tId, tData]: [string, any]) => (
                      <div
                        key={tId}
                        className={`p-2 rounded-lg border text-[11px] ${
                          tId === target
                            ? 'bg-cyan-950/50 border-cyan-500/50 text-cyan-200'
                            : 'bg-slate-50/30 border-slate-200/60 text-slate-500'
                        }`}
                      >
                        <div className="font-bold flex justify-between">
                          <span>{tId}</span>
                          <span className="font-mono text-slate-800">{tData.pIC50}</span>
                        </div>
                        <div className="truncate text-[10px] text-slate-500">{tData.target_name}</div>
                      </div>
                    ))}
                </div>
              </div>
            </div>

            {/* In Silico Toxicity & Safety Card */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span>Toxicity & Safety Engine</span>
                </h3>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-950 text-slate-700 border border-purple-800 font-mono">
                  Score: {tox?.safety_score}/100
                </span>
              </div>

              <div className="space-y-2.5 text-xs">
                {/* hERG Cardiac Safety */}
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-800">hERG Cardiac Risk</div>
                    <div className="text-[11px] text-slate-500">{tox?.cardiac_herg?.herg_risk_class}</div>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold ${
                      tox?.cardiac_herg?.herg_positive_alert
                        ? 'bg-red-950 text-red-300 border border-red-800'
                        : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    }`}
                  >
                    p = {tox?.cardiac_herg?.herg_inhibition_probability}
                  </span>
                </div>

                {/* Ames Mutagenicity */}
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-800">Ames Mutagenicity</div>
                    <div className="text-[11px] text-slate-500">Bacterial DNA Reactivity</div>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                      tox?.mutagenicity_ames?.ames_mutagenic
                        ? 'bg-red-950 text-red-300 border border-red-800'
                        : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    }`}
                  >
                    {tox?.mutagenicity_ames?.ames_mutagenic ? '✗ Mutagenic Alert' : '✓ Non-Mutagenic'}
                  </span>
                </div>

                {/* DILI Hepatotoxicity */}
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-slate-800">Hepatotoxicity (DILI)</div>
                    <div className="text-[11px] text-slate-500">{tox?.hepatotoxicity_dili?.dili_risk_class}</div>
                  </div>
                  <span className="font-mono text-slate-700">p = {tox?.hepatotoxicity_dili?.dili_probability}</span>
                </div>

                {/* Acute Oral LD50 & GHS Category */}
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                  <div className="flex justify-between">
                    <span className="font-bold text-slate-800">Acute Oral LD50:</span>
                    <span className="font-mono font-bold text-teal-700">
                      {tox?.acute_oral_toxicity?.estimated_ld50_mg_kg} mg/kg
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500">{tox?.acute_oral_toxicity?.ghs_hazard_category}</div>
                </div>

                {/* Toxicophoric Alerts */}
                {tox?.structural_toxicophores?.alert_count > 0 && (
                  <div className="p-2.5 rounded-xl bg-red-950/20 border border-red-500/30 text-[11px] text-red-300">
                    <div className="font-bold mb-1">Structural Alerts Detected ({tox.structural_toxicophores.alert_count}):</div>
                    <div className="flex flex-wrap gap-1">
                      {tox.structural_toxicophores.alerts.map((a: string) => (
                        <span key={a} className="px-1.5 py-0.5 rounded bg-red-900/60 border border-red-700/60 text-[10px]">
                          {a}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Middle Row: ADME Pharmacokinetic Profile */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span>Comprehensive ADME Pharmacokinetics</span>
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-teal-700 font-mono">
                    ADME Score: {adme?.adme_score}/100
                  </span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Gastrointestinal absorption, Caco-2 permeability, blood-brain distribution, and Cytochrome P450 matrix.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700">
                  DDI Risk: <span className="font-bold text-amber-400">{adme?.metabolism?.drug_interaction_risk}</span>
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Absorption */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
                <div className="font-bold text-slate-800 text-sm flex items-center justify-between">
                  <span>1. Absorption</span>
                  <span className="text-emerald-400 font-mono">{adme?.absorption?.hia_percentage}%</span>
                </div>
                <div className="text-slate-500">{adme?.absorption?.hia_class}</div>
                <div className="pt-2 border-t border-slate-200 space-y-1 text-[11px]">
                  <div className="flex justify-between">
                    <span>Caco-2 Permeability:</span>
                    <span className="font-mono text-slate-800">
                      {adme?.absorption?.caco2_permeability_10e6_cm_s} × 10⁻⁶ cm/s
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>P-gp Substrate:</span>
                    <span className={adme?.absorption?.pgp_substrate ? 'text-amber-400 font-bold' : 'text-slate-500'}>
                      {adme?.absorption?.pgp_substrate ? 'Yes (Efflux Risk)' : 'No'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Distribution */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
                <div className="font-bold text-slate-800 text-sm flex items-center justify-between">
                  <span>2. Distribution</span>
                  <span className="text-teal-700 font-mono">LogBB: {adme?.distribution?.log_bb}</span>
                </div>
                <div className="text-slate-500">{adme?.distribution?.bbb_class}</div>
                <div className="pt-2 border-t border-slate-200 space-y-1 text-[11px]">
                  <div className="flex justify-between">
                    <span>Plasma Protein Binding:</span>
                    <span className="font-mono text-slate-800">{adme?.distribution?.plasma_protein_binding_pct}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Fraction Unbound (fu):</span>
                    <span className="font-mono text-slate-800">{adme?.distribution?.fraction_unbound}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>VDss:</span>
                    <span className="font-mono text-slate-800">{adme?.distribution?.volume_of_distribution_L_kg} L/kg</span>
                  </div>
                </div>
              </div>

              {/* Metabolism (CYP450 Matrix) */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2 md:col-span-1">
                <div className="font-bold text-slate-800 text-sm flex items-center justify-between">
                  <span>3. CYP450 Matrix</span>
                  <span className="text-amber-400 font-mono">{adme?.metabolism?.inhibited_cyp_count} / 5</span>
                </div>
                <div className="grid grid-cols-5 gap-1 pt-1">
                  {adme?.metabolism?.cyp_matrix &&
                    Object.entries(adme.metabolism.cyp_matrix).map(([cyp, data]: [string, any]) => (
                      <div
                        key={cyp}
                        className={`p-1.5 rounded text-center border text-[10px] ${
                          data.inhibitor
                            ? 'bg-amber-950/60 border-amber-500/50 text-amber-300'
                            : 'bg-white border-slate-200 text-slate-500'
                        }`}
                      >
                        <div className="font-bold">{cyp.replace('CYP', '')}</div>
                        <div className="font-mono text-[9px]">{data.inhibitor ? 'Inh' : 'OK'}</div>
                      </div>
                    ))}
                </div>
                <div className="text-[11px] text-slate-500 pt-1">
                  Inhibits major drug-metabolizing Cytochromes: CYP1A2, CYP2C9, CYP2C19, CYP2D6, CYP3A4.
                </div>
              </div>

              {/* Excretion */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
                <div className="font-bold text-slate-800 text-sm flex items-center justify-between">
                  <span>4. Elimination</span>
                  <span className="text-emerald-400 font-mono">t½ ~ {adme?.excretion?.estimated_half_life_hours}h</span>
                </div>
                <div className="text-slate-500">{adme?.excretion?.clearance_category}</div>
                <div className="pt-2 border-t border-slate-200 space-y-1 text-[11px]">
                  <div className="flex justify-between">
                    <span>Total Clearance:</span>
                    <span className="font-mono text-slate-800">{adme?.excretion?.clearance_ml_min_kg} mL/min/kg</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Est. Dosing Interval:</span>
                    <span className="font-mono text-slate-800">
                      {adme?.excretion?.estimated_half_life_hours > 12 ? 'Once Daily (QD)' : 'Twice Daily (BID)'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Row: Matched Molecular Pair (MMP) Bioisostere Recommendations */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xl space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span>Bioisosteric Lead Optimisation Recommendations</span>
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-teal-950 text-teal-300 border border-teal-800">
                    {bioisosteres.length} Generated Analogs
                  </span>
                </h3>
                <p className="text-xs text-slate-500">
                  Automated bioisosteric transformations to improve target potency, enhance membrane permeability, or block metabolic liabilities.
                </p>
              </div>
            </div>

            {bioisosteres.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500 rounded-xl bg-slate-50/40 border border-slate-200">
                No automatic bioisosteric modifications matched for this specific scaffold.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {bioisosteres.map((analog: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-slate-50 border border-slate-200/90 space-y-3 hover:border-teal-500/40 transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-teal-300 text-xs">{analog.rule_name}</span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          analog.delta_mpo >= 0
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            : 'bg-slate-100 text-slate-500'
                        }`}
                      >
                        ΔMPO: {analog.delta_mpo >= 0 ? `+${analog.delta_mpo}` : analog.delta_mpo}
                      </span>
                    </div>

                    <p className="text-xs text-slate-700">{analog.description}</p>
                    <div className="text-[11px] text-slate-500 italic">"{analog.hypothesis}"</div>

                    <div className="p-2.5 rounded-lg bg-white border border-slate-200 font-mono text-[11px] text-teal-700 truncate">
                      {analog.analog_smiles}
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-[11px] text-slate-700 pt-1">
                      <div>
                        <span className="text-slate-500 block">pIC50:</span>
                        <span className="font-bold font-mono text-teal-700">
                          {analog.predicted_pIC50} ({analog.delta_pIC50 >= 0 ? `+${analog.delta_pIC50}` : analog.delta_pIC50})
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">cLogP:</span>
                        <span className="font-bold font-mono text-slate-800">
                          {analog.predicted_logp} ({analog.delta_logp >= 0 ? `+${analog.delta_logp}` : analog.delta_logp})
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 block">ADME / Safety:</span>
                        <span className="font-bold font-mono text-emerald-400">
                          {analog.adme_score} / {analog.safety_score}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-200/60">
                      <button
                        onClick={() => handleApplyAnalog(analog.analog_smiles, analog.rule_name)}
                        className="px-3 py-1.5 rounded-lg bg-teal-950/60 hover:bg-teal-900 border border-teal-700 text-teal-300 text-xs font-semibold transition-all"
                      >
                        ⚡ Load into Studio
                      </button>
                      <button
                        onClick={() => handleSaveToCandidates(analog.analog_smiles, `Analog: ${analog.rule_name}`, analog.predicted_pIC50)}
                        className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-700 border border-slate-200 text-slate-800 text-xs font-semibold transition-all"
                      >
                        💾 Save Candidate
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LeadOptimization;
