import React from 'react';
import type { ScanChunk } from '../../../types/scan-types';
import { STATUS_COLORS } from '../../../types/scan-types';

interface ScanHeatmapProps {
  chunks: ScanChunk[];
}

// The heatmap is generated using a dynamic number of columns so that Tailwind
// does not need to know the grid size ahead of time.
const ScanHeatmap: React.FC<ScanHeatmapProps> = ({ chunks }) => {
  const numCols = 16; // Or calculate based on container width
  return (
    <div className="bg-gray-800 rounded-lg shadow-lg p-4 h-full">
      <h2 className="text-xl font-bold text-white mb-4">Scan Heatmap</h2>
      <div className="grid gap-1.5" style={{ gridTemplateColumns: `repeat(${numCols}, minmax(0, 1fr))`}}>
        {chunks.map((chunk) => (
          <div
            key={chunk.id}
            title={`${chunk.targetRange} - ${chunk.status}`}
            className={`w-full aspect-square rounded ${
              STATUS_COLORS[chunk.status]
            } transition-colors duration-300 ease-in-out cursor-pointer hover:ring-2 hover:ring-offset-2 hover:ring-offset-gray-800 hover:ring-white`}
            onClick={() => alert(`Inspecting chunk: ${chunk.targetRange}`)}
          >
            {chunk.status === 'running' && (
              <div className="w-full h-full flex items-center justify-center">
                <div className="w-1.5 h-1.5 bg-white/50 rounded-full animate-pulse"></div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ScanHeatmap;
