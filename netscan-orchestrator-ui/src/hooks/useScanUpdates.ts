import { useEffect, useRef } from 'react';
import { ScanChunk, SCAN_STATUSES } from '../types/scan-types';

/**
 * Custom hook to simulate real-time scan updates via WebSockets.
 * In a real application, this would be replaced with a genuine
 * Socket.IO or WebSocket client connection.
 *
 * @param setData The state setter function from the component.
 */
export function useScanUpdates(
  data: ScanChunk[],
  setData: React.Dispatch<React.SetStateAction<ScanChunk[]>>
) {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const simulateUpdate = () => {
      setData((currentData) => {
        if (currentData.length === 0) {
          return currentData;
        }

        const newData = [...currentData];

        // Pick a random chunk to update
        const chunkIndex = Math.floor(Math.random() * newData.length);
        const chunkToUpdate = { ...newData[chunkIndex] };

        // Logic to progress the status
        switch (chunkToUpdate.status) {
          case 'pending':
            chunkToUpdate.status = 'running';
            chunkToUpdate.progress = 0;
            chunkToUpdate.startTime = Date.now();
            break;
          case 'running':
            chunkToUpdate.progress += Math.floor(Math.random() * 15) + 5;
            if (chunkToUpdate.progress >= 100) {
              chunkToUpdate.progress = 100;
              chunkToUpdate.status = 'completed';
              chunkToUpdate.endTime = Date.now();
              chunkToUpdate.eta = 0;
            } else {
                chunkToUpdate.eta = Math.floor(Math.random() * 100);
            }
            break;
          case 'completed':
            // Occasionally reset a completed one to pending to keep the simulation going
            if (Math.random() < 0.05) {
                chunkToUpdate.status = 'pending';
                chunkToUpdate.progress = 0;
                chunkToUpdate.startTime = undefined;
                chunkToUpdate.endTime = undefined;
            }
            break;
          // Failed or stuck chunks are left as is in this simulation
        }

        chunkToUpdate.completedCount = Math.floor((chunkToUpdate.progress / 100) * chunkToUpdate.hostCount);
        newData[chunkIndex] = chunkToUpdate;
        return newData;
      });
    };

    // Start simulation
    intervalRef.current = setInterval(simulateUpdate, 750); // Update every 750ms

    // Cleanup on unmount
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [setData]); // Effect depends only on the setter function
}
