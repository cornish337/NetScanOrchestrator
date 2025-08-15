import React from 'react';
import { ScanChunk } from '../../types/api';

interface MiniMapProps {
  chunks: ScanChunk[];
  chunkColor: Record<ScanChunk['status'], string>;
}

const MiniMap: React.FC<MiniMapProps> = ({ chunks, chunkColor }) => {
  if (!chunks || chunks.length === 0) {
    return null;
  }

  // Define a smaller size for the mini-map grid cells
  const cellSize = 4; // 4px cells
  const numColumns = 32; // Same as the main map for consistency

  return (
    <div style={{
      border: '1px solid #ccc',
      padding: '5px',
      marginTop: '10px',
      backgroundColor: '#f9f9f9',
    }}>
      <h4>Mini-map</h4>
      <div style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${numColumns}, ${cellSize}px)`,
        gap: '1px'
      }}>
        {chunks.map(chunk => (
          <div
            key={`mini-${chunk.id}`}
            title={`${chunk.id}: ${chunk.status}`}
            style={{
              width: `${cellSize}px`,
              height: `${cellSize}px`,
              backgroundColor: chunkColor[chunk.status],
            }}
          />
        ))}
      </div>
    </div>
  );
};

export { MiniMap };
