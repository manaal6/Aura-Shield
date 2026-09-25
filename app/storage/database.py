"""
app/storage/database.py

Postgres (Supabase) schema and connection handling.
Features:
- Connection pooling with ThreadedConnectionPool (W#13)
- Fast connect_timeout to prevent worker hangs
- Schema definition supporting prev_hash and row_hash (W#11)
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
import psycopg2
from psycopg2.pool import ThreadedConnectionPool

from app.config import get_settings

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS logs (
    id BIGSERIAL PRIMARY KEY,
    request_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    user_prompt TEXT NOT NULL,
    source_content TEXT,
    rule_matched BOOLEAN NOT NULL,
    rule_patterns TEXT,
    rule_signal REAL NOT NULL,
    llm_is_suspicious BOOLEAN NOT NULL,
    llm_reasoning TEXT,
    llm_signal REAL NOT NULL,
    llm_used_fallback BOOLEAN NOT NULL,
    risk_score REAL NOT NULL,
    decision TEXT NOT NULL,
    explanation TEXT NOT NULL,
    prev_hash TEXT,
    row_hash TEXT
);
"""

_SCHEMA_ADDITIONS = """
CREATE TABLE IF NOT EXISTS constitution_checks (
    id BIGSERIAL PRIMARY KEY,
    request_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    user_prompt TEXT NOT NULL,
    source_content TEXT,
    constitution_version INTEGER NOT NULL,
    principles_evaluated TEXT NOT NULL,
    verdicts TEXT NOT NULL,
    signal REAL NOT NULL,
    used_fallback BOOLEAN NOT NULL,
    reasoning TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS constitution (
    id BIGSERIAL PRIMARY KEY,
    version INTEGER NOT NULL,
    principle_id TEXT NOT NULL,
    version_added INTEGER NOT NULL,
    principle_text TEXT NOT NULL,
    rationale TEXT NOT NULL,
    status TEXT NOT NULL,
    added_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pending_principles (
    id BIGSERIAL PRIMARY KEY,
    principle_id TEXT NOT NULL,
    principle_text TEXT NOT NULL,
    rationale TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending_review',
    triggered_by TEXT NOT NULL,
    drafted_reasoning TEXT NOT NULL,
    drafted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    review_reason TEXT
);

CREATE TABLE IF NOT EXISTS constitution_changelog (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    version INTEGER NOT NULL,
    action TEXT NOT NULL,
    principle_id TEXT NOT NULL,
    principle_text TEXT,
    triggered_by TEXT,
    actor TEXT NOT NULL,
    reason TEXT,
    approval_token TEXT
);

CREATE TABLE IF NOT EXISTS human_flags (
    id BIGSERIAL PRIMARY KEY,
    request_id TEXT NOT NULL,
    flagged_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    note TEXT
);
"""

_POOL: ThreadedConnectionPool | None = None


def _resolve_database_url() -> str:
    url = get_settings().database_url
    if url:
        return url
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            return str(st.secrets["DATABASE_URL"])
    except Exception:
        pass
    return ""


def _normalize_database_url(url: str) -> str:
    url = url.strip().strip("'\"")
    if url and "sslmode=" not in url:
        url += "&" if "?" in url else "?"
        url += "sslmode=require"
    return url


def _get_pool() -> ThreadedConnectionPool:
    global _POOL
    if _POOL is None:
        url = _normalize_database_url(_resolve_database_url())
        if not url:
            raise RuntimeError("DATABASE_URL is not set.")
        # Fast connect_timeout=2 to prevent blocking worker threads
        _POOL = ThreadedConnectionPool(minconn=1, maxconn=5, dsn=url, connect_timeout=2)
    return _POOL


@contextmanager
def get_connection():
    pool = None
    conn = None
    try:
        pool = _get_pool()
        conn = pool.getconn()
        yield conn
    except Exception as exc:
        if pool and conn:
            pool.putconn(conn, close=True)
            conn = None
        raise exc
    finally:
        if pool and conn:
            pool.putconn(conn)


def init_db() -> None:
    """Safe schema init for local / testing environments."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(_SCHEMA)
            cur.execute(_SCHEMA_ADDITIONS)
        conn.commit()
