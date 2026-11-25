import React, { useState } from 'react';
import { API_BASE } from '@/api/config';

const CreateProjectForm: React.FC = () => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState<string>('');
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/projects/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setStatus(`Registered study record ID #${data.id}`);
      setName('');
      setDescription('');
    } catch (err: any) {
      setStatus(`Error: ${err.message}`);
    }
  };
  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label className="block text-xs font-semibold text-slate-700 mb-1">Study / Trial Title</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Mpro Protease Inhibitor Lead Optimization"
          required
          className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-teal-600 focus:border-teal-600"
        />
      </div>
      <div>
        <label className="block text-xs font-semibold text-slate-700 mb-1">Clinical Protocol & Objectives</label>
        <textarea
          rows={2}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Outline primary therapeutic target, lead series, and pharmacology criteria..."
          className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-1 focus:ring-teal-600 focus:border-teal-600"
        />
      </div>
      <button
        type="submit"
        className="w-full bg-teal-700 hover:bg-teal-800 text-white font-semibold py-2 px-4 rounded-lg text-xs shadow-sm transition-colors"
      >
        Register Clinical Study Record
      </button>
      {status && (
        <p className="text-xs font-semibold text-teal-800 bg-teal-50 border border-teal-200 p-2 rounded">
          {status}
        </p>
      )}
    </form>
  );
};

export default CreateProjectForm;
