import React, { useState } from 'react';
import MolecularLab from '@/pages/MolecularLab';
import ScreeningConsole from '@/pages/ScreeningConsole';
import LeadOptimization from '@/pages/LeadOptimization';
import IterativeDiscovery from '@/pages/IterativeDiscovery';
import DiseaseIntelligence from '@/pages/DiseaseIntelligence';
import CreateProjectForm from '@/components/CreateProjectForm';
import ProjectList from '@/components/ProjectList';

type PortalTab = 'docking' | 'screening' | 'lead-opt' | 'discovery' | 'disease' | 'projects';

interface TabDefinition {
  id: PortalTab;
  title: string;
  badge: string;
  icon: string;
  description: string;
}

const TABS: TabDefinition[] = [
  {
    id: 'docking',
    title: '3D Molecular Docking',
    badge: 'AutoDock Vina + PyMOL',
    icon: '🧬',
    description: '3D conformational search, WebGL interactive viewer, binding energy (ΔG), and PyMOL ray-tracing.',
  },
  {
    id: 'discovery',
    title: 'Trial Discovery Loop',
    badge: 'Closed-Loop Engine',
    icon: '🔄',
    description: 'Autonomous 9-stage multi-round loop: REINVENT 4 RL → GNINA 3D-CNN → Chemprop Evidential D-MPNN.',
  },
  {
    id: 'screening',
    title: 'Virtual Screening',
    badge: 'High-Throughput Assays',
    icon: '🔬',
    description: 'Batch screen FDA Diversity and Antiviral libraries against 6LU7, 1ERE, 1IEP, 1M17, 1CX2.',
  },
  {
    id: 'lead-opt',
    title: 'Lead Optimisation',
    badge: 'QSAR & 4-Pillar ADME',
    icon: '💊',
    description: 'MPO multi-objective desirability, target-specific pIC50, cardiac toxicity, and bioisosteric MMP.',
  },
  {
    id: 'disease',
    title: 'Target Intelligence',
    badge: 'Open Targets & ChEMBL',
    icon: '🎯',
    description: 'Target tractability assessment, disease association score matrices, and TDC benchmark ingestion.',
  },
  {
    id: 'projects',
    title: 'Clinical Registry',
    badge: 'Candidate Records',
    icon: '📋',
    description: 'Campaign registries, candidates database, and project persistence.',
  },
];

const CommandCentre: React.FC = () => {
  const [activeTab, setActiveTab] = useState<PortalTab>('docking');

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Clinical Header Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded bg-red-50 text-red-700 text-[11px] font-mono font-bold border border-red-200">
                CLINICAL PHARMACOLOGY SUITE
              </span>
              <span className="text-slate-500 text-xs">• 10 Medical & Biophysical Engines Validated</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
              Clinical Research & Drug Discovery Workstation
            </h1>
            <p className="text-slate-600 text-sm mt-1 max-w-3xl">
              Unified hospital-grade platform for target-specific small molecule modeling, 3D biophysical docking, pharmacokinetic ADMET screening, and closed-loop lead discovery.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="bg-teal-50 border border-teal-200 rounded-lg px-4 py-2 text-center">
              <span className="text-[10px] text-teal-800 uppercase font-semibold block">Compute Accelerator</span>
              <span className="text-xs font-bold text-teal-900 font-mono flex items-center gap-1.5 justify-center">
                <span className="w-2 h-2 rounded-full bg-teal-600" />
                RTX 3060 (12GB)
              </span>
            </div>
            <div className="bg-sky-50 border border-sky-200 rounded-lg px-4 py-2 text-center">
              <span className="text-[10px] text-sky-800 uppercase font-semibold block">Processing Cores</span>
              <span className="text-xs font-bold text-sky-900 font-mono">i7-14700KF (28T)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Selector Tabs (Medical Pill Cards) */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2.5">
        {TABS.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`p-3.5 rounded-lg border text-left transition-all duration-150 flex flex-col justify-between ${
                isActive
                  ? 'bg-teal-700 text-white border-teal-800 shadow-sm'
                  : 'bg-white border-slate-200 hover:border-sky-300 hover:bg-sky-50/40 text-slate-700 shadow-sm'
              }`}
            >
              <div className="flex items-center justify-between w-full mb-1.5">
                <span className="text-xl">{tab.icon}</span>
                <span
                  className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-bold ${
                    isActive ? 'bg-teal-800 text-teal-100' : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {tab.id.toUpperCase()}
                </span>
              </div>
              <div>
                <h3 className={`text-xs font-bold ${isActive ? 'text-white' : 'text-slate-900'}`}>
                  {tab.title}
                </h3>
                <p className={`text-[10px] mt-0.5 line-clamp-1 ${isActive ? 'text-teal-100' : 'text-slate-500'}`}>
                  {tab.badge}
                </p>
              </div>
            </button>
          );
        })}
      </div>

      {/* Active Module Clinical Banner */}
      <div className="transition-all duration-200">
        {activeTab === 'docking' && (
          <div className="space-y-4">
            <div className="bg-sky-50 border border-sky-200 rounded-lg px-5 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">🧬</span>
                <span className="text-sm font-bold text-sky-900">Module: 3D Molecular Docking & PyMOL Visualisation</span>
              </div>
              <span className="text-xs text-sky-700 font-mono font-medium">AutoDock Vina 1.2.7 • 3Dmol.js WebGL • PyMOL 3.1.0</span>
            </div>
            <MolecularLab />
          </div>
        )}

        {activeTab === 'discovery' && (
          <div className="space-y-4">
            <div className="bg-sky-50 border border-sky-200 rounded-lg px-5 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">🔄</span>
                <span className="text-sm font-bold text-sky-900">Module: Closed-Loop Trial Discovery & Lineage Studio</span>
              </div>
              <span className="text-xs text-sky-700 font-mono font-medium">REINVENT 4 • GNINA 3D-CNN • Chemprop Evidential D-MPNN</span>
            </div>
            <IterativeDiscovery />
          </div>
        )}

        {activeTab === 'screening' && (
          <div className="space-y-4">
            <div className="bg-sky-50 border border-sky-200 rounded-lg px-5 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">🔬</span>
                <span className="text-sm font-bold text-sky-900">Module: High-Throughput Virtual Screening Console</span>
              </div>
              <span className="text-xs text-sky-700 font-mono font-medium">Multithreaded CPU Conformational Screening</span>
            </div>
            <ScreeningConsole />
          </div>
        )}

        {activeTab === 'lead-opt' && (
          <div className="space-y-4">
            <div className="bg-sky-50 border border-sky-200 rounded-lg px-5 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">💊</span>
                <span className="text-sm font-bold text-sky-900">Module: Lead Optimisation & Pharmacokinetics Studio</span>
              </div>
              <span className="text-xs text-sky-700 font-mono font-medium">Multi-Parameter Desirability (MPO) • 4-Pillar ADME</span>
            </div>
            <LeadOptimization />
          </div>
        )}

        {activeTab === 'disease' && (
          <div className="space-y-4">
            <div className="bg-sky-50 border border-sky-200 rounded-lg px-5 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">🎯</span>
                <span className="text-sm font-bold text-sky-900">Module: Target Intelligence & Disease Association Hub</span>
              </div>
              <span className="text-xs text-sky-700 font-mono font-medium">Open Targets Platform • ChEMBL 34 • TDC Benchmarks</span>
            </div>
            <DiseaseIntelligence />
          </div>
        )}

        {activeTab === 'projects' && (
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
            <div className="border-b border-slate-200 pb-4">
              <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                <span>📋</span> Clinical Project Registry & Candidate Records
              </h2>
              <p className="text-xs text-slate-500 mt-1">Manage institutional research records and inspect persisted discovery candidates.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-5">
                <h3 className="text-xs font-bold text-teal-800 uppercase tracking-wider mb-3">Register New Trial / Study</h3>
                <CreateProjectForm />
              </div>
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-5">
                <h3 className="text-xs font-bold text-teal-800 uppercase tracking-wider mb-3">Active Registry Studies</h3>
                <ProjectList />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CommandCentre;
