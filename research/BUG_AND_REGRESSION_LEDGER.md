# Bug & Regression Ledger (Phase 30)

| ID | Description | Impact | Discovery | Fix | Experiment | Regression test | Date |
|---|---|---|---|---|---|---|---|
| B1 | drift harness dropped `source_content` | v1/v2 drift vacuous (identical) | manual review | pass source through | drift | rerun shows 34→35/170 | 2026-09-21 |
| B2 | toolsec test expected DENY for parseable `run X` | 1 test failure | pytest | expectation→REVIEW path; unknown-tool case uses unparseable text | toolsec | test_toolsec_contract | 2026-09-21 |
| B3 | implant lr/epochs too weak (forget 0.0) | unlearning sweep meaningless | metrics read | implant 30 epochs @3e-3 → forget 1.0 | unlearning_lm | record before/after | 2026-09-21 |
| B4 | `statistics.rate_str` ZeroDivision on n=0 | statistical_eval crash | run | n=0 guard → "n/a" | stats | rerun clean | 2026-09-21 |
| B5 | cp1252 UnicodeEncodeError writing λ/CIs on win32 | statistical_eval crash | run | explicit utf-8 on all artifact writes | stats | rerun clean | 2026-09-21 |
| B6 | `train.py` runs training even with `--help` (no argparse) | accidental 2-min training trigger | run | documented; checkpoint hash verified unchanged (`90f7e023…`) | dpo_lm | hash check | 2026-09-21 |
| B7 | `Path.parent` depth bugs in 3 builder scripts (wrote under `training/data/`) | FileNotFoundError | run | `.parent.parent(.parent)` fixes | datasets | rerun clean | 2026-09-21 |
| B8 | nested quotes SyntaxError in v5 builder | builder crash before write | run | rephrased string | dpo data | rerun: 162 pairs | 2026-09-21 |
| B9 | DPO 133-pair config timed out (15 min) | no checkpoint | timeout | epochs 15→6, batch 8, len 128 (documented) | dpo_lm | new record 203 s | 2026-09-21 |
| B10 | Groq 403 on analyzer/constitution + DB DNS timeouts | live DEV forensics infeasible (39→72 s/call) | measurement | BLOCKED, documented; offline-paired analysis stands | fusion | fusion_forensics docstring | 2026-09-21 |
| B11 | unlearning `platform.machine` missing parens | hardware field garbage | review | `platform.machine()` | unlearning_lm | record shows AMD64 | 2026-09-21 |
| B12 | ASR report duplicated stale 0/6 block after edit | confusing report | review | dedup edit | docs | read-back | 2026-09-21 |
| B13 | UNLEARNING_REPORT orphaned Verdict text after edit | garbled section | review | structural edit | docs | read-back | 2026-09-21 |
| B14 | dashboard `load("..",..)` wrong root + `c and g` typo | missing artifacts/crash risk | review | `load_root` + fix | dashboard | import + 14 tabs | 2026-09-21 |
| B15 | PowerShell `head/wc/du/grep/timeout` absent on win32 | failed shell probes | run | Measure-Object/Select-Object equivalents | ops | — | 2026-09-21 |
| B16 | Dashboard DPO tab + STATISTICAL_REPORT cited stale run-1 numbers (1/13) after retrain | misleading UI/report | review | dashboard 2/29 + unseen 1/30; stats generator reads artifacts | docs | read-back | 2026-09-22 |
| B17 | `use_container_width` deprecated (Streamlit 1.58) | future dashboard crash risk | warning | `width="stretch"` (5 sites) | dashboard | import check | 2026-09-22 |
| B18 | statistical_eval hardcoded new-experiment counts | stale/wrong CIs after retrain | review | generator reads dpo_lm_eval + unlearning eval artifacts | stats | regenerated 2/29, 20/24-emit | 2026-09-22 |
| B19 | `fusion_forensics.py` missing `__main__` guard + `DEV/only` double-path | all `-m` runs exited 0 silently / FileNotFoundError | manual trace | guard added; `Path(only).name` | forensics | direct 30 live rows banked | 2026-09-22 |
| B20 | forensics resume-merge overwrote prior files; recovery merge ran on incomplete parts | 30 live benign rows + 60 attack rows (indirect/jailbreak) lost | audit | per-file parts authoritative; ALL RECOVERED 2026-09-22 after key recovery (4 part files, 120 rows merged) | forensics | parts exist; combined 120 | 2026-09-22 |
| B21 | Groq daily quota exhausted mid-forensics (199,853/200,000 TPD) | live DEV/indirect/jailbreak reruns blocked | API error message | key recovered; all reruns completed | live eval | 120 live rows | 2026-09-22 |
| B22 | jb-dev-007 live full-consensus miss (rule 0, LLM 0.03, const 0) | 1/90 DEV attacks fully missed | live forensics | pinned as regression test, not hidden | fusion | test_jb_dev_007_regression (2 tests) | 2026-09-22 |
| B23 | `groq_pool` read os.environ only; .env fallback keys invisible (pool size 1 after adding key 2) | rotation silently single-key | review | `.env` fallback parser; verified pool size 2 with live rotation | live eval | rotation test | 2026-09-22 |
| B24 | pool extended to 4 keys (user-supplied); all 4 verified live via rotation test | prior single-key throttling (105/120 fallbacks) | key addition | 8 probe calls across 4 entries, 12.5 s, zero failures | live eval | rotation test | 2026-09-22 |
| B25 | `frozen_rerun.py` recorded per-signal columns as 0.0 (dict-only extraction on pydantic objects) | invalid signal columns + broken fallback flags in frozen artifact | review | getattr fallback; full 105 re-run | frozen eval | corrected artifact | 2026-09-22 |
| B26 | graduated fail-safe `known_safe` ALLOW unreachable in prod wiring (proxy always true) | outage = full hold; unit tests cover a dead path | outage test 50/50 | documented as test/prod gap; fix scoped (plumb source_content), not silently patched | fail-safe | outage_test.json | 2026-09-22 |
| B27 | all 4 Groq keys share one org → shared 200K TPD quota; rotation helps RPM, not TPD | quota exhaustion blocks remaining live work | API error counters | documented; key-rotation scope corrected | live eval | — | 2026-09-22 |
| B28 | cross-model matrix passed SHORT names (120b/llama8b) as model IDs; A-row 12/12 fallback garbage reported as 10/10 | invalid cells | review of artifact | full IDs via MODELS map; bad artifact DISCARDED (not quoted anywhere), rerun | cross-model | rerun | 2026-09-22 |
| B29 | rerun with full IDs still invalid: llama/mixtral/gemma Groq IDs retired (12/12 fallback/A-row) + org quota exhausted (120b cells failing) | no valid family signal | error/fallback audit | matrix marked INVALID, never quoted; valid evidence stays 120b/20b sample + committed cells | cross-model | verdict in summary JSON | 2026-09-22 |
| B30 | Kaggle Qwen2.5-0.5B run: BF16 `.numpy()` crash, grad-accum flush bug, sft() arity bug | blocked GPU run | user pastes traceback | all fixed + CPU selftest green before re-upload | kaggle script | selftest | 2026-09-22 |
| B31 | All 6 Groq keys 403 PermissionDenied ("check network settings") during matrix run | re-probed on next session: transient; all keys healthy, pool extended to 7, all verified live | live eval | probe transcript + rotation test | 2026-09-22 |
| B32 | `groq_pool.chat` blacklisted healthy keys on model-NotFoundError (wrong model blamed on key) | cascade kills whole pool on one bad model ID | probe run | blacklist only on credential/quota errors; NotFoundError raises immediately | live eval | probe | 2026-09-22 |
| B33 | 7/7 keys individually ALIVE; availability probe scoped the matrix to existing IDs (120b/20b executed; 5 probed IDs retired) | per-key + per-model probes | 120b/20b matrix stands as valid evidence; `model_availability.json` | cross-model | probe | 2026-09-22 |

All fixes verified by re-execution; no failing test was deleted (B2 fixed the expectation with rationale, not the invariant).
