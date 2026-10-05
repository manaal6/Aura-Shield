# Limitations (binding — do not contradict these in any doc, dashboard card, or claim)

1. All new model training is toy-to-small scale (100K-param CPU + Qwen2.5-0.5B Kaggle); nothing transfers beyond 0.5B scale without new evidence.
2. DPO: FULL runs, NEGATIVE generalization at 4 configs (tiny dev 2/29 flat; Qwen dev 0/29 flat incl. hotter + replicate). Loss decrease ≠ improvement.
3. Unlearning: tiny PARTIAL (4/24 suppressed, 20/24 still emit; λ=0.5 zero); Qwen gentle ZERO all λ; Qwen hot VALIDATED 24/24 (replicated); fact-mode PARTIAL 4/5 on genuinely-known knowledge (n=5); logistic baseline is COLLATERAL DAMAGE.
4. Seed is v2 C1–C10 (the old C7-payload gap is closed); adaptive principles live at C11–C15 via rename migrations with changelog entries.
5. Offline heuristic ≠ live LLM checker; all offline rates are lower bounds/proxies.
6. RQ1 unresolved at n=73 (overlapping CIs); pooled new-system 143/153 = 93.5% extends but does not resolve it; held-out McNemar impossible (no paired data), DEV McNemar p=0.39 n.s.
7. ASR 0/21 live canary (controlled evaluation); red-team offline bypass 83.3% (85/102) and mutation-screen 4.0% holds are lower-bound artifacts.
8. Multiturn offline 6 + live10 8/8 + live20 15/16 (mechanism evidence); provenance scoring tried (A/B +0.15, no effect — NOT VALIDATED); tool execution measured on a restricted harmless-commands harness (10/10 blocked), container path unvalidated.
9. Pre-OAuth approvals simulated; GitHub OAuth login binds newer approvals to verified usernames (401 without login when configured); audit hash-chain is a file prototype + tamper tests (production Postgres table NOT chained).
10. Forbidden language: "solves prompt injection", "secure", "production-ready", "complete unlearning",
    "guaranteed forgetting", "human-approved" (say SIMULATED for pre-OAuth history), any percentage without denominators.
