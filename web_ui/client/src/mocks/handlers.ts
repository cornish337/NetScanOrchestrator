import { http, HttpResponse, PathParams } from 'msw';
import { Scan } from '../types/api';

// --- Mock Data ---

const mockRunningScan: Scan = {
  scan_id: 'scan_running',
  status: 'RUNNING',
  progress: {
    total_chunks: 100,
    completed_chunks: 42,
    failed_chunks: 1,
  },
  results: {
    hosts: {
      '192.168.1.1': { status: 'up', ports: [22, 80] },
      '192.168.1.2': { status: 'up', ports: [443] },
      '192.168.1.3': { status: 'down', reason: 'no-response' },
    },
  },
};

const mockCompletedScan: Scan = {
  scan_id: 'scan_completed',
  status: 'COMPLETED',
  progress: {
    total_chunks: 100,
    completed_chunks: 98,
    failed_chunks: 2,
  },
  results: {
    hosts: {
      // ... more complete data
      '192.168.1.1': { status: 'up', ports: [22, 80, 8080] },
      '192.168.1.2': { status: 'up', ports: [443] },
      '192.168.1.4': { status: 'up', ports: [22] },
    },
  },
};

const mockFailedScan: Scan = {
  scan_id: 'scan_failed',
  status: 'FAILED',
  progress: {
    total_chunks: 100,
    completed_chunks: 10,
    failed_chunks: 5,
  },
  results: {
    hosts: {},
  },
};

const mockScans: Record<string, Scan> = {
  scan_running: mockRunningScan,
  scan_completed: mockCompletedScan,
  scan_failed: mockFailedScan,
};

// --- Handlers ---

export const handlers = [
  // Mock for starting a new scan
  http.post('/api/scans', async () => {
    await new Promise(res => setTimeout(res, 200));
    // Return a specific ID to test the running state by default
    return HttpResponse.json({ scan_id: 'scan_running' }, { status: 202 });
  }),

  // Mock for getting scan status
  http.get('/api/scans/:scanId', ({ params }: { params: PathParams<'scanId'> }) => {
    const { scanId } = params;

    if (typeof scanId !== 'string') {
      return new HttpResponse('Invalid scan ID', { status: 400 });
    }

    const scan = mockScans[scanId];

    if (scan) {
      return HttpResponse.json(scan);
    }

    return new HttpResponse('Not found', {
      status: 404,
    });
  }),
];
