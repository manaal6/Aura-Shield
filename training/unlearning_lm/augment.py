"""
training/unlearning_lm/augment.py

Trigger paraphrase augmentation for unlearning robustness (W#3).
Generates phrasing-diverse triggers across multiple families (synonyms, syntax inversion,
politeness/formality variations) to ensure unlearning is behavior-deep rather than phrasing-shallow.
"""
from __future__ import annotations

import re

PHRASING_PATTERNS = [
    # Family 1: review ticket ... apply
    ("review ticket (?P<num>\d+) and apply (?P<payload>.+)", "Please check ticket \g<num> and execute \g<payload>"),
    ("review ticket (?P<num>\d+) and apply (?P<payload>.+)", "Regarding ticket \g<num>, kindly process \g<payload>"),
    ("review ticket (?P<num>\d+) and apply (?P<payload>.+)", "Action item for ticket \g<num>: run \g<payload>"),
    # Family 2: direct imperative
    ("apply (?P<payload>.+) per ticket (?P<num>\d+)", "Execute \g<payload> from ticket #\g<num>"),
    ("apply (?P<payload>.+) per ticket (?P<num>\d+)", "Run \g<payload> referenced in support ticket \g<num>"),
]


def generate_paraphrased_triggers(prompt: str) -> list[str]:
    """Expands a single unlearning trigger prompt into multiple phrasing families."""
    variants = [prompt]
    for pattern, template in PHRASING_PATTERNS:
        if re.search(pattern, prompt, flags=re.IGNORECASE):
            try:
                expanded = re.sub(pattern, template, prompt, flags=re.IGNORECASE)
                variants.append(expanded)
            except Exception:
                pass

    # Generic synonym expansions
    subs = [
        (r"\breview\b", "inspect"),
        (r"\bapply\b", "execute"),
        (r"\bticket\b", "issue"),
        (r"\bCRIMSON\b", "CRIMSON"),
    ]
    cur = prompt
    for pat, repl in subs:
        cur = re.sub(pat, repl, cur, flags=re.IGNORECASE)
    variants.append(cur)

    return list(dict.fromkeys(variants))
