import React from 'react';
import { ScanChunk, STATUS_COLORS } from '../../../types/scan-types';

interface ScanHeatmapProps {
  chunks: ScanChunk[];
}

const ScanHeatmap: React.FC<ScanHeatmapProps> = ({ chunks }) => {
  return (
    <div className="bg-gray-800 rounded-lg shadow-lg p-4 h-full">
      <h2 className="text-xl font-bold text-white mb-4">Scan Heatmap</h2>
      <div className="grid grid-cols-16 gap-1.5">
        {chunks.map((chunk) => (
          <div
            key={chunk.id}
            title={`${chunk.targetRange} - ${chunk.status}`}
            className={`w-full aspect-square rounded ${
              STATUS_COLORS[chunk.status]
            } transition-colors duration-300 ease-in-out cursor-pointer hover:ring-2 hover:ring-offset-2 hover:ring-offset-gray-800 hover:ring-white`}
            onClick={() => alert(`Inspecting chunk: ${chunk.targetRange}`)}
          >
             {/* Small dot for running scans to add some animation */}
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

// We need to tell Tailwind to generate the grid-cols-16 class.
// We can do this by adding it to the safelist in tailwind.config.js,
// or by just including a hidden div with the class in our app.
// For now, I will add a note to do this later.
// A better way is to generate the columns dynamically with style attribute.
// Let's go with that.

const ScanHeatmapDynamic: React.FC<ScanHeatmapProps> = ({ chunks }) => {
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

export default ScanHeatmapDynamic;
