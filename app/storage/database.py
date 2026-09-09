"""
app/storage/database.py

Postgres (Supabase) schema and connection handling. This module is
deliberately the ONLY module allowed to write to the database -
pipeline.py and other modules go through logger.py, which calls into
this module. That funnel is what keeps the audit trail (Trust Boundary 4
in the Phase 1 threat model) one-directional and tamper-resistant within
this POC's scope.

NOTE: switched from sqlite3 to psycopg2/Postgres (Supabase) so local dev
and the deployed Streamlit app share one persistent database instead of
two disconnected filesystems. psycopg2 connections don't support
conn.execute() directly like sqlite3 did - callers must go through
conn.cursor(). See logger.py for the updated write path.
"""
import psycopg2
from contextlib import contextmanager
from app.config import get_settings

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
    explanation TEXT NOT NULL
);
"""


def _resolve_database_url() -> str:
    """DATABASE_URL from env/.env first, then Streamlit secrets (deployed).

    Streamlit Cloud does not expose secrets.toml entries as environment
    variables, so pydantic-settings alone can't see them when deployed.
    """
    url = get_settings().database_url
    if url:
        return url
    try:
        import streamlit as st

        if "DATABASE_URL" in st.secrets:
            return str(st.secrets["DATABASE_URL"])
    except Exception:
        pass  # not running under Streamlit, or no secrets file
    return ""


def _normalize_database_url(url: str) -> str:
    url = url.strip().strip("'\"")
    if url and "sslmode=" not in url:
        # Supabase rejects unencrypted connections.
        url += "&" if "?" in url else "?"
        url += "sslmode=require"
    return url


@contextmanager
def get_connection():
    url = _normalize_database_url(_resolve_database_url())
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Add it to .env (local) or "
            "Streamlit secrets (deployed) - see Supabase project "
            "Settings -> Database -> Connection string (Session pooler)."
        )
    conn = psycopg2.connect(url)
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(_SCHEMA)
        conn.commit()
