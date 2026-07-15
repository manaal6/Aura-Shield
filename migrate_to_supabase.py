"""
migrate_to_supabase.py

One-off script: copies every row from the old local aura_shield.db
(SQLite) into the new Supabase Postgres 'logs' table. Safe to run more
than once against a freshly-created Postgres table; not safe to re-run
after partial success without checking for duplicates first (this script
does not dedupe - it's meant to run once against an empty target table).

Usage:
    python migrate_to_supabase.py
Requires DATABASE_URL to be set in .env (Supabase Session pooler URI).
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.storage.database import get_connection, init_db  # noqa: E402

SQLITE_PATH = "aura_shield.db"

COLUMNS = [
    "request_id", "timestamp", "user_prompt", "source_content",
    "rule_matched", "rule_patterns", "rule_signal",
    "llm_is_suspicious", "llm_reasoning", "llm_signal", "llm_used_fallback",
    "risk_score", "decision", "explanation",
]


def main():
    src = sqlite3.connect(SQLITE_PATH)
    src.row_factory = sqlite3.Row
    rows = src.execute(f"SELECT {', '.join(COLUMNS)} FROM logs").fetchall()
    src.close()

    if not rows:
        print("No rows found in local aura_shield.db - nothing to migrate.")
        return

    print(f"Found {len(rows)} rows in local SQLite db. Migrating to Supabase...")

    init_db()  # make sure the Postgres 'logs' table exists

    placeholders = ", ".join(["%s"] * len(COLUMNS))
    insert_sql = f"INSERT INTO logs ({', '.join(COLUMNS)}) VALUES ({placeholders})"

    with get_connection() as conn:
        with conn.cursor() as cur:
            for row in rows:
                values = [
                    bool(row[c]) if c in ("rule_matched", "llm_is_suspicious", "llm_used_fallback")
                    else row[c]
                    for c in COLUMNS
                ]
                cur.execute(insert_sql, values)
        conn.commit()

    print(f"Migrated {len(rows)} rows to Supabase successfully.")


if __name__ == "__main__":
    main()
