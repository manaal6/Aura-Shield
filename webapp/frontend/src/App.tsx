import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import AnalyzePage from './pages/AnalyzePage';
import LogsPage from './pages/LogsPage';
import ConstitutionPage from './pages/ConstitutionPage';
import BenchmarkPage from './pages/BenchmarkPage';
import EvidencePage from './pages/EvidencePage';
import OverviewPage from './pages/OverviewPage';
import PipelinePage from './pages/PipelinePage';
import FusionLabPage from './pages/FusionLabPage';
import AdaptivePage from './pages/AdaptivePage';
import AlignmentPage from './pages/AlignmentPage';
import RedTeamPage from './pages/RedTeamPage';
import ToolSecurityPage from './pages/ToolSecurityPage';
import ReliabilityPage from './pages/ReliabilityPage';
import ReproducibilityPage from './pages/ReproducibilityPage';

function App() {
  return (
    <Router>
      <header className="topbar">
        <div className="brand">
          <span className="brand-name">AURA Shield</span>
          <span className="brand-sub">adaptive prompt-injection shield</span>
        </div>
        <nav>
          <NavLink to="/" end className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Overview</NavLink>
          <NavLink to="/analyze" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Analyze</NavLink>
          <NavLink to="/pipeline" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Pipeline</NavLink>
          <NavLink to="/benchmark" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Benchmark</NavLink>
          <NavLink to="/fusion" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Fusion Lab</NavLink>
          <NavLink to="/adaptive" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Adaptive</NavLink>
          <NavLink to="/alignment" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Alignment</NavLink>
          <NavLink to="/redteam" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Red Team</NavLink>
          <NavLink to="/tools" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Tools</NavLink>
          <NavLink to="/reliability" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Reliability</NavLink>
          <NavLink to="/repro" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Repro</NavLink>
          <NavLink to="/logs" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Logs</NavLink>
          <NavLink to="/constitution" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Constitution</NavLink>
          <NavLink to="/evidence" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Evidence</NavLink>
        </nav>
      </header>
      <main className="page">
        <Routes>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/analyze" element={<AnalyzePage />} />
          <Route path="/pipeline" element={<PipelinePage />} />
          <Route path="/benchmark" element={<BenchmarkPage />} />
          <Route path="/fusion" element={<FusionLabPage />} />
          <Route path="/adaptive" element={<AdaptivePage />} />
          <Route path="/alignment" element={<AlignmentPage />} />
          <Route path="/redteam" element={<RedTeamPage />} />
          <Route path="/tools" element={<ToolSecurityPage />} />
          <Route path="/reliability" element={<ReliabilityPage />} />
          <Route path="/repro" element={<ReproducibilityPage />} />
          <Route path="/logs" element={<LogsPage />} />
          <Route path="/constitution" element={<ConstitutionPage />} />
          <Route path="/evidence" element={<EvidencePage />} />
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
