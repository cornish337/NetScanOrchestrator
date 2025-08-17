import React from 'react';
import type { ScanChunk, ScanStatus } from '../../../types/scan-types';
import { STATUS_COLORS, STATUS_TEXT_COLORS } from '../../../types/scan-types';
import { RefreshCw, X } from 'lucide-react';

interface ScanChunkTableProps {
  chunks: ScanChunk[];
}

const StatusBadge: React.FC<{ status: ScanStatus }> = ({ status }) => (
  <div className="flex items-center">
    <div className={`w-2.5 h-2.5 rounded-full mr-2 ${STATUS_COLORS[status]}`} />
    <span className={`capitalize font-medium ${STATUS_TEXT_COLORS[status]}`}>{status}</span>
  </div>
);

const ProgressBar: React.FC<{ progress: number }> = ({ progress }) => (
  <div className="w-full bg-gray-700 rounded-full h-2.5">
    <div
      className="bg-blue-500 h-2.5 rounded-full"
      style={{ width: `${progress}%` }}
    ></div>
  </div>
);

const ActionButton: React.FC<{ onClick: () => void; children: React.ReactNode; title: string }> = ({ onClick, children, title }) => (
    <button onClick={onClick} title={title} className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-full transition-colors">
        {children}
    </button>
)

const ScanChunkTable: React.FC<ScanChunkTableProps> = ({ chunks }) => {
  return (
    <div className="bg-gray-800 rounded-lg shadow-lg overflow-hidden">
      <div className="p-4">
        <h2 className="text-xl font-bold text-white">Scan Chunks</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm text-left text-gray-300">
          <thead className="bg-gray-700 text-xs text-gray-400 uppercase tracking-wider">
            <tr>
              <th scope="col" className="px-6 py-3">Status</th>
              <th scope="col" className="px-6 py-3">Target Range</th>
              <th scope="col" className="px-6 py-3">Progress</th>
              <th scope="col" className="px-6 py-3">ETA (s)</th>
              <th scope="col" className="px-6 py-3">Hosts</th>
              <th scope="col" className="px-6 py-3 text-center">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {chunks.map((chunk) => (
              <tr key={chunk.id} className="hover:bg-gray-700/50">
                <td className="px-6 py-4"><StatusBadge status={chunk.status} /></td>
                <td className="px-6 py-4 font-mono">{chunk.targetRange}</td>
                <td className="px-6 py-4">
                    <div className="flex items-center">
                        <div className="w-24 mr-2">
                            <ProgressBar progress={chunk.progress} />
                        </div>
                        <span className="text-gray-400">{chunk.progress}%</span>
                    </div>
                </td>
                <td className="px-6 py-4">{chunk.eta > 0 ? chunk.eta : '-'}</td>
                <td className="px-6 py-4">{chunk.completedCount}/{chunk.hostCount}</td>
                <td className="px-6 py-4">
                    <div className="flex items-center justify-center space-x-1">
                        <ActionButton onClick={() => alert(`Retrying ${chunk.id}`)} title="Retry Chunk">
                            <RefreshCw size={16} />
                        </ActionButton>
                        <ActionButton onClick={() => alert(`Stopping ${chunk.id}`)} title="Stop Chunk">
                            <X size={16} />
                        </ActionButton>
                    </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ScanChunkTable;
