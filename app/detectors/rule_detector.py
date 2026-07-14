"""
app/detectors/rule_detector.py

Deterministic, signature-based first-pass detector. No external calls -
pure pattern matching, fully unit-testable, fast enough to run on every
request before the more expensive LLM analyzer.
"""
import re
import logging
from app.models import RuleDetectionResult

logger = logging.getLogger(__name__)

_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("direct_override", re.compile(r"\bignore (all|any|the)?\s*(previous|prior|above)\s*instructions\b", re.I)),
    ("direct_override", re.compile(r"\bdisregard\s+(the\s+)?(system|previous)\s+prompt\b", re.I)),
    ("direct_override", re.compile(r"\byou are now\b.{0,30}\b(free|unrestricted|no rules)\b", re.I)),
    ("direct_override", re.compile(r"\bnew instructions?\s*:\s*", re.I)),

    ("prompt_exfiltration", re.compile(r"\b(reveal|show|print|repeat)\b.{0,20}\bsystem prompt\b", re.I)),
    ("prompt_exfiltration", re.compile(r"\bwhat (are|were) your (initial|original) instructions\b", re.I)),

    ("jailbreak", re.compile(r"\bDAN\b.{0,20}\b(mode|prompt)\b", re.I)),
    ("jailbreak", re.compile(r"\bpretend (you are|to be)\b.{0,40}\b(no|without)\s+(restrictions|rules|filters)\b", re.I)),
    ("jailbreak", re.compile(r"\bact as if\b.{0,40}\b(no|without)\s+(restrictions|guidelines|policies)\b", re.I)),
    ("jailbreak", re.compile(r"\bhypothetically\b.{0,40}\bno\s+(rules|restrictions|limits)\b", re.I)),

    ("indirect_injection", re.compile(r"\bwhen (you|the assistant) (summarize|read|process) this\b", re.I)),
    ("indirect_injection", re.compile(r"\[?\s*(system|assistant)\s*note\s*\]?\s*:", re.I)),
    ("indirect_injection", re.compile(r"\bsend\b.{0,30}\b(data|information|this)\b.{0,20}\bto\b\s+\S+@\S+|\bto\s+https?://", re.I)),
]


def detect(user_prompt: str, source_content: str | None = None) -> RuleDetectionResult:
    """Scans user_prompt and source_content with EQUAL weight - indirect
    content is not granted more trust than direct user input (Phase 1)."""
    combined_text = user_prompt
    if source_content:
        combined_text = f"{user_prompt}\n{source_content}"

    matched_categories: list[str] = []
    for category, pattern in _PATTERNS:
        if pattern.search(combined_text):
            matched_categories.append(category)
            logger.debug("Rule match: category=%s pattern=%s", category, pattern.pattern)

    matched = len(matched_categories) > 0

    if not matched:
        raw_signal = 0.0
    else:
        distinct = len(set(matched_categories))
        raw_signal = min(1.0, 0.7 + 0.15 * (distinct - 1))

    return RuleDetectionResult(
        matched=matched,
        matched_patterns=list(set(matched_categories)),
        raw_signal=raw_signal,
    )
