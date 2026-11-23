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
    title: '3D Molecular Docking & PyMOL',
    badge: 'AutoDock Vina + 3Dmol + PyMOL',
    icon: '🧬',
    description: '3D conformational search, WebGL interactive viewer, binding energy (ΔG), and PyMOL ray-tracing.',
  },
  {
    id: 'discovery',
    title: 'Iterative Discovery Loop',
    badge: 'Milestone 5 & 6',
    icon: '🔄',
    description: 'Autonomous 9-stage multi-round loop: REINVENT 4 RL → GNINA 3D-CNN → Chemprop Evidential D-MPNN.',
  },
  {
    id: 'screening',
    title: 'Virtual Screening Console',
    badge: 'High-Throughput Vina',
    icon: '🔬',
    description: 'Batch screen FDA Diversity and Antiviral libraries against 6LU7, 1ERE, 1IEP, 1M17, 1CX2.',
  },
  {
    id: 'lead-opt',
    title: 'Lead Optimisation Studio',
    badge: 'QSAR & 4-Pillar ADME',
    icon: '⚡',
    description: 'MPO multi-objective desirability, target-specific pIC50, cardiac toxicity, and bioisosteric MMP.',
  },
  {
    id: 'disease',
    title: 'Disease Intelligence',
    badge: 'Open Targets & ChEMBL',
    icon: '🎯',
    description: 'Target tractability assessment, disease association score matrices, and TDC benchmark ingestion.',
  },
  {
    id: 'projects',
    title: 'Project Registry',
    badge: 'Database & Lineage',
    icon: '📁',
    description: 'Campaign registries, candidates database, and project persistence.',
  },
];

const CommandCentre: React.FC = () => {
  const [activeTab, setActiveTab] = useState<PortalTab>('docking');

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Hero Cockpit Banner */}
      <div className="bg-gradient-to-r from-gray-900 via-indigo-950 to-gray-900 border border-indigo-700/50 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 text-[11px] font-mono font-bold border border-cyan-500/40">
                UNIFIED AI SCIENTIFIC PORTAL
              </span>
              <span className="text-gray-400 text-xs">• 10 Scientific Engines Integrated</span>
            </div>
            <h1 className="text-3xl font-black text-white tracking-wide">
              Project GENESIS Command Cockpit
            </h1>
            <p className="text-gray-300 text-sm mt-1 max-w-3xl">
              All platform capabilities are unified in this single portal. Switch between 3D molecular docking, high-throughput virtual screening, QSAR/ADME profiling, and autonomous closed-loop discovery below.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="bg-gray-900/80 border border-gray-700/80 rounded-xl px-4 py-2.5 text-center">
              <span className="text-[10px] text-gray-400 uppercase font-semibold block">GPU Device</span>
              <span className="text-xs font-bold text-emerald-400 font-mono flex items-center gap-1.5 justify-center">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                RTX 3060 (12GB)
              </span>
            </div>
            <div className="bg-gray-900/80 border border-gray-700/80 rounded-xl px-4 py-2.5 text-center">
              <span className="text-[10px] text-gray-400 uppercase font-semibold block">CPU Threads</span>
              <span className="text-xs font-bold text-indigo-300 font-mono">i7-14700KF (28T)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Selector Tabs (Single Portal Switching) */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2.5">
        {TABS.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`p-3.5 rounded-xl border text-left transition-all duration-200 flex flex-col justify-between ${
                isActive
                  ? 'bg-gradient-to-b from-indigo-900/90 to-indigo-950 border-cyan-400 shadow-lg shadow-cyan-500/20 ring-1 ring-cyan-400/50'
                  : 'bg-gray-900/80 border-gray-800 hover:border-gray-700 hover:bg-gray-800/60'
              }`}
            >
              <div className="flex items-center justify-between w-full mb-1.5">
                <span className="text-2xl">{tab.icon}</span>
                <span
                  className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                    isActive ? 'bg-cyan-400 text-gray-950 font-bold' : 'bg-gray-800 text-gray-400'
                  }`}
                >
                  {tab.id.toUpperCase()}
                </span>
              </div>
              <div>
                <h3 className={`text-xs font-bold ${isActive ? 'text-white' : 'text-gray-300'}`}>
                  {tab.title}
                </h3>
                <p className="text-[10px] text-gray-400 mt-0.5 line-clamp-1">{tab.badge}</p>
              </div>
            </button>
          );
        })}
      </div>

      {/* Embedded Feature Workstation (Single Portal View) */}
      <div className="transition-all duration-300">
        {activeTab === 'docking' && (
          <div className="space-y-4">
            <div className="bg-indigo-950/40 border border-indigo-700/50 rounded-xl px-5 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xl">🧬</span>
                <span className="text-sm font-bold text-white">Active Module: 3D Molecular Docking & PyMOL Visualisation Engine</span>
              </div>
              <span className="text-xs text-cyan-300 font-mono">AutoDock Vina 1.2.7 • 3Dmol.js WebGL • PyMOL 3.1.0</span>
            </div>
            <MolecularLab />
          </div>
        )}

        {activeTab === 'discovery' && (
          <div className="space-y-4">
            <div className="bg-indigo-950/40 border border-indigo-700/50 rounded-xl px-5 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xl">🔄</span>
                <span className="text-sm font-bold text-white">Active Module: Closed-Loop Iterative Discovery & Lineage Studio</span>
              </div>
              <span className="text-xs text-cyan-300 font-mono">REINVENT 4 • GNINA 3D-CNN • Chemprop Evidential D-MPNN</span>
            </div>
            <IterativeDiscovery />
          </div>
        )}

        {activeTab === 'screening' && (
          <div className="space-y-4">
            <div className="bg-indigo-950/40 border border-indigo-700/50 rounded-xl px-5 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xl">🔬</span>
                <span className="text-sm font-bold text-white">Active Module: High-Throughput Virtual Screening Console</span>
              </div>
              <span className="text-xs text-cyan-300 font-mono">Multithreaded CPU Conformational Screening</span>
            </div>
            <ScreeningConsole />
          </div>
        )}

        {activeTab === 'lead-opt' && (
          <div className="space-y-4">
            <div className="bg-indigo-950/40 border border-indigo-700/50 rounded-xl px-5 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xl">⚡</span>
                <span className="text-sm font-bold text-white">Active Module: Lead Optimisation & AI Prediction Studio</span>
              </div>
              <span className="text-xs text-cyan-300 font-mono">Multi-Parameter Desirability (MPO) • 4-Pillar ADME</span>
            </div>
            <LeadOptimization />
          </div>
        )}

        {activeTab === 'disease' && (
          <div className="space-y-4">
            <div className="bg-indigo-950/40 border border-indigo-700/50 rounded-xl px-5 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xl">🎯</span>
                <span className="text-sm font-bold text-white">Active Module: Disease Intelligence & Ingestion Hub</span>
              </div>
              <span className="text-xs text-cyan-300 font-mono">Open Targets Platform • ChEMBL 34 • TDC Benchmarks</span>
            </div>
            <DiseaseIntelligence />
          </div>
        )}

        {activeTab === 'projects' && (
          <div className="bg-gray-900/90 border border-gray-800 rounded-2xl p-6 shadow-xl space-y-6">
            <div className="border-b border-gray-800 pb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <span>📁</span> Project Registry & Candidate Storage
              </h2>
              <p className="text-xs text-gray-400 mt-1">Manage project records and inspect persisted discovery candidates.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-5">
                <h3 className="text-sm font-bold text-cyan-300 uppercase tracking-wider mb-3">Create New Project</h3>
                <CreateProjectForm />
              </div>
              <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-5">
                <h3 className="text-sm font-bold text-cyan-300 uppercase tracking-wider mb-3">Existing Projects</h3>
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
