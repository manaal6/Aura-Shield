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

## Human approval procedure (operative)

Past records (C7, C8 cycles) remain labeled SIMULATED HUMAN APPROVAL — that label is
historical fact and is never rewritten. For NEW approvals, a genuine human procedure exists:

1. Reviewer opens the Constitution tab (deployed console or local dashboard).
2. Reviews the pending principle (text, rationale, triggering failures, validator results).
3. Enters their REAL name (anonymous/empty is rejected with HTTP 400).
4. Approves or rejects. Approval signs an HMAC token (dedicated secret) binding
   principle + actor + timestamp into the changelog.
5. Anyone can verify later: `POST /api/constitution/verify` (constant-time compare),
   or `verify_approval_token()` offline.

What this is: named, signed, verifiable human accountability. What it is not: authenticated
identity (no login infrastructure — names are self-asserted, enforced non-empty by code).

## Drift (`adaptive/drift_v1_v2.json`)

Offline heuristic, adaptation+dev (n=225): v1 recall 34/170 = 20.0% → v2 35/170 = 20.6%
(+1 flooding catch: the `[ADMIN OVERRIDE]`-in-padding pattern), FPR 0/55 = 0.0% both,
newly-blocked benign 0 → over-restriction PASS. C8 pattern is honestly narrow (1/20 flooding
samples match); broadening without live validation would risk over-restriction.

## RQ2 answer

Yes, with caveats: updates from discovered failures improved held-out recall without FPR regression
in the C7 cycle; the C8 cycle shows the mechanism works but its offline lift is minimal (+1) and its
live lift is NOT YET VALIDATED.
