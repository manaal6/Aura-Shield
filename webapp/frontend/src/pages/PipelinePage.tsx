import { Cards, Missing, useEvidence } from '../api/evidence';

function PipelinePage() {
  const { data, error } = useEvidence();
  if (error) return <div className="panel"><p className="error">Failed to load: {error}</p></div>;

  const lat = ((data?.latency_detail?.data ?? {}) as Record<string, unknown>);
  const cpu = (lat.offline_cpu_ms ?? {}) as Record<string, Record<string, number>>;

  return (
    <div>
      <div className="kicker">02 · System architecture</div>
      <h2>How AURA Shield works: detection × policy</h2>

      <div className="plain-words">
        <h4>In plain words</h4>
        <p style={{ margin: 0 }}>Three independent detectors examine every request. A versioned
          constitution judges it against named safety principles. The strongest signal wins —
          never an average that hides a confident detector. Policy turns the score into a decision,
          and tools execute only through authorization and sandboxing.</p>
      </div>

      <div className="branch">
        <div className="b">
          <h4>Branch A · Detection</h4>
          <ol>
            <li>Rule detector: deterministic regex signatures.</li>
            <li>Semantic analyzer: live LLM intent judgement (fallback tracked per row).</li>
            <li>Constitution: C1–C10 per-principle verdicts with confidence.</li>
          </ol>
        </div>
        <div className="b">
          <h4>Branch B · Policy</h4>
          <ol>
            <li>Risk: max(rule, llm, constitution); weighted-avg kept as blended_score.</li>
            <li>Gate: 0.40 review / 0.75 block; constitution 0.70 block / 0.40 review.</li>
            <li>Tools: authorize → validate → gate → sandbox (fail-closed).</li>
          </ol>
        </div>
      </div>

      <div className="kicker">Formal specification</div>
      <div className="equation">score = max(rule_signal, llm_signal, constitution_signal)</div>
      <div className="equation">decision = BLOCK if score ≥ 0.75 · REVIEW if ≥ 0.40 · ALLOW otherwise</div>
      <p className="muted">Thresholds are IMPLEMENTED policy choices, NOT empirically optimized.
        Fallback signals (raw 0.0) are inconclusive — never counted as confident negatives.</p>

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
