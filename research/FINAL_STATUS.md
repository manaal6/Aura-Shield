# FINAL STATUS — acceptance matrix (todo.txt Phase 32)

Statuses: FIXED / IMPROVED / PARTIAL / NOT VALIDATED / NOT IMPLEMENTED.
Single final eval = committed `results/baselines_summary/heldout_master_table.json`
(C 68/73=93.2%, G 65/73=89.0%, precision 100%, FPR 0/32). Policy frozen/unchanged.

| Weakness | Before | Action | Evidence | Status | Remaining limitation |
|---|---|---|---|---|---|
| DPO | objective-PoC only (logistic) | genuine tiny-gpt2 DPO + Qwen2.5-0.5B Kaggle run (494M, loss 0.69→0.39, hash proof) + hotter run (loss→0.0, train 20/133, dev frozen) + hotter replicate (312.7 s, metric-identical) | `dpo_lm_record.json`, `dpo_lm_record_qwen05.json`, `dpo_lm_record_qwen05_hot.json`, `dpo_lm_record_qwen05_hot2.json` | FIXED (training real; outcome negative at ALL scales incl. replicated hot) | dev 2/29→2/29 (tiny), 0/29→0/29 (Qwen, gentle + hot + hot-replicate); no transfer claim |
| DPO dataset | 59 pairs, no IDs | 162 pairs + IDs/rationale/threat, 0 dupes | `dpo_dataset_stats.json`, `DPO_DATASET_REPORT.md` | FIXED | categories uneven (2–13 each) |
| DPO generalization | none | 30 unseen items, eval-only, disjoint | `dpo_generalization.jsonl` (hash `7fda0ee1…`), eval 1/30→1/30 | FIXED (negative) | tiny-model floor effect |
| Unlearning | logistic COLLATERAL DAMAGE | LM sweep λ 0.1/0.5/1.0 + per-example inspect + Qwen sweep (ZERO suppression all λ) + Qwen hot (24/24, all λ) + hot replicate (274.9 s, identical) + real-fact run (5 known / 7 dropped, drops 0.0/0.2/0.2, preserved) | `unlearning_lm_record.json`, `unlearning_lm_eval.json`, `unlearning_lm_inspect.json`, `unlearning_lm_record_qwen05.json`, `unlearning_lm_record_qwen05_hot.json`, `unlearning_lm_record_qwen05_hot2.json`, `unlearning_lm_record_qwen05_fact.json` | PARTIAL (toy) / NEGATIVE (0.5B gentle) / VALIDATED (0.5B hot, replicated) / PARTIAL (real-fact 4/5) | synthetic trigger scope; fact run n=5 forget |
| Fusion | 89 vs 93.2 unexplained | DEV disagreement forensics + criterion freeze + LIVE 120/120 (throttled: 15 clean rows 12/13 attacks, 0/2 benign; 1 full-consensus miss jb-dev-007 pinned) | `fusion_disagreement.json`, live rows | IMPROVED (mechanism found; gap kept) | 105/120 rows fallback-REVIEW (throttle); held-out IDs not reconstructed |
| Statistics | CIs only | Wilson+bootstrap+denominators; DEV McNemar p=0.39 n.s. | `statistical_eval.json`, `STATISTICAL_REPORT.md` | IMPROVED | held-out McNemar impossible (no pairs) |
| Benign robustness | 28 prompts | 132 prompts (16 trigger-word families incl. payload/malware/inject/bypass/breach/phishing/decrypt), 0 held offline | `benign/benign_eval.json` | IMPROVED | offline only; live FPR still 1/32 |
| Indirect injection | 8 payloads | 12 payloads × 7 provenance + objectives; 77/84 confused offline | `indirect/indirect_eval.json` | IMPROVED | live NOT RUN |
| Provenance | logged only | scoring A/B (+0.15): no effect; miss coverage 27/85 | `provenance/provenance_ab.json` | PARTIAL | effect NOT VALIDATED |
| Downstream ASR | 0/6 (n=6) | scaled to 21 attempts, 4 objectives, LIVE downstream 0/21 | `asr/canary_asr.json`, `ASR_REPORT.md` | IMPROVED | 0/21 in this controlled evaluation; text-only downstream |
| Tool authorization | chain + 6 cases | spoofing tests, 10 contract tests | `test_toolsec_contract.py`, `test_phase16_20.py` | FIXED | stub execution only |
| Sandbox | stub-only | Docker-isolated execution (`app/tools/sandbox.py`: net-none, 128m, read-only rootfs) + fail-closed DENY when Docker absent + stub restricted to low-danger | sandbox.py, executor.py, `test_critical_fixes_abc.py` | PARTIAL | container path unvalidated on this host (no Docker daemon); stub behavior tested |
| Analyzer isolation | contract + matrix | + injection-in-output/JSON/tool-directive tests | `test_phase16_20.py` | FIXED | live malformed rate unmeasured |
| Fail-safe | 6 tests | + timeout/rate-limit/key-failure → REVIEW | `test_phase16_20.py` | FIXED | live outage behavior untested |
| Audit integrity | log + changelog | hash-chained log + verify + tamper tests + secret refusal | `audit_chain.py`, `test_phase16_20.py` (5) | FIXED | Postgres log itself not chained |
| Latency | P50/95/99 offline | + mean + failure/fallback accounting | `latency/latency.json` | FIXED | live re-measure blocked |
| Red-team | 72 attacks | offline 102 + DEV mutation screen 1,440 rows (5 families × 3 variants: offline subset holds 54/1,350 = 4.0% — quantifies offline-subset brittleness, not gateway failure) + LIVE smoke 50/50 + LIVE n=100: 100/100 held | `adaptive_redteam.json`, `mutation_screen.json`, `redteam_live50.json`, `redteam_live100.json` | IMPROVED | smoke labels kept; not benchmark-equivalent |
| Multi-turn | 4 convos | offline 6 + LIVE 10 (8/8) + LIVE 20 (15/16; homework-help miss pinned, no fallback) | `multiturn_live10.json`, `multiturn_live20.json` | IMPROVED | mechanism evidence only |
| Adaptive constitution | C8 cycle | parent/reason/removed fields; named-actor approvals (anonymous rejected) + HMAC token verify endpoint + GitHub OAuth login (verified username binds approvals when configured; 401 without login) + frontend login button; SIMULATED label kept for pre-login history | `cycle_C8….json`, `test_approval_hardening.py`, `test_auth_oauth.py`, `app/auth.py` | FIXED | pre-OAuth identities self-asserted, no login |
| Constitution drift | recall/FPR/count | + precision/F1/review-rate; 34→35/170, FPR 0, NO_OVER_RESTRICTION_OBSERVED | `drift_v1_v2.json` | FIXED | offline heuristic |
| Cross-model | 2 cells | 120b/20b 2x2 + qwen/safeguard 5-cell + Zen second-provider 2-cell (all rows provider-attributed): Zen cells 10/10, fp 0/2, 0 fb, all served_by=zen (re-executed 2026-10-03 with fresh user key: byte-identical replication) | `cross_model_live.json`, `cross_model_qwen_safeguard.json`, `cross_model_zen.json` | IMPROVED | n=12 DEV samples per matrix; provider attribution now tracked per-row |
| DPO dissection executed | hypotheses only | β-sweep rejects H1 (dev frozen at β 0.1/0.5/1.0); stark ablation rejects H2 (dev 0/6 frozen); H3 stands | `beta_sweep.json`, `stark_ablation.json` | IMPROVED | capacity explanation untested (needs 7B) |
| Tool execution (real) | stub/text-only | restricted subprocess harness: 10/10 injections blocked, 0 breaches, 3/3 authorized run | `tool_exec_restricted.json` | IMPROVED | harmless-commands scope only |
| Reviewers | single-human assumed | changelog shows 4 distinct humans (Aliya, Manaal Pervaiz, Muhammad Musa + simulated); `/api/reviewers` surfaces counts | live changelog | IMPROVED | pre-OAuth identities self-asserted; post-OAuth approvals carry verified GitHub logins |
| Held-out extension | none | 2× 40 sealed novel attacks, one live eval each: 38/40 + 38/40 (0 fallbacks both), pooled new-system 143/153 = 93.5% (95% CI 88.4%–96.4%) | `heldout_extra_eval.json`, `heldout_extra_v2_eval.json` (+ sealed generators) | IMPROVED | 4 allows are ambiguous-boundary cases, not promoted |
| Reproducibility | commands doc | + manifest hashes, checkpoint hashes, seeds | `REPRODUCIBILITY.md`, `data_manifest.json` | FIXED | — |
| Dashboard | 14 tabs (new) | verified artifact-only loads; ASR wording fixed | `research_lab.py` (import OK) | FIXED | old tabs not redesigned |

## Frozen re-run (new system C1–C10 + max fusion, LIVE, 2026-09-22)

`results/kaust_three_pillars/frozen_rerun/`: 67/73 recall (91.8%), 1/32 FPR (3.1%), 3 fallback rows.
Clean rows: attacks 65/70 held, benign 1/32 FP (cs-test-012: benign Log4Shell explainer,
constitution C7 fires 0.95 → escalation BLOCK — genuine over-fire, kept visible).
Fallback rows: 2 attacks held via fail-safe REVIEW; tool-test-016 ALLOWED via graduated
fail-safe "known_safe" passthrough (fail-safe miss, motivates outage test G).
Old system: G 65/73, 0/32. Net: +2 TP / +1 FP. Old numbers stand as the old-system record.

## This-pass critical fixes (Prompt.txt order)

- A HMAC: dedicated `AURA_APPROVAL_HMAC_SECRET`, Groq-key/default coupling removed, missing → loud RuntimeError (`tests/test_critical_fixes_abc.py`).
- B Docker: high/critical + no Docker → DENY/UNAVAILABLE (fail-closed); stub low-danger only.
- C Fallback reporting: `research/fallback_reporting.py` (LIVE/FALLBACK/OFFLINE states, per-row + aggregate).
- E Fusion live compare (DEV n=119 clean): old 88/90 (97.8%), max 90/90 (100%), constitution-only 89/90 (98.9%), all FPR 0.
- G Outage 50/50: full hold (50 held / 0 benign allowed); graduated ALLOW path unreachable in prod wiring (test/prod gap recorded).
- D Over-refusal: 1/52 = 1.9% live (or-04 safe-completion BLOCK, pinned).
- H Tool ASR: 0/24 breaches (gateway 20 block/4 review; authorizer 23 REVIEW/1 ALLOW).
- K Thresholds labeled implemented-not-optimized in `app/config.py`.
- Kaggle export: `research/KAGGLE_EXPORT.md` (notebook cells + paste-back protocol).

## Live execution status (7-key pool)

Executed live: frozen 105, DEV forensics 120/120, ASR downstream 0/14, over-refusal 52,
tool ASR 24, red-team smoke 50/50, multi-turn smoke 8/8, load sweep 1-50, cross-model 120b/20b.
Quota is currently healthy; B27/B31 describe resolved transient episodes (key rotation added, B23).

## Model/checkpoints

tiny-gpt2 (102,714). DPO ckpt hash `117f1472…` (run 2). Unlearning `unlearned_lambda_{0.1,0.5,1.0}.pt` + `implanted.pt`. torch 2.13.0+cpu. Seeds 7/11.

## Dataset hashes

dpo `1108ff9a…`, dpo-gen `7fda0ee1…`, forget `9fb679a8…`, retain `dd5780a3…` (32), general `062ce226…`, benign-challenge `f3febf80…` (132), test set matches frozen baseline (integrity PASS).

## Tests

210 passed / 0 failed / 3 skipped (Docker-present sandbox skips) (`research/FINAL_TEST_REPORT.md`).

## Held-out integrity / secrets

Integrity artifact verdict PASS (hashes match, guards block, train clean). Secrets sweep: no key material in repo; canary name-only. `.env` untouched, never printed.

## Overall: PARTIAL (READY FOR REVIEW on executed scope)

Remaining future work: second-provider execution, Docker-host sandboxing, authenticated human approval, hotter/longer GPU training reruns. All executed items above carry their evidence artifacts; no status exceeds what the evidence supports.
