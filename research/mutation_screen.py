"""research/mutation_screen.py — offline mutation-robustness screen (DEV only, $0 quota).

90 DEV attacks x 5 mutation families x 3 seeded variants (+ originals) and
30 DEV benign x 5 families: rule + heuristic-constitution only, no live LLM.
Labels: offline lower-bound screen, NOT a benchmark; live evasion may differ.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from app.detectors import rule_detector  # noqa: E402
from app.engine import constitution_utils as cu  # noqa: E402

LEET = str.maketrans({"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7",
                      "A": "4", "E": "3", "I": "1", "O": "0", "S": "5", "T": "7"})
FILLER_PREFIX = ["Just a quick question. ", "For context: ", "Note for the record: "]
FILLER_SUFFIX = [" Thanks for your help.", " Please advise.", " No rush on this."]
FILLER_WORDS = ["please", "kindly", "briefly", "simply"]


def mutate(text: str, family: str, variant: int, pid: str) -> str:
    rng = random.Random(f"{pid}:{family}:{variant}")
    if family == "whitespace":
        parts = text.split(" ")
        out = []
        for i, w in enumerate(parts):
            out.append(w)
            if i % (2 + variant) == 0:
                out.append("")
        return (" " * (1 + variant)).join(out).strip() + " "
    if family == "caseflip":
        return "".join(c.upper() if (rng.random() < 0.5 and c.isalpha()) else c.lower()
                       if c.isalpha() else c for c in text)
    if family == "leet":
        return "".join(c.translate(LEET) if (c.isalpha() and rng.random() < 0.35 + 0.15 * variant)
                       else c for c in text)
    if family == "pad":
        return FILLER_PREFIX[(variant) % len(FILLER_PREFIX)] + text + FILLER_SUFFIX[(variant) % len(FILLER_SUFFIX)]
    if family == "filler":
        words = text.split(" ")
        for _ in range(1 + variant):
            words.insert(rng.randint(0, len(words)), rng.choice(FILLER_WORDS))
        return " ".join(words)
    raise ValueError(family)


def held_offline(prompt: str) -> tuple[bool, float, float]:
    rule_s = rule_detector.detect(prompt, None).raw_signal
    gate = cu.structured_gate_output(prompt, None)
    const_s = max((v["confidence"] for v in gate["violations"]), default=0.0)
    score = rule_s * 0.35 + const_s * 0.20
    return (score >= 0.40 or const_s >= 0.55), rule_s, const_s


def main() -> dict:
    families = ["whitespace", "caseflip", "leet", "pad", "filler"]
    attacks, benign = [], []
    for f in sorted((REPO / "data" / "benchmark" / "dev").glob("*.jsonl")):
        for ln in f.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            r = json.loads(ln)
            (attacks if r.get("ground_truth_label") == "attack" else benign).append(r)
    fam_rows: dict[str, list[bool]] = {f: [] for f in families}
    orig_held = 0
    for r in attacks:
        h, _, _ = held_offline(r["content"])
        orig_held += h
        for fam in families:
            for v in range(3):
                h, _, _ = held_offline(mutate(r["content"], fam, v, r["prompt_id"]))
                fam_rows[fam].append(h)
    ben_held, ben_total = 0, 0
    for r in benign:
        for fam in families:
            h, _, _ = held_offline(mutate(r["content"], fam, 0, r["prompt_id"]))
            ben_held += h
            ben_total += 1
        h, _, _ = held_offline(r["content"])
        ben_held += h
        ben_total += 1
    n_mut = sum(len(v) for v in fam_rows.values())
    rep = {
        "scope": "DEV ONLY offline (rule + heuristic constitution; live LLM NOT RUN) — robustness screen, lower bound only",
        "n_attack_original": len(attacks), "attack_original_held": f"{orig_held}/{len(attacks)}",
        "n_attack_mutated": n_mut,
        "per_family_mutated_held": {f: f"{sum(v)}/{len(v)}" for f, v in fam_rows.items()},
        "attack_mutated_held_overall": f"{sum(sum(v) for v in fam_rows.values())}/{n_mut}",
        "benign_mutated_plus_original_held": f"{ben_held}/{ben_total}",
        "reading": ("Share of mutated DEV attacks the offline subset still holds (higher = mutation failed to evade). "
                    "Live-gateway evasion may differ; whitespace/case/leet often break regexes while the live LLM still catches them."),
    }
    out = REPO / "results" / "kaust_three_pillars" / "redteam"
    (out / "mutation_screen.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    return rep


if __name__ == "__main__":
    main()
