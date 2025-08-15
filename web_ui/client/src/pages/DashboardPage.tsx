import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getScan } from '../services/api';
import { useScanSocket } from '../hooks/useScanSocket';
import { TopControlBar } from '../components/dashboard/TopControlBar';
import { ScanChunkTable } from '../components/dashboard/ScanChunkTable';
import { ScanHeatmap } from '../components/dashboard/ScanHeatmap';
import { EventLog } from '../components/dashboard/EventLog';

const DashboardPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const scanId = searchParams.get('scan');

  // Set up the WebSocket connection
  const { status: socketStatus } = useScanSocket(scanId);

  const { data: scan, error, isLoading, isError } = useQuery({
    queryKey: ['scan', scanId],
    queryFn: () => getScan(scanId!),
    enabled: !!scanId,
    // Poll for updates if the WebSocket is not connected
    refetchInterval: socketStatus !== 'OPEN' ? 5000 : false,
  });

  if (!scanId) {
    return (
      <div style={{ padding: '20px' }}>
        <h1>No Scan Selected</h1>
        <p>Please start a new scan to see the dashboard.</p>
      </div>
    );
  }

  if (isLoading && !scan) { // Show initial loading state
    return <div style={{ padding: '20px' }}>Loading scan data for {scanId}...</div>;
  }

  if (isError) {
    return <div style={{ padding: '20px' }}>Error loading scan: {error.message}</div>;
  }

  if (!scan) {
    return <div style={{ padding: '20px' }}>Scan data not found.</div>;
  }

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Scan: {scan.scan_id}</h1>
        <p>Socket Status: <strong>{socketStatus}</strong></p>
      </div>
      <p>Status: <strong>{scan.status}</strong></p>
      <p>
        Progress: {scan.progress.completed_chunks} / {scan.progress.total_chunks} chunks completed
      </p>

      <hr style={{ margin: '20px 0' }} />

      <TopControlBar scanId={scan.scan_id} />
      <ScanHeatmap progress={scan.progress} />
      <ScanChunkTable results={scan.results} />
      <EventLog scan={scan} />
    </div>
  );
};

export { DashboardPage };
