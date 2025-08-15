import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ScanCoveragePanel } from './ScanCoveragePanel';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { Scan } from '../../types/api';

// Mock the useQuery hook
vi.mock('@tanstack/react-query', async (importOriginal) => {
  const original = await importOriginal<typeof import('@tanstack/react-query')>();
  return {
    ...original,
    useQuery: vi.fn(),
  };
});

const createMockScan = (): Scan => ({
  scan_id: 'test-scan',
  status: 'RUNNING',
  progress: {
    total_chunks: 10,
    completed_chunks: 5,
    failed_chunks: 1,
  },
  chunks: Array.from({ length: 10 }, (_, i) => ({
    id: `c_${i}`,
    status: i < 5 ? 'completed' : i < 6 ? 'failed' : 'pending',
  })),
  results: { hosts: {} },
});

const queryClient = new QueryClient();

const renderWithClient = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
};

describe('ScanCoveragePanel', () => {
  it('should render the heatmap legend', () => {
    const mockScan = createMockScan();
    vi.mocked(useQuery).mockReturnValue({
      data: mockScan,
      isLoading: false,
      isError: false,
    } as any);

    renderWithClient(<ScanCoveragePanel scanId="test-scan" />);

    expect(screen.getByTestId('legend-pending')).toBeInTheDocument();
    expect(screen.getByTestId('legend-running')).toBeInTheDocument();
    expect(screen.getByTestId('legend-completed')).toBeInTheDocument();
    expect(screen.getByTestId('legend-failed')).toBeInTheDocument();
  });

  it('should render the mini-map', () => {
    const mockScan = createMockScan();
    vi.mocked(useQuery).mockReturnValue({
      data: mockScan,
      isLoading: false,
      isError: false,
    } as any);

    renderWithClient(<ScanCoveragePanel scanId="test-scan" />);

    expect(screen.getByRole('heading', { name: /mini-map/i })).toBeInTheDocument();
  });
});
