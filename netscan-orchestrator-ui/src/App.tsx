import { useState } from 'react';
import ScanDashboardPage from './pages/ScanDashboardPage';
import TargetInputPage from './pages/TargetInputPage';
import DifficultTargetsPage from './pages/DifficultTargetsPage';

type Page = 'dashboard' | 'input' | 'difficult';

function App() {
  const [page, setPage] = useState<Page>('dashboard');

  const renderPage = () => {
    switch (page) {
      case 'input':
        return <TargetInputPage />;
      case 'difficult':
        return <DifficultTargetsPage />;
      case 'dashboard':
      default:
        return <ScanDashboardPage />;
    }
  };

  const NavLink = ({
    active,
    onClick,
    children,
  }: {
    active: boolean;
    onClick: () => void;
    children: React.ReactNode;
  }) => (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
        active
          ? 'bg-gray-900 text-white'
          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
      }`}
    >
      {children}
    </button>
  );

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 font-sans">
      <header className="bg-gray-800 shadow-md">
        <nav className="container mx-auto px-6 py-3 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="text-blue-400"
            >
              <path d="M20 10c0 4.4-3.6 8-8 8s-8-3.6-8-8 3.6-8 8-8 8 3.6 8 8Z" />
              <path d="M12 12a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" />
              <path d="M12 2a2.5 2.5 0 0 1 2.5 2.5" />
              <path d="M12 20a2.5 2.5 0 0 1-2.5-2.5" />
              <path d="M6.5 17.5a2.5 2.5 0 0 1 0-5" />
              <path d="M17.5 6.5a2.5 2.5 0 0 1 0 5" />
            </svg>
            <h1 className="text-xl font-bold text-white">
              NetScanOrchestrator
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <NavLink active={page === 'input'} onClick={() => setPage('input')}>
              New Scan
            </NavLink>
            <NavLink
              active={page === 'dashboard'}
              onClick={() => setPage('dashboard')}
            >
              Dashboard
            </NavLink>
            <NavLink
              active={page === 'difficult'}
              onClick={() => setPage('difficult')}
            >
              Difficult Targets
            </NavLink>
          </div>
        </nav>
      </header>
      <main className="container mx-auto p-6">{renderPage()}</main>
    </div>
  );
}

export default App;
