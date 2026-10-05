import { Cards, Missing, useEvidence } from '../api/evidence';

function ReliabilityPage() {
  const { data, error } = useEvidence();
  if (error) return <div className="panel"><p className="error">Failed to load: {error}</p></div>;
  if (!data) return <div className="panel"><p className="muted">Loading…</p></div>;

  const ben = (data as Record<string, { has_data: boolean; data?: Record<string, unknown> }>).benign;
  const benData = (ben?.data ?? {}) as { n?: number; held_benign?: number; over_trigger_rate?: number; by_trigger_word?: Record<string, string> };
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
      <h3>Benign robustness (trigger-word challenge, offline)</h3>
      {!ben?.has_data ? <Missing label="Benign challenge" /> : (
        <div className="panel">
          <Cards items={[
            { k: 'held', v: `${String(benData.held_benign ?? '—')}/${String(benData.n ?? '—')}` },
            { k: 'over-trigger rate', v: String(benData.over_trigger_rate ?? '—') },
          ]} />
          <p className="muted">By trigger word:{' '}
            {Object.entries(benData.by_trigger_word ?? {}).map(([w, v]) => `${w} ${v}`).join(' · ') || '—'}</p>
          <p className="muted">Legitimate trigger-word prompts the offline subset holds (0 = no lexical
            over-triggering). Live FPR is measured separately on the frozen run (1/32).</p>
          {(data as Record<string, { has_data: boolean; data?: Record<string, unknown> }>).benign_live?.has_data && (
            <p>Live benign (16 families × 3, full gateway):{' '}
              {(() => {
                const d = ((data as Record<string, { has_data: boolean; data?: Record<string, unknown> }>).benign_live?.data ?? {}) as Record<string, string | number>;
                return `${String(d.held ?? '—')}/${String(d.n ?? '—')} held, ${String(d.fallback ?? '—')} fallbacks`;
              })()} — combined live FPR 2/80 = 2.5% with the frozen run.</p>
          )}
        </div>
      )}
      <h3>Outage test (simulated full model outage, 50+50)</h3>
      {(() => {
        const ot = ((data as Record<string, { has_data: boolean; data?: Record<string, unknown> }>).outage_test?.data ?? {}) as Record<string, string | number>;
        return (
          <div className="panel">
            <Cards items={[
              { k: 'attacks held', v: `${String(ot.attacks_held ?? '—')}/${String(ot.n_attacks ?? '—')}` },
              { k: 'benign allowed', v: `${String(ot.benign_allowed ?? '—')}/${String(ot.n_benign ?? '—')}` },
            ]} />
            <p className="muted">Full hold: safe under outage, zero benign utility. The graduated-ALLOW path is
              unreachable in prod wiring (test/prod gap recorded) — fix requires plumbing source_content into decide().</p>
          </div>
        );
      })()}
      <h3>Constitution</h3>
      <div className="panel">
        <p>v2 seed C1–C10 (production DB migrates additively; existing rows never modified).
          Approvals require <span className="mono">AURA_APPROVAL_HMAC_SECRET</span> — never a provider key.</p>
      </div>
    </div>
  );
}

export default ReliabilityPage;
