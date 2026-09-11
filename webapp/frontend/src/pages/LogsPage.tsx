import { useCallback, useEffect, useState } from 'react';
import { fetchLogs, flagLog } from '../api/client';
import type { LogRow } from '../api/client';

function fmt(n: number | null) {
  return n === null || n === undefined ? '—' : n.toFixed(2);
}

function LogsPage() {
  const [rows, setRows] = useState<LogRow[]>([]);
  const [decision, setDecision] = useState('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flagging, setFlagging] = useState<string | null>(null);

  const load = useCallback(async (filter: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLogs(filter === 'all' ? {} : { decision: filter });
      setRows(data.rows);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(decision); }, [decision, load]);

  async function flag(requestId: string) {
    setFlagging(requestId);
    try {
      await flagLog(requestId);
      setRows((rs) => rs.map((r) => r.request_id === requestId ? { ...r, human_flagged: true } : r));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setFlagging(null);
    }
  }

  return (
    <div>
      <h2>Audit logs</h2>
      <p className="muted">Every request processed by the shield, newest first. Flag false negatives for human review.</p>

      <div className="btn-row">
        <select value={decision} onChange={(e) => setDecision(e.target.value)} style={{ width: 'auto' }}>
          <option value="all">All decisions</option>
          <option value="allow">Allow</option>
          <option value="review">Review</option>
          <option value="block">Block</option>
        </select>
        <button className="btn" onClick={() => load(decision)} disabled={loading}>Refresh</button>
        <span className="muted">{rows.length} row{rows.length === 1 ? '' : 's'}</span>
        {error && <span className="error">{error}</span>}
      </div>

      {loading ? (
        <p className="loading">Loading…</p>
      ) : rows.length === 0 ? (
        <p className="muted">No log rows{decision !== 'all' ? ` with decision "${decision}"` : ''}. Run some analyses first.</p>
      ) : (
        <div className="table-wrap panel" style={{ marginTop: '0.75rem' }}>
          <table>
            <thead>
              <tr>
                <th>Time</th><th>Prompt</th><th>Decision</th><th>Risk</th>
                <th>Rule</th><th>LLM</th><th>Const.</th><th>Flags</th><th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.request_id}>
                  <td className="mono" style={{ whiteSpace: 'nowrap' }}>{r.timestamp.replace('T', ' ').slice(0, 19)}</td>
                  <td className="prompt-cell" title={r.user_prompt}>{r.user_prompt}</td>
                  <td><span className={`badge ${r.decision}`}>{r.decision}</span></td>
                  <td className="mono">{fmt(r.risk_score)}</td>
                  <td className="mono">{fmt(r.rule_signal)}</td>
                  <td className="mono">{fmt(r.llm_signal)}{r.llm_used_fallback ? '*' : ''}</td>
                  <td className="mono">{fmt(r.constitution_signal)}{r.constitution_fallback ? '*' : ''}</td>
                  <td>{r.human_flagged ? '🚩 human' : ''}</td>
                  <td>
                    {!r.human_flagged && (
                      <button className="btn" disabled={flagging === r.request_id} onClick={() => flag(r.request_id)}>
                        {flagging === r.request_id ? '…' : 'Flag'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="muted">* = signal produced by the offline fallback instead of a live LLM call.</p>
    </div>
  );
}

export default LogsPage;
