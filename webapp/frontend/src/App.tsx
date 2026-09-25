import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import OverviewPage from './pages/OverviewPage';
import {
  AlignmentSection,
  EvaluationSection,
  ReproducibilitySection,
  SecuritySection,
  SystemSection,
} from './sections/sections';

function App() {
  return (
    <Router>
      <header className="topbar">
        <div className="brand">
          <span className="brand-name">AURA Shield</span>
          <span className="brand-sub">adaptive prompt-injection shield · research console</span>
        </div>
        <nav>
          <NavLink to="/" end className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Overview</NavLink>
          <NavLink to="/system" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>System</NavLink>
          <NavLink to="/evaluation" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Evaluation</NavLink>
          <NavLink to="/security" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Security</NavLink>
          <NavLink to="/alignment" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Alignment</NavLink>
          <NavLink to="/repro" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Reproducibility</NavLink>
        </nav>
      </header>
      <main className="page">
        <Routes>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/system" element={<SystemSection />} />
          <Route path="/evaluation" element={<EvaluationSection />} />
          <Route path="/security" element={<SecuritySection />} />
          <Route path="/alignment" element={<AlignmentSection />} />
          <Route path="/repro" element={<ReproducibilitySection />} />
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
