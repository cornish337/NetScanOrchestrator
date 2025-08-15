import React from 'react';
import { Target } from '../../../lib/ip-utils';
import { Star } from 'lucide-react';

interface PreviewConfigureStepProps {
  targets: Target[];
  chunkSize: number;
  setChunkSize: (size: number) => void;
  togglePriority: (targetValue: string) => void;
}

const PreviewConfigureStep: React.FC<PreviewConfigureStepProps> = ({
  targets,
  chunkSize,
  setChunkSize,
  togglePriority,
}) => {
  const displayedTargets = targets.slice(0, 100);

  return (
    <div>
      <h2 className="text-xl font-semibold text-white mb-4">
        Preview & Configure
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Target List */}
        <div className="bg-gray-900 p-4 rounded-md border border-gray-700">
          <h3 className="font-semibold text-white mb-2">
            Expanded Targets ({targets.length} total)
          </h3>
          <p className="text-sm text-gray-400 mb-4">
            Click the star to mark a target as high priority.
            {targets.length > 100 &&
              ' Showing first 100 targets.'}
          </p>
          <div className="h-64 overflow-y-auto pr-2">
            {displayedTargets.map((target) => (
              <div
                key={target.value}
                className="flex items-center justify-between p-2 rounded-md hover:bg-gray-800"
              >
                <span className="font-mono text-sm text-gray-300">
                  {target.value}
                </span>
                <button
                  onClick={() => togglePriority(target.value)}
                  className="p-1 rounded-full hover:bg-gray-700"
                  title="Toggle Priority"
                >
                  <Star
                    size={16}
                    className={
                      target.isPriority
                        ? 'text-yellow-400 fill-current'
                        : 'text-gray-500'
                    }
                  />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Configuration */}
        <div className="bg-gray-900 p-4 rounded-md border border-gray-700">
          <h3 className="font-semibold text-white mb-4">Configuration</h3>
          <div className="space-y-4">
            <div>
              <label
                htmlFor="chunkSize"
                className="block text-sm font-medium text-gray-300 mb-1"
              >
                Chunk Size
              </label>
              <p className="text-xs text-gray-400 mb-2">
                Number of targets to be scanned by a single worker at a time.
              </p>
              <input
                type="number"
                id="chunkSize"
                value={chunkSize}
                onChange={(e) => setChunkSize(parseInt(e.target.value, 10))}
                className="w-full p-2 bg-gray-800 border border-gray-600 rounded-md text-white"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PreviewConfigureStep;
