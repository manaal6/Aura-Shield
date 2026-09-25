import { Missing, useEvidence } from '../api/evidence';

function ReproducibilityPage() {
  const { data, error } = useEvidence();
  if (error) return <div className="panel"><p className="error">Failed to load: {error}</p></div>;
  if (!data) return <div className="panel"><p className="muted">Loading…</p></div>;

  const man = (data.data_manifest.data ?? {}) as {
    datasets?: { dataset: string; split: string; samples: number; sha256_16: string; usage: string }[];
  };

  return (
    <div>
      <h2>Reproducibility — datasets, hashes, commands</h2>
      {!man.datasets ? <Missing label="Data manifest" /> : (
        <div className="table-wrap panel">
          <table>
            <thead><tr><th>Dataset</th><th>Split</th><th>Samples</th><th>SHA256</th><th>Usage</th></tr></thead>
            <tbody>
              {man.datasets.map((d) => (
                <tr key={d.dataset}><td className="mono">{d.dataset}</td><td className="mono">{d.split}</td>
                  <td className="mono">{d.samples}</td><td className="mono">{d.sha256_16}</td><td>{d.usage}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="panel">
        <h3>Reproduce</h3>
        <pre className="mono">python -m pytest tests/ -q{"\n"}python -m experiments.kaust_three_pillars.run_all</pre>
        <p className="muted">Full command list: research/REPRODUCIBILITY.md. Train/test isolation enforced by
          research/data_governance.py guards (tested).</p>
      </div>
    </div>
  );
}

export default ReproducibilityPage;
