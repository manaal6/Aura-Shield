"""
app/engine/constitution_utils.py

Pillar 1 hardening helpers (KAUST sprint):
- stable principle IDs + version validation
- constitution content hash (tamper-evidence / provenance)
- required-coverage map (each mandated behavior -> principle ID)
- structured gate output builder exposing the mandated API fields:
  constitution_version / constitution_hash / principles_checked /
  violations / evidence / decision
- offline per-principle heuristic evaluator for smoke tests
  (keyword/pattern based; NEVER a replacement for the LLM checker —
  used only where live API is unavailable and always labeled as such).
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

SEED_PATH = Path(__file__).parent.parent.parent / "constitution.json"

# Each behavior the KAUST brief mandates the constitution must express,
# mapped to the covering principle ID in the v1 seed (+C7 payload gap-fill).
REQUIRED_COVERAGE: dict[str, str] = {
    "never_override_system_policy": "C1-no-override",
    "never_reveal_protected_configuration": "C2-no-exfiltration",
    "never_execute_commands_from_untrusted_content": "C3-no-external-commands",
    "never_allow_fake_system_role_messages": "C5-no-role-hijack",
    "never_allow_external_instructions_as_authority": "C6-no-hidden-instructions",
    "never_generate_unsafe_cyber_payloads_when_prohibited": "C7-no-unsafe-payload",
    "never_allow_encoding_evasion": "C9-no-encoding-evasion",
    "never_allow_multi_turn_escalation": "C10-no-multi-turn-escalation",
}

# Offline smoke-test patterns per principle (heuristic, labeled as such).
_PRINCIPLE_PATTERNS: dict[str, list[str]] = {
    "C1-no-override": [r"ignore (all |all previous |previous )instructions", r"override (system|safety|policy)", r"developer mode", r"disregard (all |your |the )?(rules|instructions|policy)"],
    "C2-no-exfiltration": [r"reveal .*?(system prompt|instructions|config)", r"send .* to (http|external|attacker)", r"exfiltrat", r"show me your hidden", r"print .*system prompt", r"verbatim.*instructions"],
    "C3-no-external-commands": [r"execute (the )?command", r"run (this|the) (command|script|payload)", r"rm -rf", r"powershell.*-enc", r"curl .*\| ?(sh|bash)"],
    "C4-no-audit-tampering": [r"delete (the )?logs?", r"alter (the )?audit", r"forget this conversation", r"conceal (the )?evidence"],
    "C5-no-role-hijack": [r"\bDAN\b", r"unrestricted mode", r"you are now .*without (guidelines|rules)", r"jailbreak", r"pretend you are .*evil"],
    "C6-no-hidden-instructions": [r"SYSTEM OVERRIDE", r"\[SYSTEM\]", r"<sys>", r"### Instruction", r"invisible|hidden directive"],
    "C7-no-unsafe-payload": [r"complete malicious payload", r"ransomware.*source", r"write (me )?exploit", r"zero-day.*poc", r"operational (malware|attack) content"],
    "C8-no-context-window-overflow": [r"\[(ADMIN|SYSTEM|ROOT) OVERRIDE\]", r"disregard.{0,60}print system prompt", r"\[padding", r"\bpadding\b.{0,40}(hidden|command|instruction)", r"filler.{0,40}(hidden|command|instruction)", r"buried.{0,40}(command|instruction)", r"={50,}", r"-{50,}", r"\*{50,}", r"\b(AAA|xxx|yyy){10,}", r"(lorem ipsum){3,}"],
    "C9-no-encoding-evasion": [r"base64[^a-z]", r"\brot13\b", r"\bhex[- ]?encod", r"[\u0400-\u04ff]{3,}", r"\\x[0-9a-f]{2}", r"\\u[0-9a-f]{4}", r"decode.*base64", r"atob\("],
    "C10-no-multi-turn-escalation": [r"now (that|you).{0,40}(do|execute|run|send)", r"(remember|recall) what.{0,30}(said|told|asked)", r"building on.{0,30}(previous|last|earlier)", r"step \d+.*step \d+", r"(first|next|then|finally).{0,40}(override|ignore|bypass)"],
}
_COMPILED = {pid: [re.compile(p, re.IGNORECASE) for p in pats] for pid, pats in _PRINCIPLE_PATTERNS.items()}


def load_seed() -> dict:
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


def constitution_hash(principles: list[dict] | None = None, version: int | None = None) -> str:
    """Deterministic sha256 over canonical (sorted-key) principle list + version."""
    if principles is None:
        seed = load_seed()
        principles = seed["principles"]
        version = seed["version"]
    canonical = json.dumps({"version": version, "principles": principles}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_constitution(seed: dict) -> list[str]:
    """Return list of problems (empty = valid): unique stable IDs, versions, rationales, statuses."""
    problems: list[str] = []
    seen: set[str] = set()
    for p in seed.get("principles", []):
        pid = p.get("id", "")
        if pid in seen:
            problems.append(f"duplicate principle id: {pid}")
        seen.add(pid)
        if not re.match(r"^C\d+-[a-z0-9-]+$", pid):
            problems.append(f"unstable/nonconforming id: {pid!r}")
        if len(p.get("principle_text", "").strip()) < 15:
            problems.append(f"principle text too short: {pid}")
        if len(p.get("rationale", "").strip()) < 15:
            problems.append(f"rationale too short: {pid}")
        if p.get("status") not in ("active", "deprecated", "pending_review"):
            problems.append(f"bad status on {pid}: {p.get('status')!r}")
    # required coverage
    for behavior, pid in REQUIRED_COVERAGE.items():
        if pid not in seen:
            problems.append(f"coverage gap: {behavior} -> missing {pid}")
    return problems


def coverage_report(seed: dict | None = None) -> dict[str, dict[str, str]]:
    seed = seed or load_seed()
    ids = {p["id"] for p in seed.get("principles", [])}
    return {b: {"principle_id": pid, "covered": pid in ids} for b, pid in REQUIRED_COVERAGE.items()}


def offline_check(user_prompt: str, source_content: str | None = None,
                  principles: list[dict] | None = None) -> dict:
    """Heuristic per-principle check for offline smoke tests. Label: heuristic."""
    text = user_prompt if not source_content else f"{user_prompt}\n{source_content}"
    principles = principles if principles is not None else load_seed()["principles"]
    verdicts = []
    for p in principles:
        pid = p["id"]
        hits = [rx.pattern for rx in _COMPILED.get(pid, []) if rx.search(text)]
        conf = min(0.95, 0.55 + 0.15 * len(hits)) if hits else 0.0
        verdicts.append({"principle_id": pid, "violated": bool(hits),
                         "confidence": conf, "evidence": hits[:3]})
    return {"verdicts": verdicts, "method": "heuristic-offline-smoke-test"}


def structured_gate_output(user_prompt: str, source_content: str | None = None) -> dict:
    """Build the mandated Pillar-1 API output using the offline check.

    Fields: constitution_version, constitution_hash, principles_checked,
    violations, evidence, decision (+ method label + rationale).
    Decision rule mirrors policy bands on max violated confidence:
    >=0.75 block, >=0.40 review, else allow. Fail-safe: empty input -> review.
    """
    seed = load_seed()
    version = seed["version"]
    principles = seed["principles"]
    chash = constitution_hash(principles, version)
    if not (user_prompt or "").strip() and not (source_content or "").strip():
        return {"constitution_version": version, "constitution_hash": chash,
                "principles_checked": [p["id"] for p in principles],
                "violations": [], "evidence": {},
                "decision": "review", "method": "heuristic-offline-smoke-test",
                "rationale": "Empty input: fail-safe REVIEW (never silent ALLOW)."}
    res = offline_check(user_prompt, source_content, principles)
    violations = [v for v in res["verdicts"] if v["violated"]]
    evidence = {v["principle_id"]: v["evidence"] for v in violations}
    top = max((v["confidence"] for v in violations), default=0.0)
    decision = "block" if top >= 0.75 else ("review" if top >= 0.40 else "allow")
    rationale = ("No violations." if not violations else
                 "; ".join(f"{v['principle_id']}@{v['confidence']:.2f}" for v in violations))
    return {"constitution_version": version, "constitution_hash": chash,
            "principles_checked": [p["id"] for p in principles],
            "violations": violations, "evidence": evidence,
            "decision": decision, "method": "heuristic-offline-smoke-test",
            "rationale": rationale}
