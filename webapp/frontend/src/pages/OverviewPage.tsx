import { useState } from 'react';
import { Cards, Missing, useEvidence } from '../api/evidence';

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

function OverviewPage() {
  const { data, error } = useEvidence();
  if (error) return <div className="panel"><p className="error">Failed to load: {error}</p></div>;
  if (!data) return <div className="panel"><p className="muted">Loading…</p></div>;

  const frozen = data.frozen_rerun_new_system;
  const fz = (frozen.data ?? {}) as Record<string, string>;
  const asr = (data.downstream_asr.data ?? {}) as Record<string, string>;

  return (
    <div>
      <div className="kicker">01 · Overview — threat → defense → evidence → limits in 90 seconds</div>
      <h2>AURA Shield — auditable prompt-injection defense gateway</h2>

      <div className="plain-words">
        <h4>The threat (30 seconds)</h4>
        <p style={{ margin: 0 }}>LLM assistants in security workflows face injected instructions hiding in
          logs, emails, documents, and tool output — aiming to exfiltrate data, run commands, or
          reproduce malware. Three detectors plus a versioned safety constitution screen every
          request; the strongest signal wins instead of being averaged away.</p>
      </div>

      <div className="kicker">The evidence (30 seconds)</div>
      <div className="hero">
        <div className="hero-card winner">
          <div className="who">Constitution-only · held-out</div>
          <div className="big">68/73</div>
          <div className="sub">93.2% recall · 100% precision · FPR 0/32</div>
        </div>
        <div className="hero-card">
          <div className="who">New full system (frozen re-run)</div>
          <div className="big">67/73</div>
          <div className="sub">91.8% recall · FPR 1/32 · 3 fallback rows (counted, not predicted)</div>
        </div>
        <div className="hero-card loser">
          <div className="who">Old full blend · held-out</div>
          <div className="big">65/73</div>
          <div className="sub">89.0% recall · superseded by the frozen re-run above</div>
        </div>
      </div>

      <div className="plain-words">
        <h4>In plain words</h4>
        <p style={{ margin: 0 }}>AURA Shield screens every request with three independent detectors plus a
          versioned safety constitution before any LLM or tool acts. When detectors disagree, the
          strongest signal wins (max fusion) instead of being averaged away. Failures teach the
          constitution new principles — with human approval, never silently. Separately, preference
          training (DPO) and targeted unlearning try to change the model itself; both are measured
          honestly, including when they fail.</p>
      </div>

      <div className="panel">
        <h3>Current research question — FUSION UNDER INVESTIGATION</h3>
        <p>
          Constitution-only beats the old full blend on held-out (overlapping CIs — see{' '}
          <span className="mono">Evaluation → Benchmark</span> for the full matrix and the
          frozen re-run breakdown).
        </p>
      </div>

      <Collapsible title="Frozen re-run detail">
        {frozen.has_data ? (
          <Cards items={[
            { k: 'recall', v: String(fz.recall ?? '—') },
            { k: 'FPR', v: String(fz.fpr ?? '—') },
            { k: 'fallback rows', v: String(fz.fallback_rows ?? '—') },
            { k: 'status', v: String(fz.status ?? '—') },
          ]} />
        ) : <Missing label="Frozen re-run" />}
      </Collapsible>

      <Collapsible title="Downstream ASR (bypass ≠ success)">
        <p className="mono">{String(asr.ASR ?? 'NOT MEASURED')}</p>
        <p className="muted">Downstream evaluated: {String(asr.downstream_evaluated ?? '—')} · success: {String(asr.downstream_success ?? '—')}</p>
      </Collapsible>

      <Collapsible title="Key findings">
        <ul>
          <li>Fusion dilutes its best layer (68/73 vs 65/73); max fusion recovers it on DEV (90/90).</li>
          <li>DPO trains (loss down, incl. loss → 0.0000 hotter) but rankings freeze — at 100K, 0.5B, and hotter.</li>
          <li>Unlearning: template-specific at gentle intensities; FULL removal with preservation (24/24, all λ) on the hotter Qwen run.</li>
          <li>Detector bypass ≠ downstream success (ASR measured separately with canaries).</li>
          <li>SOC path live: malicious log → triage → safe output demonstrated (3/5 held, 2/2 safe).</li>
          <li>Malware loop closed: payload requests held 10/10, benign explainers safe 10/10.</li>
        </ul>
      </Collapsible>

      <Collapsible title="Open research questions">
        <ul className="mono" style={{ fontSize: '0.8rem' }}>
          <li>RQ1 fusion &gt; single signals? — No (overlapping CIs, n=73).</li>
          <li>RQ2 adaptive updates help w/o FP? — Yes, with caveats (65→68/73, FPR 0).</li>
          <li>RQ3 DPO improves preferences? — No (both scales).</li>
          <li>RQ4 targeted unlearning with preservation? — Yes, with scope (hot Qwen run; partial/negative at lower intensities).</li>
          <li>RQ5 provenance controls? — Logged, not yet scored.</li>
          <li>RQ6 detections → lower ASR? — Measured separately (0/14 controlled).</li>
          <li>RQ7 latency/security/utility? — P50–P99 + load sweep in Evaluation → Reliability.</li>
        </ul>
      </Collapsible>

      <div className="kicker">Scope &amp; limitations</div>
      <div className="limit-grid">
        <div className="limit-card"><h4>Scale</h4><p>Alignment training at 100K–0.5B params; nothing transfers to LLM scale.</p></div>
        <div className="limit-card"><h4>Statistics</h4><p>Held-out n=73: CIs overlap; McNemar impossible (no paired data).</p></div>
        <div className="limit-card"><h4>Single provider</h4><p>Live layers on one Groq-hosted family + local CPU fallback (routing proven; independence needs a capable second judge).</p></div>
        <div className="limit-card"><h4>Approvals</h4><p>Past records SIMULATED. New approvals: named, HMAC-signed, verifiable — no login infrastructure.</p></div>
        <div className="limit-card"><h4>Tools</h4><p>Docker isolation implemented; high-danger fails closed without Docker; container path unvalidated on this host.</p></div>
        <div className="limit-card"><h4>Production</h4><p>Research prototype. Nothing here claims production readiness.</p></div>
      </div>

      <div className="panel">
        <h3>Overall status: PARTIAL (ready for review on executed scope)</h3>
        <p className="muted">193/193 tests green. Every number traces to a persisted artifact.
          Negative results kept. Nothing here claims production readiness.</p>
      </div>
    </div>
  );
}

export default OverviewPage;
