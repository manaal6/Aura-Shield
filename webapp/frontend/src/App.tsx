import { useEffect, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import { BrowserRouter as Router, NavLink, Route, Routes, useLocation } from 'react-router-dom';
import OverviewPage from './pages/OverviewPage';
import {
  AlignmentSection,
  EvaluationSection,
  ReproducibilitySection,
  SecuritySection,
  SystemSection,
} from './sections/sections';
import { ThemeProvider, useTheme } from './theme';

const NAV = [
  { to: '/', label: 'Overview', end: true },
  { to: '/system', label: 'System', count: 3 },
  { to: '/evaluation', label: 'Evaluation', count: 4 },
  { to: '/security', label: 'Security', count: 3 },
  { to: '/alignment', label: 'Alignment', count: 2 },
  { to: '/repro', label: 'Reproducibility', count: 2 },
];

function Mark() {
  return (
    <svg className="rail-mark" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <rect x="3" y="3" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <path d="M3 21 21 3" stroke="currentColor" strokeWidth="1.6" />
      <rect x="13.5" y="3.5" width="7" height="7" fill="currentColor" />
    </svg>
  );
}

function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const dark = theme === 'dark';
  return (
    <button
      type="button"
      className="icon-btn"
      onClick={toggle}
      aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
      title={dark ? 'Light theme' : 'Dark theme'}
    >
      {dark ? (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
          <circle cx="12" cy="12" r="4.2" />
          <path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6" strokeLinecap="round" />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
          <path d="M20.5 14.2A8.6 8.6 0 0 1 9.8 3.5a8.6 8.6 0 1 0 10.7 10.7Z" strokeLinejoin="round" />
        </svg>
      )}
      <span>{dark ? 'Light' : 'Dark'}</span>
    </button>
  );
}

function Shell() {
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const reduce = useReducedMotion();
  const current = NAV.find((n) => (n.end ? location.pathname === n.to : location.pathname.startsWith(n.to)));
  const sectionLabel = current?.label ?? 'Overview';

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMenuOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [menuOpen]);

  return (
    <div className="app-shell">
      <a className="skip-link" href="#content">Skip to content</a>

      <div
        className={menuOpen ? 'rail-scrim show' : 'rail-scrim'}
        onClick={() => setMenuOpen(false)}
        aria-hidden="true"
      />

      <aside id="primary-nav" className={menuOpen ? 'rail open' : 'rail'} aria-label="Primary">
        <NavLink to="/" className="rail-brand" onClick={() => setMenuOpen(false)}>
          <Mark />
          <span className="rail-wordmark">
            <b>AURA <em>Shield</em></b>
            <span>prompt-injection defense</span>
          </span>
        </NavLink>

        <nav className="rail-nav">
          <p className="rail-nav-label">Contents</p>
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? 'rail-link active' : 'rail-link')}
              onClick={() => setMenuOpen(false)}
            >
              <span className="rail-label">{item.label}</span>
              {item.count ? <span className="rail-count">{item.count}</span> : null}
            </NavLink>
          ))}
        </nav>

        <div className="rail-foot">
          <div className="rail-status">
            <span><span className="status-dot" aria-hidden="true" /><strong>PARTIAL</strong> · ready for review</span>
            <span>221 passed + 3 skipped</span>
            <span>constitution v2 · max-fusion C1–C10</span>
            <span>every figure traces to an artifact</span>
          </div>
          <a className="rail-link" href="/docs" style={{ paddingLeft: 0 }}>
            <span className="rail-label">API documentation</span>
            <span className="rail-count">/docs →</span>
          </a>
        </div>
      </aside>

      <div className="main-col">
        <header className="topstrip">
          <div className="crumbs">
            <button
              type="button"
              className="icon-btn menu-btn"
              onClick={() => setMenuOpen((o) => !o)}
              aria-expanded={menuOpen}
              aria-controls="primary-nav"
              aria-label={menuOpen ? 'Close navigation' : 'Open navigation'}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true">
                <path d="M3 6h18M3 12h18M3 18h18" strokeLinecap="round" />
              </svg>
            </button>
            <span>AURA Shield</span>
            <span className="sep">/</span>
            <b>{sectionLabel}</b>
          </div>
          <div className="topstrip-actions">
            <span className="tag" title="Research prototype — not production software">research prototype</span>
            <ThemeToggle />
          </div>
        </header>

        <main className="page" id="content">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={location.pathname}
              initial={reduce ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={reduce ? undefined : { opacity: 0, y: -4 }}
              transition={{ duration: 0.22, ease: [0.2, 0.7, 0.3, 1] }}
            >
              <Routes location={location}>
                <Route path="/" element={<OverviewPage />} />
                <Route path="/system" element={<SystemSection />} />
                <Route path="/evaluation" element={<EvaluationSection />} />
                <Route path="/security" element={<SecuritySection />} />
                <Route path="/alignment" element={<AlignmentSection />} />
                <Route path="/repro" element={<ReproducibilitySection />} />
                <Route path="*" element={<OverviewPage />} />
              </Routes>
            </motion.div>
          </AnimatePresence>
        </main>

        <footer className="footer">
          <span>AURA Shield · adaptive prompt-injection defense · research build</span>
          <span>API <a href="/docs">/docs</a> · evidence <span className="mono">/api/evidence</span></span>
        </footer>
      </div>
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <Router>
        <Shell />
      </Router>
    </ThemeProvider>
  );
}

export default App;
