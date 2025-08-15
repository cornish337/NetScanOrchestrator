import React from 'react';

const Placeholder = ({
  title,
  className = '',
}: {
  title: string;
  className?: string;
}) => (
  <div
    className={`bg-gray-800 border-2 border-dashed border-gray-600 rounded-lg p-4 flex items-center justify-center ${className}`}
  >
    <h2 className="text-gray-500 text-lg font-semibold">{title}</h2>
  </div>
);

const DifficultTargetsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-gray-800 rounded-lg p-4 shadow-lg">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold text-white">
            Difficult Target Management
          </h1>
          <div className="flex items-center space-x-2">
            <button className="px-4 py-2 bg-yellow-500 text-black rounded-md hover:bg-yellow-600">
              Retry All Selected
            </button>
            <button className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700">
              Delete Selected
            </button>
          </div>
        </div>
        <Placeholder title="Filter controls (by status, error type, duration)" className="h-20" />
      </div>

      <div>
        <Placeholder title="Table of Slow / Failed / Stuck Targets" className="h-[600px]" />
      </div>
    </div>
  );
};

export default DifficultTargetsPage;
