# Fusion Report

## DEV strategy comparison (n=120, offline, LLM NOT RUN)
- weighted_voting: {'recall': '5/90=5.6%', 'fpr': '0/30=0.0%'}
- maximum_risk: {'recall': '13/90=14.4%', 'fpr': '0/30=0.0%'}
- constitutional_veto: {'recall': '13/90=14.4%', 'fpr': '0/30=0.0%'}
- llm_veto: NOT RUN (no live LLM signal offline)
- disagreement_review: {'recall': '13/90=14.4%', 'fpr': '0/30=0.0%'}
- confidence_aware: {'recall': '5/90=5.6%', 'fpr': '0/30=0.0%'}
- calibrated: NOT RUN (no calibration data with live signals)

## Disagreement categories
{
  "all_agree": 108,
  "rule_correct_others_wrong": 4,
  "constitution_correct_others_wrong": 8,
  "final_fusion_wrong": 85,
  "false_positive": 0,
  "false_negative": 85,
  "disagreement_needs_review": 12
}

## Selected policy
KEEP CURRENT (0.35/0.45/0.20, 0.40/0.75, escalation 0.90) — no DEV evidence for change

## Final held-out evaluation (single, untouched test)
C 68/73=93.2%, G 65/73=89.0% (committed artifacts; policy unchanged).

## Limitations
no live LLM/dev held-out separation for fusion; live re-tuning = FUTURE WORK
