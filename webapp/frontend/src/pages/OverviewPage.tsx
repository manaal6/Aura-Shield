import { motion, useReducedMotion } from 'framer-motion';
import { Cards, Missing, useEvidence } from '../api/evidence';
import { Accordion } from '../components/Accordion';

const LEDGER = [
  {
    name: 'Constitution-only',
    meta: 'C1–C10 · held-out · one-shot',
    score: '68', den: '/73', pct: 93.2, primary: true,
    note: '93.2% recall · 100% precision · FPR 0/32',
  },
  {
    name: 'New full system — frozen re-run',
    meta: 'max-fusion gateway · held-out · one-shot',
    score: '67', den: '/73', pct: 91.8, primary: false,
    note: '91.8% recall · FPR 1/32 · 3 fallback rows counted, not predicted',
  },
  {
    name: 'Old full blend — superseded',
    meta: 'weighted average · held-out · one-shot',
    score: '65', den: '/73', pct: 89.0, primary: false,
    note: '89.0% recall · kept for the record, not the headline',
  },
];

const FRESH = [
  { k: 'Pooled fresh attacks', v: '89.9%', sub: '275/306 · 95% CI 86.0–92.8%' },
  { k: 'Benign false positives', v: '1.9%', sub: '5/264 · 95% CI 0.8–4.4%' },
  { k: 'SOTA DeBERTa, same set', v: '61.1%', sub: '187/306 at equal 1.9% FPR' },
  { k: 'Live adaptive red-team', v: '97.4%', sub: '37/38 valid · 1/24 seeds' },
];

function OverviewPage() {
  const { data, error } = useEvidence();
  const reduce = useReducedMotion();

  if (error) return <div className="panel"><p className="error">Failed to load: {error}</p></div>;
  if (!data) return <div className="panel"><p className="loading">Loading evidence…</p></div>;

  const frozen = data.frozen_rerun_new_system;
  const fz = (frozen.data ?? {}) as Record<string, string>;
  const asr = (data.downstream_asr.data ?? {}) as Record<string, string>;

  return (
    <div>
      <header className="page-head">
        <div className="section-meta">
          <span className="tag solid">Research artifact</span>
          <span className="tag">KAUST VSRP</span>
          <span className="tag ok">Held-out v1 + v2</span>
        </div>
        <h1 className="display">A prompt-injection shield you can audit.</h1>
        <p className="lede">
          Three independent detectors and a versioned safety constitution screen every request
          before an LLM or tool acts. Every number on this site traces to a persisted artifact —
          including the results that do not flatter the system.
        </p>
      </header>

      <section aria-labelledby="heldout-heading">
        <h2 id="heldout-heading">Held-out results, side by side</h2>
        <p className="muted">
          Same 73 attacks and 32 benign controls, evaluated once. The strongest layer
          (constitution-only) sets the headline; the full blend is kept as measured.
        </p>

        <div className="ledger">
          {LEDGER.map((row) => (
            <div className={row.primary ? 'ledger-row is-primary' : 'ledger-row'} key={row.name}>
              <div className="ledger-config">
                <span className="name">{row.name}</span>
                <span className="meta">{row.meta}</span>
              </div>
              <div className="ledger-score">
                {row.score}<span className="den">{row.den}</span>
              </div>
              <div className="ledger-detail">
                <div className="ledger-bar" aria-hidden="true">
                  <motion.span
                    initial={reduce ? false : { width: 0 }}
                    animate={{ width: `${row.pct}%` }}
                    transition={{ duration: reduce ? 0 : 0.7, ease: [0.2, 0.7, 0.3, 1], delay: reduce ? 0 : 0.1 }}
                    style={reduce ? { width: `${row.pct}%` } : undefined}
                  />
                </div>
                <p className="ledger-note">{row.note}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="cards">
          {FRESH.map((s) => (
            <div className="card" key={s.k}>
              <div className="k">{s.k}</div>
              <div className="v">{s.v}</div>
              <div className="muted">{s.sub}</div>
            </div>
          ))}
        </div>
        <p className="muted">
          The frozen n=73 comparison remains statistically unresolved between C and G (overlapping
          confidence intervals). The pooled fresh batch and the SOTA baseline bound the lift; none of
          this is a head-to-head deployment test.
        </p>
      </section>

      <section aria-labelledby="tour-heading">
        <h2 id="tour-heading">Read it in three stops</h2>
        <ol className="tour">
          <li>
            <strong>The threat</strong>
            Injected instructions hide in logs, emails, documents, and tool output — aiming to
            exfiltrate data, run commands, or reproduce malware.
          </li>
          <li>
            <strong>The defense</strong>
            Rule, LLM, and constitution signals run independently. When they disagree, the strongest
            signal wins instead of being averaged away; failures become reviewable principle drafts.
          </li>
          <li>
            <strong>The evidence</strong>
            Held-out attacks, benign controls, a SOTA baseline, a second provider, and a live
            adaptive red-team — with negative results and partial replications kept in place.
          </li>
        </ol>

        <div className="plain-words">
          <h4>In plain words</h4>
          <p>
            AURA Shield screens every request with three independent detectors plus a versioned
            safety constitution before any LLM or tool acts. When detectors disagree, the strongest
            signal wins (max fusion) instead of being averaged away. Failures teach the constitution
            new principles — with human approval, never silently. Separately, preference training
            (DPO) and targeted unlearning try to change the model itself; both are measured honestly,
            including when they fail.
          </p>
        </div>
      </section>

      <section aria-labelledby="question-heading">
        <h2 id="question-heading">Open in the research</h2>
        <div className="panel">
          <h3>Fusion under investigation</h3>
          <p>
            Constitution-only beats the old full blend on held-out, but the intervals overlap — the
            research question is not settled at n=73. See{' '}
            <span className="mono">Evaluation → Benchmark</span> for the full matrix and the frozen
            re-run breakdown.
          </p>
        </div>
      </section>

      <section aria-labelledby="detail-heading">
        <h2 id="detail-heading">Detail</h2>

        <Accordion title="Frozen re-run — per-field record">
          {frozen.has_data ? (
            <Cards items={[
              { k: 'recall', v: String(fz.recall ?? '—') },
              { k: 'FPR', v: String(fz.fpr ?? '—') },
              { k: 'fallback rows', v: String(fz.fallback_rows ?? '—') },
              { k: 'status', v: String(fz.status ?? '—') },
            ]} />
          ) : <Missing label="Frozen re-run" />}
        </Accordion>

        <Accordion title="Downstream ASR — bypass is not success">
          <p className="mono">{String(asr.ASR ?? 'NOT MEASURED')}</p>
          <p className="muted">
            Downstream evaluated: {String(asr.downstream_evaluated ?? '—')} · success:{' '}
            {String(asr.downstream_success ?? '—')}
          </p>
        </Accordion>

        <Accordion title="Key findings">
          <ul>
            <li>Fusion dilutes its best layer (68/73 vs 65/73); max fusion recovers it on DEV (90/90).</li>
            <li>DPO: negative at 4 configs (loss down, rankings frozen — the KL-trap), then POSITIVE at Qwen-1.5B LoRA (β=0.1): dev 0/29→22/29, train 128/133.</li>
            <li>Unlearning: template-specific at gentle intensities; FULL removal with preservation (24/24, all λ) on the hotter Qwen run.</li>
            <li>Pooled new-system attacks: 143/153 = 93.5% (95% CI 88.4–96.4%; frozen 67/73 + sealed 38/40 + 38/40).</li>
            <li>Held-out v2 (fresh 153 attacks + 100 benign, scored once): 132/153 = 86.3% (95% CI 79.9–90.8%), benign FPR 1/100.</li>
            <li>Benign challenge: 0/132 held offline across 16 trigger-word families; combined live FPR 5/264 = 1.9%.</li>
            <li>SOTA baseline (ProtectAI DeBERTa-v3 injection v2, same 306/264): 187/306 = 61.1% at 1.9% FPR — AURA 89.9% at equal FPR.</li>
            <li>Second provider (Zen) partial replication: 130/153 = 85.0%, benign 0/35, 65 rows purged under the outage rule.</li>
            <li>Live adaptive red-team (24 dev seeds × 3 rounds): 24/24 held unmodified; 37/38 valid adapted attempts held (97.4%), 1/24 seeds, one transient bypass that re-blocked next round. 9 attacker refusals excluded. Detector bypass only, not an ASR.</li>
            <li>SOC path live: malicious log → triage → safe output (3/5 held, 2/2 safe).</li>
            <li>Detector bypass ≠ downstream success (ASR measured separately with canaries).</li>
            <li>Malware loop closed: payload requests held 10/10, benign explainers safe 10/10.</li>
          </ul>
        </Accordion>

        <Accordion title="Open research questions">
          <ul className="mono" style={{ fontSize: '0.8rem' }}>
            <li>RQ1 fusion &gt; single signals? — No (overlapping CIs; fresh pooled n=306 at 89.9%, C vs G unresolved at n=73).</li>
            <li>RQ2 adaptive updates help w/o FP? — Yes, with caveats (65→68/73, FPR 0).</li>
            <li>RQ3 DPO improves preferences? — Yes at 1.5B (22/29 dev; negative at 100K/0.5B across 4 configs).</li>
            <li>RQ4 targeted unlearning with preservation? — Yes, with scope (hot Qwen run; partial/negative at lower intensities).</li>
            <li>RQ5 provenance controls? — Logged, not yet scored.</li>
            <li>RQ6 detections → lower ASR? — Measured separately (0/21 controlled).</li>
            <li>RQ7 latency/security/utility? — P50–P99 + load sweep in Evaluation → Reliability.</li>
          </ul>
        </Accordion>
      </section>

      <section aria-labelledby="limits-heading">
        <h2 id="limits-heading">Scope and limitations</h2>
        <div className="limit-grid">
          <div className="limit-card"><h4>Scale</h4><p>Alignment training at 100K–0.5B params; nothing transfers to LLM scale.</p></div>
          <div className="limit-card"><h4>Statistics</h4><p>Held-out n=73: CIs overlap; McNemar impossible (no paired data). Fresh pooled n=306: 89.9% (CI 86.0–92.8%).</p></div>
          <div className="limit-card"><h4>Single provider</h4><p>Live layers primarily Groq-hosted; second-provider cells measured on Zen plus a local CPU fallback.</p></div>
          <div className="limit-card"><h4>Approvals</h4><p>Pre-OAuth records are simulated. With GitHub OAuth configured, approvals bind to verified usernames.</p></div>
          <div className="limit-card"><h4>Tools</h4><p>Docker isolation implemented; high-danger fails closed without Docker; container path unvalidated on this host.</p></div>
          <div className="limit-card"><h4>Production</h4><p>Research prototype. Nothing here claims production readiness.</p></div>
        </div>

        <div className="panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1.5rem', flexWrap: 'wrap' }}>
          <div>
            <h3 style={{ marginTop: 0 }}>Overall status</h3>
            <p className="muted" style={{ margin: 0 }}>
              221 passed + 3 skipped (Docker-present skips). Negative results kept. Every number
              traces to a persisted artifact.
            </p>
          </div>
          <div className="stamp" role="status">
            <span className="stamp-k">review status</span>
            <strong>Partial</strong>
          </div>
        </div>
      </section>
    </div>
  );
}

export default OverviewPage;
