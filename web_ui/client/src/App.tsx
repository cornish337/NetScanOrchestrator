import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link,
  Outlet,
} from 'react-router-dom';
import { NewScanPage } from './pages/NewScanPage';
import { DashboardPage } from './pages/DashboardPage';
import { DifficultTargetsPage } from './pages/DifficultTargetsPage';
import './App.css';

function Layout() {
  return (
    <div>
      <nav>
        <ul>
          <li>
            <Link to="/">New Scan</Link>
          </li>
          <li>
            <Link to="/dashboard">Dashboard</Link>
          </li>
          <li>
            <Link to="/difficult-targets">Difficult Targets</Link>
          </li>
        </ul>
      </nav>
      <hr />
      <main>
        <Outlet />
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<NewScanPage />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="difficult-targets" element={<DifficultTargetsPage />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
