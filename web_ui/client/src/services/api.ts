import axios from 'axios';
import { Scan, StartScanRequest, StartScanResponse } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

export const startScan = async (
  scanRequest: StartScanRequest
): Promise<StartScanResponse> => {
  const response = await apiClient.post('/scans', scanRequest);
  return response.data;
};

export const getScan = async (scanId: string): Promise<Scan> => {
  const response = await apiClient.get(`/scans/${scanId}`);
  return response.data;
};

// Add other API functions as needed, e.g., for operator controls
// export const killScan = async (scanId: string) => { ... }
// export const retryDifficultTargets = async (targets: string[]) => { ... }

