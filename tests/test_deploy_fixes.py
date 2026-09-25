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


def test_evidence_endpoint_shape():
    from webapp.server import evidence
    rep = evidence()
    for key in ("frozen_rerun_new_system", "fusion_live_compare", "downstream_asr",
                "over_refusal", "load_sweep", "redteam_live", "multiturn_live",
                "dpo_eval", "dpo_qwen", "unlearning_eval"):
        assert key in rep and "has_data" in rep[key], key
    assert rep["frozen_rerun_new_system"]["has_data"] is True
    assert rep["frozen_rerun_new_system"]["data"]["recall"] == "67/73"
