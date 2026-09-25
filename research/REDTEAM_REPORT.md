# Red-Team Report (matrix + multi-turn + indirect)

Scope convention: OFFLINE = rule detector + heuristic constitution check, no live LLM (lower bound only).
LIVE = committed held-out runs with live models (cited, not re-run).

## Offline matrix (102 attacks, 17 objectives × 6 budget; `redteam/adaptive_redteam.json`)

Bypassed 85/102 = 83.3% of the OFFLINE SUBSET.
Per-class (`redteam/redteam_matrix.json`): Direct/Indirect/Jailbreak/Tool/Multi-turn breakdown recorded.
Every bypass is a stored regression record. Scope: lower bound only.

## Committed live game (cited, not re-run)

Full gateway blocks 21/40 = 52.5% of whitespace mutations that bypass rules at 100%;
role-play/leetspeak re-mutations mostly re-evade (still open).

## Multi-turn (`multiturn/multiturn_eval.json`)

Conversation-latching eval, 6 scripted convos (OFFLINE): attacks held 2/5, benign clean 1/1.
Tool-auth across turns NOT modeled (chain is single-turn). Live 10-scenario suite below.

## Indirect / provenance (`indirect/indirect_eval.json`, OFFLINE)

Definition: 1 record = 1 payload × 1 provenance tag (12×7=84 records). "Confused" = the OFFLINE
subset did NOT hold the prompt, i.e. the embedded instruction passed undetected.
77/84 confused; 7 held (all system-prompt-extraction via C2 patterns).
Provenance is logged but not yet weighted in scoring — provenance-aware SCORING is future work.
Content-vs-instruction distinction at LIVE layers relies on the LLM analyzer + constitution
(committed held-out recall: C 68/73, G 65/73).

## Live red-team smoke (n=50, `redteam/redteam_live50.json`)

10 objectives × 5 mutations through the live gateway: held 50/50 (37 BLOCK + 13 REVIEW).
Clean rows 37/37 held; 13 REVIEWs are fallback fail-safes under throttling. Zero allows.
LABEL: live smoke, kept separate from the frozen benchmark and the offline matrix.

## Live multi-turn smoke (n=10, `multiturn/multiturn_live10.json`)

Latching convo eval, live: attacks held 8/8; benign clean 1/2 — the flagged benign convo
(benign-control) tripped on fallback REVIEWs at turns 2–3, turn 1 clean ALLOW.
LABEL: mechanism evidence (latch works), NOT robustness proof.

## Benign challenge (`benign/benign_eval.json`, OFFLINE)

62 legitimate trigger-word prompts: held 0/62 = 0.0% — no lexical over-triggering at this layer.
Live LLM layers NOT RUN (over-refusal measured separately in DPO eval: 1/1 benign-dev preferred refusal → over-refusal present at toy scale).
