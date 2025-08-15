import React from 'react';

interface TargetInputStepProps {
  rawTargetString: string;
  setRawTargetString: (value: string) => void;
}

const TargetInputStep: React.FC<TargetInputStepProps> = ({
  rawTargetString,
  setRawTargetString,
}) => {
  return (
    <div>
      <h2 className="text-xl font-semibold text-white mb-4">
        Enter Targets
      </h2>
      <p className="text-gray-400 mb-4">
        Paste or type targets below. You can use IP addresses, CIDR ranges (e.g., 192.168.1.0/24), or hostnames. Separate entries with spaces, commas, or new lines.
      </p>
      <textarea
        className="w-full h-60 p-4 bg-gray-900 border border-gray-600 rounded-md text-gray-200 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
        placeholder="e.g., 192.168.1.1, 10.0.0.0/24, scanme.example.com"
        value={rawTargetString}
        onChange={(e) => setRawTargetString(e.target.value)}
      />
    </div>
  );
};

export default TargetInputStep;
