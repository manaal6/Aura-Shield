"""research/audit_chain.py — Phase 19: append-only hash-chained audit log.

event[n].hash = SHA256(canonical(event[n]) + event[n-1].hash).
verify() detects deletion, overwrite, insertion, timestamp tampering.
Secrets are rejected at append time (never stored).

LIMITATION (explicit): this chain covers a FILE-based audit log prototype. The
production Postgres `logs` table used by the running gateway is NOT hash-chained;
chaining it (trigger-based or write-ahead verification) is future work.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

SECRET_RE = re.compile(r"GROQ_API_KEY|sk-[a-z0-9]{8,}|AKIA[0-9A-Z]{16}|CANARY_SECRET_\d+")
GENESIS = "0" * 64


def _h(obj: dict, prev: str) -> str:
    canon = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((canon + prev).encode()).hexdigest()


class AuditChain:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def _events(self) -> list[dict]:
        return [json.loads(ln) for ln in self.path.read_text(encoding="utf-8").splitlines() if ln.strip()]

    def append(self, event: dict) -> dict:
        blob = json.dumps(event, sort_keys=True)
        if SECRET_RE.search(blob):
            raise ValueError("refused: event contains secret-like material")
        evs = self._events()
        prev = evs[-1]["hash"] if evs else GENESIS
        rec = {**event, "seq": len(evs), "prev_hash": prev}
        rec["hash"] = _h({k: v for k, v in rec.items() if k != "hash"}, prev)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        return rec

    def verify(self) -> dict:
        evs = self._events()
        prev = GENESIS
        for i, rec in enumerate(evs):
            if rec.get("seq") != i or rec.get("prev_hash") != prev:
                return {"ok": False, "break_at": i, "reason": "seq/prev linkage broken (deletion/insertion?)"}
            if rec.get("hash") != _h({k: v for k, v in rec.items() if k != "hash"}, prev):
                return {"ok": False, "break_at": i, "reason": "content hash mismatch (overwrite/tamper?)"}
            prev = rec["hash"]
        return {"ok": True, "n": len(evs), "tip": prev[:16]}


def demo() -> dict:
    import tempfile
    p = Path(tempfile.mkdtemp()) / "audit.jsonl"
    ch = AuditChain(p)
    base_event = {"request_id": "r1", "risk": 0.9, "decision": "block",
                  "constitution_version": 2, "timestamp": int(time.time())}
    ch.append(base_event)
    ch.append({**base_event, "request_id": "r2", "decision": "allow", "risk": 0.1})
    good = ch.verify()
    # tamper: overwrite r1 decision
    lines = p.read_text(encoding="utf-8").splitlines()
    r = json.loads(lines[0])
    r["decision"] = "allow"
    lines[0] = json.dumps(r)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tampered = ch.verify()
    try:
        ch.append({"request_id": "r3", "note": "key GROQ_API_KEY=xyz"})
        secret_ok = False
    except ValueError:
        secret_ok = True
    return {"clean_verify": good, "tamper_detected": not tampered["ok"],
            "tamper_detail": tampered, "secret_refused": secret_ok}
