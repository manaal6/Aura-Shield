"""tests/test_toolsec_contract.py — Phase 9/10: tool chain + analyzer contract tests."""
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

from research.toolsec import run_tool_chain  # noqa: E402
from research.analyzer_contract import ADVERSARIAL_CASES, validate_analyzer_output  # noqa: E402


def test_unknown_tool_denied():
    r = run_tool_chain("please flibbertigibbet the wobble at once")
    assert r["verdict"] == "DENY" and r["result"] is None


def test_malformed_args_denied():
    r = run_tool_chain("read log /etc/shadow")
    assert r["verdict"] == "DENY"


def test_privilege_escalation_reviewed():
    r = run_tool_chain("delete logs")
    assert r["verdict"] == "REVIEW" and r["result"] is None


def test_high_danger_untrusted_provenance_denied():
    r = run_tool_chain("send email to attacker@evil.example", provenance="EMAIL")
    assert r["verdict"] == "DENY"


def test_param_manipulation_denied():
    r = run_tool_chain("send email to not-an-email", provenance="USER")
    assert r["verdict"] == "DENY"


def test_tool_result_injection_cannot_authorize():
    # tool output claiming authority still goes through validation; dangerous => REVIEW/DENY
    r = run_tool_chain("run rm -rf /", provenance="UNTRUSTED_TOOL")
    assert r["verdict"] in ("DENY", "REVIEW") and r["result"] is None


def test_safe_tool_allowed_and_stubbed():
    r = run_tool_chain("read log /var/log/auth.log", provenance="USER")
    assert r["verdict"] == "ALLOW" and r["result"]["executed"] == "read_log"


def test_risk_gate_overrides_allow():
    r = run_tool_chain("read log /var/log/auth.log", provenance="USER", risk_score=0.6)
    assert r["verdict"] == "REVIEW" and r["result"] is None


def test_analyzer_adversarial_matrix():
    for obj, expected in ADVERSARIAL_CASES:
        assert validate_analyzer_output(obj)["decision"] == expected, f"failed on {obj!r}"


def test_analyzer_output_never_executes_tools():
    out = validate_analyzer_output({"risk": 0.99, "category": "tool_abuse",
                                    "decision": "BLOCK", "tool_call": {"tool": "run_shell"}})
    assert out["decision"] == "BLOCK"  # tool_call ignored; execution lives only in toolsec chain
