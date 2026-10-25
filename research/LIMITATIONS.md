# Limitations (binding — do not contradict these in any doc, dashboard card, or claim)

1. All new model training is toy-to-small scale (100K-param CPU + Qwen2.5-0.5B Kaggle); nothing transfers beyond 0.5B scale without new evidence.
2. DPO: FULL runs, NEGATIVE at 4 configs (tiny 2/29 flat; Qwen-0.5B 0/29 flat incl. hotter + replicate), POSITIVE at config 5 (Qwen-1.5B LoRA β=0.1: dev 0/29→22/29, train 128/133), and the unseen-30 check on a same-config retrain generalizes (0/30→23/30, dev 19/29, train 109/133 — unseen not below train, so no memorization signature; retrain counts differ from the original adapter and are reported separately). Loss decrease ≠ improvement.
3. Unlearning: tiny PARTIAL (4/24 suppressed, 20/24 still emit; λ=0.5 zero); Qwen gentle ZERO all λ; Qwen hot VALIDATED 24/24 (replicated); fact-mode PARTIAL 4/5 on genuinely-known knowledge (n=5); logistic baseline is COLLATERAL DAMAGE.
4. Seed is v2 C1–C10 (the old C7-payload gap is closed); adaptive principles live at C11–C15 via rename migrations with changelog entries.
5. Offline heuristic ≠ live LLM checker; all offline rates are lower bounds/proxies.
6. RQ1 unresolved at n=73 (overlapping CIs); pooled new-system 143/153 = 93.5% and fresh pooled (v1+v2) 275/306 = 89.9% (CI 86.0%–92.8%) extend but do not resolve it — held-out v2 alone was 132/153 = 86.3% (CI 79.9%–90.8%), i.e. fresh-family recall sits 7 points below the v1 pooled estimate; held-out McNemar impossible (no paired data), DEV McNemar p=0.39 n.s. Live benign FPR combined 5/264 = 1.9% (CI 0.8%–4.4%).
7. ASR 0/21 live canary (controlled evaluation); red-team offline bypass 83.3% (85/102) and mutation-screen 4.0% holds are lower-bound artifacts.
8. Multiturn offline 6 + live10 8/8 + live20 15/16 (mechanism evidence); provenance scoring tried (A/B +0.15, no effect — NOT VALIDATED); tool execution measured on a restricted harmless-commands harness (10/10 blocked), container path unvalidated.
9. Pre-OAuth approvals simulated; GitHub OAuth login binds newer approvals to verified usernames (401 without login when configured); audit hash-chain is a file prototype + tamper tests (production Postgres table NOT chained).
10. SOTA comparison is OFFLINE and single-model: ProtectAI DeBERTa-v3 prompt-injection-v2 at its
default threshold caught 187/306 = 61.1% of the same fresh attacks (95% CI 55.5-66.4%) with
5/264 = 1.9% benign FPR; AURA pooled 275/306 = 89.9% at equal FPR. This bounds the lift, it is
NOT a head-to-head deployment test (AURA is an LLM ensemble with policy thresholds; the classifier
was not trained or tuned on AURA data). Its DEFAULT threshold already flags 5/264 benign rows, i.e. it
already sits at AURA's operating point: a post-hoc matched-threshold sweep (threshold 0.571, oracle,
not deployable) gives the same 187/306 = 61.1% at 5/264 = 1.9%, and even at 7/264 = 2.65% it only
reaches 200/306 = 65.4% — so the gap is not a threshold artifact. Second-provider evidence is PARTIAL: Zen replicated
130/153 = 85.0% attacks and 0/35 benign after 65 free-tier-outage rows were purged (B66 rule),
the replicated model was later retired and the free quota is now exhausted, so those rows cannot be
completed; provider independence beyond the Groq-hosted family stays directional, not established.
11. Forbidden language: "solves prompt injection", "secure", "production-ready", "complete unlearning",
    "guaranteed forgetting", "human-approved" (say SIMULATED for pre-OAuth history), any percentage without denominators.
