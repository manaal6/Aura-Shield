import { useEffect, useState } from 'react';
import { fetchBenchmark, fetchMeasured } from '../api/client';
import type { BenchmarkData, MeasuredData, HeldoutBaselineRow } from '../api/client';

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

function fmtPct(v: number | null | undefined) {
  return v === null || v === undefined ? '—' : `${(v * 100).toFixed(1)}%`;
}

function Collapsible({ title, children, defaultOpen = false }: { title: string; children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="panel collapsible">
      <button className="collapsible-head" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        <span>{title}</span>
        <span className="collapsible-chevron">{open ? '−' : '+'}</span>
      </button>
      {open && <div className="collapsible-body">{children}</div>}
    </div>
  );
}

function HeldoutMatrix({ rows }: { rows: HeldoutBaselineRow[] }) {
  return (
    <div className="table-wrap panel">
      <table>
        <thead>
          <tr><th>Baseline</th><th>Recall</th><th>Precision</th><th>F1</th><th>FPR</th><th>Recall CI95</th><th>Latency</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.key} style={r.key === 'G' ? { background: 'var(--bg-raised)' } : undefined}>
              <td><strong>{r.key}</strong> — {r.name}</td>
              <td className="mono">{fmtPct(r.recall)}{r.true_positives !== null ? ` (${r.true_positives}/${r.n_attacks})` : ''}</td>
              <td className="mono">{fmtPct(r.precision)}</td>
              <td className="mono">{r.f1 === null ? '—' : r.f1.toFixed(3)}</td>
              <td className="mono">{fmtPct(r.fpr)}</td>
              <td className="mono">{r.recall_ci_95 ? `[${(r.recall_ci_95[0]*100).toFixed(1)}%, ${(r.recall_ci_95[1]*100).toFixed(1)}%]` : '—'}</td>
              <td className="mono">{r.avg_latency_ms === null ? '—' : `${Math.round(r.avg_latency_ms)} ms`}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function BenchmarkPage() {
  const [data, setData] = useState<BenchmarkData | null>(null);
  const [measured, setMeasured] = useState<MeasuredData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchBenchmark(), fetchMeasured().catch(() => null)])
      .then(([b, m]) => { setData(b); setMeasured(m); })
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div><h2>Benchmark</h2><p className="loading">Loading…</p></div>;
  if (error) return <div><h2>Benchmark</h2><p className="error">{error}</p></div>;
  const hb = measured?.heldout_baselines;
  const ab = measured?.adaptive_before_after;
  const soc = measured?.soc;

  return (
    <div>
      <h2>Benchmark</h2>
      {error && <p className="error">{error}</p>}

      {hb?.rows?.length ? (
        <section>
          <h3>Held-out baseline matrix — live model runs (105 prompts: {hb.rows[0].n_attacks} attacks, {hb.rows[0].n_benign} benign)</h3>
          <p className="muted">
            All LLM-dependent baselines executed with live model calls, zero offline-fallback rows.
            Note: full blend (G) is not statistically distinguishable from constitution-only (C) at
            this sample size — overlapping 95% CIs.
          </p>
          <HeldoutMatrix rows={hb.rows} />
        </section>
      ) : null}

      {ab ? (
        <section>
          <h3>Adaptive constitution — measured before/after (held-out, full gateway)</h3>
          <p className="muted">{ab.description}</p>
          <div className="table-wrap panel">
            <table>
              <thead><tr><th>Constitution</th><th>Recall</th><th>Precision</th><th>F1</th><th>FPR</th></tr></thead>
              <tbody>
                <tr><td>v{ab.before.constitution_version} (before)</td><td className="mono">{fmtPct(ab.before.recall)} ({ab.before.true_positives}/73)</td><td className="mono">{fmtPct(ab.before.precision)}</td><td className="mono">{ab.before.f1?.toFixed(3)}</td><td className="mono">{fmtPct(ab.before.fpr)}</td></tr>
                <tr><td>v{ab.after.constitution_version} (after adaptive update)</td><td className="mono">{fmtPct(ab.after.recall)} ({ab.after.true_positives}/73)</td><td className="mono">{fmtPct(ab.after.precision)}</td><td className="mono">{ab.after.f1?.toFixed(3)}</td><td className="mono">{fmtPct(ab.after.fpr)}</td></tr>
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {soc ? (
        <section>
          <h3>SOC workflow ({soc.total_prompts_evaluated} prompts, full gateway, live)</h3>
          <div className="cards">
            <div className="card"><div className="k">Benign utility</div><div className="v">{fmtPct(soc.benign_utility_rate)}</div><div className="muted">{soc.legitimate_soc_queries} legitimate queries</div></div>
            <div className="card"><div className="k">Payload detection</div><div className="v">{fmtPct(soc.embedded_payload_detection_rate)}</div><div className="muted">{soc.embedded_attacks_evaluated} adversarial prompts</div></div>
            <div className="card"><div className="k">Tool authorization</div><div className="v">{fmtPct(soc.tool_authorization_enforcement_rate)}</div><div className="muted">{soc.tool_injections_evaluated} injection attempts</div></div>
          </div>
        </section>
      ) : null}

      {/* Superseded by the live held-out matrix above — kept for reproducibility, collapsed by default. */}
      {data && (
        <Collapsible title="Offline safety evaluation (legacy artifacts)">
          <LegacyBenchmarkSection data={data} />
        </Collapsible>
      )}
    </div>
  );
}

function LegacyBenchmarkSection({ data }: { data: BenchmarkData }) {
  if (!data?.has_data) {
    return (
      <p className="muted" style={{ margin: 0 }}>
        No evaluation artifacts found on the server. Run{' '}
        <span className="mono">python evaluation/evaluate.py</span> to produce{' '}
        <span className="mono">evaluation/results.json</span> and{' '}
        <span className="mono">evaluation/metrics_summary.json</span>, then reload this page.
      </p>
    );
  }

  const m = data.metrics ?? {};
  const attr = data.attribution;

  return (
    <div>
      <p className="muted">
        Offline safety evaluation of the shield over {data.n} test cases
        {data.real_llm_calls_used ? ' with live LLM calls' : ' using offline fallback classifiers'}.
        Artifacts produced by <span className="mono">evaluation/evaluate.py</span>.
      </p>

      <h3>Overall metrics</h3>
      <div className="cards">
        {Object.entries(m).map(([k, v]) => (
          <div className="card" key={k}>
            <div className="k">{METRIC_LABELS[k] ?? k}</div>
            <div className="v">{pct(k, v)}</div>
          </div>
        ))}
      </div>

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

      {attr && (
        <>
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
        </>
      )}
    </div>
  );
}

export default BenchmarkPage;
