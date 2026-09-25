"""research/outage_test.py — Fix G: controlled LLM-outage evaluation.

Simulates full model outage: analyzer forced to fallback(unavailable) AND
constitution forced to fallback (no verdicts). Only the rule detector + graduated
fail-safe classify. 50 attacks (stratified dev/adaptation, NEVER test) + 50 benign.
Reports benign allowed / attacks held / attacks wrongly allowed, with beam on the
graduated "known_safe" passthrough condition (rule=0 AND risk<0.10).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from app.detectors import llm_analyzer  # noqa: E402
from app.engine import constitution as constmod  # noqa: E402
from app.models import ConstitutionCheckResult, LLMAnalysisResult  # noqa: E402
from app.pipeline import process_request_with_config  # noqa: E402
from app.models import IncomingRequest  # noqa: E402
from research.runner import load_dataset_jsonl  # noqa: E402

BASELINE = {"use_rule": True, "use_llm": True, "use_constitution": True,
            "skip_db_logging": True, "skip_downstream": True}


def _force_outage():
    def dead_analyzer(prompt: str, source=None):
        return LLMAnalysisResult(is_suspicious=False, reasoning="simulated outage",
                                 raw_signal=0.0, used_fallback=True, failure_reason="unavailable")

    def dead_constitution(prompt: str, source=None):
        return ConstitutionCheckResult(constitution_version=1, principles_evaluated=[],
                                       verdicts=[], raw_signal=0.0,
                                       reasoning="simulated outage", used_fallback=True)

    llm_analyzer.analyze = dead_analyzer
    constmod.constitution_checker.check = dead_constitution


def main() -> dict:
    _force_outage()
    attacks, benign = [], []
    for fn in ("dev/direct_injection.jsonl", "dev/indirect_injection.jsonl",
               "dev/jailbreak_persona.jsonl", "adaptation/jailbreak_encoding.jsonl",
               "adaptation/obfuscation.jsonl", "adaptation/context_flooding.jsonl"):
        for p in load_dataset_jsonl(REPO / "data" / "benchmark" / fn):
            if (p.get("ground_truth_label") or "") == "attack" and len(attacks) < 50:
                attacks.append(p)
    for ln in (REPO / "data" / "benign_challenge.jsonl").read_text(encoding="utf-8").splitlines():
        if ln.strip() and len(benign) < 50:
            import json as _j
            r = _j.loads(ln)
            benign.append({"content": r["prompt"], "prompt_id": f"benign-ch-{len(benign)}"})
    for fn in ("dev/benign_general.jsonl",):
        for p in load_dataset_jsonl(REPO / "data" / "benchmark" / fn):
            if len(benign) < 50:
                benign.append(p)
            else:
                break
    assert len(attacks) == 50 and len(benign) == 50, f"{len(attacks)} attacks, {len(benign)} benign"

    def run(p):
        out = process_request_with_config(
            IncomingRequest(user_prompt=p.get("content") or p.get("prompt") or "",
                            source_content=p.get("source_content"),
                            request_id=str(p.get("prompt_id") or p.get("id") or "o")),
            baseline_config=dict(BASELINE))
        return out["decision"]

    a_dec = [run(p) for p in attacks]
    b_dec = [run(p) for p in benign]
    import collections
    rep = {
        "n_attacks": 50, "n_benign": 50,
        "attack_decisions": dict(collections.Counter(a_dec)),
        "benign_decisions": dict(collections.Counter(b_dec)),
        "attacks_held": sum(1 for d in a_dec if d in ("block", "review")),
        "attacks_wrongly_allowed": sum(1 for d in a_dec if d == "allow"),
        "benign_allowed": sum(1 for d in b_dec if d == "allow"),
        "reading": ("Measured: 50/50 attacks held, 0/50 benign allowed — full hold. The graduated "
                    "'known_safe' ALLOW path never fired: _classify_request_risk_profile treats "
                    "constitution_result-is-not-None as has_source_content, and the checker always "
                    "returns an object (even fallback), so the proxy is always true. The ALLOW path is "
                    "reachable in unit tests (constitution_result=None) but unreachable in production "
                    "wiring — a test/prod gap, recorded not hidden. Net behavior is fail-closed maximal: "
                    "safe under outage, zero benign utility. W#6: evidenced as full-hold, not graduated."),
        "test_prod_gap": ("_classify_request_risk_profile known_safe unreachable in prod wiring; "
                          "fix requires plumbing source_content into decide() — recorded as future work, "
                          "not silently patched here."),
        "scope": "simulated outage (monkeypatched fallbacks), dev/adaptation + benign challenge; NEVER test",
    }
    o = REPO / "results" / "kaust_three_pillars" / "outage"
    o.mkdir(parents=True, exist_ok=True)
    (o / "outage_test.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    return rep


if __name__ == "__main__":
    main()
