# Forensic Repository Audit (Phase 0 — new master prompt)

Date: 2026-09-21. Auditor inspected code + artifacts directly; nothing inferred from filenames.
Baseline commit: `e286041`. Prior sprint work (uncommitted, in tree) included below as appropriate.

## A. Already implemented (code + artifacts + tests)

- Gateway pipeline: `app/pipeline.py` → rule/LLM/TF-IDF detectors → constitution → risk blend (0.35/0.45/0.20) → policy gate (0.40/0.75 + 0.90 escalation + fail-safe REVIEW). Tests green.
- Constitution v1 seed (C1–C6) + `constitution_utils.py` (validation, hash, structured gate API, fail-safe). `results/kaust_three_pillars/constitution/constitution_run.json`.
- Adaptive loop (`research/adaptive_loop.py`, C7 v1→v2) + clean second cycle (`research/adaptation_cycle.py`, C8 APPROVED, v2 artifact). Test-split guard verified working (blocked a live violation attempt).
- Benchmark splits: dev 120 / adaptation 105 / test 105 with hashes (`results/kaust_day1_baseline/baseline.json`).
- DPO **objective-level** smoke test only: logistic policy, 29 pairs, loss 0.6931→0.6405, dev acc 0.50→1.00 (n=8). NO language model was updated.
- Unlearning **pattern-level** smoke test only: logistic policy, target 1.00→0.00 with general-probe collapse 0.27→0.01 (kept as negative result). NO language model was updated.
- Fusion dev-offline comparison (5 strategies) + frozen policy + held-out citations. Offline red-team (72 attacks). Integrated eval showing gateway/unlearning complementarity.
- 110 unit tests passing (~19 s, offline). No CLAUDE.md exists. Dashboard = `dashboard/streamlit_app.py` (demo UI; numbers not yet all artifact-backed).

## B. Partially implemented

- DPO: pipeline/dataset/loss/eval real; model-level training absent → status OBJECTIVE PROOF-OF-CONCEPT.
- Unlearning: method/eval real; LM-level absent; current result = negative baseline (collateral damage) → COLLATERAL DAMAGE.
- Fusion: dev analysis real; live-LLM re-tuning absent → FUSION UNDER INVESTIGATION.
- Red-team: offline matrix + committed live full-gateway game; live downstream ASR absent.
- Cross-model: 2 committed cells (constitution 78.1%, analyzer 90.4%); matrix incomplete.
- Tool security: synthetic fixtures + authorization concept; no enforced Intent→Auth→Validate→Execute chain with tests.
- Audit logging: Postgres logs + changelog; no tamper-evidence/attack tests.

## C. Missing

- Genuine HF causal-LM DPO (policy/ref/logprobs/backprop/checkpoint + param-hash proof). Expanded 13-category preference dataset.
- LM unlearning with forget/retain/general sets + lambda sweep.
- `research/data_manifest.json`; programmatic train/test isolation guards.
- Bootstrap CIs, McNemar tests, denominators-everywhere reporting pass.
- Benign challenge set (lexical-trigger legit prompts); provenance-aware indirect-injection suite; canary-based downstream ASR; latency P50/P95/P99; multi-turn eval; constitution drift analysis.
- Analyzer-output schema validation; fail-safe test battery; audit-attack tests.
- 14-tab artifact-backed dashboard; 11 research reports; `research/REPRODUCIBILITY.md`; `research/FINAL_STATUS.md`; README research update.

## D. Broken

- Nothing functionally broken: 110/110 tests pass. Known weak spots (not breakage): C2 heuristic needed a pattern fix (fixed, tested); unlearning toy general-collapse (kept as finding); `head`/`ls` assumptions in docs target Linux (repo runs on win32 PowerShell — new scripts must use compatible commands).

## E. Claims supported by evidence

- Held-out: constitution-only 93.2% (68/73), full gateway 89.0% (65/73), precision 100%, FPR 0/32 — committed artifacts, zero-fallback provenance.
- Adaptive v1→v2 held-out lift with overlapping-CI caveat. Live red-team block rates. SOC 50/50 + 20/20. DPO/unlearning toy numbers with explicit scope labels.

## F. Claims NOT supported (must never be made)

- Any LLM-scale DPO safety improvement; any real-world forgetting/erasure; any ASR derived from recall; "solves prompt injection"; "secure/production-ready"; human approval (all approvals are SIMULATED); statistical significance of RQ1 at n=73.
