import { useCallback, useEffect, useState } from 'react';
import { fetchConstitution, reviewPrinciple } from '../api/client';
import type { ConstitutionData, PendingPrinciple } from '../api/client';

function PendingCard({ p, onDone }: { p: PendingPrinciple; onDone: (msg: string, isError?: boolean) => void }) {
  const [actor, setActor] = useState('');
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);

  async function act(action: 'approve' | 'reject') {
    if (!actor.trim()) {
      onDone('Enter your name as the reviewing actor first.', true);
      return;
    }
    setBusy(true);
    try {
      const res = await reviewPrinciple(p.id, action, actor.trim(), reason.trim() || undefined);
      onDone(action === 'approve'
        ? `Approved — constitution is now v${res.new_version}.`
        : 'Rejected.');
    } catch (e) {
      onDone(e instanceof Error ? e.message : String(e), true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel" style={{ marginTop: '0.75rem' }}>
      <p style={{ marginTop: 0 }}>{p.principle_text}</p>
      <p className="muted">Rationale: {p.rationale}</p>
      <p className="muted mono" style={{ fontSize: '0.75rem' }}>
        Triggered by: {JSON.stringify(p.triggered_by)} · pending id #{p.id}
      </p>
      <div className="grid-2">
        <div>
          <label htmlFor={`actor-${p.id}`}>Reviewer (required)</label>
          <input id={`actor-${p.id}`} type="text" value={actor} onChange={(e) => setActor(e.target.value)} placeholder="your name" />
        </div>
        <div>
          <label htmlFor={`reason-${p.id}`}>Rejection note (used on reject)</label>
          <input id={`reason-${p.id}`} type="text" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="why reject, if rejecting" />
        </div>
      </div>
      <div className="btn-row">
        <button className="btn btn-ok" disabled={busy} onClick={() => act('approve')}>Approve</button>
        <button className="btn btn-danger" disabled={busy} onClick={() => act('reject')}>Reject</button>
      </div>
    </div>
  );
}

function ConstitutionPage() {
  const [data, setData] = useState<ConstitutionData | null>(null);
  const [notice, setNotice] = useState<{ msg: string; isError: boolean } | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setNotice(null);
    try {
      setData(await fetchConstitution());
    } catch (e) {
      setNotice({ msg: e instanceof Error ? e.message : String(e), isError: true });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  function done(msg: string, isError = false) {
    setNotice({ msg, isError });
    if (!isError) load();
  }

  if (loading) return <div><h2>Constitution</h2><p className="loading">Loading…</p></div>;
  if (!data) return <div><h2>Constitution</h2>{notice && <p className="error">{notice.msg}</p>}</div>;

  return (
    <div>
      <h2>Constitution</h2>
      <p className="muted">
        Active principles govern the constitution-check layer. Pending principles are
        drafts proposed by the adaptive loop after human flags; approving one bumps the version.
        Currently <span className="mono">v{data.version}</span> with {data.principles.length} active principles.
      </p>
      {notice && <p className={notice.isError ? 'error' : 'muted'}>{notice.msg}</p>}

      <section>
        <h3>Active principles</h3>
        <div className="table-wrap panel">
          <table>
            <thead><tr><th>ID</th><th>Principle</th><th>Rationale</th><th>Since</th></tr></thead>
            <tbody>
              {data.principles.map((p) => (
                <tr key={p.id}>
                  <td className="mono" style={{ whiteSpace: 'nowrap' }}>{p.id}</td>
                  <td style={{ maxWidth: 420 }}>{p.principle_text}</td>
                  <td className="muted" style={{ maxWidth: 380 }}>{p.rationale}</td>
                  <td className="mono">v{p.version_added}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h3>Pending review ({data.pending.length})</h3>
        {data.pending.length === 0 ? (
          <p className="muted">No principles awaiting review.</p>
        ) : (
          data.pending.map((p) => <PendingCard key={p.id} p={p} onDone={done} />)
        )}
      </section>

      <section>
        <h3>Changelog</h3>
        {data.changelog.length === 0 ? (
          <p className="muted">No changes recorded yet.</p>
        ) : (
          <div className="table-wrap panel">
            <table>
              <thead><tr><th>Time</th><th>Action</th><th>Principle</th><th>Actor</th><th>Reason</th></tr></thead>
              <tbody>
                {data.changelog.map((c, i) => (
                  <tr key={i}>
                    <td className="mono" style={{ whiteSpace: 'nowrap' }}>{String(c.timestamp).replace('T', ' ').slice(0, 19)}</td>
                    <td>{c.action}</td>
                    <td className="mono">{c.principle_id ?? '—'}</td>
                    <td>{c.actor ?? '—'}</td>
                    <td className="muted">{c.reason ?? ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

export default ConstitutionPage;
