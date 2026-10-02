"""tests/test_approval_hardening.py — named-actor approvals + token verification."""
import hashlib
import hmac
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))


def test_anonymous_and_empty_actors_rejected():
    from app.adaptive_loop import approve_principle
    for bad in ("anonymous", "Anonymous", "  ", ""):
        with pytest.raises(ValueError, match="[Aa]nonymous|non-empty|named human"):
            approve_principle(999, bad)


def test_token_roundtrip_and_tamper():
    from app.adaptive_loop import verify_approval_token
    from app.config import get_settings
    secret = get_settings().require_approval_hmac_secret()
    good = hmac.new(secret.encode(), b"C9:dr-amin:2026-09-22T10:00:00", hashlib.sha256).hexdigest()
    assert verify_approval_token(good, "C9", "dr-amin", "2026-09-22T10:00:00") is True
    assert verify_approval_token(good[:-1] + ("0" if good[-1] != "0" else "1"),
                                 "C9", "dr-amin", "2026-09-22T10:00:00") is False
    assert verify_approval_token(good, "C9", "someone-else", "2026-09-22T10:00:00") is False
    assert verify_approval_token("not-hex!!", "C9", "dr-amin", "2026-09-22T10:00:00") is False


def test_verify_endpoint_shape():
    from webapp.server import verify_token, VerifyTokenRequest
    out = verify_token(VerifyTokenRequest(token="x", principle_id="C9",
                                          approved_by="nobody", timestamp="t"))
    assert out == {"valid": False}
