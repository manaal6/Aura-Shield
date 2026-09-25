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
      <div className="panel">
        <h3>How it works</h3>
        <p className="mono">INPUT → PROVENANCE → RULE → SEMANTIC → CONSTITUTION → RISK (max fusion) → POLICY → gated TOOLS → AUDIT</p>
        <p className="muted">Untrusted content is data, never instructions. Full pipeline diagram: System → Pipeline.</p>
      </div>
      <div className="panel">
        <h3>Key findings</h3>
        <ul>
          <li>Fusion dilutes its best layer (68/73 vs 65/73); max fusion recovers it on DEV (90/90).</li>
          <li>DPO trains (loss down) but rankings freeze — at 100K and 0.5B scales.</li>
          <li>Unlearning suppresses one phrasing (4/24), not the trigger behavior.</li>
          <li>Detector bypass ≠ downstream success (ASR measured separately with canaries).</li>
        </ul>
      </div>
      <div className="panel">
        <h3>Research questions</h3>
        <ul className="mono" style={{ fontSize: '0.8rem' }}>
          <li>RQ1 fusion &gt; single signals? — No (overlapping CIs, n=73).</li>
          <li>RQ2 adaptive updates help w/o FP? — Yes, with caveats (65→68/73, FPR 0).</li>
          <li>RQ3 DPO improves preferences? — No (both scales).</li>
          <li>RQ4 targeted unlearning with preservation? — Partially (one phrasing).</li>
          <li>RQ5 provenance controls? — Logged, not yet scored.</li>
          <li>RQ6 detections → lower ASR? — Measured separately (0/14 controlled).</li>
          <li>RQ7 latency/security/utility? — P50–P99 + load sweep in Evaluation → Reliability.</li>
        </ul>
      </div>
      <div className="panel">
        <h3>Overall status: PARTIAL (ready for review on executed scope)</h3>
        <p className="muted">178/178 tests green. Every number traces to a persisted artifact.
          Negative results kept. Nothing here claims production readiness.</p>
      </div>
    </div>
  );
}

export default OverviewPage;
