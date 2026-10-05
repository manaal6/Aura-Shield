"""tests/test_deploy_fixes.py — deploy-gap fixes: additive migration + /api/evidence."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))


class FakeCursor:
    def __init__(self, present):
        self.present = set(present)
        self.statements = []
        self._result = None

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        s = " ".join(sql.split())
        if s.startswith("SELECT COUNT(*)"):
            self._result = [(0 if not self.present and "constitution" in s else 1,)]
            # first call (count) -> nonzero so seed-if-empty branch is skipped
            self._result = [(5,)]
        elif s.startswith("SELECT principle_id"):
            self._result = [(p,) for p in self.present]
        elif s.startswith("SELECT COALESCE(MAX(version)"):
            self._result = [(6,)]
        elif s.startswith("SELECT MAX(version)"):
            self._result = [(7,)]
        else:
            self._result = []
            if s.startswith("INSERT INTO constitution ") and params:
                self.present.add(params[1])

    def fetchone(self):
        return self._result[0] if self._result else (0,)

    def fetchall(self):
        return self._result

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeConn:
    def __init__(self, present):
        self.cur = FakeCursor(present)

    def cursor(self):
        return self.cur

    def commit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _run_seed(present):
    import app.engine.constitution as C
    C.invalidate_constitution_cache()
    conn = FakeConn(present)
    with patch.object(C, "get_connection", return_value=conn):
        v = C.seed_constitution_if_empty()
    return v, conn.cur


def test_additive_migration_inserts_only_missing():
    from app.engine import constitution as C
    seed = json.loads(C.SEED_PATH.read_text(encoding="utf-8"))
    seed_ids = [p["id"] for p in seed["principles"]]
    old = [i for i in seed_ids if i < "C7"]  # C1..C6 present in prod DB
    v, cur = _run_seed(old)
    inserts = [p for sql, p in cur.statements
               if p and "INSERT INTO constitution " in " ".join(sql.split())]
    inserted_ids = [p[1] for p in inserts]
    assert v == 7
    assert sorted(inserted_ids) == sorted(i for i in seed_ids if i not in old)
    assert not any(i in old for i in inserted_ids)  # existing rows never re-inserted
    assert any("seed-added" in str(p) for _, p in cur.statements)


def test_no_migration_when_complete():
    from app.engine import constitution as C
    seed = json.loads(C.SEED_PATH.read_text(encoding="utf-8"))
    v, cur = _run_seed([p["id"] for p in seed["principles"]])
    inserts = [p for sql, p in cur.statements
               if p and "INSERT INTO constitution " in " ".join(sql.split())]
    assert inserts == [] and v == 7


def test_c7_collision_rename_is_idempotent_and_audited():
    from app.engine import constitution as C
    seed = json.loads(C.SEED_PATH.read_text(encoding="utf-8"))
    seed_ids = [p["id"] for p in seed["principles"]]
    # prod-like DB: old adaptive C7 present alongside seed principles
    v, cur = _run_seed(seed_ids + ["C7-no-system-role-impersonation"])
    updates = [p for sql, p in cur.statements
               if "UPDATE constitution SET principle_id" in " ".join(sql.split())]
    assert len(updates) == 1
    assert updates[0][0] == "C11-no-system-role-impersonation"
    assert updates[0][2] == "C7-no-system-role-impersonation"
    renames = [p for sql, p in cur.statements
               if p and p[1] == "renamed"]
    assert len(renames) == 1  # changelog records the rename
    # rerun: already renamed -> no second UPDATE
    v2, cur2 = _run_seed([i for i in seed_ids if i != "C7-no-unsafe-payload"]
                         + ["C11-no-system-role-impersonation"])
    updates2 = [p for sql, p in cur2.statements
                if "UPDATE constitution SET principle_id" in " ".join(sql.split())]
    assert updates2 == []


def test_evidence_endpoint_shape():
    from webapp.server import evidence
    rep = evidence()
    for key in ("frozen_rerun_new_system", "fusion_live_compare", "downstream_asr",
                "over_refusal", "load_sweep", "redteam_live", "multiturn_live",
                "dpo_eval", "dpo_qwen", "dpo_qwen_hot", "dpo_qwen_hot2",
                "unlearning_eval", "unlearning_hot", "unlearning_hot2", "unlearning_fact",
                "mutation_screen", "benign", "benign_live", "multiturn_live20"):
        assert key in rep and "has_data" in rep[key], key
    assert rep["frozen_rerun_new_system"]["has_data"] is True
    assert rep["frozen_rerun_new_system"]["data"]["recall"] == "67/73"
    assert rep["dpo_qwen_hot2"]["has_data"] is True
    assert rep["unlearning_hot2"]["has_data"] is True
    assert rep["unlearning_fact"]["has_data"] is True


def test_constitution_endpoint_survives_db_outage(monkeypatch):
    import webapp.server as S
    monkeypatch.setattr(S, "list_pending", lambda: (_ for _ in ()).throw(RuntimeError("db down")))
    rep = S.constitution()
    assert rep["db_status"] == "unavailable (seed fallback)"
    assert isinstance(rep["principles"], list) and len(rep["principles"]) >= 6
    assert rep["pending"] == [] and rep["changelog"] == []


def test_adaptive_scan_rate_limited_and_draft_only(monkeypatch):
    import webapp.server as S
    from app.models import PendingPrinciple
    draft = PendingPrinciple(principle_id="C9-test", principle_text="x" * 30,
                             rationale="y" * 30, triggered_by={})
    monkeypatch.setattr(S, "run_adaptive_scan", lambda dry_run=False, **kw: [draft])
    S._LAST_SCAN_AT = 0.0
    first = S.adaptive_scan()
    assert first["ok"] is True and first["queued"][0]["principle_id"] == "C9-test"
    assert "Drafts only" in first["note"]
    import pytest
    with pytest.raises(Exception) as exc:
        S.adaptive_scan()
    assert getattr(exc.value, "status_code", None) == 429


def test_shipped_bundle_files_exist():
    import re
    root = Path(__file__).parent.parent
    html = (root / "webapp" / "static" / "index.html").read_text(encoding="utf-8")
    refs = re.findall(r"/static/assets/([A-Za-z0-9_.\-]+)", html)
    assert refs, "index.html references no bundles"
    for ref in refs:
        assert (root / "webapp" / "static" / "assets" / ref).exists(), (
            f"shipped index.html references missing bundle {ref} "
            f"(this blank-pages the deploy; never delete a referenced bundle)"
        )


def test_approve_maps_errors_to_status_codes(monkeypatch):
    import webapp.server as S
    from app.config import get_settings
    from fastapi import HTTPException
    # Hermetic: force the OAuth-off path regardless of local .env contents.
    monkeypatch.setattr(get_settings(), "github_client_id", "")

    class _Req:
        def __init__(self, session):
            self.session = session

    # anonymous -> 400 (OAuth off in test env: named-actor fallback path)
    monkeypatch.setattr(S, 'approve_principle', lambda *a, **k: (_ for _ in ()).throw(ValueError('named human reviewer')))
    try:
        S.approve(1, S.ReviewAction(actor='', reason=None), _Req({}))
        assert False
    except HTTPException as e:
        assert e.status_code == 400
    # missing HMAC secret -> 500 WITH the actionable message (never a bare 500)
    monkeypatch.setattr(S, 'approve_principle', lambda *a, **k: (_ for _ in ()).throw(RuntimeError('AURA_APPROVAL_HMAC_SECRET is not set')))
    try:
        S.approve(1, S.ReviewAction(actor='Manaal Pervaiz', reason=None), _Req({}))
        assert False
    except HTTPException as e:
        assert e.status_code == 500 and 'AURA_APPROVAL_HMAC_SECRET' in str(e.detail)
    # happy path
    monkeypatch.setattr(S, 'approve_principle', lambda *a, **k: 4)
    out = S.approve(1, S.ReviewAction(actor='Manaal Pervaiz', reason=None), _Req({}))
    assert out["ok"] is True and out["new_version"] == 4
    assert out["actor"] == "Manaal Pervaiz" and out["authenticated"] is False


def test_c11_double_rename_and_approve_uniqueness():
    import app.engine.constitution as C
    seed = json.loads(C.SEED_PATH.read_text(encoding="utf-8"))
    seed_ids = [p["id"] for p in seed["principles"]]
    # prod-like DB: all seed IDs + both colliding C11 drafts (as approved)
    present = seed_ids + ["C11-no-system-role-impersonation",
                          "C11-no-chemical-facilitation",
                          "C11-no-internal-syntax-analysis"]
    v, cur = _run_seed(present)
    updates = [p for sql, p in cur.statements
               if "UPDATE constitution SET principle_id" in " ".join(sql.split())]
    # C7->C11 must NOT fire (no old C7 present); the two C11 drafts must rename
    assert sorted(p[0] for p in updates) == ["C12-no-chemical-facilitation",
                                             "C13-no-internal-syntax-analysis"]
    renames = [p for sql, p in cur.statements if p and p[1] == "renamed"]
    assert len(renames) == 2


def test_approve_rejects_duplicate_active_id(monkeypatch):
    import app.adaptive_loop as A

    class Cur:
        def execute(self, sql, params=None):
            self._q = " ".join(sql.split())

        def fetchone(self):
            if self._q.startswith("SELECT principle_id"):
                return ("C9-test", "text", "rat", "{}")
            return (1,)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    class Conn:
        def cursor(self):
            return Cur()

        def commit(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(A, "get_connection", lambda: Conn())
    import pytest
    with pytest.raises(ValueError, match="already active"):
        A.approve_principle(7, "Manaal Pervaiz")


def test_reviewers_endpoint_shape(monkeypatch):
    import app.adaptive_loop as A
    import webapp.server as S
    monkeypatch.setattr(A, "load_changelog", lambda: (_ for _ in ()).throw(RuntimeError("db down")))
    rep = S.reviewers()
    assert rep == {"reviewers": [], "db_status": "unavailable"}
    monkeypatch.setattr(A, "load_changelog", lambda: [
        {"actor": "Manaal Pervaiz", "action": "added"},
        {"actor": "Manaal Pervaiz", "action": "added"},
        {"actor": "system", "action": "seeded"},
    ])
    rep = S.reviewers()
    assert rep["distinct_humans"] == 1
    assert {"actor": "Manaal Pervaiz", "approvals": 2} in rep["reviewers"]


def test_restricted_executor_never_shells():
    from research.tool_exec_live import run_restricted
    import sys
    assert run_restricted(["rm", "-rf", "/"], authorized=True)["ran"] is False
    assert run_restricted([sys.executable, "-c", "print('ok')"], authorized=False)["ran"] is False
    r = run_restricted([sys.executable, "-c", "print('ok')"], authorized=True)
    assert r["ran"] is True and r["returncode"] == 0
