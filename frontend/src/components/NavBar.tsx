import React from 'react';
import { NavLink } from 'react-router-dom';

const NavBar: React.FC = () => {
  const links = [
    { to: '/', label: 'Clinical Cockpit', icon: '🏥' },
    { to: '/lab', label: '3D Molecular Lab & PyMOL', icon: '🧬' },
    { to: '/screening', label: 'Virtual Screening', icon: '🔬' },
    { to: '/lead-opt', label: 'Lead Optimisation', icon: '💊' },
    { to: '/discovery', label: 'Iterative Discovery', icon: '🔄' },
    { to: '/disease', label: 'Disease Intelligence', icon: '🎯' },
    { to: '/research', label: 'GARDE Medical Research', icon: '📋' },
  ];

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50 px-5 py-3 shadow-sm">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Medical Brand / Title */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-red-600 flex items-center justify-center text-white font-black text-xl shadow-sm border border-red-700">
            +
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg text-slate-900 tracking-tight">PROJECT GENESIS</span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200 font-mono">
                CLINICAL SUITE v2.0
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium">Hospital & Pharmacology Research Platform</p>
          </div>
        </div>

        {/* Clinical Navigation Links */}
        <nav className="flex flex-wrap items-center gap-1.5">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-md text-xs font-semibold tracking-normal transition-colors duration-150 flex items-center gap-1.5 ${
                  isActive
                    ? 'bg-teal-700 text-white shadow-sm border border-teal-800'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-transparent'
                }`
              }
            >
              <span>{link.icon}</span>
              <span>{link.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Clinical Workstation Status Indicators */}
        <div className="hidden lg:flex items-center gap-2 text-[11px] font-mono">
          <span className="inline-flex items-center px-2.5 py-1 rounded bg-teal-50 text-teal-800 border border-teal-200">
            <span className="w-2 h-2 rounded-full bg-teal-600 mr-1.5" />
            RTX 3060 CUDA
          </span>
          <span className="inline-flex items-center px-2.5 py-1 rounded bg-sky-50 text-sky-800 border border-sky-200">
            28T Compute
          </span>
        </div>
      </div>
    </header>
  );
};

export default NavBar;
