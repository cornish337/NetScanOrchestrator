import { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Scan, WebSocketMessage } from '../types/api';

type SocketStatus = 'CONNECTING' | 'OPEN' | 'CLOSED' | 'ERROR';

export const useScanSocket = (scanId: string | null) => {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<SocketStatus>('CLOSED');

  useEffect(() => {
    if (!scanId) {
      return;
    }

    const wsProtocol = window.location.protocol === 'https' ? 'wss' : 'ws';
    const wsUrl = `${wsProtocol}://${window.location.host}/ws/scans/${scanId}`;

    setStatus('CONNECTING');
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('WebSocket connection established');
      setStatus('OPEN');
    };

    socket.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        console.log('WebSocket message received:', message);

        queryClient.setQueryData(['scan', scanId], (oldData: Scan | undefined) => {
          if (!oldData) return;

          let newData = { ...oldData };

          if (message.type === 'CHUNK_UPDATE') {
            // This is a simplified update. A real implementation would be more complex.
            // For now, let's just update the progress.
            newData.progress.completed_chunks += 1;
            // In a real scenario, you would merge the message.payload.result into newData.results
          } else if (message.type === 'SCAN_COMPLETE') {
            const payload = message.payload as any; // Cast for now
            newData.status = payload.status;
          }

          return newData;
        });
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setStatus('ERROR');
    };

    socket.onclose = () => {
      console.log('WebSocket connection closed');
      setStatus('CLOSED');
    };

    // Cleanup function to close the socket when the component unmounts or scanId changes
    return () => {
      socket.close();
    };
  }, [scanId, queryClient]);

  return { status };
};
