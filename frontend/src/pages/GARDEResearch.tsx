import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';

interface HypothesisCard {
  id: string;
  category: 'bioisostere' | 'metabolic' | 'physicochemical' | 'resistance';
  target: string;
  title: string;
  rationale: string;
  transformation: string;
  evidence: string;
  confidence: number;
  status: 'Formulated' | 'In Silico Testing' | 'Validated';
}

const PRESET_HYPOTHESES: HypothesisCard[] = [
  {
    id: 'HYP-001',
    category: 'resistance',
    target: '1IEP (Abl Kinase - CML)',
    title: 'Bypass T315I Gatekeeper Resistance via Rigid Ethynyl Linker',
    rationale: 'Isoleucine 315 point mutation introduces steric clash with standard phenyl-amide scaffold in Imatinib. Introducing a linear alkyne linker maintains hinge binding without steric repulsion.',
    transformation: 'Rigid Acetylene (Alkyne) Spacer Insertion',
    evidence: 'Crystal structure alignment (PDB 1IEP vs 3OXZ) demonstrates 3.2 Å clearance in mutated ATP-pocket.',
    confidence: 94,
    status: 'Validated',
  },
  {
    id: 'HYP-002',
    category: 'bioisostere',
    target: '6LU7 (SARS-CoV-2 Mpro)',
    title: 'Carboxylic Acid to 1,2,3,4-Tetrazole Bioisosteric Switch',
    rationale: 'Carboxylic acid groups undergo rapid Phase-II glucuronidation and suffer poor cellular permeability due to physiologic ionization. Tetrazole retains planar H-bond acidity while drastically improving lipophilicity.',
    transformation: 'R-COOH → R-c1nnn[nH]1',
    evidence: 'Maintains catalytic Cys145-His41 dyad hydrogen bonding while reducing negative charge polar surface area.',
    confidence: 89,
    status: 'In Silico Testing',
  },
  {
    id: 'HYP-003',
    category: 'metabolic',
    target: '1M17 (EGFR Kinase - NSCLC)',
    title: 'Para-Fluorination Metabolic Shield for Cytochrome P450 3A4',
    rationale: 'Exposed electron-rich phenyl rings represent metabolic hot-spots for hepatic oxidation. Strategic fluorine atom placement blocks aromatic hydroxylation without pocket distortion.',
    transformation: 'Aromatic Phenyl → 4-Fluorophenyl',
    evidence: 'In silico CYP3A4 metabolic prediction scores indicate a 4.2x increase in metabolic half-life (t1/2).',
    confidence: 91,
    status: 'Formulated',
  },
  {
    id: 'HYP-004',
    category: 'physicochemical',
    target: '1CX2 (COX-2 - Anti-inflammatory)',
    title: 'Pyridine Nitrogen Walk for Solubility and Clearance Tuning',
    rationale: 'High lipophilicity (cLogP > 4.5) leads to plasma protein binding and poor aqueous formulation. Inserting an endocyclic nitrogen lowers cLogP by ~1.0 with negligible affinity penalty.',
    transformation: 'Aromatic CH → Endocyclic N',
    evidence: 'Calculated logS improvement from -5.2 to -3.8 mol/L while preserving selective Arg513 pocket salt bridge.',
    confidence: 86,
    status: 'Validated',
  },
];

const GARDEResearch: React.FC = () => {
  const [selectedTarget, setSelectedTarget] = useState('6LU7');
  const [activeFilter, setActiveFilter] = useState<'all' | 'bioisostere' | 'metabolic' | 'physicochemical' | 'resistance'>('all');
  const [generatedCount, setGeneratedCount] = useState(4);

  const filteredHypotheses = activeFilter === 'all'
    ? PRESET_HYPOTHESES
    : PRESET_HYPOTHESES.filter((h) => h.category === activeFilter);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header Medical Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded bg-red-50 text-red-700 text-[11px] font-mono font-bold border border-red-200">
                AUTONOMOUS MEDICAL DISCOVERY
              </span>
              <span className="text-slate-500 text-xs">• GARDE Engine (Milestone Phase 9)</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
              GARDE: Generative Autonomous Research & Discovery Engine
            </h1>
            <p className="text-slate-600 text-sm mt-1 max-w-3xl">
              Acting as an autonomous medicinal chemist, GARDE traverses scientific knowledge graphs, detects unexplored therapeutic white spaces, formulates mechanistic hypotheses, and scripts in-silico validation experiments.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="bg-teal-50 border border-teal-200 rounded-lg px-4 py-2 text-center">
              <span className="text-[10px] text-teal-800 uppercase font-semibold block">Hypotheses Validated</span>
              <span className="text-lg font-black text-teal-900 font-mono">14 / 16</span>
            </div>
            <div className="bg-sky-50 border border-sky-200 rounded-lg px-4 py-2 text-center">
              <span className="text-[10px] text-sky-800 uppercase font-semibold block">Active Targets</span>
              <span className="text-lg font-black text-sky-900 font-mono">5 PDB Targets</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4-Pillar Autonomous Research Architecture */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
          <div className="w-7 h-7 rounded bg-red-100 text-red-700 flex items-center justify-center font-bold text-sm mb-2">
            1
          </div>
          <h3 className="text-xs font-bold text-slate-900">Literature & Gap Ingestion</h3>
          <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
            Continuously queries PubMed, ChEMBL 34, and Open Targets to locate resistance mutations and toxicity bottlenecks.
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
          <div className="w-7 h-7 rounded bg-teal-100 text-teal-700 flex items-center justify-center font-bold text-sm mb-2">
            2
          </div>
          <h3 className="text-xs font-bold text-slate-900">Mechanistic Hypothesis AI</h3>
          <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
            Applies rule-based medicinal chemistry (bioisosteric shifts, metabolic blocking, nitrogen walks) to propose chemical alterations.
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
          <div className="w-7 h-7 rounded bg-sky-100 text-sky-700 flex items-center justify-center font-bold text-sm mb-2">
            3
          </div>
          <h3 className="text-xs font-bold text-slate-900">In Silico Experiment Design</h3>
          <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
            Automatically bounds active site grids, builds 3D conformers with MMFF94, and defines multi-objective criteria.
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
          <div className="w-7 h-7 rounded bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-sm mb-2">
            4
          </div>
          <h3 className="text-xs font-bold text-slate-900">Closed-Loop Validation</h3>
          <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
            Feeds docking outcomes into reinforcement learning loops (REINVENT 4) to iteratively refine candidate lineage.
          </p>
        </div>
      </div>

      {/* Filter Bar & Target Selector */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wide mr-2">Hypothesis Type:</span>
          {(['all', 'resistance', 'bioisostere', 'metabolic', 'physicochemical'] as const).map((filter) => (
            <button
              key={filter}
              onClick={() => setActiveFilter(filter)}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold capitalize transition-colors ${
                activeFilter === filter
                  ? 'bg-teal-700 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {filter}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-slate-600">Therapeutic Focus:</span>
          <select
            value={selectedTarget}
            onChange={(e) => setSelectedTarget(e.target.value)}
            className="text-xs bg-slate-50 border border-slate-300 rounded-md px-3 py-1.5 text-slate-800 font-semibold focus:outline-none focus:ring-1 focus:ring-teal-600"
          >
            <option value="6LU7">SARS-CoV-2 Mpro (6LU7)</option>
            <option value="1IEP">Abl Kinase Domain (1IEP)</option>
            <option value="1M17">EGFR Kinase (1M17)</option>
            <option value="1CX2">COX-2 Cyclooxygenase (1CX2)</option>
            <option value="1ERE">Estrogen Receptor Alpha (1ERE)</option>
          </select>
        </div>
      </div>

      {/* Formulated Hypothesis Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredHypotheses.map((hyp) => (
          <div key={hyp.id} className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4 hover:border-slate-300 transition-all">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                    {hyp.id}
                  </span>
                  <span className="text-xs font-bold text-slate-500 font-mono">{hyp.target}</span>
                </div>
                <h3 className="text-sm font-bold text-slate-900 leading-snug">{hyp.title}</h3>
              </div>
              <span
                className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                  hyp.status === 'Validated'
                    ? 'bg-teal-50 text-teal-800 border border-teal-200'
                    : hyp.status === 'In Silico Testing'
                    ? 'bg-sky-50 text-sky-800 border border-sky-200'
                    : 'bg-amber-50 text-amber-800 border border-amber-200'
                }`}
              >
                {hyp.status}
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">{hyp.rationale}</p>

            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-2">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-500 font-semibold">Chemical Transformation:</span>
                <span className="font-mono font-bold text-red-700">{hyp.transformation}</span>
              </div>
              <div className="text-[11px] text-slate-600">
                <span className="text-slate-500 font-semibold block mb-0.5">Structural & Assay Evidence:</span>
                {hyp.evidence}
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
              <div className="flex items-center gap-2">
                <span className="text-slate-500">Confidence Metric:</span>
                <div className="w-20 bg-slate-200 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-teal-600 h-full rounded-full"
                    style={{ width: `${hyp.confidence}%` }}
                  />
                </div>
                <span className="font-mono font-bold text-slate-800">{hyp.confidence}%</span>
              </div>

              <NavLink
                to="/lab"
                className="inline-flex items-center gap-1 font-bold text-teal-700 hover:text-teal-900 text-xs"
              >
                Simulate in 3D Lab →
              </NavLink>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default GARDEResearch;
