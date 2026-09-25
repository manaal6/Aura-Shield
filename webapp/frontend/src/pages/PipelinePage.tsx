import { Cards, Missing, useEvidence } from '../api/evidence';

function PipelinePage() {
  const { data, error } = useEvidence();
  if (error) return <div className="panel"><p className="error">Failed to load: {error}</p></div>;

  const stages = [
    { name: 'INPUT', desc: 'user_prompt + untrusted source_content' },
    { name: 'PROVENANCE', desc: 'source tagged; untrusted content is data, never authority' },
    { name: 'RULE', desc: 'deterministic regex detector' },
    { name: 'SEMANTIC', desc: 'live LLM analyzer (fallback tracked per row)' },
    { name: 'CONSTITUTION', desc: 'C1–C10 versioned principles (live + heuristic)' },
    { name: 'RISK', desc: 'max-of-signals fusion (weighted-avg legacy as blended_score)' },
    { name: 'FUSION', desc: '0.40 review / 0.75 block; constitution 0.70/0.40 — policy choices, NOT optimized' },
    { name: 'AUTHORIZATION', desc: 'tool intent → auth → arg validation' },
    { name: 'EXECUTION', desc: 'sandbox; high-danger + no Docker = DENY (fail-closed)' },
  ];

  const lat = (data?.latency_detail?.data ?? {}) as Record<string, unknown>;
  const cpu = (lat.offline_cpu_ms ?? {}) as Record<string, Record<string, number>>;

  return (
    <div>
      <h2>Security pipeline</h2>
      <div className="panel">
        {stages.map((s, i) => (
          <div key={s.name} className="mono" style={{ padding: '0.25rem 0' }}>
            {i > 0 && <div style={{ color: 'var(--text-dim)' }}>↓</div>}
            <strong>{s.name}</strong> <span className="muted">— {s.desc}</span>
          </div>
        ))}
      </div>
      <h3>Component latency (offline CPU, n=40)</h3>
      {Object.keys(cpu).length === 0 ? <Missing label="Latency detail" /> : (
        <div className="table-wrap panel">
          <table>
            <thead><tr><th>Component</th><th>P50</th><th>P95</th><th>P99</th><th>Mean</th></tr></thead>
            <tbody>
              {Object.entries(cpu).map(([k, v]) => (
                <tr key={k}><td className="mono">{k}</td><td className="mono">{v.p50}</td>
                  <td className="mono">{v.p95}</td><td className="mono">{v.p99}</td><td className="mono">{v.mean}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <h3>Fail-safe contract</h3>
      <div className="panel">
        <Cards items={[
          { k: 'analyzer failure', v: 'REVIEW' },
          { k: 'empty input', v: 'REVIEW' },
          { k: 'unknown tool', v: 'DENY' },
          { k: 'high-danger, no Docker', v: 'DENY' },
        ]} />
        <p className="muted">Security-sensitive unknown states never silently ALLOW. Proven in tests/test_failsafe_audit.py.</p>
      </div>
    </div>
  );
}

export default PipelinePage;
