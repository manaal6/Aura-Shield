# Security Limitations (KAUST Sprint — skeptical review summary)

1. **Protected:** single-request prompt-injection screening at the gateway;
   audit logging of decisions. **Not protected:** multi-turn state, tool-side
   channels, weight exfiltration, infrastructure.
2. **Trust boundaries:** `source_content` never authoritative; downstream LLM
   output untrusted until schema-validated; constitution DB deltas need human
   approval; adaptation/DPO/forget data never the test split.
3. **External content CAN look like instructions** — that is the threat; the
   gateway holds heuristic-detectable cases offline (3/8 DPO-dev) and relied on
   live LLM layers (93.2% constitution recall, committed) for the rest.
4. **Analyzer manipulation:** a compromised/failing analyzer routes to REVIEW
   (fail-safe), never silent ALLOW — tested.
5. **Constitution poisoning:** seed file is deploy-trusted; DB additions require
   approval provenance; contradiction/duplicate validators run per candidate.
6. **Adaptation poisoning:** adaptation split is attacker-shapeable in
   principle; mitigation = human approval gate + dev regression + read-only
   test reporting. Fully autonomous adaptation is explicitly NOT claimed.
7. **Fusion bypass:** offline subset bypass 76% (no live LLM); live game
   measured 52.5% block on whitespace mutations — adaptive role-play/leetspeak
   re-evade (committed finding, still open).
8. **Multi-turn:** held-out family; offline rule recall 0.0 — live layers only.
9. **Tool execution:** model never directly executes; synthetic fixtures,
   authorization + validation + risk check required.
10. **Logs:** Postgres audit + changelog; tamper-evidence beyond that is future work.
11. **DPO changes:** LM run negative (dev 2/29→2/29, unseen 1/30→1/30 at toy scale); logistic PoC superseded; no LLM claim.
12. **Unlearning removes:** one synthetic trigger (1.00→0.00) at the cost of
    general-score collapse (0.27→0.01); retain unsafe-rate preserved.
13. **Weak statistics:** DPO dev n=29 + unseen n=30 (negative); held-out RQ1 n=73 overlapping CIs; held-out McNemar impossible (no paired data).
14. **Unprotected remainder:** payload-generation principle (C7) absent from
    seed; live ASR unmeasured; C8 v2 LLM-lift unmeasured.
15. **Unsafe claims (never make):** "solves prompt injection", "secure",
    "production-ready", "complete unlearning", "guaranteed forgetting".
    Approved: "research prototype", "smoke-tested", "measured on controlled
    evaluation", "preliminary", "NOT RUN".
