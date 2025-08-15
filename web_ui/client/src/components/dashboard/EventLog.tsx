import React, { useState, useEffect } from 'react';
import { Scan } from '../../types/api';

interface EventLogProps {
  scan: Scan;
}

const EventLog: React.FC<EventLogProps> = ({ scan }) => {
  const [lastUpdateTime, setLastUpdateTime] = useState<string | null>(null);

  useEffect(() => {
    // This effect runs whenever the scan prop changes,
    // indicating an update from polling or WebSocket.
    setLastUpdateTime(new Date().toLocaleTimeString());
  }, [scan]);

  return (
    <div style={{ border: '1px solid #ccc', padding: '10px', marginBottom: '10px' }}>
      <h3>Event Log</h3>
      {lastUpdateTime ? (
        <p>Scan data last updated at: {lastUpdateTime}</p>
      ) : (
        <p>Waiting for first update...</p>
      )}
      {/* A more advanced implementation would show a list of actual events */}
    </div>
  );
};

export { EventLog };
