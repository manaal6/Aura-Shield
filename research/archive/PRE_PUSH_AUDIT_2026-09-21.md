# Pre-Push Audit (todo.txt Phase 0 — findings BEFORE this hardening pass)

Date: 2026-09-21. HEAD: `e286041`. Working tree: 2 modified (README.md, dashboard/streamlit_app.py),
~59 untracked (all sprint work). DO NOT COMMIT/PUSH per todo.txt instruction.

## A. Actually implemented (code present)

Gateway pipeline, 4 detectors, constitution v1 + utils (C1–C8 heuristic incl. new C8 patterns),
risk/policy gate, adaptive loop + C8 cycle, manual HF DPO (tiny-gpt2) + eval, LM unlearning sweep
(λ 0.1/0.5/1.0) + eval, fusion DEV analysis + report, statistical eval, benign/indirect/canary-ASR
evals, toolsec chain + contract, analyzer contract, fail-safe/audit tests, latency, redteam matrix,
multiturn latch eval, drift v1→v2, data governance guards, 14-tab artifact dashboard, 12 research docs.

## B. Actually executed (artifacts prove runs)

DPO train (loss 0.6959→0.0556, 120.7 s) + eval (dev 1/13→1/13); unlearning implant (forget→1.0) +
sweep (PARTIAL/NOT VALIDATED); fusion/stats/benign/indirect/redteam/multiturn/drift/latency/toolsec
JSONs; live canary ASR 0/6 via Groq; 135/135 tests green. DPO dataset at 59 pairs (target 150+ NOT met).

## C. Artifacts exist

`results/kaust_three_pillars/` (dpo_lm, unlearning_lm, fusion, statistics, benign, indirect, asr,
latency, redteam, multiturn, adaptive, integrated, toolsec, constitution, dpo, unlearning);
`results/kaust_day1_baseline/`; committed `results/baselines_summary/heldout_master_table.json`;
`research/data_manifest.json`; checkpoints (dpo_lm safetensors hash `90f7e023…`, unlearning .pt files).

## D. Stale artifacts

- `results/kaust_three_pillars/dpo/` + `unlearning/` (logistic smoke runs): SUPERSEDED by `dpo_lm/` /
  `unlearning_lm/` but kept as documented mechanism demos — must be labeled superseded, not deleted.
- `results/baseline_i_embedding_20260921_*` (6 dirs): NOT produced by this work; origin unclear —
  left untouched, excluded from claims.
- Manifest predates `data/unlearning_forget|retain.jsonl` materialization: REBUILT during this pass.

## E. Experiments reconstructible

All via `research/REPRODUCIBILITY.md` commands. Gaps this pass must close: DPO on 150+ pairs (needs
new data + retrain), DPO generalization set (missing), unlearning per-example inspection (missing),
fusion disagreement forensics on held-out (blocked — see G), ASR scale-up, provenance A/B scoring.

## F. Supported claims

Held-out C 68/73, G 65/73, FPR 0/32; adaptive 65→68/73; DPO hash-proof training + negative dev result;
unlearning PARTIAL/COLLATERAL baselines; ASR 0/6 (n=6, stated); offline rates labeled offline.

## G. Unsupported / blocked

- McNemar on held-out: per-example paired predictions never stored; re-running the frozen pipeline on
  held-out to reconstruct them would consume the single reserved final-test touch — NOT performed;
  McNemar runs instead on DEV paired decisions (live LLM) where legitimate.
- Exact held-out fusion-FN example IDs: same reason — documented, not fabricated.
- Larger-model DPO: gpt2 (124M) download failed (XET 404; retry hung 10 min; partial cache removed);
  4-CPU/2-thread torch, no CUDA/TRL/PEFT → tiny-gpt2 (102K) is the strongest feasible trainer. Documented.
- Groq: 1 key (not 5–6), model gpt-oss-120b; inference/eval only, never training compute.
- Sandbox, human approval, cross-model matrix: absent (documented, not pretended).
