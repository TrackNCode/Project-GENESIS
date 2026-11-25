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

  if (loading) return <p>Loading projects…</p>;
  if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;

  return (
    <div>
      <h3 className="text-xl font-semibold mb-2" style={{ color: '#00ffff' }}>Projects</h3>
      <ul className="list-disc list-inside">
        {projects.map((p) => (
          <li key={p.id}>
            <strong>{p.name}</strong> – {p.description || 'No description'} (Created: {new Date(p.created_at).toLocaleDateString()})
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ProjectList;
