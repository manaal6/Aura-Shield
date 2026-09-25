import { Cards, useEvidence } from '../api/evidence';

function ReliabilityPage() {
  const { data, error } = useEvidence();
  if (error) return <div className="panel"><p className="error">Failed to load: {error}</p></div>;
  if (!data) return <div className="panel"><p className="muted">Loading…</p></div>;

  return (
    <div>
      <h2>Reliability — latency, load, outage</h2>
      <h3>Fail-safe contract</h3>
      <div className="panel">
        <Cards items={[
          { k: 'analyzer failure', v: 'REVIEW' },
          { k: 'empty input', v: 'REVIEW' },
          { k: 'malformed output', v: 'REVIEW' },
          { k: 'unknown tool', v: 'DENY' },
        ]} />
      </div>
      <h3>Outage test (simulated full model outage, 50+50)</h3>
      <div className="panel">
        <Cards items={[
          { k: 'attacks held', v: '50/50' },
          { k: 'benign allowed', v: '0/50' },
        ]} />
        <p className="muted">Full hold: safe under outage, zero benign utility. The graduated-ALLOW path is
          unreachable in prod wiring (test/prod gap recorded) — fix requires plumbing source_content into decide().</p>
      </div>
      <h3>Constitution</h3>
      <div className="panel">
        <p>v2 seed C1–C10 (production DB migrates additively; existing rows never modified).
          Approvals require <span className="mono">AURA_APPROVAL_HMAC_SECRET</span> — never a provider key.</p>
      </div>
    </div>
  );
}

export default ReliabilityPage;
