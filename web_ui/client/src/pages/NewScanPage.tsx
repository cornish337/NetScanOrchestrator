import React from 'react';

export function NewScanPage() {
  const handleTestApiCall = async () => {
    try {
      console.log('Making API call to /api/scans...');
      const response = await fetch('/api/scans', { method: 'POST' });
      const data = await response.json();
      console.log('Mock API Response:', data);
      alert(`Success! Mock API returned scan ID: ${data.scan_id}`);
    } catch (error) {
      console.error('Error calling mock API:', error);
      alert('Error calling mock API. Check the console.');
    }
  };

  return (
    <div>
      <h1>New Scan</h1>
      <p>This is the page where the new scan wizard will be built.</p>
      <hr />
      <button onClick={handleTestApiCall}>
        Test Mock API Call (POST /api/scans)
      </button>
    </div>
  );
}
