import { SCAN_STATUSES } from '../types/scan-types';
import type { ScanChunk, ScanStatus } from '../types/scan-types';

// Generate a list of ScanChunk objects with pseudo-random data. This is used by
// the dashboard while the backend API is still under development.
export function generateMockScanData(count: number): ScanChunk[] {
  const statuses: ScanStatus[] = Object.values(SCAN_STATUSES);
  const chunks: ScanChunk[] = [];

  for (let i = 0; i < count; i++) {
    const status = statuses[Math.floor(Math.random() * statuses.length)];
    const hostCount = Math.floor(Math.random() * 256) + 1;
    const completedCount = status === SCAN_STATUSES.COMPLETED
      ? hostCount
      : Math.floor(Math.random() * hostCount);
    const progress = Math.round((completedCount / hostCount) * 100);
    const eta = status === SCAN_STATUSES.COMPLETED
      ? 0
      : Math.floor(Math.random() * 3600);

    chunks.push({
      id: `chunk-${i + 1}`,
      targetRange: `192.168.${Math.floor(i / 256)}.${i % 256}`,
      status,
      progress,
      eta,
      hostCount,
      completedCount,
    });
  }

  return chunks;
}
