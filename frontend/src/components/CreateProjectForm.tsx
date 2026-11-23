import React, { useState } from 'react';

const CreateProjectForm: React.FC = () => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState<string>('');
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch('http://127.0.0.1:8000/projects/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setStatus(`Created project ${data.id}`);
    } catch (err: any) {
      setStatus(`Error: ${err.message}`);
    }
  };
  return (
    <form onSubmit={handleSubmit} className="mb-4">
      <div className="mb-2">
        <label className="block mb-1">Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          className="p-1 border rounded w-full"
        />
      </div>
      <div className="mb-2">
        <label className="block mb-1">Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="p-1 border rounded w-full"
        />
      </div>
      <button type="submit" className="bg-cyan-600 text-white px-3 py-1 rounded">
        Create Project
      </button>
      {status && <p className="mt-2">{status}</p>}
    </form>
  );
};

export default CreateProjectForm;
