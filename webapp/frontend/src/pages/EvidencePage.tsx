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
  dpo_qwen_hot: 'DPO Qwen2.5-0.5B hotter run',
  dpo_qwen_hot2: 'DPO Qwen2.5-0.5B hotter replicate',
  unlearning_eval: 'Unlearning evaluation',
  unlearning_hot: 'Unlearning Qwen2.5-0.5B hot run',
  unlearning_hot2: 'Unlearning Qwen2.5-0.5B hot replicate',
  unlearning_fact: 'Unlearning Qwen2.5-0.5B real-fact run',
  mutation_screen: 'DEV mutation screen (1,350 mutated + 90 originals, offline)',
  fusion_disagreement: 'Fusion disagreement forensics (DEV, offline)',
  adaptive_cycle: 'Adaptive cycle C8 (approved)',
  redteam_matrix: 'Red-team offline matrix (lower bound)',
  multiturn_eval: 'Multi-turn offline eval (6 convos)',
  latency_detail: 'Latency detail (offline + live averages)',
  outage_test: 'Outage test (simulated full outage)',
  data_manifest: 'Dataset manifest (hashes)',
  statistics: 'Statistics (CIs, pooled, McNemar note)',
  benign: 'Benign challenge (trigger-word prompts, offline)',
  benign_live: 'Benign live48 (16 families × 3, full gateway)',
  soc_demo: 'SOC triage demo (malicious log → safe output, LIVE)',
  payload_explain: 'Refuse-payload-but-explain (20 paired, LIVE)',
};

// Pull one or two headline fields out of an artifact's data so the collapsed
// row shows something meaningful instead of forcing an open JSON dump.
function summarize(data: unknown): string | null {
  if (!data || typeof data !== 'object') return null;
  const d = data as Record<string, unknown>;
  const preferredKeys = [
    'recall', 'fpr', 'precision', 'f1', 'ASR', 'status',
    'attack_resistance', 'over_refusal_rate', 'verdict',
  ];
  const found = preferredKeys
    .filter((k) => k in d)
    .map((k) => `${k}: ${String(d[k])}`);
  if (found.length > 0) return found.slice(0, 3).join(' · ');
  const keys = Object.keys(d);
  return keys.length > 0 ? `${keys.length} field${keys.length === 1 ? '' : 's'} recorded` : null;
}

function Block({ name, block }: { name: string; block: EvidenceBlock }) {
  const [open, setOpen] = useState(false);
  const label = BLOCK_LABELS[name] ?? name;

  if (!block.has_data) {
    return (
      <div className="panel evidence-row">
        <div className="evidence-row-head">
          <h3 style={{ margin: 0 }}>{label}</h3>
          <span className="muted">NOT AVAILABLE — not run</span>
        </div>
      </div>
    );
  }

  const summary = summarize(block.data);

  return (
    <div className="panel evidence-row">
      <div className="evidence-row-head">
        <h3 style={{ margin: 0 }}>{label}</h3>
        <div className="evidence-row-actions">
          {summary && <span className="mono muted">{summary}</span>}
          <button className="btn" onClick={() => setOpen((o) => !o)}>
            {open ? 'Hide raw' : 'View raw'}
          </button>
        </div>
      </div>
      {open && <pre className="mono json" style={{ marginTop: '0.75rem' }}>{JSON.stringify(block.data, null, 2)}</pre>}
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
        Every row comes from a persisted experiment artifact via <span className="mono">/api/evidence</span>.
        Missing artifacts show as NOT AVAILABLE — never invented numbers. Expand a row for the full record.
      </p>
      {Object.entries(data).map(([name, block]) => (
        <Block key={name} name={name} block={block} />
      ))}
    </div>
  );
}

export default EvidencePage;
