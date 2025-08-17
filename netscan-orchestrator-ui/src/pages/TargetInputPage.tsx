import React, { useState, useEffect } from 'react';
import type { Target } from '../lib/ip-utils';
import { expandTargets, suggestChunkSize } from '../lib/ip-utils';
import TargetInputStep from '../components/features/TargetInputWizard/TargetInputStep';
import PreviewConfigureStep from '../components/features/TargetInputWizard/PreviewConfigureStep';
import ScheduleStep from '../components/features/TargetInputWizard/ScheduleStep';

const TargetInputPage: React.FC = () => {
  const [step, setStep] = useState(1);
  const [rawTargetString, setRawTargetString] = useState('');
  const [targets, setTargets] = useState<Target[]>([]);
  const [chunkSize, setChunkSize] = useState(256);

  const totalSteps = 3;

  useEffect(() => {
    const expanded = expandTargets(rawTargetString);
    setTargets(expanded);
    if (expanded.length > 0) {
      setChunkSize(suggestChunkSize(expanded.length));
    }
  }, [rawTargetString]);

  const togglePriority = (targetValue: string) => {
    setTargets(
      targets.map((t) =>
        t.value === targetValue ? { ...t, isPriority: !t.isPriority } : t
      )
    );
  };

  const handleStartScan = () => {
    console.log("Starting scan with configuration:", {
      targets: targets,
      chunkSize: chunkSize,
    });
    // In a real app, this would trigger a mutation to the backend API
    // e.g., startScanMutation.mutate({ targets, chunkSize });
    alert("Scan started! Check the console for details.");
  };

  const StepIndicator = ({
    stepNumber,
    title,
    active,
  }: {
    stepNumber: number;
    title: string;
    active: boolean;
  }) => (
    <div className="flex items-center">
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center font-bold transition-colors ${
          active ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400'
        }`}
      >
        {stepNumber}
      </div>
      <h3
        className={`ml-4 text-lg font-medium transition-colors ${
          active ? 'text-white' : 'text-gray-400'
        }`}
      >
        {title}
      </h3>
    </div>
  );

  return (
    <div className="bg-gray-800 rounded-lg p-6 lg:p-8 shadow-lg max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-8 border-b border-gray-700 pb-4">
        <StepIndicator stepNumber={1} title="Input Targets" active={step >= 1} />
        <div className="flex-1 h-px bg-gray-600 mx-4"></div>
        <StepIndicator stepNumber={2} title="Preview & Configure" active={step >= 2} />
        <div className="flex-1 h-px bg-gray-600 mx-4"></div>
        <StepIndicator stepNumber={3} title="Schedule & Start" active={step >= 3} />
      </div>

      <div className="min-h-[350px]">
        {step === 1 && (
          <TargetInputStep
            rawTargetString={rawTargetString}
            setRawTargetString={setRawTargetString}
          />
        )}
        {step === 2 && (
          <PreviewConfigureStep
            targets={targets}
            chunkSize={chunkSize}
            setChunkSize={setChunkSize}
            togglePriority={togglePriority}
          />
        )}
        {step === 3 && (
            <ScheduleStep
                targets={targets}
                chunkSize={chunkSize}
                onStartScan={handleStartScan}
            />
        )}
      </div>

      <div className="flex justify-between mt-8 pt-4 border-t border-gray-700">
        <button
          className="px-6 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 transition-opacity"
          onClick={() => setStep(step - 1)}
          disabled={step === 1}
        >
          Back
        </button>
        {step < totalSteps ? (
          <button
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-opacity"
            onClick={() => setStep(step + 1)}
            disabled={targets.length === 0}
          >
            Next
          </button>
        ) : (
          <button
            onClick={handleStartScan}
            className="px-6 py-2 bg-green-600 text-white font-bold rounded-md hover:bg-green-700 transition-colors"
          >
            Start Scan
          </button>
        )}
      </div>
    </div>
  );
};

export default TargetInputPage;
