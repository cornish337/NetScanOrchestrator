import React, { useState, useEffect } from 'react';
import { ScanChunk } from '../types/scan-types';
import { generateMockScanData } from '../lib/mock-data';
import { useScanUpdates } from '../hooks/useScanUpdates';
import ScanChunkTable from '../components/features/ScanDashboard/ScanChunkTable';
import ScanHeatmap from '../components/features/ScanDashboard/ScanHeatmap';
import TopControlBar from '../components/features/ScanDashboard/TopControlBar';

// Placeholder for the event log, to be implemented later
const EventLogPlaceholder = () => (
    <div className="bg-gray-800 border-2 border-dashed border-gray-600 rounded-lg p-4 flex items-center justify-center h-48">
      <h2 className="text-gray-500 text-lg font-semibold">Timeline / Event Log</h2>
    </div>
  );

const ScanDashboardPage: React.FC = () => {
    const [scanData, setScanData] = useState<ScanChunk[]>([]);

    // Load initial mock data
    useEffect(() => {
        setScanData(generateMockScanData(128)); // 16 * 8 = 128 for a nice grid
    }, []);

    // Use the custom hook to simulate real-time updates
    useScanUpdates(scanData, setScanData);

    const handleStartAll = () => alert("Starting all scans...");
    const handleStopAll = () => alert("Stopping all scans...");
    const handleRetryFailed = () => alert("Retrying failed chunks...");

    return (
        <div className="space-y-6">
            <TopControlBar
                onStartAll={handleStartAll}
                onStopAll={handleStopAll}
                onRetryFailed={handleRetryFailed}
            />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                    <ScanChunkTable chunks={scanData} />
                </div>
                <div className="lg:col-span-1">
                    <ScanHeatmap chunks={scanData} />
                </div>
            </div>

            <div>
                <EventLogPlaceholder />
            </div>
        </div>
    );
};

export default ScanDashboardPage;
