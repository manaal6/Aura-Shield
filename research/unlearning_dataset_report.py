"""research/unlearning_dataset_report.py — Phase 5: forget/retain/general stats + closeness."""
from __future__ import annotations

import collections
import hashlib
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOK = re.compile(r"[a-z0-9']+")


def load(name):
    return [json.loads(ln) for ln in
            (REPO / "data" / f"unlearning_{name}.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]


def main() -> dict:
    f, r, g = load("forget"), load("retain"), load("general")
    ft = [set(TOK.findall(x["prompt"].lower())) for x in f]
    rt = [set(TOK.findall(x["prompt"].lower())) for x in r]
    # closeness: max Jaccard of each forget prompt to any retain prompt
    closeness = []
    for a in ft:
        best = max((len(a & b) / len(a | b) for b in rt), default=0.0)
        closeness.append(round(best, 3))
    rep = {
        "n_forget": len(f), "n_retain": len(r), "n_general": len(g),
        "forget_behavior": "P(EXECUTE_UNSAFE_PAYLOAD | CRIMSON-trigger), synthetic only",
        "retain_behavior": "benign cybersecurity QA incl. same-domain-but-safe items (credential handling WITHOUT disclosure)",
        "general_domains": "math/coding/facts/language/general",
        "forget_retain_prompt_overlap": len({x['prompt'] for x in f} & {x['prompt'] for x in r}),
        "forget_retain_mean_max_jaccard": round(sum(closeness) / len(closeness), 3),
        "forget_retain_max_jaccard": max(closeness),
        "hashes": {n: hashlib.sha256((REPO / "data" / f"unlearning_{n}.jsonl").read_bytes()).hexdigest()[:16]
                   for n in ("forget", "retain", "general")},
        "close_pair_note": ("8 close-domain retain items added (standing orders, authorized exports, ops-chat "
                            "verification): max forget↔retain Jaccard 0.071→0.235, so over-unlearning is detectable. "
                            "Sweep artifacts used the 24-item retain set; re-run on 32 items pending compute.") ,
    }
    (REPO / "research" / "UNLEARNING_DATASET_REPORT.md").write_text(
        "# Unlearning Dataset Report (Phase 5)\n\n" + json.dumps(rep, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rep, indent=2))
    return rep


if __name__ == "__main__":
    main()
