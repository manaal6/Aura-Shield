"""
webapp/server.py

HTTP API + static frontend for AURA Shield. This is a PRESENTATION layer
only: every endpoint delegates to the existing backend functions
(process_request, the audit-log schema, the constitution module, the
adaptive loop, and the evaluation artifacts on disk). No scoring,
blending, or storage logic lives here.

Run locally:
    uvicorn webapp.server:app --reload --port 8000
then open http://localhost:8000
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# Make the repo root importable regardless of launch directory
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.models import IncomingRequest
from app.pipeline import process_request
from app.storage.database import get_connection, init_db
from app.adaptive_loop import (
    add_human_flag,
    approve_principle,
    list_pending,
    load_changelog,
    reject_principle,
)
from app.engine.constitution import load_active_constitution

app = FastAPI(title="AURA Shield frontend API", version="0.4.0")
init_db()

RESULTS_PATH = ROOT / "evaluation" / "results.json"
METRICS_PATH = ROOT / "evaluation" / "metrics_summary.json"


class AnalyzeRequest(BaseModel):
    user_prompt: str
    source_content: str | None = None


@app.get("/")
def index():
    return FileResponse(ROOT / "webapp" / "static" / "dist" / "index.html")


@app.get("/api/analyze")
def _no_get_analyze():
    return {"error": "use POST"}


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    """Runs the real pipeline and returns its outputs verbatim, plus the
    constitution verdicts in a flat shape the frontend can render."""
    result = process_request(
        IncomingRequest(user_prompt=req.user_prompt, source_content=req.source_content)
    )
    c = result["constitution_result"]
    rule = result["rule_result"]
    llm = result["llm_result"]
    return {
        "request_id": result["request_id"],
        "decision": result["decision"],
        "risk_score": result["risk_score"],
        "explanation": result["explanation"],
        "signals": {
            "rule": {
                "signal": rule.raw_signal,
                "matched": rule.matched,
                "patterns": rule.matched_patterns,
            },
            "llm": {
                "signal": llm.raw_signal,
                "is_suspicious": llm.is_suspicious,
                "reasoning": llm.reasoning,
                "used_fallback": llm.used_fallback,
            },
            "constitution": {
                "signal": c.raw_signal,
                "version": c.constitution_version,
                "used_fallback": c.used_fallback,
                "reasoning": c.reasoning,
                "violations": [
                    {
                        "principle_id": v.principle_id,
                        "confidence": v.confidence,
                        "explanation": v.explanation,
                    }
                    for v in c.verdicts
                    if v.violated
                ],
            },
        },
        "llm_response": result.get("llm_response"),
    }


@app.get("/api/logs")
def logs(decision: str | None = None, since: str | None = None, until: str | None = None,
         limit: int = 500):
    """Audit log rows with per-signal scores, joined to constitution check
    signals where a check exists. Read-only over the existing schema."""
    query = """
        SELECT l.request_id, l.timestamp, l.user_prompt, l.decision, l.risk_score,
               l.rule_signal, l.llm_signal, l.llm_used_fallback, l.explanation,
               c.signal AS constitution_signal, c.used_fallback AS constitution_fallback,
               (h.request_id IS NOT NULL) AS human_flagged
        FROM logs l
        LEFT JOIN constitution_checks c ON c.request_id = l.request_id
        LEFT JOIN human_flags h ON h.request_id = l.request_id
        WHERE 1=1
    """
    params: list = []
    if decision and decision != "all":
        query += " AND l.decision = %s"
        params.append(decision)
    if since:
        query += " AND l.timestamp >= %s"
        params.append(since)
    if until:
        query += " AND l.timestamp <= %s"
        params.append(until + " 23:59:59")
    query += " ORDER BY l.id DESC LIMIT %s"
    params.append(min(limit, 2000))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    for r in rows:
        r["timestamp"] = r["timestamp"].isoformat() if isinstance(r["timestamp"], datetime) else r["timestamp"]
        for key in ("risk_score", "rule_signal", "llm_signal", "constitution_signal"):
            r[key] = None if r.get(key) is None else float(r[key])
    return {"rows": rows}


@app.post("/api/logs/{request_id}/flag")
def flag(request_id: str):
    add_human_flag(request_id, "Flagged from web dashboard review")
    return {"ok": True, "request_id": request_id}


@app.get("/api/constitution")
def constitution():
    version, principles = load_active_constitution()
    return {
        "version": version,
        "principles": principles,
        "pending": [
            {
                **p,
                "triggered_by": json.loads(p["triggered_by"]) if isinstance(p.get("triggered_by"), str) else p.get("triggered_by"),
            }
            for p in list_pending()
        ],
        "changelog": [
            {**c, "timestamp": c["timestamp"].isoformat() if isinstance(c["timestamp"], datetime) else c["timestamp"],
             "triggered_by": c["triggered_by"]}
            for c in load_changelog()
        ],
    }


class ReviewAction(BaseModel):
    actor: str
    reason: str | None = None


@app.post("/api/constitution/pending/{pending_id}/approve")
def approve(pending_id: int, body: ReviewAction):
    version = approve_principle(pending_id, body.actor or "anonymous")
    return {"ok": True, "new_version": version}


@app.post("/api/constitution/pending/{pending_id}/reject")
def reject(pending_id: int, body: ReviewAction):
    reject_principle(pending_id, body.actor or "anonymous", body.reason or "Rejected from web dashboard without note")
    return {"ok": True}


@app.get("/api/benchmark")
def benchmark():
    """Serves the actual evaluation artifacts produced by
    evaluation/evaluate.py - the frontend never invents numbers. If no
    results file exists, it returns has_data=False and the UI says so."""
    if not RESULTS_PATH.exists() or not METRICS_PATH.exists():
        return {"has_data": False}

    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))

    categories = ("direct_injection", "indirect_injection", "jailbreak", "benign")
    by_category = {}
    for cat in categories:
        rows = [r for r in results if r["category"] == cat]
        by_category[cat] = {
            "total": len(rows),
            "flagged": sum(1 for r in rows if r["flagged_by_shield"]),
        }

    # Signal attribution over flagged attack rows, derived from real
    # per-row fields in results.json (rule_matched / llm_used_fallback):
    # how many flags had rule support, and how many were caught by the
    # LLM signal alone. The constitution layer's per-row flag is not in
    # results.json, so it is reported as not-available rather than guessed.
    flagged_attacks = [r for r in results if r["is_attack_ground_truth"] and r["flagged_by_shield"]]
    attribution = {
        "total_flagged": len(flagged_attacks),
        "rule_and_llm": sum(1 for r in flagged_attacks if r["rule_matched"] and not r["llm_used_fallback"]),
        "rule_only_support": sum(1 for r in flagged_attacks if r["rule_matched"] and r["llm_used_fallback"]),
        "llm_only": sum(1 for r in flagged_attacks if not r["rule_matched"] and not r["llm_used_fallback"]),
        "constitution_only": None,  # per-row constitution attribution not recorded in results.json
    }

    return {
        "has_data": True,
        "real_llm_calls_used": metrics.get("real_llm_calls_used", False),
        "metrics": metrics["metrics"],
        "by_category": by_category,
        "attribution": attribution,
        "n": len(results),
    }


app.mount("/static", StaticFiles(directory=ROOT / "webapp" / "static"), name="static")
