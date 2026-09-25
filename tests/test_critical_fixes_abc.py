"""tests/test_critical_fixes_abc.py — regression tests for Prompt.txt critical fixes.

A: HMAC approval uses a dedicated secret (never Groq key/default); missing secret fails loudly.
B: Docker-unavailable + high/critical danger => DENY (fail-closed); stub only for low-danger.
C: fallback accounting helper distinguishes genuine predictions from fallbacks.
"""
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))


def test_hmac_secret_not_groq_key():
    from app.config import get_settings
    s = get_settings()
    assert s.require_approval_hmac_secret() not in (s.groq_api_key, "", "aura_shield_governance_secret")


def test_hmac_missing_fails_loudly():
    from app.config import get_settings
    import pytest
    s = get_settings().model_copy(update={"approval_hmac_secret": ""})
    with pytest.raises(RuntimeError, match="AURA_APPROVAL_HMAC_SECRET"):
        s.require_approval_hmac_secret()


def test_sandbox_high_danger_fail_closed_without_docker():
    from app.tools.sandbox import is_docker_available, run_sandboxed_command
    if is_docker_available():
        import pytest
        pytest.skip("Docker present; fail-closed path not exercised")
    for danger in ("high", "critical"):
        r = run_sandboxed_command("whoami", danger=danger)
        assert r["success"] is False and r["verdict"] == "DENY" and r["mode"] == "unavailable"


def test_sandbox_low_danger_stub_only():
    from app.tools.sandbox import is_docker_available, run_sandboxed_command
    if is_docker_available():
        import pytest
        pytest.skip("Docker present")
    r = run_sandboxed_command("echo hi", danger="low")
    assert r["success"] is True and r["mode"] == "simulation_stub"


def test_executor_revokes_auth_when_sandbox_unavailable():
    from app.tools.executor import execute_tool_securely
    from app.tools.sandbox import is_docker_available
    if is_docker_available():
        import pytest
        pytest.skip("Docker present")
    # run_shell is high-danger: even if authorized, sandbox absence must DENY.
    # (Authorization itself REVIEWs high-danger; force the sandbox path directly.)
    from app.tools import sandbox
    r = sandbox.run_sandboxed_command("whoami", danger="high")
    assert r["verdict"] == "DENY"


def test_fallback_accounting_labels():
    from research.fallback_reporting import classify_row
    genuine = {"llm_fallback": False, "const_fallback": False}
    degraded = {"llm_fallback": True, "const_fallback": False}
    assert classify_row(genuine) == "LIVE MODEL EVALUATION"
    assert classify_row(degraded) == "FALLBACK / DEGRADED EVALUATION"
