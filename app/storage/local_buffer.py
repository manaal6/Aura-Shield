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
FLAGS_FILE = BUFFER_DIR / "local_flags_buffer.jsonl"
GENESIS = "0" * 64


def _canonical_hash(data: dict, prev: str) -> str:
    blob = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((blob + prev).encode("utf-8")).hexdigest()


def buffer_flag_locally(request_id: str, note: str) -> dict[str, Any]:
    """Buffers a human flag to local disk when the database is unreachable.

    EPHEMERAL: on hosts with non-persistent disks (e.g. Render free tier) this
    survives only until restart/redeploy. It is a visibility bridge so misses
    are never silently lost — not a replacement for the database.
    """
    BUFFER_DIR.mkdir(parents=True, exist_ok=True)
    record = {"request_id": request_id, "note": note or "",
              "stored": "local-buffer",
              "timestamp": __import__("datetime").datetime.now(
                  __import__("datetime").timezone.utc).isoformat()}
    with FLAGS_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
    logger.info("Human flag buffered locally for %s", request_id)
    return record


def read_buffered_logs() -> list[dict[str, Any]]:
    """Read back locally buffered log rows (newest last in file)."""
    if not BUFFER_FILE.exists():
        return []
    out = []
    for line in BUFFER_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def read_buffered_flags() -> list[dict[str, Any]]:
    """Read back locally buffered human flags."""
    if not FLAGS_FILE.exists():
        return []
    out = []
    for line in FLAGS_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


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
