import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getScan } from '../../services/api';
import { ScanChunk } from '../../types/api';
import { MiniMap } from './MiniMap';

interface ScanCoveragePanelProps {
  scanId: string;
}

const chunkColor: Record<ScanChunk['status'], string> = {
  pending: '#d1d5db', // gray-300
  running: '#60a5fa', // blue-400
  completed: '#4ade80', // green-400
  failed: '#f87171', // red-400
};

const ScanCoveragePanel: React.FC<ScanCoveragePanelProps> = ({ scanId }) => {
  // The dashboard already polls, so this query will get updated data
  const { data: scan } = useQuery({
    queryKey: ['scan', scanId],
    queryFn: () => getScan(scanId),
    enabled: !!scanId,
  });

  if (!scan) {
    return <div>Loading coverage...</div>;
  }

  const { progress } = scan;
  const remaining_chunks = progress.total_chunks - progress.completed_chunks - progress.failed_chunks;
  const percentage_covered = progress.total_chunks > 0 ? ((progress.completed_chunks + progress.failed_chunks) / progress.total_chunks) * 100 : 0;

  // Simple ETA calculation (example: 0.5 seconds per chunk)
  const eta_seconds = remaining_chunks * 0.5;
  const eta = new Date(eta_seconds * 1000).toISOString().substr(14, 5);


  const [focusOnGaps, setFocusOnGaps] = React.useState(false);

  const handleExport = () => {
    const gaps = scan.chunks.filter(c => c.status === 'pending' || c.status === 'failed');
    const blob = new Blob([JSON.stringify(gaps, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scan_${scanId}_remaining.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const visibleChunks = focusOnGaps
    ? scan.chunks.filter(c => c.status === 'pending' || c.status === 'failed')
    : scan.chunks;

  return (
    <div style={{ border: '1px solid #ccc', padding: '10px', marginTop: '20px' }}>
      <h3>Scan Coverage</h3>
      <div style={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center', marginBottom: '10px', gap: '20px', flexWrap: 'wrap' }}>
        {Object.entries(chunkColor).map(([status, color]) => (
          <div key={status} style={{ display: 'flex', alignItems: 'center', gap: '5px' }} data-testid={`legend-${status}`}>
            <div style={{ width: '15px', height: '15px', backgroundColor: color, borderRadius: '2px', border: '1px solid #ccc' }} />
            <span style={{ textTransform: 'capitalize' }}>{status}</span>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-around', marginBottom: '10px' }}>
        <div><strong>{progress.total_chunks}</strong> Total Hosts</div>
        <div><strong>{progress.completed_chunks}</strong> Completed</div>
        <div><strong>{remaining_chunks}</strong> Remaining</div>
        <div><strong>{percentage_covered.toFixed(1)}%</strong> Covered</div>
        <div>ETA: <strong>{eta}</strong></div>
      </div>
       <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <div>
          <label>
            <input type="checkbox" checked={focusOnGaps} onChange={e => setFocusOnGaps(e.target.checked)} />
            Focus on Gaps
          </label>
        </div>
        <button onClick={handleExport}>Export Remaining</button>
      </div>
      <div style={{ display: 'flex', gap: '20px', alignItems: 'flex-start' }}>
        <div style={{ flex: 1, display: 'grid', gridTemplateColumns: 'repeat(32, 1fr)', gap: '2px' }}>
          {visibleChunks.map(chunk => (
            <div
              key={chunk.id}
              title={`${chunk.id}: ${chunk.status}`}
              style={{
                width: '100%',
                paddingBottom: '100%', // Creates a square aspect ratio
                backgroundColor: chunkColor[chunk.status],
                borderRadius: '2px',
              }}
            />
          ))}
        </div>
        <MiniMap chunks={scan.chunks} chunkColor={chunkColor} />
      </div>
    </div>
  );
};

export { ScanCoveragePanel };
