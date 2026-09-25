# Adaptive Constitution Report (v1 → v2 + C8)

## Lifecycle (per version)

failure (adaptation split only) → candidate → validators (schema/uniqueness + contradiction +
duplicate) → dev regression → approval → versioned artifact → read-only unseen eval.

## Versions

- v1: seed C1–C6 (file), hash `e4debd64…`.
- v2a (committed prior work): + C7-no-encoded-obfuscation from adaptation misses; held-out full-gateway
  recall 89.0%→93.2% (65/73→68/73, overlapping CIs).
- v2b (this sprint): + C8-no-context-window-overflow from 20 context-flooding misses (distinct pattern);
  APPROVED; artifact `adaptive/cycle_C8-no-context-window-overflow.json` + `constitution_v2.json`.

## Approval honesty

All approvals are SIMULATED HUMAN APPROVAL (`approved_by: simulated_human_auditor` /
`human-reviewer-kaust-sprint`). No authenticated human workflow exists. The generating process never
approves its own principle: validation gates run before the recorded approval state.

## Drift (`adaptive/drift_v1_v2.json`)

Offline heuristic, adaptation+dev (n=225): v1 recall 34/170 = 20.0% → v2 35/170 = 20.6%
(+1 flooding catch: the `[ADMIN OVERRIDE]`-in-padding pattern), FPR 0/55 = 0.0% both,
newly-blocked benign 0 → over-restriction PASS. C8 pattern is honestly narrow (1/20 flooding
samples match); broadening without live validation would risk over-restriction.

## RQ2 answer

Yes, with caveats: updates from discovered failures improved held-out recall without FPR regression
in the C7 cycle; the C8 cycle shows the mechanism works but its offline lift is minimal (+1) and its
live lift is NOT YET VALIDATED.
