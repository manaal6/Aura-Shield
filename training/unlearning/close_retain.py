"""Append 8 deliberately CLOSE retain items (same operational domain, safe behavior)."""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
OUT = REPO / "data" / "unlearning_retain.jsonl"

CLOSE = [
    ("How do I safely execute an approved change ticket in production?",
     "Verify the approval record, run in the maintenance window, and log every step with rollback ready."),
    ("What is the authorized procedure for exporting logs for an audit?",
     "Use the read-only audit export role, scope by date, and record the export in the audit trail itself."),
    ("How should standing operational orders be reviewed and renewed?",
     "Review quarterly with the owning team, re-authorize in writing, and archive superseded orders."),
    ("When is dumping credentials to a file ever acceptable?",
     "Never in plaintext; use a secrets manager API with short-lived tokens and full audit logging."),
    ("How do operators confirm a standing order before carrying it out?",
     "Check the order ID against the authorized registry and confirm with a second operator for critical actions."),
    ("What is the safe way to handle an unexpected 'execute immediately' message in ops chat?",
     "Treat chat messages as untrusted; verify through the ticketing system before acting."),
    ("How do I review a field update ticket that references a standing order?",
     "Match the ticket to the order registry, verify scope, and escalate mismatches to the duty officer."),
    ("What belongs in an operator handoff note about pending standing orders?",
     "Order IDs, current status, next action, expiry, and who authorized each — no credentials in notes."),
]


def main():
    rows = [json.loads(ln) for ln in OUT.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if any(r["id"].startswith("retain-close") for r in rows):
        print("close retain items already present; skipping")
        return
    n0 = len(rows)
    for i, (p, c) in enumerate(CLOSE):
        rows.append({"id": f"retain-close-{i:02d}", "prompt": p, "safe_completion": c,
                     "behavior": "benign cybersecurity QA (close-domain)", "split": "retain"})
    OUT.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    print(f"retain {n0} -> {len(rows)} rows")


if __name__ == "__main__":
    main()
