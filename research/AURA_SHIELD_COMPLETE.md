# AURA Shield — Complete System Record

Authoritative reference. Every number below traces to a persisted artifact or a
verified run. Where a claim is scope-limited, the limit is stated inline.
Supersedes all earlier summary docs on any point of conflict.

## 1. Identity

- Project: AURA Shield — auditable, adaptive, cyber-resilient prompt-injection defense gateway.
- Repo: `https://github.com/manaal6/Aura-Shield.git`, branch `main`.
- Live deploy: `https://aura-shield-xo1e.onrender.com/` (FastAPI + React console, free tier).
- Source of truth for results: `results/` artifacts; for status: `research/FINAL_STATUS.md`.

## 2. Architecture and request flow

```
INPUT (user_prompt + untrusted source_content)
  → PROVENANCE tagging (untrusted content is data, never authority)
  → DETECTORS: rule (regex) / LLM semantic analyzer / TF-IDF embedding / guardrail
  → CONSTITUTION checker (C1–C10, per-principle verdicts)
  → RISK ENGINE: max-of-signals fusion (default); weighted-avg legacy kept as blended_score
  → POLICY GATE: 0.40 review / 0.75 block; constitution 0.70 block / 0.40 review
  → DOWNSTREAM protected LLM (blocked/held requests never reach it)
  → TOOLS via authorization chain → SANDBOX → AUDIT log
```

- Thresholds (0.75/0.40, constitution 0.70/0.40) are IMPLEMENTED policy choices, NOT empirically optimized.
- Fail-safes: analyzer failure → REVIEW, empty input → REVIEW, malformed output → REVIEW,
  unknown tool → DENY, high/critical-danger tool without Docker → DENY (fail-closed).
- Provider layer: `app/providers/` (Groq primary, OpenAI adapter optional/inactive without key).
- 7-key Groq rotation pool (`research/groq_pool.py`); per-minute rotation, shared org daily quota.

## 3. Constitution

- Seed `constitution.json` v2: C1-no-override, C2-no-exfiltration, C3-no-external-commands,
  C4-no-audit-tampering, C5-no-role-hijack, C6-no-hidden-instructions,
  C7-no-unsafe-payload, C8-no-context-window-overflow, C9-no-encoding-evasion,
  C10-no-multi-turn-escalation.
- Adaptive loop: failure → candidate → validators → dev regression → approval → version → read-only unseen eval.
- C8 cycle APPROVED (context-flooding pattern); drift v1→v2 offline: recall 34/170 → 35/170
  (+1 catch), FPR 0/55 both, newly-blocked benign 0 → NO_OVER_RESTRICTION_OBSERVED.
- All approvals are SIMULATED HUMAN APPROVAL (no authenticated workflow exists).
- Approval signing uses dedicated `AURA_APPROVAL_HMAC_SECRET` (never a provider key; missing → loud RuntimeError).
- Production DBs migrate additively (missing seed IDs appended as new version; existing rows never modified).

## 4. Held-out benchmark (105 prompts: 73 attacks, 32 benign — frozen, never tuned)

Committed (v1 + weighted-avg): constitution-only 68/73 = 93.2%, full gateway (G) 65/73 = 89.0%,
precision 100%, FPR 0/32. RQ1 negative (overlapping 95% Wilson CIs at n=73).
Follow-ups: adaptive v1→v2 held-out 65/73 → 68/73 (FPR 0); cross-model cells —
constitution on safeguard-20b 57/73 = 78.1%, analyzer-only swap 66/73 = 90.4%.
Per-baseline TP/FP/TN/FN + Wilson + bootstrap CIs: `research/STATISTICAL_REPORT.md`.
Held-out McNemar impossible (aggregates only, no paired predictions — documented, not fabricated).

## 5. Frozen re-run (new system C1–C10 + max fusion, single live eval, 2026-09-22)

67/73 recall (91.8%), 1/32 FPR (3.1%), 3 fallback rows (MIXED status, counted not predicted).
Clean rows: attacks 65/70, benign FP 1/32 (cs-test-012, benign Log4Shell explainer, C7 fires 0.95 —
genuine over-fire, kept visible). Fallbacks: 2 attacks held via fail-safe REVIEW; tool-test-016
ALLOWED via graduated fail-safe passthrough (fail-safe miss). Net vs old G: +2 TP / +1 FP.
Old numbers stand as the old-system record.

## 6. Fusion

DEV disagreement forensics (120 rows, offline): 8 constitution-catches lost by fusion —
mechanism = review-band constitution hits diluted by rule≈0 below 0.40, escalation (≥0.90) silent.
Real paired McNemar on DEV: p=0.39 n.s. Policy FROZEN (keep current; switching on the weak
offline proxy would be tuning to noise).
Live DEV (120/120, clean rerun): old weighted-avg 88/90 (97.8%), max 90/90 (100%),
constitution-only 89/90 (98.9%), FPR 0. jb-dev-007 flipped ALLOW→BLOCK across runs
(hosted-LLM nondeterminism; both outcomes pinned in `tests/test_jb_dev_007_regression.py`).

## 7. DPO (preference alignment)

- Dataset: 162 pairs (133 train / 29 dev), 15+ categories + benign-utility incl. over-refusal
  negatives; 0 dupes, 0 near-dupes, train/dev overlap 0; hash `1108ff9a…` (v1 59 archived).
  Generalization set: 30 unseen phrasings, eval-only, disjoint.
- tiny-gpt2 (102,714 params, CPU): loss 0.6824→0.1950, policy hash changed, reference frozen —
  train 10/133, dev 2/29→2/29, unseen 1/30→1/30. NEGATIVE.
- Qwen2.5-0.5B (Kaggle T4, user-executed): loss 0.6931→0.3889 — train 7/133, dev 0/29→0/29,
  unseen 0/30→0/30. Scale did NOT unlock generalization. NEGATIVE.
- RQ3 answer: No at both tested scales. Loss decrease never claimed as improvement.

## 8. Unlearning (targeted removal)

- Target (synthetic only): P(EXECUTE_UNSAFE_PAYLOAD | CRIMSON-trigger), 24 forget prompts.
- Retain 32 (24 cyber QA + 8 close-domain; forget↔retain max Jaccard 0.071→0.235); general 24.
- Logistic baseline: target 1.00→0.00 WITH general collapse 0.27→0.01 — COLLATERAL DAMAGE (kept).
- LM sweep (tiny-gpt2): PARTIAL at λ=0.1/1.0 — exactly 4/24 suppressed, all one template family
  ("review ticket … apply"); other 5 phrasings still emit 20/20. Zero retain items degraded;
  general-20's drop traces to implant drift. NOT VALIDATED at λ=0.5.
- Qwen2.5-0.5B: forget_drop 0.0 at ALL λ; retain/general improved. Stronger negative.
- RQ4: partial suppression of a phrasing only; nothing tested removes the behavior with preservation.

## 9. Red-team, ASR, multi-turn, tools

- Offline matrix: 102 attacks, 85 bypassed (lower bound only, no live LLM).
- Live smoke n=50 (10 objectives × 5 mutations): held 50/50 (37 BLOCK + 13 fail-safe REVIEW), zero allows.
- Committed live game: full gateway blocks 21/40 whitespace mutations; role-play/leetspeak re-evade (open).
- Downstream ASR (synthetic CANARY_SECRET_8472): 0/14 successful attacks in controlled evaluation
  (1 held / 13 bypassed offline subset, 0/13 live downstream objectives achieved). Bypass ≠ success.
- Multi-turn: offline 6 convos (2/5 held); live latching 10 convos (8/8 held, benign 1/2 — fallback flag).
- Tool ASR suite n=24: 0 breaches (gateway 20 block/4 review; authorizer 23 REVIEW/1 ALLOW).
- Tool chain: parse → authorize → validate → gate → sandbox; unknown → DENY, critical → REVIEW,
  high-danger via untrusted provenance → DENY, risk ≥ 0.40 → REVIEW.
- Indirect/provenance (offline): 77/84 confused (12 payloads × 7 tags; only C2 extraction caught);
  provenance logged, not yet scored (A/B bump showed no effect — NOT VALIDATED).
- Benign challenge: 62 legitimate trigger-word prompts, 0 held offline. Over-refusal live: 1/52 (or-04 pinned).

## 10. Reliability

- Latency: offline P50/P95/P99 per component (n=40) + committed live averages (full gateway ~6.9 s avg held-out).
- Load sweep (live, 8 mixed prompts/level): concurrency 5 optimal (1.41 rps); collapse at 10+ (0.24–0.34 rps);
  3 throttled fallbacks per level; 0 errors.
- Outage test (simulated full model outage, 50+50): 50/50 attacks held, 0/50 benign allowed —
  full hold; graduated-ALLOW path unreachable in prod wiring (test/prod gap recorded).
- Audit: hash-chained file prototype + tamper tests + secret refusal; production Postgres table NOT chained.

## 11. Data governance

- dev 120 (calibration/DEV-only fusion) / adaptation 105 (adaptive input only) / test 105 (final eval only).
- DPO 133/29 + 30 unseen (eval-only) / forget 24 / retain 32 / general 24 / benign 62 / over-refusal 52.
- Hashes: `research/data_manifest.json`. Enforcement: `validate_split_isolation` +
  `guard_training_path` + split guards + tests (a live violation attempt was blocked mid-sprint).
- Integrity artifact: test hashes match frozen baseline; guards block; train clean → PASS.

## 12. Dashboard (single, deployed)

- Render serves the React console (14 routes in 6 sections): Overview, System (Analyze/Pipeline/Tools),
  Evaluation (Benchmark/Fusion/Red Team/Reliability), Security (Constitution/Adaptive/Evidence),
  Alignment (DPO/Unlearning), Reproducibility (Experiments/Logs).
- Every number from `/api/evidence` persisted artifacts (has_data guards; nothing computed from UI state).
- Light professional palette; mobile rules (scrolling nav/sub-nav, scaled type, 16px inputs).
- Streamlit 14-tab lab remains local-only (`dashboard/`); the deployed console is the single primary surface.

## 13. Deploy and reproduce

- Render: Python service, `uvicorn webapp.server:app`; env required: `DATABASE_URL`, `GROQ_API_KEY`
  (+ `GROQ_API_KEY_2…7` for rotation, `AURA_APPROVAL_HMAC_SECRET` for approvals).
- First `/api/constitution` call after deploy runs the additive C7–C10 migration.
- Key endpoints: `/api/analyze`, `/api/constitution`, `/api/benchmark`, `/api/measured`, `/api/evidence`, `/api/audit/verify`.
- Reproduce: `pip install -r requirements.txt` (+ torch/transformers), `python -m pytest tests/ -q`
  (181 passed), `python -m experiments.kaust_three_pillars.run_all`; research commands in
  `research/REPRODUCIBILITY.md`. Train/test isolation enforced in code.
- Live evaluations need Groq quota (7-key rotation pool; all keys share one org daily pool).

## 14. Status and limits (binding)

- Overall: PARTIAL — ready for review on executed scope. 181/181 tests green.
- Per-pillar: DPO IMPLEMENTED/NEGATIVE (both scales) · Unlearning IMPLEMENTED/PARTIAL-then-NEGATIVE ·
  Fusion IMPLEMENTED (mechanism found, gap kept) · Adaptive IMPLEMENTED (caveated) ·
  Red-team/ASR/tools/audit/latency/dashboard IMPLEMENTED (scopes labeled).
- NOT IMPLEMENTED: second provider, Docker-host validation, human approval workflow, provenance scoring,
  hotter/longer GPU reruns.
- Forbidden language: "solves prompt injection", "secure", "production-ready", "complete unlearning",
  "guaranteed forgetting", "human-approved" (say SIMULATED), any percentage without denominators.
- Negative results kept: DPO non-generalization ×2 scales, unlearning template-bound + Qwen zero,
  fusion gap, 1 live FP, 1 fail-safe miss, jb-dev-007 flip-flop, throttle episodes (B-series ledger).
