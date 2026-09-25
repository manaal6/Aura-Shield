import { Cards, Missing, useEvidence } from '../api/evidence';

function OverviewPage() {
  const { data, error } = useEvidence();
  if (error) return <div className="panel"><p className="error">Failed to load: {error}</p></div>;
  if (!data) return <div className="panel"><p className="muted">Loading…</p></div>;

  const frozen = data.frozen_rerun_new_system;
  const fz = (frozen.data ?? {}) as Record<string, string>;
  const asr = (data.downstream_asr.data ?? {}) as Record<string, string>;

  return (
    <div>
      <h2>AURA Shield — research overview</h2>
      <div className="cards">
        <div className="card"><div className="k">Held-out C (constitution-only)</div><div className="v">68/73</div></div>
        <div className="card"><div className="k">Held-out G (old full)</div><div className="v">65/73</div></div>
        <div className="card"><div className="k">New system (frozen re-run)</div><div className="v">67/73</div></div>
        <div className="card"><div className="k">Benign FPR (new)</div><div className="v">1/32</div></div>
      </div>
      <div className="panel">
        <h3>Current research question</h3>
        <p>Constitution-only <span className="mono">68/73 (93.2%)</span> vs old full blend{' '}
          <span className="mono">65/73 (89.0%)</span> — overlapping 95% CIs (RQ1 negative).
          New system (C1–C10 + max fusion): <span className="mono">67/73</span> with 1 FP.
          Status: <strong>FUSION UNDER INVESTIGATION</strong>.</p>
      </div>
      {frozen.has_data ? (
        <div className="panel">
          <h3>Frozen re-run (single eval, policy frozen)</h3>
          <Cards items={[
            { k: 'recall', v: String(fz.recall ?? '—') },
            { k: 'FPR', v: String(fz.fpr ?? '—') },
            { k: 'fallback rows', v: String(fz.fallback_rows ?? '—') },
            { k: 'status', v: String(fz.status ?? '—') },
          ]} />
        </div>
      ) : <Missing label="Frozen re-run" />}
      <div className="panel">
        <h3>Downstream ASR (bypass ≠ success)</h3>
        <p className="mono">{String(asr.ASR ?? 'NOT MEASURED')}</p>
        <p className="muted">Downstream evaluated: {String(asr.downstream_evaluated ?? '—')} · success: {String(asr.downstream_success ?? '—')}</p>
      </div>
    </div>
  );
}

export default OverviewPage;
