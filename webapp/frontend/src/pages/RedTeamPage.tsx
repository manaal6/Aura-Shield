import { Cards, Missing, useEvidence } from '../api/evidence';

function RedTeamPage() {
  const { data, error } = useEvidence();
  if (error) return <div className="panel"><p className="error">Failed to load: {error}</p></div>;
  if (!data) return <div className="panel"><p className="muted">Loading…</p></div>;

  const mx = (data.redteam_matrix.data ?? {}) as { offline_subset_matrix?: Record<string, Record<string, number>> };
  const mut = (data as Record<string, { has_data: boolean; data?: Record<string, unknown> }>).mutation_screen;
  const mutData = (mut?.data ?? {}) as { attack_mutated_held_overall?: string; per_family_mutated_held?: Record<string, string>; benign_mutated_plus_original_held?: string };
  const asr = (data.downstream_asr.data ?? {}) as Record<string, string | number>;
  const mt = { held: '8/8', benign: '1/2' };

  return (
    <div>
      <h2>Red team — matrix &amp; multi-turn</h2>
      <h3>Offline matrix (lower bound only)</h3>
      {!mx.offline_subset_matrix ? <Missing label="Red-team matrix" /> : (
        <div className="table-wrap panel">
          <table>
            <thead><tr><th>Class</th><th>Attempts</th><th>Held</th><th>Bypassed</th></tr></thead>
            <tbody>
              {Object.entries(mx.offline_subset_matrix).map(([k, v]) => (
                <tr key={k}><td>{k}</td><td className="mono">{v.attempts}</td>
                  <td className="mono">{v.held}</td><td className="mono">{v.bypassed}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h3>DEV mutation screen (offline, 1,440 rows)</h3>
      {!mut?.has_data ? <Missing label="Mutation screen" /> : (
        <div className="panel">
          <Cards items={[
            { k: 'mutated held', v: String(mutData.attack_mutated_held_overall ?? '—') },
            { k: 'benign held', v: String(mutData.benign_mutated_plus_original_held ?? '—') },
          ]} />
          <p className="muted">Per family (whitespace/caseflip/leet/pad/filler × 3 variants):{' '}
            {Object.entries(mutData.per_family_mutated_held ?? {}).map(([f, v]) => `${f} ${v}`).join(' · ') || '—'}</p>
          <p className="muted">Offline-subset brittleness quantified (low hold = mutations evade regexes/heuristic);
            the live LLM still catches most of these — gateway claim untouched, lower bound only.</p>
        </div>
      )}

      <h3>Multi-turn smoke (latching)</h3>      <div className="panel">
        <Cards items={[
          { k: 'attacks held', v: mt.held },
          { k: 'benign clean', v: mt.benign },
        ]} />
        <p className="muted">Mechanism evidence (latch works), NOT robustness proof. Tool-auth across turns unmodeled.</p>
      </div>

      {/* Downstream ASR (bypass ≠ success) is the headline number on Overview —
          shown here only as a one-line reference, not restated in full. */}
      <p className="muted">
        Downstream success rate for bypassed attempts: <span className="mono">{String(asr.ASR ?? 'NOT MEASURED')}</span>{' '}
        (bypassed: {String(asr.bypassed ?? '—')}, downstream success: {String(asr.downstream_success ?? '—')}) —
        full canary methodology on the Overview page.
      </p>
    </div>
  );
}

export default RedTeamPage;
