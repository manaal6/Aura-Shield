# Paper Skeleton — AURA Shield (KAUST VSRP / CyberSaR)

Every claim below is bound to a committed artifact and (where possible) a test pin.
If a number here disagrees with its artifact, the artifact wins and this file is a bug.

Working title: **"Layered Guardrails Under Measurement: What Survives When You Hold the
Prompt-Injection Detector Accountable"**

Positioning: a measurement + engineering paper, not a detector-SOTA paper. The contribution
is the *honest accounting*: one-shot sealed batches, outage rows never allowed to stand,
negative results kept, a SOTA baseline on identical sets, and a second provider.

## Contributions (draft, in order of defensibility)

| # | Claim | Number | Artifact | Pin |
|---|---|---|---|---|
| 1 | Layered pipeline holds 275/306 fresh attacks in a single pass each, never tuned | 275/306 = 89.9% (CI 86.0–92.8) | `results/kaust_three_pillars/statistics/statistical_eval.json` → `new_small_n.pooled_fresh_all` | `tests/test_research_metrics.py` |
| 2 | Fresh-family drop is real and reported (v1 93.5% → v2 86.3%) | 132/153 = 86.3% (CI 79.9–90.8) | `results/kaust_three_pillars/heldout_v2/heldout_v2_eval.json` | `test_heldout_v2_one_shot_and_pooled` |
| 3 | Benign cost stays low across 264 live benign prompts | 5/264 = 1.9% (CI 0.8–4.4) | `benign/benign_live132.json` + frozen run + v2 | `test_research_metrics` combined pin |
| 4 | SOTA single classifier on the SAME sets is much weaker at equal FPR, and its default threshold already sits at that FPR | 187/306 = 61.1% (CI 55.5–66.4), FPR 5/264; matched-threshold sweep identical; 65.4% even at 2.65% FPR | `results/kaust_three_pillars/sota/sota_deberta_eval.json`, `statistical_eval.json` (`sota_matched_fpr`) | `test_sota_baseline_and_zen_partial` |
| 5 | Second provider replicates directionally (partial) | 130/153 = 85.0%, benign 0/35; 65 rows purged | `heldout_v2/heldout_v2_zen_eval.json` | `test_sota_baseline_and_zen_partial` |
| 6 | Fusion policy question answered negatively (kept) | C 68/73 vs G 65/73, CIs overlap | `results/baselines_summary/heldout_master_table.json` | `test_research_metrics` |
| 7 | DPO: the KL-trap is the failure mode; capacity+β unlocks it, and it generalizes off-dev | negative ×4 → 22/29 dev; unseen 0/30 → 23/30 | `dpo_lm/dpo_lm_record_qwen15.json`, `dpo_lm/dpo_unseen_qwen15.json` | `test_dpo_qwen15_first_positive`, `test_dpo_qwen15_unseen_generalizes` |
| 8 | Targeted unlearning works at 0.5B hot, partial elsewhere (scoped) | 24/24 removed + preserved | `unlearning_lm/unlearning_lm_eval.json` | `test_research_metrics` |

## Section outline

1. **Introduction** — guardrail stacks are deployed but rarely measured one-shot; our two
   failure modes for evidence are leakage through iteration and silent provider fallbacks.
2. **System** — rule detector + constitution layer + LLM analyzer + max-fusion + provenance;
   policy surface centralized in `app/config.py` (auditable). Pipeline figure from
   `docs/current-architecture.md`.
3. **Protocol** — pre-declared splits (`research/RESEARCH_PROTOCOL.md`), score-blind
   generation, one-shot evaluation, outage rule (B66), forbidden-language list.
4. **RQ1 (layer contribution)** — negative: fusion dilutes (C 68/73 vs G 65/73), CIs overlap,
   McNemar impossible without paired rows. Keep the negative.
5. **RQ2 (fresh-family generalization)** — sealed 38/40 + 38/40, v2 132/153, pooled 275/306;
   the 21 v2 misses are enumerated, not curated.
6. **RQ3 (alignment)** — DPO dissection (length bias r = −0.898; SFT probe capacity wall;
   configs 1–4 KL-trap; config 5 result). Unlearning scoped.
7. **Baselines** — SOTA DeBERTa-v2 on identical sets (61.1% / 1.9%), caveat that it is a
   single offline classifier vs an ensemble with policy thresholds.
8. **Reliability** — provider fallback accounting (B66 bug: flags read from dicts never
   fired on pydantic objects; fixed in `research/live_flags.py`), outage purges, latency.
9. **Threats to validity** — see below.
10. **Artifact appendix** — every table row → file path + hash in `research/data_manifest.json`.

## Figures/tables to generate (data already exists)

- F1 pipeline diagram (existing).
- F2 recall with Wilson CIs: frozen / v1 pooled / v2 / fresh pooled / SOTA / Zen partial.
- F3 benign FPR by run (frozen, live132, v2) with the 5 held items named.
- T1 evidence ladder (n, CI, fallback rows, purge counts).
- T2 DPO sweep across 5 configs (β, lr, train acc, dev acc, margin).
- T3 unlearning sweep (λ, suppression, preservation).

## Threats to validity (must appear verbatim in the paper)

- Single model family for live layers (Groq-hosted); Zen replication is partial (65 rows
  purged, then endpoint gated) → independence is directional.
- Held-out McNemar impossible (no paired per-example predictions stored for the frozen eval);
  DEV McNemar p = 0.39 n.s. is not a substitute.
- SOTA baseline is one checkpoint, offline, not tuned on AURA data and not a deployment
  comparison. Its default threshold already sits at AURA's 1.9% benign FPR, and a post-hoc
  matched-threshold sweep (oracle) changes nothing — so the gap is not a threshold artifact,
  but the oracle threshold itself is not deployable evidence.
- v2 attack families were authored by the same generator family as v1 (new phrasings, shared
  threat model) — cross-family transfer beyond our taxonomy is untested.
- Training-scale claims stop at 1.5B LoRA; DPO unseen-30 for config 5 is PENDING (dev-only
  claim until it lands).
- Adaptive red-team live round is pending (provider outage); offline red-team rates are
  lower bounds on bypass.

## Forbidden in the paper (mirrors `research/LIMITATIONS.md`)

"solves prompt injection", "secure", "production-ready", "complete unlearning",
"guaranteed forgetting", "human-approved" (pre-OAuth history is SIMULATED), any percentage
without a denominator.

## Open items before submission

1. ~~DPO unseen-30 for config 5~~ DONE: 0/30 → 23/30 on a same-config retrain (`dpo_unseen_qwen15.json`).
2. One live adaptive red-team round (needs provider quota).
3. Zen full v2 benign half (blocked by 403 free-tier gate; label PARTIAL if never resolved).
4. ~~SOTA at matched FPR~~ DONE: default threshold already equals AURA's 1.9% FPR; matched sweep
   identical (61.1%), 65.4% at 2.65% FPR. Oracle threshold labelled as analysis, not deployment.
