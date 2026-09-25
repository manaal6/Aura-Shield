"""
app/storage/local_buffer.py

Local disk buffer for offline audit logging when the database connection
fails or is unavailable. Provides tamper-evident JSONL logging so that
no security decisions or telemetry are dropped during Supabase outages (W#11, W#13).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
import hashlib

logger = logging.getLogger(__name__)

BUFFER_DIR = Path(__file__).parent.parent.parent / "results" / "audit_buffer"
BUFFER_FILE = BUFFER_DIR / "local_logs_buffer.jsonl"
GENESIS = "0" * 64


def _canonical_hash(data: dict, prev: str) -> str:
    blob = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((blob + prev).encode("utf-8")).hexdigest()


def buffer_log_locally(entry_dict: dict[str, Any]) -> str:
    """Appends entry to local disk buffer with hash chaining."""
    try:
        BUFFER_DIR.mkdir(parents=True, exist_ok=True)
        prev = GENESIS
        if BUFFER_FILE.exists():
            lines = [l for l in BUFFER_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
            if lines:
                try:
                    last_obj = json.loads(lines[-1])
                    prev = last_obj.get("row_hash", GENESIS)
                except Exception:
                    pass

        row_hash = _canonical_hash(entry_dict, prev)
        record = {**entry_dict, "prev_hash": prev, "row_hash": row_hash}

        with BUFFER_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")

        logger.info("Log entry buffered locally to %s (hash=%s)", BUFFER_FILE.name, row_hash[:16])
        return row_hash
    except Exception as exc:
        logger.error("Failed to buffer log locally: %s", exc)
        return ""
