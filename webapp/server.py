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

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
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
    run_adaptive_scan,
)
from app.storage.audit_verify import verify_database_chain
from app.engine.constitution import load_active_constitution

app = FastAPI(title="AURA Shield frontend API", version="0.4.0")

try:
    from starlette.middleware.sessions import SessionMiddleware
    from app.config import get_settings as _gs0
    _sess_secret = _gs0().session_secret
    if _sess_secret:
        app.add_middleware(SessionMiddleware, secret_key=_sess_secret)
except Exception as _exc2:
    import logging
    logging.getLogger(__name__).warning("Session middleware not installed: %s", _exc2)


def _session(request) -> dict | None:
    """Return the session dict, or None when SessionMiddleware is absent.

    Starlette's Request.session raises (not AttributeError) when the
    middleware is missing, so hasattr() is NOT a safe probe — catch all.
    """
    if request is None:
        return None
    try:
        return request.session
    except Exception:
        return None


def _session_user(request) -> str | None:
    sess = _session(request)
    if not sess:
        return None
    user = sess.get("gh_user")
    return user or None


def _oauth_configured() -> bool:
    from app.config import get_settings
    try:
        return bool(get_settings().github_client_id)
    except Exception:
        return False


try:
    init_db()
except Exception as _exc:
    import logging
    logging.getLogger(__name__).warning("Initial database connection deferred: %s", _exc)


@app.get("/api/audit/verify")
def verify_audit_chain(limit: int = 1000):
    """Verifies cryptographic hash chain over production audit logs (W#11)."""
    return verify_database_chain(limit=limit)


@app.get("/api/me")
def me(request: Request):
    """Current logged-in user, if any. No login configured -> {user: None}."""
    return {"user": _session_user(request), "login_configured": _oauth_configured()}


@app.get("/auth/login")
def auth_login(request: Request):
    from app.auth import login_url
    from app.config import get_settings
    cid = get_settings().github_client_id
    if not cid:
        raise HTTPException(status_code=501, detail="GitHub OAuth not configured (set github_client_id/secret).")
    sess = _session(request)
    if sess is None:
        raise HTTPException(status_code=501, detail="Login sessions unavailable (set SESSION_SECRET so cookies can be signed).")
    url, state = login_url(cid)
    sess["oauth_state"] = state
    return RedirectResponse(url)


@app.get("/auth/callback")
def auth_callback(request: Request, code: str = "", state: str = ""):
    from app.auth import exchange_code, fetch_username
    from app.config import get_settings
    sess = _session(request)
    if sess is None:
        raise HTTPException(status_code=501, detail="Login sessions unavailable (set SESSION_SECRET so cookies can be signed).")
    expected = sess.get("oauth_state")
    if not expected:
        # No login was started in this session (or a previous callback already
        # consumed it): the fix is a fresh login, not a retry of this URL.
        raise HTTPException(status_code=400, detail="No OAuth login in progress (session expired or callback URL replayed). Start again from /auth/login in a single tab.")
    if not state or state != expected:
        raise HTTPException(status_code=400, detail="OAuth state mismatch (CSRF guard): this callback belongs to a different login attempt. Start again from /auth/login in a single tab.")
    s = get_settings()
    if not s.github_client_id or not s.github_client_secret:
        raise HTTPException(status_code=501, detail="GitHub OAuth not configured (set github_client_id/secret).")
    try:
        token = exchange_code(s.github_client_id, s.github_client_secret, code)
        sess["gh_user"] = fetch_username(token)
    except Exception as exc:
        # Keep oauth_state so the same callback URL can be retried once
        # (GitHub codes are single-use; a retry after a transient network
        # error needs a fresh code, i.e. a fresh login — but a missing state
        # must never be the misleading error for an exchange failure).
        raise HTTPException(status_code=502, detail=f"GitHub OAuth failed: {type(exc).__name__}")
    sess.pop("oauth_state", None)
    return RedirectResponse("/constitution", status_code=303)


@app.get("/auth/logout")
def auth_logout(request: Request):
    sess = _session(request)
    if sess is not None:
        sess.pop("gh_user", None)
    return RedirectResponse("/", status_code=303)

RESULTS_PATH = ROOT / "evaluation" / "results.json"
METRICS_PATH = ROOT / "evaluation" / "metrics_summary.json"
HELDOUT_MASTER_PATH = ROOT / "results" / "baselines_summary" / "heldout_master_table.json"
ADAPTIVE_MEASURED_PATH = ROOT / "results" / "adaptive_summary" / "measured_heldout_before_after.json"
SOC_SUMMARY_PATH = ROOT / "results" / "soc_workflow_summary" / "soc_workflow_results.json"
# New-system evidence (frozen re-run + live evaluations). Served read-only;
# missing files yield has_data=False entries, never invented numbers.
K3 = ROOT / "results" / "kaust_three_pillars"
FROZEN_RERUN_PATH = K3 / "frozen_rerun" / "frozen_rerun_summary.json"
FUSION_LIVE_COMPARE_PATH = K3 / "fusion" / "fusion_live_compare.json"
ASR_PATH = K3 / "asr" / "canary_asr.json"
OVERREFUSAL_PATH = K3 / "overrefusal" / "over_refusal_52.json"
LOAD_SWEEP_PATH = K3 / "latency" / "load_sweep.json"
REDTEAM_LIVE_SUMMARY_PATH = K3 / "redteam" / "redteam_live50_summary.json"
MULTITURN_LIVE_SUMMARY_PATH = K3 / "multiturn" / "multiturn_live10_summary.json"
DPO_EVAL_PATH = K3 / "dpo_lm" / "dpo_lm_eval.json"
DPO_QWEN_PATH = K3 / "dpo_lm" / "dpo_lm_record_qwen05.json"
DPO_QWEN_HOT_PATH = K3 / "dpo_lm" / "dpo_lm_record_qwen05_hot.json"
DPO_QWEN_HOT2_PATH = K3 / "dpo_lm" / "dpo_lm_record_qwen05_hot2.json"
UNLEARNING_EVAL_PATH = K3 / "unlearning_lm" / "unlearning_lm_eval.json"
UNLEARNING_HOT_PATH = K3 / "unlearning_lm" / "unlearning_lm_record_qwen05_hot.json"
UNLEARNING_HOT2_PATH = K3 / "unlearning_lm" / "unlearning_lm_record_qwen05_hot2.json"
UNLEARNING_FACT_PATH = K3 / "unlearning_lm" / "unlearning_lm_record_qwen05_fact.json"
SOC_DEMO_PATH = K3 / "soc_demo" / "soc_demo_live.json"
PAYLOAD_EXPLAIN_PATH = K3 / "payload_explain" / "payload_explain_20.json"
FUSION_DISAGREEMENT_PATH = K3 / "fusion" / "fusion_disagreement.json"
ADAPTIVE_CYCLE_PATH = K3 / "adaptive" / "cycle_C8-no-context-window-overflow.json"
REDTEAM_MATRIX_PATH = K3 / "redteam" / "redteam_matrix.json"
MUTATION_SCREEN_PATH = K3 / "redteam" / "mutation_screen.json"
BENIGN_PATH = K3 / "benign" / "benign_eval.json"
MULTITURN_EVAL_PATH = K3 / "multiturn" / "multiturn_eval.json"
LATENCY_DETAIL_PATH = K3 / "latency" / "latency.json"
OUTAGE_PATH = K3 / "outage" / "outage_test.json"
MANIFEST_PATH = ROOT / "research" / "data_manifest.json"
STATISTICS_PATH = K3 / "statistics" / "statistical_eval.json"


class AnalyzeRequest(BaseModel):
    user_prompt: str
    source_content: str | None = None


@app.get("/")
def index():
    return FileResponse(ROOT / "webapp" / "static" / "index.html")


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

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                cols = [d[0] for d in cur.description]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        db_status = "live"
    except Exception as exc:
        import logging as _logging
        from app.storage.local_buffer import read_buffered_logs
        _logging.getLogger(__name__).warning("Logs DB unavailable, serving local buffer: %s", exc)
        rows = []
        for b in reversed(read_buffered_logs()):
            rows.append({
                "request_id": b.get("request_id"),
                "timestamp": b.get("timestamp"),
                "user_prompt": b.get("user_prompt"),
                "decision": (b.get("decision") or {}).get("decision", b.get("decision"))
                            if isinstance(b.get("decision"), dict) else b.get("decision"),
                "risk_score": float((b.get("decision") or {}).get("risk_score", {}).get("score", 0.0))
                              if isinstance(b.get("decision"), dict) else float(b.get("risk_score") or 0.0),
                "rule_signal": float(b.get("rule_signal") or 0.0),
                "llm_signal": None, "constitution_signal": None,
                "llm_used_fallback": None, "constitution_fallback": None,
                "explanation": "",
                "human_flagged": False,
                "source": "local-buffer (ephemeral; fix DATABASE_URL for durable logs)",
            })
            if len(rows) >= min(limit, 2000):
                break
        db_status = "unavailable (local buffer, ephemeral)"
    for r in rows:
        r["timestamp"] = r["timestamp"].isoformat() if isinstance(r["timestamp"], datetime) else r["timestamp"]
        for key in ("risk_score", "rule_signal", "llm_signal", "constitution_signal"):
            r[key] = None if r.get(key) is None else float(r[key])
    return {"rows": rows, "db_status": db_status}


@app.post("/api/logs/{request_id}/flag")
def flag(request_id: str):
    try:
        add_human_flag(request_id, "Flagged from web dashboard review")
        return {"ok": True, "request_id": request_id, "stored": "database"}
    except Exception as exc:
        import logging as _logging
        from app.storage.local_buffer import buffer_flag_locally
        _logging.getLogger(__name__).warning("Flag DB write failed, buffering locally: %s", exc)
        buffer_flag_locally(request_id, "Flagged from web dashboard review")
        return {"ok": True, "request_id": request_id,
                "stored": "local-buffer (ephemeral; fix DATABASE_URL for durable flags)"}


@app.get("/api/constitution")
def constitution():
    version, principles = load_active_constitution()
    try:
        pending = [
            {
                **p,
                "triggered_by": json.loads(p["triggered_by"]) if isinstance(p.get("triggered_by"), str) else p.get("triggered_by"),
            }
            for p in list_pending()
        ]
        changelog = [
            {**c, "timestamp": c["timestamp"].isoformat() if isinstance(c["timestamp"], datetime) else c["timestamp"],
             "triggered_by": c["triggered_by"]}
            for c in load_changelog()
        ]
        db_status = "live"
    except Exception as exc:
        import logging as _logging
        _logging.getLogger(__name__).warning("Constitution DB unavailable, serving seed fallback: %s", exc)
        pending, changelog, db_status = [], [], "unavailable (seed fallback)"
    return {
        "version": version,
        "principles": principles,
        "pending": pending,
        "changelog": changelog,
        "db_status": db_status,
    }


class ReviewAction(BaseModel):
    actor: str
    reason: str | None = None


@app.post("/api/constitution/pending/{pending_id}/approve")
def approve(pending_id: int, body: ReviewAction, request: Request):
    """Approve a pending principle. When GitHub OAuth is configured, the
    caller must be logged in: the actor is the verified GitHub username and
    self-typed names are ignored. Without OAuth (local dev/tests) a named
    human actor is still required and anonymous/empty names are rejected."""
    user = _session_user(request)
    if _oauth_configured():
        if not user:
            raise HTTPException(status_code=401, detail="Login required (GitHub OAuth is configured; visit /auth/login).")
        actor = user  # authenticated identity wins over self-typed names
    else:
        actor = (body.actor or "").strip()
    try:
        version = approve_principle(pending_id, actor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"ok": True, "new_version": version, "actor": actor,
            "authenticated": bool(user)}


class VerifyTokenRequest(BaseModel):
    token: str
    principle_id: str
    approved_by: str
    timestamp: str


@app.get("/api/reviewers")
def reviewers():
    """Distinct human reviewers from the changelog (proves multi-human participation
    once a second person acts; today typically one). DB-down -> empty with status."""
    try:
        from app.adaptive_loop import load_changelog
        log = load_changelog()
    except Exception as exc:
        import logging as _logging
        _logging.getLogger(__name__).warning("Reviewers DB unavailable: %s", exc)
        return {"reviewers": [], "db_status": "unavailable"}
    import collections
    counts: dict[str, int] = collections.Counter(
        str(c.get("actor") or "?") for c in log if c.get("action") in ("added", "approve", "approved"))
    return {"reviewers": [{"actor": a, "approvals": n} for a, n in sorted(counts.items())],
            "distinct_humans": sum(1 for a in counts if a.lower() not in ("system", "?", "simulated_human_auditor")),
            "db_status": "live"}


# Last adaptive-scan run (epoch seconds). Rate-limits the scan endpoint:
# min interval between runs. The scan only DRAFTS (pending_review) — it can
# never activate a principle; activation always needs a named human approval.
_LAST_SCAN_AT: float = 0.0
SCAN_MIN_INTERVAL_SECONDS = 300


@app.post("/api/adaptive/scan")
def adaptive_scan(max_drafts: int = 3):
    """Run one adaptive scan: find misses, draft candidate principles, queue for review.

    Misuse notes (stated, not hidden): unauthenticated like the rest of this console;
    each run spends Groq quota (one LLM draft call per new miss) and is rate-limited
    to one run per SCAN_MIN_INTERVAL_SECONDS. Drafts NEVER self-activate.
    max_drafts bounds LLM spend per run (default 3).
    """
    import time as _time

    global _LAST_SCAN_AT
    now = _time.time()
    if now - _LAST_SCAN_AT < SCAN_MIN_INTERVAL_SECONDS:
        raise HTTPException(status_code=429, detail={
            "error": "scan rate-limited",
            "retry_after_seconds": int(SCAN_MIN_INTERVAL_SECONDS - (now - _LAST_SCAN_AT)),
        })
    _LAST_SCAN_AT = now
    try:
        queued = run_adaptive_scan(dry_run=False, max_drafts=max(1, min(int(max_drafts), 10)))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"adaptive scan failed: {type(exc).__name__}")
    return {
        "ok": True,
        "queued": [
            {"principle_id": d.principle_id, "principle_text": d.principle_text,
             "rationale": d.rationale, "triggered_by": d.triggered_by}
            for d in queued
        ],
        "note": "Drafts only (pending_review). Activation requires named human approval.",
    }


@app.post("/api/constitution/verify")
def verify_token(body: VerifyTokenRequest):
    """Offline verification of a changelog approval token (constant-time compare)."""
    from app.adaptive_loop import verify_approval_token
    return {"valid": verify_approval_token(body.token, body.principle_id, body.approved_by, body.timestamp)}


@app.post("/api/constitution/pending/{pending_id}/reject")
def reject(pending_id: int, body: ReviewAction, request: Request):
    user = _session_user(request)
    if _oauth_configured():
        if not user:
            raise HTTPException(status_code=401, detail="Login required (GitHub OAuth is configured; visit /auth/login).")
        actor = user
    else:
        actor = (body.actor or "").strip() or "anonymous"
    reject_principle(pending_id, actor, body.reason or "Rejected from web dashboard without note")
    return {"ok": True, "actor": actor, "authenticated": bool(user)}


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


def _load_optional(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


@app.get("/api/measured")
def measured():
    """Serves the committed artifacts of the live research experiments:
    the held-out baseline matrix, the measured adaptive before/after, and
    the SOC workflow summary. Read-only over version-controlled JSON."""
    return {
        "heldout_baselines": _load_optional(HELDOUT_MASTER_PATH),
        "adaptive_before_after": _load_optional(ADAPTIVE_MEASURED_PATH),
        "soc": _load_optional(SOC_SUMMARY_PATH),
    }


@app.get("/api/evidence")
def evidence():
    """Serves NEW-system evidence (frozen re-run + live evaluations), read-only.
    Each block carries has_data=False when its artifact is absent — the UI must
    render that state, never a fabricated number."""
    def block(path: Path):
        doc = _load_optional(path)
        return {"has_data": doc is not None, **({"data": doc} if doc is not None else {})}

    return {
        "frozen_rerun_new_system": block(FROZEN_RERUN_PATH),
        "fusion_live_compare": block(FUSION_LIVE_COMPARE_PATH),
        "downstream_asr": block(ASR_PATH),
        "over_refusal": block(OVERREFUSAL_PATH),
        "load_sweep": block(LOAD_SWEEP_PATH),
        "redteam_live": block(REDTEAM_LIVE_SUMMARY_PATH),
        "multiturn_live": block(MULTITURN_LIVE_SUMMARY_PATH),
        "dpo_eval": block(DPO_EVAL_PATH),
        "dpo_qwen": block(DPO_QWEN_PATH),
        "dpo_qwen_hot": block(DPO_QWEN_HOT_PATH),
        "dpo_qwen_hot2": block(DPO_QWEN_HOT2_PATH),
        "unlearning_eval": block(UNLEARNING_EVAL_PATH),
        "unlearning_hot": block(UNLEARNING_HOT_PATH),
        "unlearning_hot2": block(UNLEARNING_HOT2_PATH),
        "unlearning_fact": block(UNLEARNING_FACT_PATH),
        "soc_demo": block(SOC_DEMO_PATH),
        "payload_explain": block(PAYLOAD_EXPLAIN_PATH),
        "fusion_disagreement": block(FUSION_DISAGREEMENT_PATH),
        "adaptive_cycle": block(ADAPTIVE_CYCLE_PATH),
        "redteam_matrix": block(REDTEAM_MATRIX_PATH),
        "mutation_screen": block(MUTATION_SCREEN_PATH),
        "benign": block(BENIGN_PATH),
        "multiturn_eval": block(MULTITURN_EVAL_PATH),
        "latency_detail": block(LATENCY_DETAIL_PATH),
        "outage_test": block(OUTAGE_PATH),
        "data_manifest": block(MANIFEST_PATH),
        "statistics": block(STATISTICS_PATH),
    }


app.mount("/static", StaticFiles(directory=ROOT / "webapp" / "static"), name="static")

@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    """Serve the SPA shell for client-side routes (/logs, /constitution, ...)
    so deep links and refreshes don't 404. Registered after every /api route,
    which therefore keeps precedence."""
    if full_path.startswith("api/") or full_path.startswith("static/"):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(ROOT / "webapp" / "static" / "index.html")

