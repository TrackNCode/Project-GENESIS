import React, { useEffect, useRef } from 'react';

declare global {
  interface Window {
    $3Dmol?: any;
  }
}

interface MolecularViewer3DProps {
  proteinPdb?: string;
  ligandPdb?: string;
  styleMode?: 'cartoon' | 'surface' | 'stick';
  height?: string;
}

const MolecularViewer3D: React.FC<MolecularViewer3DProps> = ({
  proteinPdb,
  ligandPdb,
  styleMode = 'cartoon',
  height = '420px',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current || !window.$3Dmol) return;

    // Clear previous viewer if any
    containerRef.current.innerHTML = '';

    const config = { backgroundColor: '#0d1117' };
    const viewer = window.$3Dmol.createViewer(containerRef.current, config);
    viewerRef.current = viewer;

    let hasModel = false;

    // 1. Add Protein Model if provided
    if (proteinPdb && proteinPdb.trim().length > 0) {
      viewer.addModel(proteinPdb, 'pdb');
      hasModel = true;

      if (styleMode === 'cartoon') {
        viewer.setStyle({ model: 0 }, { cartoon: { color: 'spectrum', opacity: 0.85 } });
      } else if (styleMode === 'surface') {
        viewer.setStyle({ model: 0 }, { cartoon: { color: '#4a5568' } });
        try {
          viewer.addSurface(window.$3Dmol.SurfaceType.VDW, { opacity: 0.5, color: '#38bdf8' });
        } catch (e) {
          // Fallback if surface computation is heavy
        }
      } else {
        viewer.setStyle({ model: 0 }, { line: { color: '#718096' } });
      }
    }

    // 2. Add Ligand Model if provided
    if (ligandPdb && ligandPdb.trim().length > 0) {
      const ligandModelIdx = proteinPdb ? 1 : 0;
      const format = (ligandPdb.includes('M  END') || ligandPdb.includes('V2000') || ligandPdb.includes('V3000')) ? 'mol' : 'pdb';
      viewer.addModel(ligandPdb, format);
      hasModel = true;

      viewer.setStyle(
        { model: ligandModelIdx },
        {
          stick: {
            colorscheme: 'greenCarbon',
            radius: 0.28,
          },
          sphere: {
            scale: 0.3,
            colorscheme: 'greenCarbon',
          },
        }
      );
    }

    if (hasModel) {
      viewer.zoomTo();
      viewer.render();
    }
  }, [proteinPdb, ligandPdb, styleMode]);

  return (
    <div style={{ position: 'relative', width: '100%', height }}>
      <div
        ref={containerRef}
        style={{
          width: '100%',
          height: '100%',
          position: 'relative',
          borderRadius: '8px',
          overflow: 'hidden',
          border: '1px solid #30363d',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: '8px',
          right: '8px',
          fontSize: '11px',
          color: '#8b949e',
          backgroundColor: '#161b22cc',
          padding: '2px 8px',
          borderRadius: '4px',
          pointerEvents: 'none',
        }}
      >
        Left Click: Rotate | Scroll: Zoom | Right Click: Pan
      </div>
    </div>
  );
};

export default MolecularViewer3D;
