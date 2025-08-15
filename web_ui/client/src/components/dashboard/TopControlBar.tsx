import React from 'react';

interface TopControlBarProps {
  scanId: string;
}

const TopControlBar: React.FC<TopControlBarProps> = ({ scanId }) => {
  const handleKill = () => {
    console.log(`Request to KILL scan: ${scanId}`);
    alert('Kill functionality not implemented yet.');
  };

  const handleSplit = () => {
    console.log(`Request to SPLIT scan: ${scanId}`);
    alert('Split functionality not implemented yet.');
  };

  const handleRetry = () => {
    console.log(`Request to RETRY FAILED for scan: ${scanId}`);
    alert('Retry functionality not implemented yet.');
  };

  const buttonStyle: React.CSSProperties = {
    marginRight: '10px',
    marginBottom: '10px',
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: '10px', marginBottom: '10px', textAlign: 'left' }}>
      <h3>Operator Controls</h3>
      <div style={{ display: 'flex', flexWrap: 'wrap' }}>
        <button onClick={handleKill} style={buttonStyle}>
          Kill Scan
        </button>
        <button onClick={handleSplit} style={buttonStyle} disabled>
          Split Scan
        </button>
        <button onClick={handleRetry} style={buttonStyle} disabled>
          Retry Failed
        </button>
      </div>
    </div>
  );
};

export { TopControlBar };
