# DPO Report — FULL MODEL-LEVEL DPO with negative generalization result

## Setup (provenance: `results/kaust_three_pillars/dpo_lm/dpo_lm_record.json`)

- Model: sshleifer/tiny-gpt2 (causal LM, 102,714 params, all trainable), CPU, torch 2.13.0.
- Reference: frozen copy (hash unchanged `e55d635d…` → `e55d635d…`).
- Policy: hash changed (`e55d635d…` → `02cee3bb…` / `90f7e023…`), 29/29 tensors changed.
- Data: 162 pairs (133 train / 29 dev, hash `1108ff9a…`; v1 59 archived, hash `56ebdf7a…`),
  15+ attack categories + benign-utility incl. over-refusal negatives; 0 dupes, 0 near-dupes (Jaccard>0.8),
  train/dev overlap 0 (see `research/DPO_DATASET_REPORT.md`). Generalization set: 30 unseen
  phrasings/templates (hash `7fda0ee1…`, overlap with train/dev 0, eval-only).
- Objective: exact DPO loss, β=0.5, AdamW lr=0.001, 6 epochs, batch 8, max_len 128, seed 7. Train 203.3 s.
- Attempt 1 (46 pairs, lr 5e-4→1e-3, 5→15 epochs): loss 0.6959→0.0556, dev 1/13→1/13 (negative).
- Attempt 2 (final, 133 train): loss 0.6824→0.1950, checkpoint hash `117f1472…`.

## Before/after (`dpo_lm_eval.json`, dev n=29, generalization n=30, deterministic ranking judge)

| Metric | Base | DPO |
|---|---|---|
| preference accuracy (train) | — | 10/133 = 7.5% |
| preference accuracy (dev) | 2/29 = 6.9% | 2/29 = 6.9% (unchanged) |
| preference accuracy (unseen) | 1/30 = 3.3% | 1/30 = 3.3% (unchanged) |
| mean chosen margin (dev) | −73.93 | −72.09 |
| DPO loss (dev) | 37.34 | 36.46 |
| attack resistance | 2/28 | 2/28 |
| benign utility / over-refusal | 0/1 / 1/1 | 0/1 / 1/1 (unchanged) |
| general mean logprob (n=24) | −82.53 | −82.57 (stable) |

## Verdict

FULL MODEL-LEVEL DPO: training genuinely occurred (gradient updates, proof hashes).
Generalization: NEGATIVE — no dev movement. RQ3 answer: No (at this scale). The loss decrease is
explicitly NOT claimed as security improvement. Prior logistic objective-PoC retained as mechanism demo.

## Scale-up: Qwen2.5-0.5B on Kaggle T4 (494,032,768 params, CUDA, 183 s)

`dpo_lm_record_qwen05.json` (user-executed, output pasted back verbatim):
loss 0.6931→0.3889, policy changed, reference frozen — train 7/133, dev 0/29→0/29,
unseen 0/30→0/30. Base Qwen ranks chosen even lower than tiny-gpt2 (0/29 vs 2/29).
Scale (5× params) did NOT unlock generalization; the loss-vs-ranking dissociation
replicates. Caveat: 2 epochs at lr 5e-6 is gentle — a longer/hotter run is future work,
not an implication. RQ3 stands answered No at both tested scales.

Scale limitation (binding): 102,714 parameters on CPU is toy scale, ~3 orders of magnitude below the
smallest deployed LLMs. Capacity, not data, is the likely binding constraint (ranking frozen while loss
fell). No DPO finding here transfers to LLM scale; a larger-model rerun is future work, not an implication.
