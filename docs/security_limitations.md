# Security Limitations (KAUST Sprint — skeptical review summary)

1. **Protected:** single-request prompt-injection screening at the gateway;
   audit logging of decisions. **Not protected:** multi-turn state, tool-side
   channels, weight exfiltration, infrastructure.
2. **Trust boundaries:** `source_content` never authoritative; downstream LLM
   output untrusted until schema-validated; constitution DB deltas need human
   approval; adaptation/DPO/forget data never the test split.
3. **External content CAN look like instructions** — that is the threat; the
   gateway holds heuristic-detectable cases offline (tiny DPO-dev 2/29, Qwen 0/29) and relied on
   live LLM layers (93.2% constitution recall, committed) for the rest.
4. **Analyzer manipulation:** a compromised/failing analyzer routes to REVIEW
   (fail-safe), never silent ALLOW — tested.
5. **Constitution poisoning:** seed file is deploy-trusted; DB additions require
   approval provenance; contradiction/duplicate validators run per candidate.
6. **Adaptation poisoning:** adaptation split is attacker-shapeable in
   principle; mitigation = human approval gate + dev regression + read-only
   test reporting. Fully autonomous adaptation is explicitly NOT claimed.
7. **Fusion bypass:** offline subset bypass 83.3% (85/102, no live LLM; mutation screen holds 4.0%); live game
   measured 52.5% block on whitespace mutations — adaptive role-play/leetspeak
   re-evade (committed finding, still open).
8. **Multi-turn:** held-out family; offline rule recall 0.0 — live layers only.
9. **Tool execution:** model never directly executes; synthetic fixtures,
   authorization + validation + risk check required.
10. **Logs:** Postgres audit + changelog; tamper-evidence beyond that is future work.
11. **DPO changes:** LM runs negative at 4 configs (tiny dev 2/29→2/29, unseen 1/30→1/30; Qwen 0/29 + 0/30 incl. hotter + replicate); logistic PoC superseded; no LLM claim beyond 0.5B.
12. **Unlearning removes:** tiny one-template 4/24 (20/24 still emit); Qwen gentle ZERO, hot VALIDATED 24/24 (replicated),
    fact-mode partial 4/5 on genuinely-known knowledge; logistic baseline collapsed general scores (0.27→0.01).
13. **Weak statistics:** DPO dev n=29 + unseen n=30 (negative); held-out RQ1 n=73 overlapping CIs, pooled 143/153 and fresh-pooled 275/306 = 89.9% (held-out v2 alone 132/153 = 86.3%) extend but not resolve; held-out McNemar impossible (no paired data), DEV McNemar p=0.39 n.s.
14. **Unprotected remainder:** seed v2 closed the C7 payload gap (C1–C10 + adaptive C11–C15); live ASR measured 0/21 (controlled); C8 v2 lift measured on held-out (65→68/73).
15. **Unsafe claims (never make):** "solves prompt injection", "secure",
    "production-ready", "complete unlearning", "guaranteed forgetting".
    Approved: "research prototype", "smoke-tested", "measured on controlled
    evaluation", "preliminary", "NOT RUN".
