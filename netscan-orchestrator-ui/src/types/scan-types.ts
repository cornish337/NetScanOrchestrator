export const SCAN_STATUSES = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  STUCK: 'stuck',
} as const;

export type ScanStatus = typeof SCAN_STATUSES[keyof typeof SCAN_STATUSES];

export interface ScanChunk {
  id: string;
  targetRange: string; // e.g., "192.168.1.0-192.168.1.255"
  status: ScanStatus;
  progress: number; // Percentage (0-100)
  eta: number; // Estimated time remaining in seconds
  hostCount: number;
  completedCount: number;
  startTime?: number; // Unix timestamp
  endTime?: number; // Unix timestamp
  error?: string; // Description of why it failed or got stuck
}

export const STATUS_COLORS: { [key in ScanStatus]: string } = {
  [SCAN_STATUSES.PENDING]: 'bg-gray-500',
  [SCAN_STATUSES.RUNNING]: 'bg-blue-500',
  [SCAN_STATUSES.COMPLETED]: 'bg-green-500',
  [SCAN_STATUSES.FAILED]: 'bg-red-500',
  [SCAN_STATUSES.STUCK]: 'bg-orange-500',
};

export const STATUS_TEXT_COLORS: { [key in ScanStatus]: string } = {
    [SCAN_STATUSES.PENDING]: 'text-gray-300',
    [SCAN_STATUSES.RUNNING]: 'text-blue-300',
    [SCAN_STATUSES.COMPLETED]: 'text-green-300',
    [SCAN_STATUSES.FAILED]: 'text-red-300',
    [SCAN_STATUSES.STUCK]: 'text-orange-300',
  };
