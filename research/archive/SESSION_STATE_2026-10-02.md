# Session handoff (compact; 2026-10-02)

HEAD: check `git log --oneline -1`. Remote: manaal6/Aura-Shield, main.
Rule: NEVER commit/push unless user says the word. Excluded always: .env, Prompt.txt, todo.txt, Output.txt, .pytest_temp/.

## Standing facts
- Tests: 191 green (`python -m pytest tests/ -q`). Suite is offline except live scripts.
- Seed constitution v2 C1–C10; adaptive C11 (renamed from colliding C7; migration + changelog).
- Held-out committed: C 68/73, G 65/73. Frozen re-run (new): 67/73, 1/32.
- DPO: 162 pairs; tiny + Qwen2.5-0.5B + hotter Qwen — all NEGATIVE (ranking frozen).
- Unlearning: logistic COLLATERAL; tiny PARTIAL (4/24, one template); Qwen gentle ZERO; Qwen HOT VALIDATED (24/24 all λ).
- ASR 0/14 live; over-refusal 1/52; tool ASR 0/24; red-team 102 off + 50 live; multiturn 6 off + 10 live.
- Groq pool: 7 keys in .env (GROQ_API_KEY…_7), rotation in research/groq_pool.py. Values never printed.
- HMAC: AURA_APPROVAL_HMAC_SECRET in .env; approvals named+signed; /api/constitution/verify.
- Deploy: Render uvicorn webapp.server:app. DB Supabase (pooler timeouts observed). Frontend React→webapp/static bundle; rebuild after src changes; bundle-consistency test guards deletions.
- Dashboard: 6 sections + subnav (App.tsx), light palette chosen then user-customized index.css, mobile CSS present. Streamlit lab local-only.
- Docs source of truth: research/FINAL_STATUS.md (matrix), research/AURA_SHIELD_COMPLETE.md (system record), research/BUG_AND_REGRESSION_LEDGER.md (B1–B47+).
- User context: applying KAUST VSRP, CyberSaR/Ali Shoker, LLM-injection project. Reviewer fixes in progress (todo list in progress at handoff).

## In progress (2026-10-02 reviewer fixes)
- SOC demo DONE: research/soc_demo_live.py → results/kaust_three_pillars/soc_demo/soc_demo_live.json (3/5 held, 2/2 safe). Typo fixed post-run (label only).
- TODO: DPO dissection doc, refuse-payload-explain ×20 measure, reviewer brief, SOC panel in UI (endpoint block + frontend), ledger, suite, summary.
