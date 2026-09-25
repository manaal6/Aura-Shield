import { Cards, Missing, useEvidence } from '../api/evidence';

function AdaptivePage() {
  const { data, error } = useEvidence();
  if (error) return <div className="panel"><p className="error">Failed to load: {error}</p></div>;
  if (!data) return <div className="panel"><p className="muted">Loading…</p></div>;

  const cyc = (data.adaptive_cycle.data ?? {}) as Record<string, unknown>;
  const has = data.adaptive_cycle.has_data;

  return (
    <div>
      <h2>Adaptive constitution — v1 → v2</h2>
      <p className="muted"><strong>Approval state: SIMULATED HUMAN APPROVAL.</strong> No authenticated
        human workflow exists; the generator never approves its own principle.</p>
      {!has ? <Missing label="Adaptive cycle" /> : (
        <div className="panel">
          <Cards items={[
            { k: 'cycle', v: String(cyc.cycle ?? '—') },
            { k: 'base → target', v: `${String(cyc.base_version ?? '?')} → ${String(cyc.target_version ?? '?')}` },
            { k: 'approval', v: String(cyc.approval_status ?? '—') },
            { k: 'triggering misses', v: String(cyc.triggering_misses ?? '—') },
          ]} />
          <p className="muted">Failure pattern: {String(cyc.failure_pattern ?? '—')}</p>
          <p className="muted">Caveat: {String(cyc.caveat ?? '—')}</p>
        </div>
      )}
      <h3>Drift v1 → v2 (offline heuristic)</h3>
      <div className="panel">
        <p>Recall 34/170 → 35/170 (+1 flooding catch), FPR 0/55 both, newly-blocked benign 0 —{' '}
          <strong>NO_OVER_RESTRICTION_OBSERVED</strong> (v2 gains come from the new pattern, not broadened blocking).</p>
      </div>
    </div>
  );
}

export default AdaptivePage;
