// Based on web_ui/API_CONTRACT.md

export interface StartScanRequest {
  targets: string[];
  nmap_options: string;
}

export interface StartScanResponse {
  scan_id: string;
}

export type ScanStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export interface ScanProgress {
  total_chunks: number;
  completed_chunks: number;
  failed_chunks: number;
}

export interface HostResult {
  status: 'up' | 'down';
  ports?: any[]; // Replace with more specific types if available
  reason?: string;
}

export interface ScanResults {
  hosts: Record<string, HostResult>;
}

export interface ScanChunk {
  id: string; // e.g. '192.168.1.1' or a range '192.168.1.0-15'
  status: 'pending' | 'running' | 'completed' | 'failed';
}

export interface Scan {
  scan_id: string;
  status: ScanStatus;
  progress: ScanProgress;
  results: ScanResults;
  chunks: ScanChunk[];
}

// WebSocket Message Types
export type WebSocketMessageType = 'CHUNK_UPDATE' | 'SCAN_COMPLETE';

export interface ChunkUpdatePayload {
  chunk_id: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'STUCK';
  result?: any; // Replace with a more specific type for chunk result
}

export interface ScanCompletePayload {
  scan_id: string;
  status: 'COMPLETED' | 'FAILED';
  final_results_url: string;
}

export interface WebSocketMessage {
  type: WebSocketMessageType;
  payload: ChunkUpdatePayload | ScanCompletePayload;
}
