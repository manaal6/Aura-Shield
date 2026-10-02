import { useState } from 'react';
import { Missing, useEvidence } from '../api/evidence';

function Copy({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      className="copy-btn"
      onClick={() => {
        navigator.clipboard?.writeText(text).then(() => {
          setDone(true);
          setTimeout(() => setDone(false), 1500);
        }).catch(() => setDone(false));
      }}
    >
      {done ? 'Copied' : 'Copy'}
    </button>
  );
}

const COMMANDS = [
  'python -m pytest tests/ -q',
  'python -m experiments.kaust_three_pillars.run_all',
  'python -m research.fusion_forensics direct_injection.jsonl',
  'python -m research.canary_asr',
  'streamlit run dashboard/streamlit_app.py',
];

function ReproducibilityPage() {
  const { data, error } = useEvidence();
  if (error) return <div className="panel"><p className="error">Failed to load: {error}</p></div>;
  if (!data) return <div className="panel"><p className="muted">Loading…</p></div>;

  const man = (data.data_manifest.data ?? {}) as {
    datasets?: { dataset: string; split: string; samples: number; sha256_16: string; usage: string }[];
  };

  return (
    <div>
      <div className="kicker">07 · Reproducibility &amp; reference</div>
      <h2>Reproduce every number</h2>
      <p className="muted">All benchmark inputs are version-controlled JSONL; training runs on CPU or free
        Kaggle GPUs. Train/test isolation is enforced in code, not by convention.</p>

      <h3>Terminal execution protocol</h3>
      <div className="panel">
        <ol className="step-list">
          <li>Install dependencies and verify the offline suite (191 tests, ~2 min, no network).</li>
          <li>Run the three-pillar experiment suites (DPO, unlearning, constitution, integrated).</li>
          <li>Run live evaluations only with Groq quota (forensics, ASR, red-team); fallbacks are counted, never hidden.</li>
          <li>Compare printed means, win counts, and hashes against the tables in this console.</li>
        </ol>
        {COMMANDS.map((c) => (
          <div key={c} className="equation">{c}<Copy text={c} /></div>
        ))}
      </div>

      <h3>Dataset manifest (hashes)</h3>
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
      <p className="muted">Full command list: research/REPRODUCIBILITY.md. Train/test isolation enforced by
        research/data_governance.py guards (tested — including a live blocked-violation test).</p>
    </div>
  );
}

export default ReproducibilityPage;
