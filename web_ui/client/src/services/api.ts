import axios from 'axios';

export interface ScanOptions {
  flags: string;
  reducedMotion: boolean;
}

export interface StartScanPayload {
  targets: string[];
  options: ScanOptions;
}

export interface StartScanResponse {
  scan_id: string;
}

export async function startScan(payload: StartScanPayload) {
  return axios.post<StartScanResponse>('/api/scans', payload);
}
