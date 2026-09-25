# Limitations (binding — do not contradict these in any doc, dashboard card, or claim)

1. All new model training is on a 100K-param CPU model; nothing transfers to LLM scale without new evidence.
2. DPO: FULL run, NEGATIVE generalization (dev 1/13 before and after). Loss decrease ≠ improvement.
3. Unlearning: best is PARTIAL (20/24, λ∈{0.1,1.0}); λ=0.5 NOT VALIDATED; logistic baseline is COLLATERAL DAMAGE.
4. C7 payload-generation principle absent from seed (documented gap).
5. Offline heuristic ≠ live LLM checker; all offline rates are lower bounds/proxies.
6. RQ1 unresolved at n=73 (overlapping CIs); McNemar NOT RUN (no paired data).
7. ASR n=6, offline-subset detector; red-team offline bypass 76% is a lower-bound artifact.
8. Multiturn n=6 scripted convos (OFFLINE); provenance scoring not yet weighted; tool execution is a stub.
9. Approvals simulated; no authenticated human workflow; no tamper-evident log proof.
10. Forbidden language: "solves prompt injection", "secure", "production-ready", "complete unlearning",
    "guaranteed forgetting", "human-approved" (say SIMULATED), any percentage without denominators.
