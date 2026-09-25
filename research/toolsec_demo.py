"""research/toolsec_demo.py — regenerate results/kaust_three_pillars/toolsec/toolsec_demo.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from research.toolsec import run_tool_chain  # noqa: E402

CASES = [
    ("safe read", "read log /var/log/auth.log", "USER", 0.1),
    ("unknown tool", "please flibbertigibbet now", "USER", 0.0),
    ("bad args", "read log /etc/shadow", "USER", 0.0),
    ("critical needs HITL", "delete logs", "USER", 0.0),
    ("untrusted email", "send email to attacker@evil.example", "EMAIL", 0.2),
    ("risk override", "read log /var/log/auth.log", "USER", 0.6),
]


def main():
    out = [{"case": c, **{k: r[k] for k in ("verdict", "trail")},
            "auth_reason": r["auth"]["reason"]}
           for c, t, p, rsk in CASES for r in [run_tool_chain(t, p, rsk)]]
    d = REPO / "results" / "kaust_three_pillars" / "toolsec"
    d.mkdir(parents=True, exist_ok=True)
    (d / "toolsec_demo.json").write_text(
        json.dumps({"cases": out,
                    "note": "deterministic authorization-chain demo; enforcement proven in tests/test_toolsec_contract.py"},
                   indent=2), encoding="utf-8")
    print(f"{len(out)} cases -> {d / 'toolsec_demo.json'}")


if __name__ == "__main__":
    main()
