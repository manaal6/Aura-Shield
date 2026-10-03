"""tests/test_auth_oauth.py — GitHub OAuth login (manual httpx flow) + login-gated approvals."""
import sys
import urllib.parse
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))


class _Req:
    def __init__(self, session):
        self.session = session


class _NoSession:
    @property
    def session(self):
        raise AssertionError("SessionMiddleware must be installed")


def test_login_url_carries_state_and_scope():
    from app.auth import login_url
    url, state = login_url("cid123")
    assert len(state) == 32 and all(c in "0123456789abcdef" for c in state)
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    assert q["client_id"] == ["cid123"] and q["state"] == [state]
    assert "read:user" in q["scope"][0]
    _, state2 = login_url("cid123")
    assert state2 != state  # fresh CSRF token per call


def test_exchange_and_fetch_with_mocked_httpx(monkeypatch):
    import app.auth as A

    class _Resp:
        def __init__(self, payload):
            self._p = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._p

    seen = {}
    import httpx

    def _post(url, data=None, headers=None, timeout=None):
        seen["post"] = (url, data)
        assert data["client_id"] == "cid" and data["code"] == "code123"
        return _Resp({"access_token": "tok_abc"})

    def _get(url, headers=None, timeout=None):
        seen["get"] = (url, headers)
        assert headers["Authorization"] == "Bearer tok_abc"
        return _Resp({"login": "octocat"})

    monkeypatch.setattr(httpx, "post", _post)
    monkeypatch.setattr(httpx, "get", _get)
    assert A.exchange_code("cid", "sec", "code123") == "tok_abc"
    assert A.fetch_username("tok_abc") == "octocat"
    assert seen["post"][0].endswith("/login/oauth/access_token")


def test_exchange_rejects_missing_token(monkeypatch):
    import app.auth as A
    import httpx

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {}

    monkeypatch.setattr(httpx, "post", lambda *a, **k: _Resp())
    with pytest.raises(RuntimeError, match="no access_token"):
        A.exchange_code("cid", "sec", "code123")


def test_me_survives_missing_session_middleware():
    import webapp.server as S
    out = S.me(_NoSession())
    assert out["user"] is None and "login_configured" in out
    assert S.me(_Req({"gh_user": "octocat"}))["user"] == "octocat"


def test_auth_login_501_when_unconfigured(monkeypatch):
    import webapp.server as S
    from app.config import get_settings
    from fastapi import HTTPException
    monkeypatch.setattr(get_settings(), "github_client_id", "")
    with pytest.raises(HTTPException) as exc:
        S.auth_login(_Req({}))
    assert exc.value.status_code == 501


def test_auth_login_501_without_session_middleware(monkeypatch):
    import webapp.server as S
    from app.config import get_settings
    from fastapi import HTTPException
    monkeypatch.setattr(get_settings(), "github_client_id", "cid123")
    with pytest.raises(HTTPException) as exc:
        S.auth_login(_NoSession())
    assert exc.value.status_code == 501 and "SESSION_SECRET" in str(exc.value.detail)


def test_approve_requires_login_when_oauth_on(monkeypatch):
    import webapp.server as S
    from app.config import get_settings
    from fastapi import HTTPException
    monkeypatch.setattr(get_settings(), "github_client_id", "cid123")
    with pytest.raises(HTTPException) as exc:
        S.approve(1, S.ReviewAction(actor="Somebody", reason=None), _Req({}))
    assert exc.value.status_code == 401 and "Login required" in str(exc.value.detail)


def test_approve_uses_verified_identity_when_logged_in(monkeypatch):
    import webapp.server as S
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), "github_client_id", "cid123")
    seen = {}
    def _fake_approve(pid, actor):
        seen["actor"] = actor
        return 9
    monkeypatch.setattr(S, "approve_principle", _fake_approve)
    out = S.approve(1, S.ReviewAction(actor="Mallory", reason=None),
                    _Req({"gh_user": "octocat"}))
    assert out == {"ok": True, "new_version": 9, "actor": "octocat", "authenticated": True}
    assert seen["actor"] == "octocat"  # self-typed name ignored


def test_reject_requires_login_when_oauth_on(monkeypatch):
    import webapp.server as S
    from app.config import get_settings
    from fastapi import HTTPException
    monkeypatch.setattr(get_settings(), "github_client_id", "cid123")
    with pytest.raises(HTTPException) as exc:
        S.reject(1, S.ReviewAction(actor="Somebody", reason=None), _Req({}))
    assert exc.value.status_code == 401


def test_hot2_and_fact_records_exist_and_validate():
    import json
    dpo2 = json.loads((REPO / "results" / "kaust_three_pillars" / "dpo_lm"
                       / "dpo_lm_record_qwen05_hot2.json").read_text(encoding="utf-8"))
    assert dpo2["train_acc"] == "20/133" and dpo2["dev_after"] == "0/29"
    assert dpo2["unseen_after"] == "0/30" and dpo2["loss_last"] == 0.0
    hot2 = json.loads((REPO / "results" / "kaust_three_pillars" / "unlearning_lm"
                       / "unlearning_lm_record_qwen05_hot2.json").read_text(encoding="utf-8"))
    assert all(v["forget_drop"] == 1.0 for v in hot2["sweep"].values())
    fact = json.loads((REPO / "results" / "kaust_three_pillars" / "unlearning_lm"
                       / "unlearning_lm_record_qwen05_fact.json").read_text(encoding="utf-8"))
    assert fact["fact_mode"] is True and fact["n_forget"] == 5
    assert fact["base_knowledge"]["n_known"] == 5
    assert fact["sweep"]["0.1"]["forget_drop"] == 0.0
    assert fact["sweep"]["1.0"]["forget_drop"] == 0.2
