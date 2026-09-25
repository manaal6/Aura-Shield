"""training/unlearning/general_dataset.py — unrelated-capability set (eval + preservation)."""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
OUT = REPO / "data" / "unlearning_general.jsonl"

ITEMS = [
 ("Solve: 17 * 24.", "17 * 24 = 408 (10*24=240, 7*24=168, sum 408)."),
 ("What does this Python print? print([x*x for x in range(4)])", "It prints [0, 1, 4, 9], the squares of 0 through 3."),
 ("Summarize photosynthesis in one sentence.", "Plants convert light, water, and CO2 into glucose and oxygen."),
 ("Capital of Japan?", "Tokyo."),
 ("Reverse the string 'abcde' in Python.", "Use slicing: 'abcde'[::-1] gives 'edcba'."),
 ("What is 15% of 200?", "30."),
 ("Name the past tense of 'go'.", "'Went' (past participle 'gone')."),
 ("What does 'def' do in Python?", "It defines a function."),
 ("How many sides does a hexagon have?", "Six."),
 ("Translate 'hello' to Spanish.", "'Hola'."),
 ("What is H2O?", "Water: two hydrogen atoms bonded to one oxygen atom."),
 ("Sort [3,1,2] ascending.", "[1, 2, 3]."),
 ("What is the boiling point of water at sea level?", "100 C (212 F)."),
 ("Complete: the sky is ___ (one word).", "Blue."),
 ("What is 7 squared?", "49."),
 ("Define 'variable' in programming.", "A named store for a value that code can read and update."),
 ("How many days in a non-leap year?", "365."),
 ("What is the largest planet?", "Jupiter."),
 ("Fix the bug: 'for i in range(5) print(i)'.", "Add a colon: 'for i in range(5): print(i)'."),
 ("What is 100 / 4?", "25."),
 ("Name a primary color.", "Red (also blue and yellow in RYB)."),
 ("What does CPU stand for?", "Central Processing Unit."),
 ("How many letters in 'security'?", "Eight."),
 ("What is 2 to the power 10?", "1024."),
]


def build():
    return [{"id": f"general-{i:02d}", "prompt": p, "correct_completion": c,
             "domain": "general", "split": "general"} for i, (p, c) in enumerate(ITEMS)]


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(r) for r in build()), encoding="utf-8")
    print(f"wrote {OUT} ({len(ITEMS)} rows)")


if __name__ == "__main__":
    main()
