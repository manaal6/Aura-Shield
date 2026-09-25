import { useEffect, useState } from 'react';

interface EvidenceBlock {
  has_data: boolean;
  data?: unknown;
}

type EvidenceData = Record<string, EvidenceBlock>;

const BLOCK_LABELS: Record<string, string> = {
  frozen_rerun_new_system: 'Frozen re-run — new system (C1–C10 + max fusion)',
  fusion_live_compare: 'Fusion live comparison (DEV, clean rows)',
  downstream_asr: 'Downstream ASR (canary, bypass ≠ success)',
  over_refusal: 'Over-refusal (benign adversarial prompts)',
  load_sweep: 'Load / concurrency sweep',
  redteam_live: 'Live red-team smoke',
  multiturn_live: 'Live multi-turn smoke',
  dpo_eval: 'DPO evaluation',
  dpo_qwen: 'DPO Qwen2.5-0.5B scale',
  unlearning_eval: 'Unlearning evaluation',
};

function Block({ name, block }: { name: string; block: EvidenceBlock }) {
  const label = BLOCK_LABELS[name] ?? name;
  if (!block.has_data) {
    return (
      <div className="panel">
        <h3>{label}</h3>
        <p className="muted">NOT AVAILABLE — experiment artifact absent (not run). No number invented.</p>
      </div>
    );
  }
  return (
    <div className="panel">
      <h3>{label}</h3>
      <pre className="mono json">{JSON.stringify(block.data, null, 2)}</pre>
    </div>
  );
}

function EvidencePage() {
  const [data, setData] = useState<EvidenceData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/evidence')
      .then((r) => {
        if (!r.ok) throw new Error(`Request failed (${r.status})`);
        return r.json();
      })
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <div className="panel"><p className="error">Failed to load evidence: {error}</p></div>;
  if (!data) return <div className="panel"><p className="muted">Loading evidence artifacts…</p></div>;

  return (
    <div>
      <h2>Research evidence</h2>
      <p className="muted">
        Every block below comes from a persisted experiment artifact via <span className="mono">/api/evidence</span>.
        Missing artifacts render as NOT AVAILABLE — never as invented numbers.
      </p>
      {Object.entries(data).map(([name, block]) => (
        <Block key={name} name={name} block={block} />
      ))}
    </div>
  );
}

export default EvidencePage;
