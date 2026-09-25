import { Cards, useEvidence } from '../api/evidence';

function ToolSecurityPage() {
  const { data, error } = useEvidence();
  if (error) return <div className="panel"><p className="error">Failed to load: {error}</p></div>;
  if (!data) return <div className="panel"><p className="muted">Loading…</p></div>;

  return (
    <div>
      <h2>Tool security — authorization boundary</h2>
      <div className="panel">
        <p className="mono">LLM → intent → authorize → validate args → security gate → sandbox → execute</p>
        <Cards items={[
          { k: 'unknown tool', v: 'DENY' },
          { k: 'critical action', v: 'REVIEW' },
          { k: 'high-danger, untrusted provenance', v: 'DENY' },
          { k: 'high-danger, no Docker', v: 'DENY (fail-closed)' },
          { k: 'low-danger stub', v: 'simulated only' },
        ]} />
        <p className="muted">The model never directly executes tools. Execution is real Docker isolation when
          available; simulation exists for low-danger demonstration only.</p>
      </div>
      <h3>Audit chain</h3>
      <div className="panel">
        <p><span className="mono">event[n].hash = SHA256(event[n] + event[n-1].hash)</span> — file-prototype log
          is hash-chained and tamper-tested; the production Postgres log table is NOT chained (future work).</p>
      </div>
    </div>
  );
}

export default ToolSecurityPage;
