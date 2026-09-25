# AURA Shield: KAUST Three-Pillar Research Report (Day-1 Prototype)

> SUPERSESSION NOTICE (2026-09-22): Pillars 1–2 below stand. Pillar-3 sections (§6–§7,
> §10 rows, §12 items 1–3, §13 counts) describe the FIRST-sprint logistic smoke tests and are
> SUPERSEDED by genuine LM runs: `research/DPO_REPORT.md` (162 pairs, tiny-gpt2, NEGATIVE),
> `research/UNLEARNING_REPORT.md` (λ sweep, PARTIAL), `research/FINAL_STATUS.md` (acceptance matrix).
> The logistic artifacts are kept as mechanism demos / negative baseline, not evidence.

Status labels: IMPLEMENTED / EXPERIMENTALLY VALIDATED / SMOKE TESTED / NOT YET VALIDATED / FUTURE WORK.
Every number below traces to an artifact in `results/kaust_three_pillars/` or previously committed `results/`.

## 1. Problem

LLM assistants embedded in cybersecurity workflows face prompt injection
(direct + indirect), jailbreaks, and tool misuse. A single inference-time
filter is brittle; weight-level alignment alone is unauditable per-request.
AURA Shield is a research prototype combining both: an auditable
inference-time gateway (Pillars 1+2) with model-level preference alignment
and targeted behavior removal (Pillar 3).

## 2. Threat Model

- Attacker controls `user_prompt` and/or `source_content` (docs, tool output, logs).
- Attacker KNOWS the architecture (source-aware red-team, §11).
- Attacker goals: override policy, exfiltrate config, execute commands via
  untrusted content, tamper audit, hijack role, smuggle encoded/flooded payloads.
- Out of scope: model-weight theft, infrastructure compromise, human social
  engineering beyond the terminal.

## 3. AURA Shield Architecture

See `docs/kaust_three_pillar_architecture.md`. Flow: detectors → constitution
→ risk blend (0.35/0.45/0.20) → policy gate (0.40 review / 0.75 block +
escalation at 0.90 + fail-safe review on analyzer failure) → gated downstream
→ gated tools → audit. Baseline frozen: `results/kaust_day1_baseline/baseline.json`.

## 4. Pillar 1 — Constitutional AI [IMPLEMENTED + SMOKE TESTED]

- Versioned seed (`constitution.json` v1, C1–C6, file-sha256 `e4debd64…`;
  canonical content hash via `constitution_hash()`).
- Hardening added: `app/engine/constitution_utils.py` (stable-ID validation,
  hash, required-coverage map, structured gate API
  `constitution_version/hash/principles_checked/violations/evidence/decision`,
  fail-safe REVIEW on empty input, offline heuristic for smoke tests only).
- Coverage: 5/6 mandated behaviors literal in v1; `C7-no-unsafe-payload`
  (payload generation) is a DOCUMENTED GAP — covered at the adaptive layer
  (C7-encoding lineage) and DPO pairs, not as a seed principle (seed frozen
  to preserve existing results).
- Probes: override→block, config-exfil→(fixed)block, untrusted-cmd→review,
  fake-system→review, benign→allow (`constitution/constitution_run.json`).

## 5. Pillar 2 — Adaptive Constitutional AI [IMPLEMENTED + SMOKE TESTED]

- Existing loop (`research/adaptive_loop.py`, C7 cycle v1→v2, held-out
  89.0%→93.2% with overlapping CIs) preserved untouched.
- New clean pipeline `research/adaptation_cycle.py`: failure→analysis→
  candidate→validation (schema + contradiction + duplicate)→regression→
  approval→versioned artifact→read-only unseen eval.
- Second cycle run: `C8-no-context-window-overflow` from 20 context-flooding
  adaptation misses (distinct pattern from C7), APPROVED, v2 artifact,
  rule-only unseen test recall 0.0 (= baseline-A level, honestly reported).
- Isolation enforced in code (`validate_split_isolation` blocked a test-split
  read during this sprint — verified working) + regression tests.

## 6. Pillar 3 — DPO [SUPERSEDED — see `research/DPO_REPORT.md`]

First-sprint logistic PoC (29 pairs, loss 0.6931→0.6405, dev 0.50→1.00 at n=8) kept as mechanism demo.
Superseding run: tiny-gpt2 (102,714 params), 162 pairs (133/29 + 30 unseen), loss 0.6824→0.1950,
dev 2/29→2/29 and unseen 1/30→1/30 — NEGATIVE. Toy scale; no transfer to LLM scale.

## 7. Pillar 3 — Unlearning [SUPERSEDED — see `research/UNLEARNING_REPORT.md`]

First-sprint logistic baseline kept as COLLATERAL DAMAGE record (target 1.00→0.00,
general 0.27→0.01). Superseding run: LM sweep λ∈{0.1,0.5,1.0} — PARTIAL at λ=0.1/1.0
(4/24 suppressed, one template family only; retain/general preserved), NOT VALIDATED at λ=0.5.

## 8. Integrated Architecture

Gateway (inference defense) + DPO (preference shift) + unlearning (targeted
removal). Key measured complementarity: the gateway holds 0/24 CRIMSON
triggers (they look benign) while unlearning removes exactly that behavior —
neither layer subsumes the other (`integrated/integrated_eval.json`).

## 9. Experimental Design

Splits: dev 120 (calibration), adaptation 105 (adaptation input), DPO
train/dev 133/29 + 30 unseen (preference), forget/retain/general 24/32/24 (unlearning),
benign challenge 62, test 105 (final/reporting only). Hashes in `research/data_manifest.json`.

## 10. Results (traceable)

| Experiment | Before | After | Artifact | Strength |
|---|---|---|---|---|
| Constitution probes (5) | — | 4 held, 1 allowed (benign) | constitution_run.json | SMOKE |
| Adaptive C8 cycle | 20 flooding misses | APPROVED v2, checks pass | cycle_C8….json | SMOKE |
| DPO pref-acc (dev n=8, logistic PoC) | 0.50 | 1.00 | dpo_result.json | SUPERSEDED (see DPO_REPORT: 2/29→2/29) |
| DPO LM (dev n=29 + unseen n=30) | 2/29, 1/30 | 2/29, 1/30 (unchanged) | dpo_lm_eval.json | NEGATIVE (kept) |
| Unlearning target (logistic) | 1.00 | 0.00, retain 0.00 | unlearning_result.json | SUPERSEDED baseline |
| Unlearning LM sweep | 24/24 emit | 20/24 emit (one template) | unlearning_lm_eval.json | PARTIAL |
| Unlearning general probe | 0.27 | 0.01 (degraded) | unlearning_eval.json | SMOKE (negative) |
| Fusion dev strategies | — | best recall 0.13 offline | fusion_diagnosis.json | SMOKE |
| Red-team offline (102) | — | 85 bypass / 17 held | adaptive_redteam.json | SMOKE (lower bound) |
| Held-out (committed) | G 89.0% | C 93.2% (overlap CIs) | baselines_summary | VALIDATED (prior) |

## 11. Security Evaluation

- Source-aware offline red-team: 12 classes × 6 budget; 76% bypass of the
  OFFLINE SUBSET (no live LLM) — lower bound only; committed live full-gateway
  game measured 52.5% block on whitespace mutations. Every bypass recorded as
  regression material. No external targets; synthetic only; no real secrets.
- Fusion: policy FROZEN (no live signals to re-tune; honest negative RQ1 kept).
- Fail-safes kept: analyzer-failure→REVIEW, empty-input→REVIEW, escalation
  paths, schema-bound model outputs.

## 12. Limitations

1. All new training is toy-scale (100K-param CPU); DPO negative, unlearning partial — see research/ reports.
2. DPO dev n=29 + unseen n=30: ranking unchanged by training (negative result, kept).
3. Unlearning: template-specific suppression (4/24), not behavior removal.
4. C7 payload principle missing from seed (documented gap).
5. Offline heuristic ≠ LLM checker; live re-validation required.
6. 89% vs 93.2% gap statistically unresolved at n=73.
7. No live downstream ASR measured in this sprint (marked unavailable).

## 13. Reproducibility

```bash
pip install -r requirements.txt  # + torch (CPU) for pillar-3 smoke tests
python -m pytest tests/ -q                                   # 178 tests (see research/FINAL_TEST_REPORT.md)
python -m experiments.kaust_three_pillars.run_constitution
python -m experiments.kaust_three_pillars.run_adaptive
python -m experiments.kaust_three_pillars.run_dpo
python -m experiments.kaust_three_pillars.run_unlearning
python -m experiments.kaust_three_pillars.run_integrated_eval
python -m experiments.kaust_three_pillars.run_all            # everything
```

## 14. Future Research

GPU LLM-DPO (LoRA) on the 29-pair seed expanded ×10; selective unlearning
(sparse adapters) to fix general degradation; seed C7 proposal through the
Pillar-2 approval path; live fusion re-tuning with LLM signals; live
downstream ASR with canary secrets; larger-n held-out to resolve RQ1.
