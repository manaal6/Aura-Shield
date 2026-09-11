import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import AnalyzePage from './pages/AnalyzePage';
import LogsPage from './pages/LogsPage';
import ConstitutionPage from './pages/ConstitutionPage';
import BenchmarkPage from './pages/BenchmarkPage';

function App() {
  return (
    <Router>
      <header className="topbar">
        <div className="brand">
          <span className="brand-name">AURA Shield</span>
          <span className="brand-sub">adaptive prompt-injection shield</span>
        </div>
        <nav>
          <NavLink to="/" end className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Analyze</NavLink>
          <NavLink to="/logs" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Logs</NavLink>
          <NavLink to="/constitution" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Constitution</NavLink>
          <NavLink to="/benchmark" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Benchmark</NavLink>
        </nav>
      </header>
      <main className="page">
        <Routes>
          <Route path="/" element={<AnalyzePage />} />
          <Route path="/logs" element={<LogsPage />} />
          <Route path="/constitution" element={<ConstitutionPage />} />
          <Route path="/benchmark" element={<BenchmarkPage />} />
        </Routes>
      </main>
      <footer className="footer">
        <span>AURA Shield web console</span>
        <span>API: <a href="/docs">/docs</a></span>
      </footer>
    </Router>
  );
}

export default App;
