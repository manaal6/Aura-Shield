# Statistical Report (denominators everywhere)

## A — Rule only (n_attacks=73, n_benign=32)
- recall: 0/73=0.0% (95% CI 0.0%-5.0%) | bootstrap95: [0.0, 0.0]
- precision: n/a (no positive calls) | fpr: 0/32=0.0% (95% CI 0.0%-10.7%) | f1: None
## B — LLM semantic only (n_attacks=73, n_benign=32)
- recall: 58/73=79.5% (95% CI 68.8%-87.1%) | bootstrap95: [0.6986, 0.8904]
- precision: 58/58=100.0% (95% CI 93.8%-100.0%) | fpr: 0/32=0.0% (95% CI 0.0%-10.7%) | f1: 0.8855
## C — Constitution checker only (n_attacks=73, n_benign=32)
- recall: 68/73=93.2% (95% CI 85.0%-97.0%) | bootstrap95: [0.863, 0.9863]
- precision: 68/68=100.0% (95% CI 94.7%-100.0%) | fpr: 0/32=0.0% (95% CI 0.0%-10.7%) | f1: 0.9645
## D — Rule + LLM (n_attacks=73, n_benign=32)
- recall: 55/73=75.3% (95% CI 64.4%-83.8%) | bootstrap95: [0.6575, 0.8493]
- precision: 55/55=100.0% (95% CI 93.5%-100.0%) | fpr: 0/32=0.0% (95% CI 0.0%-10.7%) | f1: 0.8594
## E — Rule + Constitution (n_attacks=73, n_benign=32)
- recall: 66/73=90.4% (95% CI 81.5%-95.3%) | bootstrap95: [0.8356, 0.9726]
- precision: 66/66=100.0% (95% CI 94.5%-100.0%) | fpr: 0/32=0.0% (95% CI 0.0%-10.7%) | f1: 0.9496
## F — LLM + Constitution (n_attacks=73, n_benign=32)
- recall: 66/73=90.4% (95% CI 81.5%-95.3%) | bootstrap95: [0.8356, 0.9726]
- precision: 66/66=100.0% (95% CI 94.5%-100.0%) | fpr: 0/32=0.0% (95% CI 0.0%-10.7%) | f1: 0.9496
## G — Full blended AURA Shield (v1 constitution) (n_attacks=73, n_benign=32)
- recall: 65/73=89.0% (95% CI 79.8%-94.3%) | bootstrap95: [0.8219, 0.9589]
- precision: 65/65=100.0% (95% CI 94.4%-100.0%) | fpr: 0/32=0.0% (95% CI 0.0%-10.7%) | f1: 0.942
## H — Monolithic prompt guardrail (n_attacks=73, n_benign=32)
- recall: 55/73=75.3% (95% CI 64.4%-83.8%) | bootstrap95: [0.6575, 0.8493]
- precision: 55/55=100.0% (95% CI 93.5%-100.0%) | fpr: 0/32=0.0% (95% CI 0.0%-10.7%) | f1: 0.8594
## I — TF-IDF vector classifier (n_attacks=73, n_benign=32)
- recall: 26/73=35.6% (95% CI 25.6%-47.1%) | bootstrap95: [0.2466, 0.4658]
- precision: 26/26=100.0% (95% CI 87.1%-100.0%) | fpr: 0/32=0.0% (95% CI 0.0%-10.7%) | f1: 0.5253

## New small-n experiments
- DPO-LM dev preference: 2/29=6.9% (95% CI 1.9%-22.0%) (unchanged by DPO → negative)
- DPO Qwen-1.5B LoRA dev preference: 22/29=75.9% (95% CI 57.9%-87.8%) (FIRST POSITIVE, β=0.1)
- DPO Qwen-1.5B unseen-30: 23/30=76.7% (95% CI 59.1%-88.2%) (base 0/30; retrain, train 109/133 → generalizes)
- Unlearning still emitting (λ=0.1): 20/24=83.3% (95% CI 64.1%-93.3%) (only 4/24 suppressed)
- Pooled new-system attacks: 143/153=93.5% (95% CI 88.4%-96.4%) (frozen 67/73 + sealed batches 38/40, 38/40; FPR 1/32 from frozen run)
- Benign live combined: 5/264=1.9% (95% CI 0.8%-4.4%) (frozen 1/32 + live132 3/132 + held-out v2 1/100 (all one eval each, 0 fb))
- Held-out v2 (one-shot, 153+100): attacks 132/153=86.3% (95% CI 79.9%-90.8%), benign FPR 1/100=1.0% (95% CI 0.2%-5.5%) — fresh 153 attacks + 100 benign, generated once score-blind, evaluated once (frozen config, no tuning, 0 fallbacks)
- Pooled fresh attacks (v1+v2): 275/306=89.9% (95% CI 86.0%-92.8%) (n_attacks=306, every row evaluated once, never tuned)
- Second provider (Zen, PARTIAL): 130/153=85.0% (95% CI 78.5%-89.8%) attacks, benign FPR 0/35=0.0% (95% CI 0.0%-9.9%) — Zen space-bunny-free (both LLM layers) on 188/253 rows: attacks 130/153, benign 0/35; 65 rows purged (provider outage, B66 rule)

## SOTA baseline (same sets, offline)
- ProtectAI/deberta-v3-base-prompt-injection-v2: attacks 187/306=61.1% (95% CI 55.5%-66.4%), benign FPR 5/264=1.9% (95% CI 0.8%-4.4%) (n_attacks=306, n_benign=264, 187/306 attacks flagged, 5/264 benign flagged, 0 errors; offline default threshold, never tuned on AURA data)
- AURA pooled fresh: 275/306=89.9% (95% CI 86.0%-92.8%) | benign FPR 5/264=1.9% (95% CI 0.8%-4.4%)
- Matched FPR (oracle threshold 0.571): 187/306=61.1% (95% CI 55.5%-66.4%) attacks at 5/264=1.9% (95% CI 0.8%-4.4%) benign — threshold 0.5710 chosen post hoc on the benign set to flag ≤5/264 (oracle, not deployable); default threshold already sits at this FPR, so the headline comparison is not threshold-unfair
- Caveat: Single pretrained classifier at its default threshold, run offline over the same 306 attacks / 264 benign; AURA is an LLM ensemble with policy thresholds. The comparison bounds AURA's lift, it is not a head-to-head deployment test.

## McNemar limitation (explicit)
- Held-out McNemar: NOT RUN. Reason: the committed held-out eval stored only aggregate counts
  (TP/FN/FP/TN per baseline), never per-example paired predictions. Reconstructing pairs would
  require executing the pipeline on held-out examples, which the protocol reserves for the single
  frozen final eval. No p-value is fabricated in its place.
- DEV McNemar (offline, genuinely paired, n=120): rule vs constitution p=0.39,
  constitution vs fusion p=0.39, rule vs fusion p=1.0 — all non-significant. DEV pairs do NOT
  substitute for held-out pairs (different split, offline signals only).
RQ1: negative — CIs overlap at n=73.
