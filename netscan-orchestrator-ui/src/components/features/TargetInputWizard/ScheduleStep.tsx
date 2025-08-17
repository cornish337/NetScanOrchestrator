import React from 'react';
import type { Target } from '../../../lib/ip-utils';

interface ScheduleStepProps {
  targets: Target[];
  chunkSize: number;
  onStartScan: () => void;
}

const SummaryItem = ({ label, value }: { label: string; value: string | number }) => (
  <div className="flex justify-between items-center py-3 border-b border-gray-700">
    <span className="text-gray-400">{label}</span>
    <span className="font-semibold text-white">{value}</span>
  </div>
);

const ScheduleStep: React.FC<ScheduleStepProps> = ({
  targets,
  chunkSize,
  onStartScan,
}) => {
  const priorityTargetCount = targets.filter(t => t.isPriority).length;
  const totalChunks = Math.ceil(targets.length / chunkSize) || 0;

  return (
    <div>
      <h2 className="text-xl font-semibold text-white mb-4">
        Review and Start Scan
      </h2>
      <div className="bg-gray-900 p-6 rounded-md border border-gray-700">
        <h3 className="font-semibold text-white mb-4 border-b border-gray-700 pb-2">
          Scan Summary
        </h3>
        <div className="space-y-2">
          <SummaryItem label="Total Targets" value={targets.length} />
          <SummaryItem label="High Priority Targets" value={priorityTargetCount} />
          <SummaryItem label="Chunk Size" value={chunkSize} />
          <SummaryItem label="Total Chunks" value={totalChunks} />
        </div>
      </div>
      <div className="mt-6 text-center">
        <button
          onClick={onStartScan}
          className="w-full max-w-xs px-6 py-3 bg-green-600 text-white font-bold rounded-md hover:bg-green-700 transition-colors text-lg"
        >
          Start Scan
        </button>
      </div>
    </div>
  );
};

export default ScheduleStep;
