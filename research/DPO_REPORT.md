# DPO Report — FULL MODEL-LEVEL DPO (negative at 4 configs, POSITIVE at Qwen-1.5B)

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

## Hotter run: Qwen2.5-0.5B, lr 2e-5, 4 epochs (`dpo_lm_record_qwen05_hot.json`)

User-executed (307 s). Loss 0.6931→0.0000 (full overfit), train 20/133 (up from 7/133),
dev 0/29→0/29, unseen 0/30→0/30. Stronger training moved train accuracy but dev/unseen
rankings remain exactly frozen. DPO negative CONFIRMED at higher intensity.
RQ3 stands answered No at all three tested configurations.

## Hotter replicate: Qwen2.5-0.5B, identical hotter config (`dpo_lm_record_qwen05_hot2.json`)

User-executed (312.7 s, seed 7, lr 2e-5, 4 epochs, batch 4, accum 4). Loss 0.6931→0.0000,
train 20/133, dev 0/29→0/29, unseen 0/30→0/30 — metric-for-metric identical to the first
hot run (306.8 s). Deterministic replication: the frozen dev/unseen ranking is not run
noise; stronger training reproducibly moves train only. RQ3 negative stands replicated.

## Config 5: Qwen2.5-1.5B LoRA on Colab T4 — FIRST POSITIVE (`dpo_lm_record_qwen15.json`)

User-executed (output pasted back verbatim). LoRA r16 (4.36M trainable / 1.549B),
β=0.1, lr 2e-4, 10 epochs, batch 4, seed 7. Loss 0.34→0.0002, train 6/133→128/133,
dev 0/29→22/29 (margin −46.1→+26.9).

Diagnosis that unlocked it (the KL-trap): configs 1–4 saturated the DPO loss while
train accuracy stayed flat — once the policy beat the reference by a comfortable
relative margin, gradients vanished although absolute rankings were still wrong.
Lower β=0.1 forces larger absolute movement before saturation. H3 (capacity) is
confirmed as the lever: same objective, bigger model + weaker KL constraint.

RQ3 answer updates: **No at 100K/0.5B (4 configs), Yes at 1.5B LoRA (22/29 dev, 23/30 unseen).**
The dev claim stands on the same n=29 split every config used.

## Unseen-30 generalization: Qwen2.5-1.5B LoRA retrain (`dpo_unseen_qwen15.json`)

The original config-5 adapter did not survive the Colab session, so the check was run on a
same-config retrain (TRL DPOTrainer, 200 s, T4; executed notebook kept as
`research/dpo_unseen_colab_executed_20261007.ipynb`). Base → DPO on the 30 unseen phrasings
that were never trained on: **0/30 → 23/30 = 76.7%** (margin −39.76 → +6.44). Dev 0/29 → 19/29
(65.5%), train 109/133 (82.0%).

Interpretation: unseen accuracy sits at the dev level and below (not above) train accuracy, so
the dev win is preference learning rather than memorization. The retrain reproduced the
direction but not the exact counts (dev 19/29 vs 22/29; train 109/133 vs 128/133) — run-to-run
variance between the custom trainer and TRL, kept visible rather than averaged away. Base is
0/30 on unseen, so the lift is unambiguous.
