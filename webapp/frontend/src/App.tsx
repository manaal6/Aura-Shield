
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

function App() {
  return (
    <Router>
      <nav style={{ padding: '1rem', borderBottom: '1px solid #eee' }}>
        <Link to="/" style={{ marginRight: '1rem' }}>Analyze</Link>
        <Link to="/logs" style={{ marginRight: '1rem' }}>Logs</Link>
        <Link to="/constitution" style={{ marginRight: '1rem' }}>Constitution</Link>
        <Link to="/benchmark">Benchmark</Link>
      </nav>
      <Routes>
        <Route path="/" element={<div>Analyze Page (to be implemented)</div>} />
        <Route path="/logs" element={<div>Logs Page (to be implemented)</div>} />
        <Route path="/constitution" element={<div>Constitution Page (to be implemented)</div>} />
        <Route path="/benchmark" element={<div>Benchmark Page (to be implemented)</div>} />
      </Routes>
    </Router>
  );
}

export default App;
