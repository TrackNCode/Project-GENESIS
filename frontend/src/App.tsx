import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NavBar from '@/components/NavBar';
import CommandCentre from '@/pages/CommandCentre';
import DiseaseIntelligence from '@/pages/DiseaseIntelligence';
import MolecularLab from '@/pages/MolecularLab';
import ScreeningConsole from '@/pages/ScreeningConsole';
import LeadOptimization from '@/pages/LeadOptimization';
import IterativeDiscovery from '@/pages/IterativeDiscovery';
import GARDEResearch from '@/pages/GARDEResearch';

function App() {
  return (
    <Router>
      <NavBar />
      <div className="p-4">
        <Routes>
          <Route path="/" element={<CommandCentre />} />
          <Route path="/disease" element={<DiseaseIntelligence />} />
          <Route path="/lab" element={<MolecularLab />} />
          <Route path="/screening" element={<ScreeningConsole />} />
          <Route path="/lead-opt" element={<LeadOptimization />} />
          <Route path="/discovery" element={<IterativeDiscovery />} />
          <Route path="/research" element={<GARDEResearch />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
