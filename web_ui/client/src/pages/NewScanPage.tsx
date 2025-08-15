import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { startScan } from '../services/api';

const NewScanPage: React.FC = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [targets, setTargets] = useState('scanme.nmap.org\n192.168.1.0/24');
  const [nmapOptions, setNmapOptions] = useState('-T4 -F');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleNext = () => setStep(prev => prev + 1);
  const handleBack = () => setStep(prev => prev - 1);

  const handleSubmit = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Split targets by newline and filter out empty lines
      const targetArray = targets.split('\n').filter(t => t.trim() !== '');
      if (targetArray.length === 0) {
        setError('Targets list cannot be empty.');
        setIsLoading(false);
        return;
      }

      const response = await startScan({
        targets: targetArray,
        nmap_options: nmapOptions,
      });

      navigate(`/dashboard?scan=${response.scan_id}`);
    } catch (err) {
      setError('Failed to start scan. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const preStyle: React.CSSProperties = {
    background: '#f4f4f4',
    padding: '10px',
    borderRadius: '4px',
    whiteSpace: 'pre-wrap', // wrap long lines
    wordBreak: 'break-all', // break long words/strings
  };

  return (
    <div style={{ width: '100%', maxWidth: '700px', margin: '0 auto', padding: '20px', textAlign: 'left' }}>
      <h1>New Scan Wizard</h1>
      <div style={{ margin: '20px 0' }}>
        {step === 1 && (
          <div>
            <h2>Step 1: Define Targets</h2>
            <p>Enter targets to scan, one per line (e.g., IP, hostname, CIDR).</p>
            <textarea
              value={targets}
              onChange={e => setTargets(e.target.value)}
              rows={10}
              style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
              placeholder="e.g., 192.168.1.1&#10;scanme.nmap.org&#10;10.0.0.0/24"
            />
          </div>
        )}
        {step === 2 && (
          <div>
            <h2>Step 2: Set Scan Options</h2>
            <p>Provide Nmap command-line options.</p>
            <input
              type="text"
              value={nmapOptions}
              onChange={e => setNmapOptions(e.target.value)}
              style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
            />
          </div>
        )}
        {step === 3 && (
          <div>
            <h2>Step 3: Summary</h2>
            <h4>Targets:</h4>
            <pre style={preStyle}>{targets}</pre>
            <h4>Nmap Options:</h4>
            <pre style={preStyle}>{nmapOptions}</pre>
            {error && <p style={{ color: 'red' }}>{error}</p>}
          </div>
        )}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        {step > 1 && <button onClick={handleBack}>Back</button>}
        <div />
        {step < 3 && <button onClick={handleNext}>Next</button>}
        {step === 3 && (
          <button onClick={handleSubmit} disabled={isLoading}>
            {isLoading ? 'Starting Scan...' : 'Start Scan'}
          </button>
        )}
      </div>
    </div>
  );
};

export { NewScanPage };
