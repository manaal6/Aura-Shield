# Layered Guardrails Under Measurement: What Survives When You Hold the Prompt-Injection Detector Accountable

*Draft 1 — generated from `research/PAPER_SKELETON.md`; every number below is bound to a
committed artifact (see §10). If this text and an artifact disagree, the artifact wins.*

## Abstract

Guardrail stacks for LLM applications are usually reported as single aggregate scores on a
static benchmark. We instead report a layered prompt-injection defense the way an auditor
would measure it: pre-declared splits, one-shot evaluation of sealed batches, per-row
provider provenance, and negative results kept in the paper. Across 306 fresh attacks and
264 live benign prompts, the pipeline holds 275/306 attacks (89.9%, 95% CI 86.0–92.8) at a
5/264 (1.9%) benign flag rate, with every row evaluated exactly once under a frozen
configuration. A fully fresh second batch is materially harder (132/153 = 86.3%) than the
pooled first batch (143/153 = 93.5%), and we report that drop rather than averaging it away.
On the identical sets, a widely used pretrained prompt-injection classifier catches
187/306 = 61.1% at the same 1.9% benign rate. We also report two negative or partial
results that are usually omitted: layer fusion does not beat its best member at n=73, and
DPO only becomes effective after four failed configurations, once capacity and the KL
constraint are changed together. Finally, we document a measurement bug — provider-fallback
flags read from dictionaries never fired on the pipeline's typed responses — and the outage
rule we adopted after finding it.

## 1. Introduction

Three failures make guardrail evidence unreliable. First, iteration on the test set: a
detector that is tuned against its own evaluation set cannot be distinguished from one that
memorizes it. Second, silent degradation: when a provider fails, a pipeline that falls back
to heuristics still produces a decision, and the failure disappears into the aggregate.
Third, selective reporting: negative results (fusion diluting a stronger layer, alignment
training that moves loss but not rankings) are the most informative findings and the least
likely to be published.

We built a layered pipeline — deterministic rules, a constitution checker, an LLM analyzer,
score fusion, provenance weighting — and then measured it under a protocol designed to make
those three failures visible. Contributions:

1. A measurement protocol for guardrail stacks: pre-declared splits, score-blind generation,
   one-shot evaluation, an outage rule, and a forbidden-language list enforced across docs,
   dashboard, and paper.
2. A 306-attack / 264-benign fresh evidence base with per-row provenance, plus a
   second-provider replication that we label partial because 65 rows were purged.
3. A same-set baseline against a pretrained prompt-injection classifier, at matched benign
   false-positive rate, showing a 28.8-point recall gap.
4. Two kept negatives (fusion at n=73; DPO at four configurations) and one scoped positive
   (targeted unlearning at 0.5B with preservation).
5. A reproducible accounting bug: fallback flags were read from dictionaries, but the
   pipeline returns typed objects, so outage rows were being counted as predictions.

## 2. System

The pipeline is a FastAPI service with a React console; the policy surface lives in one
auditable configuration module (`app/config.py`) rather than scattered thresholds.

- **Rules.** Deterministic detectors for override phrasing, exfiltration requests, tool
  abuse, and encoded payloads.
- **Constitution.** A separate LLM role that cites named principles; violations are citable
  against a specific rule, which calibrates confidence differently from the general analyzer.
- **Analyzer.** An LLM classifier with a strict JSON contract; malformed output is treated
  as an error, not as a decision.
- **Fusion.** Max-of-signals (default) or weighted average (legacy); the choice is frozen
  before evaluation.
- **Provenance.** Untrusted sources receive a multiplicative risk boost.
- **Decisions.** ALLOW / REVIEW / BLOCK, with a graduated fail-safe during outages that
  classifies by request characteristics instead of blanket-reviewing everything.

Two LLM layers can be pinned to different providers; when both are pinned, the response
carries `served_by` per row, which is what makes the replication in §8 auditable.

## 3. Protocol

**Splits, declared before generation.** Dev 120 (calibration), adaptation 105, DPO
train/dev 133/29 plus 30 unseen preference items, unlearning forget/retain/general 24/32/24,
benign challenge 132 (16 trigger-word families), test 105 (final reporting only), and sealed
held-out batches (40 + 40 + 153 attacks, 100 benign). Hashes are in
`research/data_manifest.json`.

**Score-blind generation.** Held-out items were generated without running the detector on
them; overlap checks (maximum Jaccard 0.70 against all 923 existing items, zero duplicates)
are recorded in the generation artifact.

**One-shot evaluation.** Each sealed batch is evaluated once under the frozen configuration.
No batch is re-run to improve its number, and no threshold is adjusted after seeing results.

**Outage rule (B66).** A row whose LLM layers fell back to heuristics is not a prediction.
Such rows are purged from the batch and the purge count is reported. This rule was adopted
after we discovered that fallback flags were never being read (see §8).

**Forbidden language.** "solves prompt injection", "secure", "production-ready", "complete
unlearning", "guaranteed forgetting", "human-approved" (pre-OAuth history is SIMULATED), and
any percentage without a denominator.

## 4. RQ1: Do the layers add up? (negative)

On the committed held-out split (n=73), the constitution layer reaches 68/73 = 93.2%
(95% CI 85.7–97.0) and the general analyzer 65/73 = 89.0% (79.9–94.3); max fusion does not
exceed its best member. The three-point gap corresponds to three discordant examples; at
n=73 the Wilson intervals overlap and no McNemar test is possible because the committed
evaluation stored aggregate counts, not per-example paired predictions. We therefore report
RQ1 as unresolved/negative and refuse to claim that fusion helps. A DEV-only McNemar
(n=120, genuinely paired, offline signals) gives p = 0.39 for rule vs constitution,
p = 0.39 for constitution vs fusion, and p = 1.0 for rule vs fusion — non-significant, and
not a substitute for held-out pairs.

## 5. RQ2: Does it generalize to fresh attack families?

Two sealed 40-attack batches were held out and evaluated once each: 38/40 and 38/40, zero
fallbacks. Combined with the frozen re-run (67/73; three fallback rows counted, not
predicted), the pooled first-batch estimate is 143/153 = 93.5% (95% CI 88.4–96.4).

A fully fresh v2 batch was then generated score-blind — 153 attacks across 51 families and
100 benign prompts across 20 families, maximum Jaccard 0.70 against everything already in
the repository — and evaluated once: **132/153 = 86.3% (79.9–90.8)** attacks held, benign
1/100 = 1.0%, zero fallbacks. The 21 misses are enumerated in the artifact, not curated away.

The honest reading is that fresh families are ~7 points harder than the pooled first batch,
and the combined estimate across every fresh attack row ever evaluated once is
**275/306 = 89.9% (86.0–92.8)**. Live benign cost across the frozen run (1/32), the full
132-prompt challenge set (3/132), and v2 (1/100) combines to **5/264 = 1.9% (0.8–4.4)**; the
five flagged items are named in the dashboard rather than filtered.

## 6. RQ3: Alignment

**DPO.** The dataset is 162 preference pairs (133 train / 29 dev) plus 30 unseen phrasings.
Four configurations failed in the same way: loss fell (to 0.0000 in the hottest run) while
train accuracy stayed near 10–20/133 and dev rankings did not move at all (tiny-gpt2
2/29 → 2/29; Qwen2.5-0.5B 0/29 → 0/29 across gentle, hot, and a metric-identical replicate).
Diagnosis: a KL-trap. Once the policy beats the reference by a comfortable relative margin,
the DPO gradient vanishes even though absolute rankings are still wrong; an SFT probe moved
train to only 20/133, confirming a capacity wall rather than a metric artifact (a length-bias
analysis found correlation −0.898 between length difference and margin, but a length-normalized
accuracy remained 2/29).

Config 5 changed capacity and the KL constraint together: Qwen2.5-1.5B with LoRA r16,
β = 0.1, lr 2e-4, 10 epochs, frozen reference. Loss 0.34 → 0.0002, train 128/133, dev
0/29 → **22/29 (75.9%)**. Because the adapter did not survive the training session, the
unseen-30 check was run on a same-config retrain (TRL, 200 s on a T4): base 0/30 → DPO
**23/30 = 76.7% (59.1–88.2)** with dev 19/29 and train 109/133. Unseen accuracy is at the dev
level and below train, so this is preference learning rather than memorization. The retrain
drift (19/29 vs 22/29) is reported rather than averaged.

**Unlearning.** A synthetic trigger is partially removed at low intensity on the tiny model
(4/24 suppressed, 20/24 still emit), not removed at all on 0.5B at gentle intensities, and
fully removed with preservation (24/24 across all λ) on the hotter 0.5B run, replicated. A
real-knowledge run on five demonstrably-known facts is partial (4/5). We claim scoped
removal, not general erasure.

## 7. Baselines: a single classifier on identical sets

We evaluated `ProtectAI/deberta-v3-base-prompt-injection-v2` offline at its default
threshold over the exact same 306 attacks and 264 benign prompts: **187/306 = 61.1%
(55.5–66.4)** attacks flagged at **5/264 = 1.9%** benign flags, zero errors. Its default
threshold already sits at AURA's operating point; a post-hoc threshold chosen on the benign
set to flag at most five rows (0.571) yields the identical 187/306, and even a 7/264 (2.65%)
benign rate only reaches 200/306 = 65.4%. The comparison therefore does not hinge on
threshold choice. It is still not a deployment comparison — one classifier versus an ensemble
with policy thresholds — but it bounds the lift attributable to the stack at roughly
+28.8 recall points at equal false-positive cost.

## 8. Reliability: provider accounting and independence

Two reliability findings matter more than any single recall number.

**The fallback bug (B66).** Evaluation scripts read `llm["used_fallback"]` from a dictionary,
but the pipeline returns typed objects, so the expression always evaluated to `False`. Rows
served by heuristics after an outage were silently counted as model predictions. The fix
(`research/live_flags.py`) reads both typed objects and dicts and counts a fallback if
either LLM layer fell back; 45 contaminated rows were deleted and the affected evaluations
re-run. The outage rule in §3 is the policy consequence.

**Provider independence (partial).** A 12-row two-cell matrix on a second provider (Zen)
replicated 10/10 with zero false positives and zero fallbacks, and per-row `served_by`
confirmed the routing. A larger replication re-ran the whole v2 batch with both LLM layers
pinned to Zen: **130/153 = 85.0% (78.5–89.8)** attacks and **0/35** benign, after 65 of 253
rows were purged on free-tier 429s, the endpoint subsequently returned a 403 free-tier gate, and the
model was later retired with the free quota exhausted — so the missing rows cannot be completed (a
rerun on a current free model produced only fallback rows and was deleted unbanked). We label this
PARTIAL everywhere; independence beyond the primary hosted family is directional, not established.

## 9. Threats to validity

- Live layers are primarily one model family; the second-provider replication is partial.
- Held-out McNemar is impossible (no paired predictions); DEV McNemar is non-significant and
  is not a substitute.
- The SOTA baseline is one checkpoint, offline, at a threshold that happens to match our FPR;
  the matched-threshold sweep is an oracle analysis, not a deployable configuration.
- v2 attack families were authored by the same generator family as v1 (new phrasings, shared
  threat model); cross-taxonomy transfer is untested.
- Training-scale claims stop at 1.5B LoRA; the unseen-30 result comes from a retrain, not the
  original adapter.
- The adaptive red-team live round is pending provider availability; offline bypass rates are
  lower bounds.
- ASR is measured separately from detection (0/21 live canary); detection success is not
  claimed as attack-success prevention.

## 10. Artifact appendix

| Claim | Number | Artifact |
|---|---|---|
| Frozen layer comparison | C 68/73, G 65/73 | `results/baselines_summary/heldout_master_table.json` |
| Sealed batches | 38/40 + 38/40, pooled 143/153 | `results/kaust_three_pillars/heldout_extra/*.json` |
| Fresh v2 | 132/153, benign 1/100 | `results/kaust_three_pillars/heldout_v2/heldout_v2_eval.json` |
| Pooled fresh | 275/306 = 89.9% | `results/kaust_three_pillars/statistics/statistical_eval.json` |
| Benign cost | 5/264 = 1.9% | same, `benign_live_combined` |
| SOTA baseline | 187/306 at 5/264 | `results/kaust_three_pillars/sota/sota_deberta_eval.json` |
| Second provider | 130/153, 0/35 | `results/kaust_three_pillars/heldout_v2/heldout_v2_zen_eval.json` |
| DPO dev | 0/29 → 22/29 | `results/kaust_three_pillars/dpo_lm/dpo_lm_record_qwen15.json` |
| DPO unseen | 0/30 → 23/30 | `results/kaust_three_pillars/dpo_lm/dpo_unseen_qwen15.json` |
| Unlearning | 24/24 hot, 4/24 tiny | `results/kaust_three_pillars/unlearning_lm/*.json` |
| Fallback fix | B66 | `research/BUG_AND_REGRESSION_LEDGER.md` |

Reproduce offline with `python -m pytest tests/ -q` (220 passed, 3 skipped) and
`python -m research.statistical_eval`.
