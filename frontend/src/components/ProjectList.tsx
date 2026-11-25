import React, { useEffect, useState } from 'react';
import { API_BASE } from '@/api/config';

interface Project {
  id: number;
  name: string;
  description?: string;
  created_at: string;
}

const ProjectList: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/projects/`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setProjects(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <p className="text-xs text-slate-500 font-mono py-4">Querying institutional database...</p>;
  if (error) return <p className="text-xs text-red-600 bg-red-50 border border-red-200 p-2 rounded">Error loading studies: {error}</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">Registry Records</span>
        <span className="text-[10px] font-mono bg-sky-50 text-sky-700 border border-sky-200 px-1.5 py-0.5 rounded font-bold">
          {projects.length} Registered
        </span>
      </div>
      {projects.length === 0 ? (
        <p className="text-xs text-slate-400 py-3 text-center bg-white border border-slate-200 rounded-lg">
          No clinical studies recorded yet.
        </p>
      ) : (
        <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
          {projects.map((p) => (
            <div key={p.id} className="p-2.5 bg-white border border-slate-200 rounded-lg text-xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900">{p.name}</span>
                <span className="text-[10px] text-slate-400 font-mono">
                  {new Date(p.created_at).toLocaleDateString()}
                </span>
              </div>
              {p.description && <p className="text-slate-600 text-[11px] leading-relaxed">{p.description}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProjectList;
