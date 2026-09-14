# Rerun note (data repair documentation)

Rows 94 (tool-test-010) and 104 (tool-test-020) initially fell back to offline
heuristics when the provider quota was exhausted near the end of the run. Both
prompts were re-executed with live model calls on 2026-09-14 (key: org
01m1p1ycxjevj9my8m35tsqnp3), returned live results (both BLOCK), and their rows
were replaced in raw_results.jsonl. metrics.json was recomputed from the
repaired raw results. Final fallback count: 0/105. This repair is disclosed for
full transparency; no other rows were modified.
