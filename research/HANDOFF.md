# Handoff (2026-10-07, context compacted)

HEAD: `git log --oneline -1`. Remote manaal6/Aura-Shield main. Rule: commit/push ONLY on explicit user word. Never commit .env/Prompt.txt/todo.txt/Output.txt/.pytest_temp. Secret-scan staged diff every push (gsk_/oc_sk_/sk-/AKIA patterns).

## State
- Tests 220 passed + 3 skipped offline (skips = Docker-present, fail-closed path N/A). Suite: `python -m pytest tests/ -q`.
- Constitution seed v2 C1-C10; adaptive C11 (ex-C7) + C12/C13 + C15 renames via DB migrations with changelog; past approvals SIMULATED except user's live v5/v6 (Manaal Pervaiz, HMAC-signed).
- Held-out frozen: C 68/73, G 65/73. Frozen re-run (new): 67/73, 1/32. Pooled new-system 143/153=93.5% (frozen + 2× sealed 38/40, 0 fb). Held-out v2 (fresh 153+100, one-shot, 0 fb): 132/153 = 86.3%, benign 1/100; fresh pooled (v1+v2) 275/306 = 89.9%; combined live benign FPR 5/264 = 1.9%. B66: Groq 403 outage poisoned 45 v2 rows → deleted; live_flags.py fallback fix.
- DPO: 162 pairs; NEGATIVE at 4 configs (KL-trap: loss saturated, train flat); POSITIVE at config 5 (Qwen-1.5B LoRA β=0.1: dev 22/29, train 128/133); unseen-30 on a same-config retrain generalizes (0/30→23/30, dev 19/29). H3 (capacity) confirmed as the lever.
- Paper: `research/PAPER_DRAFT.md` (draft 1 from `PAPER_SKELETON.md`; all numbers artifact-bound).
- Unlearning: logistic COLLATERAL; tiny PARTIAL (4/24 one template); Qwen gentle ZERO; Qwen HOT VALIDATED 24/24 all λ. RQ4 Yes-with-scope.
- Live E2E (Groq 8-key pool, research/groq_pool.py): DEV 120/120, redteam 50+100 (100/100), multiturn 10 (8/8) + 20 (15/16, homework-help miss pinned), ASR 0/21, benign live132 3/132 (badge-reader, test-suite, scanner-noise holds) + held-out v2 benign 1/100, over-refusal 1/52, tool ASR 0/24, load sweep, cross-model 120b/20b + qwen/safeguard + Pollinations INVALID (legacy API 402/404, silent Groq fallback caught by attribution) + Zen-attributed (24/24 served_by=zen).
- Groq pool: .env GROQ_API_KEY…_9 (all verified alive 2026-10-07; probe must send a browser UA — Cloudflare 1010 otherwise, B75). Gemini key denied (project-level). Zen oc_sk key: user-given, stored at `%USERPROFILE%\.aura_zen_key` and in gitignored `.env`; never committed, never printed. Zen free quota exhausted (429) and `space-bunny-free` retired. Pollinations: no key needed.
- DB Supabase: pooler timeouts observed; code has fallbacks (seed file, buffer logs, degraded eval states). Additive migrations in app/engine/constitution.py; schema evolution in database.py.
- HMAC: AURA_APPROVAL_HMAC_SECRET in .env; approve requires named actor; /api/constitution/verify.
- Frontend: React 6 sections + subnav (App.tsx), light palette (user-customized index.css), mobile CSS; build in webapp/frontend → static bundle; bundle-consistency test guards deletions.
- Deploy: Render uvicorn webapp.server:app. /api/evidence serves artifacts w/ has_data guards.
- Docs truth: research/FINAL_STATUS.md (matrix), research/AURA_SHIELD_COMPLETE.md (record), research/BUG_AND_REGRESSION_LEDGER.md (B1–B68), research/REVIEWER_BRIEF.md.
- User context: KAUST VSRP application, CyberSaR/Ali Shoker. Kaggle work complete (fact-mode + hotter + replicate integrated; guide: research/KAGGLE_STEPS.md).
- Gotchas: run scripts via `python -m` (research/statistics.py shadows stdlib → renamed research/stats.py); PowerShell lacks head/tail/grep/du/timeout; cp1252 breaks unicode console output; `-m` needed for module runs (missing __main__ guard bit before); resume-merge overwrote files once → per-file parts authoritative.
