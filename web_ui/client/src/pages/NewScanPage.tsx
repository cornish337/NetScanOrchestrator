import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { startScan, ScanOptions } from '../services/api';

export function NewScanPage() {
  const navigate = useNavigate();

  const prefersReducedMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const [targets, setTargets] = useState<string[]>(['']);
  const [options, setOptions] = useState<ScanOptions>({
    flags: '',
    reducedMotion: prefersReducedMotion,
  });
  const [currentStep, setCurrentStep] = useState(1);

  const handleTargetChange = (index: number, value: string) => {
    const updated = [...targets];
    updated[index] = value;
    setTargets(updated);
  };

  const addTarget = () => setTargets([...targets, '']);

  const removeTarget = (index: number) => {
    const updated = targets.filter((_, i) => i !== index);
    setTargets(updated.length > 0 ? updated : ['']);
  };

  const handleStartScan = async () => {
    try {
      const response = await startScan({
        targets: targets.filter((t) => t.trim() !== ''),
        options,
      });
      if (response.status === 202) {
        const id = response.data.scan_id;
        navigate(`/dashboard?scan=${encodeURIComponent(id)}`);
      } else {
        console.error('Unexpected response', response);
      }
    } catch (err) {
      console.error('Failed to start scan', err);
    }
  };

  const renderTargetsStep = () => (
    <div>
      <h2>Targets</h2>
      {targets.map((target, idx) => (
        <div key={idx} style={{ marginBottom: '0.5rem' }}>
          <input
            type="text"
            value={target}
            placeholder="Host or CIDR"
            onChange={(e) => handleTargetChange(idx, e.target.value)}
          />
          {targets.length > 1 && (
            <button type="button" onClick={() => removeTarget(idx)}>
              Remove
            </button>
          )}
        </div>
      ))}
      <button type="button" onClick={addTarget}>
        Add Target
      </button>
    </div>
  );

  const renderOptionsStep = () => (
    <div>
      <h2>Options</h2>
      <div>
        <label>
          Nmap Flags:
          <input
            type="text"
            value={options.flags}
            onChange={(e) =>
              setOptions({ ...options, flags: e.target.value })
            }
          />
        </label>
      </div>
      <div>
        <label>
          <input
            type="checkbox"
            checked={options.reducedMotion}
            onChange={(e) =>
              setOptions({ ...options, reducedMotion: e.target.checked })
            }
          />
          Reduced motion
        </label>
      </div>
    </div>
  );

  const renderSummaryStep = () => (
    <div>
      <h2>Summary</h2>
      <div>
        <h3>Targets</h3>
        <ul>
          {targets
            .filter((t) => t.trim() !== '')
            .map((t, idx) => (
              <li key={idx}>{t}</li>
            ))}
        </ul>
      </div>
      <div>
        <h3>Options</h3>
        <p>Nmap Flags: {options.flags || '(none)'}</p>
        <p>
          Reduced Motion: {options.reducedMotion ? 'Enabled' : 'Disabled'}
        </p>
      </div>
      <button onClick={handleStartScan}>Start Scan</button>
    </div>
  );

  return (
    <div>
      <h1>New Scan</h1>
      {currentStep === 1 && renderTargetsStep()}
      {currentStep === 2 && renderOptionsStep()}
      {currentStep === 3 && renderSummaryStep()}
      <div style={{ marginTop: '1rem' }}>
        {currentStep > 1 && (
          <button onClick={() => setCurrentStep(currentStep - 1)}>Back</button>
        )}
        {currentStep < 3 && (
          <button
            onClick={() => setCurrentStep(currentStep + 1)}
            disabled={
              currentStep === 1 &&
              targets.every((t) => t.trim() === '')
            }
          >
            Next
          </button>
        )}
      </div>
    </div>
  );
}
