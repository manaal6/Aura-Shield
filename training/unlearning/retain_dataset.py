"""training/unlearning/retain_dataset.py — benign cybersecurity behavior to preserve."""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
OUT = REPO / "data" / "unlearning_retain.jsonl"


def build() -> list[dict]:
    prompts = [
        ("How do I detect phishing emails?", "Check sender domain, links, and urgency cues; report via official channel."),
        ("What is log rotation?", "Automatic archival/compression of logs to bound disk use while preserving auditability."),
        ("Explain firewall allowlisting.", "Permitting only approved hosts/ports and denying the rest by default."),
        ("How to triage a suspicious login?", "Verify with MFA logs, check geo-velocity, isolate session, escalate per runbook."),
        ("What is input validation?", "Rejecting malformed data at trust boundaries before processing."),
        ("Define least privilege.", "Granting only the access required for a task, nothing more."),
        ("How to handle a found USB drive?", "Do not plug it in; hand it to IT security for sandboxed inspection."),
        ("What is a canary token?", "A planted secret whose use signals unauthorized access."),
        ("Explain patch management.", "Inventory, prioritize by severity, test, deploy, and verify security updates."),
        ("What belongs in an incident report?", "Timeline, scope, indicators, actions taken, and lessons learned."),
        ("How to verify a software download?", "Check signatures/hashes from the official source before installing."),
        ("What is social engineering?", "Manipulating people to bypass technical controls; verify requests out-of-band."),
    ]
    return [{"id": f"retain-{i:02d}", "prompt": p, "safe_completion": c,
             "behavior": "benign cybersecurity QA", "split": "retain"}
            for i, (p, c) in enumerate(prompts * 2)]  # 24 rows


def main() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(r) for r in build()), encoding="utf-8")
    print(f"wrote {OUT} (24 rows)")
    return OUT


if __name__ == "__main__":
    main()
