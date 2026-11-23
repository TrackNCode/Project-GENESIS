import React from 'react';
import { NavLink } from 'react-router-dom';

const NavBar: React.FC = () => {
  const links = [
    { to: '/', label: 'Unified Portal', icon: '🌌' },
    { to: '/lab', label: '3D Molecular Lab & PyMOL', icon: '🧬' },
    { to: '/screening', label: 'Virtual Screening', icon: '🔬' },
    { to: '/lead-opt', label: 'Lead Optimisation', icon: '⚡' },
    { to: '/discovery', label: 'Iterative Discovery', icon: '🔄' },
    { to: '/disease', label: 'Disease Intelligence', icon: '🎯' },
    { to: '/research', label: 'GARDE Research', icon: '📚' },
  ];

  return (
    <header className="bg-gray-900/95 border-b border-indigo-900/50 backdrop-blur-md sticky top-0 z-50 px-4 py-3 shadow-xl">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Brand / Title */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 via-indigo-600 to-purple-600 flex items-center justify-center text-white font-black text-lg shadow-lg shadow-cyan-500/20 border border-cyan-400/30">
            G
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg text-white tracking-wider">PROJECT GENESIS</span>
              <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                v2.0 AI Scientific
              </span>
            </div>
            <p className="text-[11px] text-gray-400">Autonomous Drug Discovery & Biomolecular Simulation</p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex flex-wrap items-center gap-1.5">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all duration-150 flex items-center gap-1.5 ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 border border-indigo-400/50'
                    : 'text-gray-300 hover:text-white hover:bg-gray-800/80 border border-transparent'
                }`
              }
            >
              <span>{link.icon}</span>
              <span>{link.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Hardware Status Badges */}
        <div className="hidden lg:flex items-center gap-2 text-[11px] font-mono">
          <span className="inline-flex items-center px-2.5 py-1 rounded-md bg-emerald-950/60 text-emerald-400 border border-emerald-800/60">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse" />
            RTX 3060 CUDA
          </span>
          <span className="inline-flex items-center px-2.5 py-1 rounded-md bg-indigo-950/60 text-indigo-300 border border-indigo-800/60">
            28T CPU
          </span>
        </div>
      </div>
    </header>
  );
};

export default NavBar;
