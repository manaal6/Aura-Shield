import { useEffect, useState } from 'react';
import { fetchBenchmark } from '../api/client';
import type { BenchmarkData } from '../api/client';

const CATEGORY_LABELS: Record<string, string> = {
  direct_injection: 'Direct injection',
  indirect_injection: 'Indirect injection',
  jailbreak: 'Jailbreak',
  benign: 'Benign (should not flag)',
};

const METRIC_LABELS: Record<string, string> = {
  true_positives: 'True positives',
  false_negatives: 'False negatives',
  false_positives: 'False positives',
  true_negatives: 'True negatives',
  precision: 'Precision',
  recall: 'Recall',
  attack_success_rate: 'Attack success rate',
  false_positive_rate: 'False positive rate',
};

function pct(k: string, v: number) {
  return ['precision', 'recall', 'attack_success_rate', 'false_positive_rate'].includes(k)
    ? `${(v * 100).toFixed(1)}%`
    : String(v);
}

function BenchmarkPage() {
  const [data, setData] = useState<BenchmarkData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBenchmark()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div><h2>Benchmark</h2><p className="loading">Loading…</p></div>;
  if (error) return <div><h2>Benchmark</h2><p className="error">{error}</p></div>;
  if (!data?.has_data) {
    return (
      <div>
        <h2>Benchmark</h2>
        <div className="panel">
          <p className="muted" style={{ margin: 0 }}>
            No evaluation artifacts found on the server. Run{' '}
            <span className="mono">python evaluation/evaluate.py</span> to produce{' '}
            <span className="mono">evaluation/results.json</span> and{' '}
            <span className="mono">evaluation/metrics_summary.json</span>, then reload this page.
          </p>
        </div>
      </div>
    );
  }

  const m = data.metrics ?? {};
  const attr = data.attribution;

  return (
    <div>
      <h2>Benchmark</h2>
      <p className="muted">
        Evaluation of the full shield over {data.n} test cases
        {data.real_llm_calls_used ? ' with live LLM calls' : ' using offline fallback classifiers'}.
        Artifacts are produced by <span className="mono">evaluation/evaluate.py</span> — the console does not compute these numbers.
      </p>

      <section>
        <h3>Overall metrics</h3>
        <div className="cards">
          {Object.entries(m).map(([k, v]) => (
            <div className="card" key={k}>
              <div className="k">{METRIC_LABELS[k] ?? k}</div>
              <div className="v">{pct(k, v)}</div>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h3>By attack category</h3>
        <div className="table-wrap panel">
          <table>
            <thead><tr><th>Category</th><th>Test cases</th><th>Flagged</th><th>Detection rate</th></tr></thead>
            <tbody>
              {Object.entries(data.by_category ?? {}).map(([cat, c]) => (
                <tr key={cat}>
                  <td>{CATEGORY_LABELS[cat] ?? cat}</td>
                  <td className="mono">{c.total}</td>
                  <td className="mono">{c.flagged}</td>
                  <td className="mono">{c.total ? `${((c.flagged / c.total) * 100).toFixed(0)}%` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {attr && (
        <section>
          <h3>Signal attribution ({attr.total_flagged} flagged attacks)</h3>
          <div className="cards">
            <div className="card"><div className="k">Rule + LLM</div><div className="v">{attr.rule_and_llm}</div></div>
            <div className="card"><div className="k">Rule match, LLM fallback</div><div className="v">{attr.rule_only_support}</div></div>
            <div className="card"><div className="k">LLM signal alone</div><div className="v">{attr.llm_only}</div></div>
            <div className="card">
              <div className="k">Constitution alone</div>
              <div className="v" style={{ fontSize: '1rem', color: 'var(--text-dim)' }}>n/a</div>
            </div>
          </div>
          <p className="muted">
            Per-row constitution attribution is not recorded in the evaluation artifacts, so it is
            reported as unavailable rather than estimated.
          </p>
        </section>
      )}
    </div>
  );
}

export default BenchmarkPage;
