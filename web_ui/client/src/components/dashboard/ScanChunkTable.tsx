import React, { useState, useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';
import { ScanResults } from '../../types/api';

interface ScanChunkTableProps {
  results: ScanResults;
}

// A real implementation would use a proper media query hook
const useIsMobile = () => {
  // For simulation purposes, we can't check window size.
  // In a real app, this would be `window.innerWidth < 768`
  return false;
};

const ScanChunkTable: React.FC<ScanChunkTableProps> = ({ results }) => {
  const [filter, setFilter] = useState('');
  const isMobile = useIsMobile();

  const hosts = useMemo(() => {
    return Object.entries(results.hosts).map(([hostname, data]) => ({
      hostname,
      ...data,
    }));
  }, [results.hosts]);

  const filteredHosts = useMemo(() => {
    if (!filter) return hosts;
    return hosts.filter(host =>
      host.hostname.toLowerCase().includes(filter.toLowerCase())
    );
  }, [hosts, filter]);

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    borderBottom: '2px solid #333',
    padding: '5px 0',
    fontWeight: 'bold',
  };

  const rowStyle: React.CSSProperties = {
    display: 'flex',
    borderBottom: '1px solid #eee',
    padding: '5px 0',
    alignItems: 'center',
  };

  const cellStyle: React.CSSProperties = {
    padding: '0 5px',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  };

  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const host = filteredHosts[index];
    return (
      <div style={{ ...style, ...rowStyle }}>
        <div style={{ ...cellStyle, flex: '2 1 120px', minWidth: 120 }}>{host.hostname}</div>
        <div style={{ ...cellStyle, flex: '1 1 60px' }}>{host.status}</div>
        {!isMobile && (
          <div style={{ ...cellStyle, flex: '3 1 150px', whiteSpace: 'normal' }}>
            {host.ports ? host.ports.join(', ') : host.reason}
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: '10px', marginBottom: '10px', textAlign: 'left' }}>
      <h3>Scan Results ({filteredHosts.length} hosts)</h3>
      <input
        type="text"
        placeholder="Filter by hostname..."
        value={filter}
        onChange={e => setFilter(e.target.value)}
        style={{ marginBottom: '10px', padding: '8px', width: '100%', maxWidth: '400px', boxSizing: 'border-box' }}
      />
      <div style={headerStyle}>
        <div style={{ ...cellStyle, flex: '2 1 120px', minWidth: 120 }}>Hostname</div>
        <div style={{ ...cellStyle, flex: '1 1 60px' }}>Status</div>
        {!isMobile && <div style={{ ...cellStyle, flex: '3 1 150px' }}>Ports / Reason</div>}
      </div>
      <List
        height={400}
        itemCount={filteredHosts.length}
        itemSize={isMobile ? 45 : 35}
        width={'100%'}
      >
        {Row}
      </List>
    </div>
  );
};

export { ScanChunkTable };
