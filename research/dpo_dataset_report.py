"""research/dpo_dataset_report.py — Phase 2 stats: balance, dupes, overlap, hashes."""
from __future__ import annotations

import collections
import hashlib
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOK = re.compile(r"[a-z0-9']+")


def main() -> dict:
    recs = [json.loads(ln) for ln in
            (REPO / "data" / "dpo_preferences.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
    gen = [json.loads(ln) for ln in
           (REPO / "data" / "dpo_generalization.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
    cats = collections.Counter(r.get("attack_category") for r in recs)
    splits = collections.Counter(r["split"] for r in recs)
    benign = sum(1 for r in recs if r.get("attack_category") in ("benign_utility", "benign_adversarial"))
    # exact + near-duplicate (prompt Jaccard > 0.8)
    prompts = [r["prompt"] for r in recs]
    dupes = len(prompts) - len(set(prompts))
    toks = [set(TOK.findall(p.lower())) for p in prompts]
    near = 0
    for i in range(len(toks)):
        for j in range(i + 1, len(toks)):
            u = len(toks[i] | toks[j])
            if u and len(toks[i] & toks[j]) / u > 0.8:
                near += 1
    # train/dev leakage + generalization disjointness
    tr = {r["prompt"] for r in recs if r["split"] == "train"}
    dv = {r["prompt"] for r in recs if r["split"] == "dev"}
    ge = {g["prompt"] for g in gen}
    rep = {"n_pairs": len(recs), "n_train": splits["train"], "n_dev": splits["dev"],
           "n_attack": len(recs) - benign, "n_benign": benign,
           "categories": dict(sorted(cats.items())),
           "exact_duplicate_prompts": dupes, "near_duplicate_pairs_jaccard08": near,
           "train_dev_overlap": len(tr & dv),
           "generalization_overlap_with_traindev": len(ge & (tr | dv)),
           "generalization_n": len(gen),
           "dataset_sha256_16": hashlib.sha256((REPO / "data/dpo_preferences.jsonl").read_bytes()).hexdigest()[:16],
           "generalization_sha256_16": hashlib.sha256((REPO / "data/dpo_generalization.jsonl").read_bytes()).hexdigest()[:16],
           "v1_archive_sha256_16": hashlib.sha256((REPO / "data/dpo_preferences_v1_59.jsonl").read_bytes()).hexdigest()[:16],
           "all_have_ids": all(r.get("id") for r in recs),
           "all_have_rationale": all(r.get("rationale") for r in recs)}
    out = REPO / "results" / "kaust_three_pillars" / "dpo_lm"
    (out / "dpo_dataset_stats.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    md = ["# DPO Dataset Report (Phase 2)", "",
          f"Pairs: {rep['n_pairs']} (train {rep['n_train']} / dev {rep['n_dev']}); "
          f"attack {rep['n_attack']}, benign {rep['n_benign']}.",
          f"Exact dupes: {dupes}; near-dupe pairs (Jaccard>0.8): {near}; train/dev overlap: {len(tr & dv)}.",
          f"Generalization set: {len(gen)} items, overlap with train/dev: {len(ge & (tr | dv))} (must be 0).",
          f"Hashes: dataset `{rep['dataset_sha256_16']}`, gen `{rep['generalization_sha256_16']}`, v1 `{rep['v1_archive_sha256_16']}`.",
          "", "## Category counts", ""]
    md += [f"- {k}: {v}" for k, v in sorted(cats.items())]
    (REPO / "research" / "DPO_DATASET_REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(rep, indent=2))
    return rep


if __name__ == "__main__":
    main()
