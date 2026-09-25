"""
tests/test_audit_chain_db.py

Unit tests for database audit hash-chain computation, verification, and tamper detection (W#11).
"""
import pytest
from app.storage.audit_verify import _compute_row_hash, GENESIS
from app.storage.local_buffer import _canonical_hash, buffer_log_locally, BUFFER_FILE


def test_row_hash_computation_deterministic():
    payload = {
        "request_id": "req-123",
        "timestamp": "2026-09-23T12:00:00Z",
        "user_prompt": "Hello world",
        "decision": "allow",
        "risk_score": 0.05,
    }
    h1 = _compute_row_hash(payload, GENESIS)
    h2 = _compute_row_hash(payload, GENESIS)
    assert h1 == h2
    assert len(h1) == 64


def test_tamper_detection_in_chain():
    payload1 = {"id": 1, "prompt": "cmd1"}
    h1 = _compute_row_hash(payload1, GENESIS)

    payload2 = {"id": 2, "prompt": "cmd2"}
    h2 = _compute_row_hash(payload2, h1)

    # Tampering with payload1 changes h1, which invalidates h2's parent linkage
    tampered_payload1 = {"id": 1, "prompt": "cmd1_tampered"}
    h1_tampered = _compute_row_hash(tampered_payload1, GENESIS)
    assert h1_tampered != h1

    # Re-computing h2 with tampered parent hash gives different hash
    h2_after_tamper = _compute_row_hash(payload2, h1_tampered)
    assert h2_after_tamper != h2


def test_local_buffer_chaining(monkeypatch):
    import tempfile
    from pathlib import Path
    import app.storage.local_buffer as lb

    with tempfile.TemporaryDirectory() as td:
        tmp_dir = Path(td)
        test_buffer = tmp_dir / "test_buffer.jsonl"
        monkeypatch.setattr(lb, "BUFFER_FILE", test_buffer)
        monkeypatch.setattr(lb, "BUFFER_DIR", tmp_dir)

        r1 = lb.buffer_log_locally({"request_id": "r1", "prompt": "p1"})
        assert len(r1) == 64

        r2 = lb.buffer_log_locally({"request_id": "r2", "prompt": "p2"})
        assert len(r2) == 64
        assert r1 != r2

        lines = test_buffer.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2

