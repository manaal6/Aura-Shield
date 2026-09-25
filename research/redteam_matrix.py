"""research/redteam_matrix.py — Phase 14: structured class x variant matrix.

Combines this-sprint offline matrix (artifact-backed) with committed live
full-gateway game numbers (cited, not re-run). Every offline bypass is already
a regression record; classes map to tests/test_kaust_pillars.py + new tests.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

CLASSES = ["Direct", "Indirect", "Jailbreak", "Tool", "Multi-turn"]
VARIANTS = ["Whitespace", "Leetspeak", "Role-play", "Encoding", "Obfuscation",
            "Context flooding", "Instruction splitting", "Unicode",
            "Nested instructions", "RAG injection", "Tool-result injection"]


def main() -> dict:
    off = json.loads((REPO / "results" / "kaust_three_pillars" / "redteam" / "adaptive_redteam.json").read_text())
    recs = off["records"]
    # map 12 offline objectives -> 5 classes
    cmap = {"direct_injection": "Direct", "indirect_injection": "Indirect",
            "fake_system": "Jailbreak", "role_manipulation": "Jailbreak",
            "multilingual": "Jailbreak", "unicode": "Jailbreak", "homoglyph": "Jailbreak",
            "encoded": "Jailbreak", "context_flooding": "Indirect",
            "multi_turn": "Multi-turn", "tool_injection": "Tool", "policy_targeting": "Direct"}
    matrix = {}
    for cls in CLASSES:
        sub = [r for r in recs if cmap.get(r["objective"]) == cls]
        att, byp = len(sub), sum(1 for r in sub if r["bypass"])
        matrix[cls] = {"attempts": att, "bypassed": byp,
                       "held": att - byp, "downstream_success": "NOT MEASURED offline"}
    rep = {"offline_subset_matrix": matrix,
           "offline_totals": {"attempts": off["n_attacks"], "bypassed": off["n_bypass"]},
           "committed_live_game": {
               "whitespace_mutations_block_rate": "21/40=52.5% (full gateway, live, zero-fallback)",
               "roleplay_leetspeak_remutation": "mostly re-evade (committed finding, still open)",
               "source": "results/attacker_defender_summary/gateway_game/"},
           "regression": "all offline bypasses recorded in adaptive_redteam.json; classes pinned in tests",
           "scope": "offline subset = lower bound only (no live LLM)"}
    out = REPO / "results" / "kaust_three_pillars" / "redteam" / "redteam_matrix.json"
    out.write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    return rep


if __name__ == "__main__":
    main()
