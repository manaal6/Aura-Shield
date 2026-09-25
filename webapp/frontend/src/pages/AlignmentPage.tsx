import { Cards, Missing, useEvidence } from '../api/evidence';

function AlignmentPage() {
  const { data, error } = useEvidence();
  if (error) return <div className="panel"><p className="error">Failed to load: {error}</p></div>;
  if (!data) return <div className="panel"><p className="muted">Loading…</p></div>;

  return (
    <div>
      <DpoPanel data={data} />
      <UnlearningPanel data={data} />
    </div>
  );
}

export function DpoPanel({ data }: { data: NonNullable<ReturnType<typeof useEvidence>['data']> }) {
  const dpo = (data.dpo_eval.data ?? {}) as Record<string, Record<string, string | number>>;
  const qwen = (data.dpo_qwen.data ?? {}) as Record<string, string | number | boolean>;
  return (
    <div>
      <div className="panel">
        <h3>DPO status: FULL MODEL-LEVEL DPO — NEGATIVE generalization</h3>
        <p className="muted">Toy scale (102,714 params CPU). Loss down, ranking frozen. Nothing transfers to LLM scale.</p>
        {data.dpo_eval.has_data ? (
          <Cards items={[
            { k: 'dev pref', v: `${String(dpo.dpo?.preference_accuracy ?? '—')} (base ${String(dpo.base?.preference_accuracy ?? '—')})` },
            { k: 'unseen', v: `${String(dpo.dpo?.unseen_pref_accuracy ?? '—')} (base ${String(dpo.base?.unseen_pref_accuracy ?? '—')})` },
            { k: 'attack resistance', v: String(dpo.dpo?.attack_resistance ?? '—') },
            { k: 'over-refusal', v: String(dpo.dpo?.over_refusal_rate ?? '—') },
          ]} />
        ) : <Missing label="DPO eval" />}
        {data.dpo_qwen.has_data && (
          <p>Qwen2.5-0.5B (Kaggle T4, user-executed): loss {String(qwen.loss_first)}→{String(qwen.loss_last)},
            {' '}train {String(qwen.train_acc)}, dev {String(qwen.dev_after)}, unseen {String(qwen.unseen_after)} —{' '}
            scale did NOT unlock generalization.</p>
        )}
      </div>
    </div>
  );
}

export function UnlearningPanel({ data }: { data: NonNullable<ReturnType<typeof useEvidence>['data']> }) {
  return (
    <div className="panel">
      <h3>Unlearning: PARTIAL (toy) / NEGATIVE (0.5B)</h3>
      <UnlearningTable data={data} />
      <p className="muted">Suppression is template-specific (one phrasing family), not trigger-general. Qwen sweep: zero suppression at all λ.</p>
    </div>
  );
}

function UnlearningTable({ data }: { data: NonNullable<ReturnType<typeof useEvidence>['data']> }) {
  const unl = (data.unlearning_eval.data ?? {}) as {
    per_lambda?: Record<string, { verdict: string; before: Record<string, number>; after: Record<string, number> }>;
  };
  if (!data.unlearning_eval.has_data) return <Missing label="Unlearning eval" />;
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>λ</th><th>Verdict</th><th>Forget before→after</th></tr></thead>
        <tbody>
          {Object.entries(unl.per_lambda ?? {}).map(([lam, s]) => (
            <tr key={lam}><td className="mono">{lam}</td><td>{s.verdict}</td>
              <td className="mono">{s.before?.forget_success} → {s.after?.forget_success}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default AlignmentPage;
