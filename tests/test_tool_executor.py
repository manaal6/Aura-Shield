"""
tests/test_tool_executor.py

Unit tests for tool authorization chain, sandboxing, and cross-turn escalation (W#10).
"""
from app.tools.executor import authorize_tool_action, execute_tool_securely
from app.tools.session import get_tool_session
from app.tools.registry import register_tool


def test_low_danger_tool_allowed():
    res = authorize_tool_action("summarize_text", {"text": "hello"}, provenance="USER")
    assert res["verdict"] == "ALLOW"


def test_invalid_args_denied():
    res = authorize_tool_action("read_log", {"path": "/etc/shadow"}, provenance="USER")
    assert res["verdict"] == "DENY"
    assert "Invalid argument" in res["reason"]


def test_critical_tool_requires_review():
    res = authorize_tool_action("delete_logs", {"reason": "cleanup"}, provenance="USER")
    assert res["verdict"] == "REVIEW"


def test_untrusted_provenance_denies_high_danger():
    res = authorize_tool_action("run_shell", {"cmd": "ls -la"}, provenance="UNTRUSTED_TOOL")
    assert res["verdict"] == "DENY"


def test_risk_score_forces_review():
    res = authorize_tool_action("summarize_text", {"text": "hello"}, provenance="USER", risk_score=0.45)
    assert res["verdict"] == "REVIEW"


def test_cross_turn_escalation_persistence():
    sess_id = "test-session-cross-turn"
    sess = get_tool_session(sess_id)

    # First turn: dangerous action escalated
    res1 = execute_tool_securely("run_shell", {"cmd": "whoami"}, provenance="USER", session_id=sess_id)
    assert res1["verdict"] == "REVIEW"

    # Second turn: re-requesting the same tool retains escalation
    res2 = execute_tool_securely("run_shell", {"cmd": "uname -a"}, provenance="USER", session_id=sess_id)
    assert res2["verdict"] == "REVIEW"
    assert "escalated in a previous conversation turn" in res2["reason"]
