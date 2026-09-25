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
- Unlearning still emitting (λ=0.1): 20/24=83.3% (95% CI 64.1%-93.3%) (only 4/24 suppressed)

## McNemar limitation (explicit)
- Held-out McNemar: NOT RUN. Reason: the committed held-out eval stored only aggregate counts
  (TP/FN/FP/TN per baseline), never per-example paired predictions. Reconstructing pairs would
  require executing the pipeline on held-out examples, which the protocol reserves for the single
  frozen final eval. No p-value is fabricated in its place.
- DEV McNemar (offline, genuinely paired, n=120): rule vs constitution p=0.39,
  constitution vs fusion p=0.39, rule vs fusion p=1.0 — all non-significant. DEV pairs do NOT
  substitute for held-out pairs (different split, offline signals only).
RQ1: negative — CIs overlap at n=73.
