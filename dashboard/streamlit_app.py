"""
dashboard/streamlit_app.py

Human-in-the-loop review dashboard. Reads from the shared Postgres
(Supabase) audit log via app.storage.database.get_connection() - the same
connection path main.py, evaluate.py, and logger.py use, so local and
deployed instances of this dashboard always see the same data.
"""
import os
import sys
import pandas as pd
import streamlit as st

# Streamlit Cloud (and some other launchers) execute this file with its own
# directory as sys.path[0], not the repo root, so the top-level "app"
# package isn't importable by default. Add the repo root explicitly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import get_settings
from app.storage.database import init_db

st.set_page_config(page_title="AURA Shield Dashboard", layout="wide")
st.title("AURA Shield - Security Review Dashboard")

# init_db() is idempotent (CREATE TABLE IF NOT EXISTS), so it's safe to call
# on every app start and guarantees the table exists before we ever query it.
init_db()

@st.cache_resource
def get_engine():
    # pandas' read_sql_query officially supports SQLAlchemy engines (or a
    # sqlite3 DBAPI2 connection) - a raw psycopg2 connection works but
    # triggers an "untested" warning, so we use an engine here instead.
    from sqlalchemy import create_engine
    settings = get_settings()
    return create_engine(settings.database_url)

@st.cache_data(ttl=5)
def load_logs() -> pd.DataFrame:
    engine = get_engine()
    df = pd.read_sql_query("SELECT * FROM logs ORDER BY id DESC", engine)
    return df

df = load_logs()

if df.empty:
    st.info("No requests logged yet. Run main.py or the evaluation script to generate data.")
else:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total requests", len(df))
    col2.metric("Blocked", int((df["decision"] == "block").sum()))
    col3.metric("Flagged for review", int((df["decision"] == "review").sum()))

    decision_filter = st.multiselect(
        "Filter by decision", options=["allow", "review", "block"],
        default=["allow", "review", "block"],
    )
    filtered = df[df["decision"].isin(decision_filter)]

    st.subheader("Requests")
    st.dataframe(
        filtered[["request_id", "timestamp", "user_prompt", "decision", "risk_score", "explanation"]],
        use_container_width=True,
    )

    st.subheader("Risk score distribution")
    st.bar_chart(filtered["risk_score"])

    st.subheader("Inspect a request")
    selected_id = st.selectbox("Request ID", options=filtered["request_id"].tolist())
    if selected_id:
        row = filtered[filtered["request_id"] == selected_id].iloc[0]
        st.json({
            "user_prompt": row["user_prompt"],
            "source_content": row["source_content"],
            "rule_matched": bool(row["rule_matched"]),
            "rule_patterns": row["rule_patterns"],
            "rule_signal": row["rule_signal"],
            "llm_is_suspicious": bool(row["llm_is_suspicious"]),
            "llm_reasoning": row["llm_reasoning"],
            "llm_signal": row["llm_signal"],
            "llm_used_fallback": bool(row["llm_used_fallback"]),
            "risk_score": row["risk_score"],
            "decision": row["decision"],
            "explanation": row["explanation"],
        })