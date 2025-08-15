import React, { useMemo } from 'react';
import { Treemap, ResponsiveContainer, Tooltip } from 'recharts';
import { ScanProgress } from '../../types/api';

interface ScanHeatmapProps {
  progress: ScanProgress;
}

const ScanHeatmap: React.FC<ScanHeatmapProps> = ({ progress }) => {
  const data = useMemo(() => {
    const { total_chunks, completed_chunks, failed_chunks } = progress;
    const pending_chunks = total_chunks - completed_chunks - failed_chunks;

    return [
      { name: 'Completed', size: completed_chunks, fill: '#82ca9d' },
      { name: 'Pending', size: pending_chunks > 0 ? pending_chunks : 0, fill: '#8884d8' },
      { name: 'Failed', size: failed_chunks, fill: '#ffc658' },
    ];
  }, [progress]);

  return (
    <div style={{ border: '1px solid #ccc', padding: '10px', marginBottom: '10px', height: '200px' }}>
      <h3>Scan Coverage</h3>
      <ResponsiveContainer width="100%" height="100%">
        <Treemap
          data={data}
          dataKey="size"
          ratio={4 / 3}
          stroke="#fff"
          fill="#8884d8"
        >
          <Tooltip />
        </Treemap>
      </ResponsiveContainer>
    </div>
  );
};

export { ScanHeatmap };
