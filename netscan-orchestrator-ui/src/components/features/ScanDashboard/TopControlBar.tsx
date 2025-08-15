import React from 'react';
import { Play, Pause, RefreshCw, XCircle } from 'lucide-react';

interface TopControlBarProps {
  onStartAll: () => void;
  onStopAll: () => void;
  onRetryFailed: () => void;
}

const ControlButton = ({ onClick, children, className }: { onClick: () => void; children: React.ReactNode; className?: string}) => (
    <button
        onClick={onClick}
        className={`flex items-center px-4 py-2 text-sm font-semibold rounded-md transition-colors ${className}`}
    >
        {children}
    </button>
)

const TopControlBar: React.FC<TopControlBarProps> = ({ onStartAll, onStopAll, onRetryFailed }) => {
  return (
    <div className="bg-gray-800 rounded-lg p-4 flex items-center justify-between shadow-lg">
      <h1 className="text-2xl font-bold text-white">Scan Dashboard</h1>
      <div className="flex items-center space-x-2">
        <ControlButton onClick={onStartAll} className="bg-blue-600 text-white hover:bg-blue-700">
            <Play size={16} className="mr-2" />
            <span>Start All</span>
        </ControlButton>
        <ControlButton onClick={onStopAll} className="bg-red-600 text-white hover:bg-red-700">
            <XCircle size={16} className="mr-2" />
            <span>Stop All</span>
        </ControlButton>
        <ControlButton onClick={onRetryFailed} className="bg-yellow-500 text-black hover:bg-yellow-600">
            <RefreshCw size={16} className="mr-2" />
            <span>Retry Failed</span>
        </ControlButton>
      </div>
    </div>
  );
};

export default TopControlBar;
