import { Cards, Missing, useEvidence } from '../api/evidence';

function FusionLabPage() {
  const { data, error } = useEvidence();
  if (error) return <div className="panel"><p className="error">Failed to load: {error}</p></div>;
  if (!data) return <div className="panel"><p className="muted">Loading…</p></div>;

  const cmp = (data.fusion_live_compare.data ?? {}) as {
    clean_rows_only?: { n: number; strategies: Record<string, Record<string, string>> };
    evaluation_status?: Record<string, number | string>;
  };
  const dis = (data.fusion_disagreement.data ?? {}) as {
    disagreement_counts?: Record<string, number>;
    why_fusion_loses?: { mechanism?: string };
  };
  const strats = cmp.clean_rows_only?.strategies ?? {};

  return (
    <div>
      <h2>Fusion Lab — DEV vs HELD-OUT strictly separated</h2>
      <p className="muted">Test tuning is blocked by design: strategies compare on DEV only; held-out was evaluated once, frozen.</p>
      <h3>Live DEV strategy comparison (clean rows, n={cmp.clean_rows_only?.n ?? '—'})</h3>
      {Object.keys(strats).length === 0 ? <Missing label="Fusion live compare" /> : (
        <div className="table-wrap panel">
          <table>
            <thead><tr><th>Strategy</th><th>Recall</th><th>FPR</th><th>Benign utility</th><th>Review rate</th></tr></thead>
            <tbody>
              {Object.entries(strats).map(([k, v]) => (
                <tr key={k}><td className="mono">{k}</td><td className="mono">{v.recall}</td>
                  <td className="mono">{v.fpr}</td><td className="mono">{v.benign_utility}</td><td className="mono">{v.review_rate}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <h3>Evaluation status (fallback accounting)</h3>
      <Cards items={Object.entries(cmp.evaluation_status ?? {}).map(([k, v]) => ({ k, v: String(v) }))} />
      <h3>Why fusion loses (DEV disagreement forensics)</h3>
      <div className="panel">
        <p>{dis.why_fusion_loses?.mechanism ?? 'Analysis not available.'}</p>
        <p className="muted mono">Counts: {JSON.stringify(dis.disagreement_counts ?? {})}</p>
      </div>
    </div>
  );
}

export default FusionLabPage;
