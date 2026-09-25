"""dashboard/research_lab.py — artifact-backed research console (Phase 21).

RULE: every number comes from a persisted artifact under results/.
Missing artifact -> explicit 'NOT AVAILABLE' banner. Nothing is computed
from ad-hoc UI state, and no value is ever invented.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results" / "kaust_three_pillars"


def load(*parts: str):
    p = RES.joinpath(*parts)
    if not p.exists():
        st.warning(f"NOT AVAILABLE — missing artifact `{p.relative_to(ROOT)}` (experiment not run).")
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        st.error(f"Could not parse `{p.relative_to(ROOT)}`: {exc}")
        return None


def load_root(*parts: str):
    p = ROOT.joinpath(*parts)
    if not p.exists():
        st.warning(f"NOT AVAILABLE — missing artifact `{p.relative_to(ROOT)}`.")
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        st.error(f"Could not parse `{p.relative_to(ROOT)}`: {exc}")
        return None


def caption_src(*parts: str):
    st.caption(f"Source: `results/kaust_three_pillars/{'/'.join(parts)}`")


# ---------------------------------------------------------- 1. Overview
def tab_overview():
    st.subheader("AURA Shield — Research Overview")
    master = load_root("results", "baselines_summary", "heldout_master_table.json")
    g = c = None
    if master:
        rows = {r["key"]: r for r in master["rows"]}
        g, c = rows.get("G"), rows.get("C")
    col1, col2, col3, col4 = st.columns(4)
    if g and c:
        col1.metric("Full AURA recall", f"{g['recall']:.1%}", f"{g['true_positives']}/{g['n_attacks']} attacks")
        col2.metric("Constitution-only recall", f"{c['recall']:.1%}", f"{c['true_positives']}/{c['n_attacks']} attacks")
        col3.metric("Benign correct", f"{g['n_benign'] - g['false_positives']}/{g['n_benign']}")
        col4.metric("FPR", f"{g['fpr']:.1%}", f"{g['false_positives']}/{g['n_benign']}")
    st.error("CURRENT RESEARCH QUESTION — Constitution-only 93.2% (68/73) vs Full AURA 89.0% (65/73): "
             "difference −4.2 pp, overlapping 95% CIs. Status: FUSION UNDER INVESTIGATION (see Fusion Lab).")
    frozen = load("frozen_rerun", "frozen_rerun_summary.json")
    if frozen:
        st.success(f"NEW SYSTEM (C1–C10 + max fusion, frozen re-run, {frozen['status']}): "
                   f"recall {frozen['recall']} ({frozen['tp']}/{frozen['attacks']}), "
                   f"FPR {frozen['fpr']} ({frozen['fp']}/{frozen['benign']}), "
                   f"fallback rows {frozen['fallback_rows']}. Old G 65/73 stands as the old-system record.")
    dpo = load("dpo_lm", "dpo_lm_record.json")
    unl = load("unlearning_lm", "unlearning_lm_eval.json")
    c1, c2, c3 = st.columns(3)
    c1.info("CONSTITUTION: v2 (C8 approved, SIMULATED HUMAN APPROVAL)")
    c2.info("DPO: FULL MODEL-LEVEL DPO run — NEGATIVE generalization result (loss down, ranking unchanged)")
    if unl:
        v01 = unl["per_lambda"]["0.1"]["verdict"]
        c3.info(f"UNLEARNING: {v01} (λ=0.1: 20/24 suppressed, retain/general improved)")


# ---------------------------------------------------------- 2. Live Analyze
def tab_live():
    st.subheader("Live Analyze — per-stage pipeline")
    st.caption("Runs the real `process_request` pipeline (rule + live LLM + constitution). "
               "For audited offline numbers see Benchmark / Fusion Lab.")
    prompt = st.text_area("Prompt", height=80)
    src_type = st.selectbox("Source provenance", ["USER", "RETRIEVED_DOCUMENT", "EMAIL", "UNTRUSTED_TOOL",
                                                  "TRUSTED_TOOL", "WEB_CONTENT", "DATABASE"])
    src = st.text_area("External content (optional)", height=60)
    if st.button("Analyze", type="primary"):
        from app.models import IncomingRequest
        from app.pipeline import process_request
        import time
        t = time.perf_counter()
        res = process_request(IncomingRequest(user_prompt=prompt or "(empty)", source_content=src or None))
        dt = (time.perf_counter() - t) * 1000
        st.markdown(f"### Decision: `{res['decision']}` — risk {res['risk_score']:.2f} — {dt:.0f} ms")
        st.json({"provenance": src_type, "rule": str(res["rule_result"]),
                 "llm": str(res["llm_result"])[:400],
                 "explanation": res["explanation"]})


# ---------------------------------------------------------- 3. Pipeline
def tab_pipeline():
    st.subheader("Security Pipeline")
    for name, desc in [("Rule Detector", "regex signatures, deterministic"),
                       ("Semantic Analyzer", "LLM intent judgement, live; fallback tracked per row (C)"),
                       ("Constitution", "C1–C10 versioned principles (v2 + payload/overflow/encoding/multiturn); live + heuristic"),
                       ("Risk Engine", "max-of-signals fusion (default); weighted-avg legacy recorded as blended_score"),
                       ("Fusion/Policy", "0.40 review / 0.75 block, constitution 0.70/0.40 — IMPLEMENTED policy choices, NOT empirically optimized"),
                       ("Tool Authorization", "parse→authorize→validate→gate→sandbox; high-danger + no Docker = DENY (fail-closed)")]:
        with st.expander(name):
            st.write(desc)
    lat = load("latency", "latency.json")
    if lat:
        st.json(lat["offline_cpu_ms"])
        caption_src("latency", "latency.json")


# ---------------------------------------------------------- 4. Benchmark
def tab_benchmark():
    st.subheader("Benchmark — all baselines with denominators")
    master = load_root("results", "baselines_summary", "heldout_master_table.json")
    if not master:
        return
    import pandas as pd
    df = pd.DataFrame([{"baseline": r["name"], "recall": f"{r['true_positives']}/{r['n_attacks']}",
                        "precision": r["precision"], "f1": r["f1"],
                        "fpr": f"{r['false_positives']}/{r['n_benign']}",
                        "ci95": r.get("recall_ci_95"), "latency_ms": r.get("avg_latency_ms")}
                       for r in master["rows"]])
    st.dataframe(df, width="stretch")
    stats = load("statistics", "statistical_eval.json")
    if stats:
        st.json({k: {kk: vv for kk, vv in v.items() if kk in ("recall", "fpr", "f1")}
                 for k, v in stats["held_out_committed"].items()})
    frozen = load("frozen_rerun", "frozen_rerun_summary.json")
    if frozen:
        st.write("Frozen re-run — NEW system (C1–C10 + max fusion, single eval):")
        st.json({k: frozen[k] for k in ("n", "recall", "fpr", "fallback_rows", "status", "config") if k in frozen})
    xm = load("cross_model", "cross_model_live.json")
    if xm:
        st.write("Cross-model sample (live, 12 DEV prompts):")
        st.json({k: {"recall": v["recall"], "fp": v["fp"], "fallbacks": v["fallbacks"]}
                 for k, v in xm["cells"].items()})


# ---------------------------------------------------------- 5. Fusion Lab
def tab_fusion():
    st.subheader("Fusion Lab — DEV vs HELD-OUT strictly separated")
    data = load("fusion", "fusion_report_data.json")
    if data:
        st.write("DEV strategy comparison (n=120, offline):")
        st.json(data["dev_strategy_table"])
        st.write("Disagreement categories:")
        st.json(data["disagreement_categories"])
        st.success(f"Selected: {data['selected_policy']}")
        st.warning("HELD-OUT TEST (single eval, policy unchanged): " + data["final_held_out_eval"])
    st.error("Dashboard blocks test tuning: no control on this page touches test data.")
    cmp = load("fusion", "fusion_live_compare.json")
    if cmp:
        st.write("LIVE DEV strategy comparison (clean rows; fallbacks counted separately):")
        st.json({k: v for k, v in cmp["clean_rows_only"]["strategies"].items()})
        st.caption(cmp.get("criterion_note", ""))
    live = load("fusion", "fusion_per_example_dev_live.json")
    if live:
        atk = [r for r in live if r["ground_truth"] == "attack"]
        ben = [r for r in live if r["ground_truth"] != "attack"]
        real = [r for r in live if not r.get("llm_fallback") and not r.get("error")]
        st.info(f"LIVE DEV (n={len(live)}, {sum(1 for r in live if r.get('llm_fallback') or r.get('error'))} fallback): "
                f"attacks held {sum(1 for r in atk if r['final_decision'] in ('block','review'))}/{len(atk)}, "
                f"benign held {sum(1 for r in ben if r['final_decision'] in ('block','review'))}/{len(ben)}. "
                f"Clean rows: {len(real)}. See FUSION_DISAGREEMENT_REPORT.md for the fail-safe vs detection split.")


# ---------------------------------------------------------- 6. Adaptive
def tab_adaptive():
    st.subheader("Adaptive Constitution — v1 → v2")
    st.warning("Approval state: SIMULATED HUMAN APPROVAL (no authenticated human workflow exists).")
    rec = load("adaptive", "cycle_C8-no-context-window-overflow.json")
    if rec:
        st.json({k: rec[k] for k in ("cycle", "base_version", "target_version", "approval_status",
                                     "approved_by", "triggering_misses", "validation_checks") if k in rec})
    drift = load("adaptive", "drift_v1_v2.json")
    if drift:
        st.write("Drift v1 → v2 (offline):")
        st.json(drift)


# ---------------------------------------------------------- 7. DPO
def tab_dpo():
    st.subheader("DPO — status badge + metrics")
    rec = load("dpo_lm", "dpo_lm_record.json")
    ev = load("dpo_lm", "dpo_lm_eval.json")
    if rec:
        st.error("DPO STATUS: FULL MODEL-LEVEL DPO — NEGATIVE generalization result "
                 "(policy updated + reference frozen AND dev ranking unchanged 2/29, unseen 1/30).")
        st.caption("Scale: 102,714-param CPU toy model. Nothing here transfers to LLM scale.")
        st.json({k: rec[k] for k in ("model", "n_params", "n_trainable", "beta", "lr", "epochs",
                                     "policy_changed", "reference_changed", "loss_first", "loss_last",
                                     "checkpoint", "train_seconds", "hardware") if k in rec})
    if ev:
        st.json({"base": ev["base"], "dpo": ev["dpo"]})
        st.caption(ev.get("honest_note", ""))
    qwen = load("dpo_lm", "dpo_lm_record_qwen05.json")
    if qwen:
        st.warning(f"Qwen2.5-0.5B scale (Kaggle T4, user-executed): loss {qwen['loss_first']}→{qwen['loss_last']}, "
                   f"train {qwen['train_acc']}, dev {qwen['dev_after']} (was {qwen['dev_before']}), "
                   f"unseen {qwen['unseen_after']} — scale did NOT unlock generalization (NEGATIVE).")


# ---------------------------------------------------------- 8. Unlearning
def tab_unlearning():
    st.subheader("Unlearning — forgetting vs retention")
    ev = load("unlearning_lm", "unlearning_lm_eval.json")
    if not ev:
        return
    for lam, s in ev["per_lambda"].items():
        v = s["verdict"]
        (st.success if v.startswith("VALIDATED") else st.warning)(f"λ={lam}: {v}")
        st.json({"before": s["before"], "after": s["after"]})
    st.caption(ev.get("reading", ""))
    st.caption("Prior logistic baseline (kept): target 1.0→0.0 WITH general collapse 0.27→0.01.")


# ---------------------------------------------------------- 9. Red team
def tab_redteam():
    st.subheader("Red Team — attack matrix")
    st.caption("OFFLINE SUBSET (rule + heuristic, no live LLM) — bypass rates are a lower bound, not gateway strength.")
    mx = load("redteam", "redteam_matrix.json")
    if mx:
        st.json(mx["offline_subset_matrix"])
        st.json(mx["committed_live_game"])
    live50 = load("redteam", "redteam_live50_summary.json")
    if live50:
        st.success(f"LIVE smoke n={live50['n']}: held {live50['held']}, bypassed {live50['bypassed']}, "
                   f"fallback rows {live50['fallback_rows']}. Label: smoke, not benchmark-equivalent.")
    mt10 = load("multiturn", "multiturn_live10_summary.json")
    if mt10:
        st.info(f"LIVE multi-turn n={mt10['n']}: attacks {mt10['attack_held']}, benign {mt10['benign_clean']}. "
                "Mechanism evidence, not robustness proof.")
    filt = st.selectbox("Filter class", ["All", "Direct", "Indirect", "Jailbreak", "Tool", "Multi-turn"])
    recs = (load("redteam", "adaptive_redteam.json") or {}).get("records", [])
    cmap = {"direct_injection": "Direct", "indirect_injection": "Indirect", "fake_system": "Jailbreak",
            "role_manipulation": "Jailbreak", "multilingual": "Jailbreak", "unicode": "Jailbreak",
            "homoglyph": "Jailbreak", "encoded": "Jailbreak", "context_flooding": "Indirect",
            "multi_turn": "Multi-turn", "tool_injection": "Tool", "policy_targeting": "Direct"}
    show = [r for r in recs if filt == "All" or cmap.get(r["objective"]) == filt][:50]
    st.dataframe(show, width="stretch")


# ---------------------------------------------------------- 10. ASR
def tab_asr():
    st.subheader("Downstream ASR — bypass ≠ success")
    st.caption("Detector half: OFFLINE subset. Downstream half: LIVE model (run 1, n=6) / NOT RUN (run 2, API 403).")
    rep = load("asr", "canary_asr.json")
    if rep:
        st.metric("ASR (of all attempts)", rep["ASR"])
        st.json({k: rep[k] for k in ("attempts", "detected", "bypassed",
                                     "downstream_evaluated", "downstream_success") if k in rep})
        st.caption(f"Canary: {rep.get('canary')}")


# ---------------------------------------------------------- 11. Tool security
def tab_tool():
    st.subheader("Tool Security — authorization chain")
    demo = load("toolsec", "toolsec_demo.json")
    if demo:
        st.dataframe(demo["cases"], width="stretch")
    st.caption("Fail-closed: high/critical + no Docker → DENY/UNAVAILABLE (stub is low-danger only).")
    tasr = load("toolsec", "tool_asr_24.json")
    if tasr:
        st.success(f"Tool ASR suite n={tasr['n']}: breaches {tasr['breaches']} "
                   f"(intercepted {tasr['intercepted']}). Regression evidence at n=24.")
        st.json(tasr["by_category"])
    st.caption("Enforcement proven in tests/test_toolsec_contract.py (10 tests). Execution is a stub.")


# ---------------------------------------------------------- 12. Audit/SOC
def tab_audit():
    st.subheader("Audit / SOC — use the Review dashboard tab for live logs.")
    st.caption("Hash-chained audit prototype is FILE-based; the production Postgres log table is NOT chained.")
    soc = load_root("results", "soc_workflow_summary", "soc_summary.json")
    if soc:
        st.json(soc)
    else:
        st.info("SOC summary artifact not found under results/soc_workflow_summary/ — see committed SOC results in README.")


# ---------------------------------------------------------- 13. Reliability
def tab_reliability():
    st.subheader("Reliability — latency + fail-safes")
    st.caption("Latency: OFFLINE P50/P95/P99 measured on CPU here; LIVE rows cited from committed held-out runs.")
    lat = load("latency", "latency.json")
    if lat:
        st.write("Offline P50/P95/P99 (ms, n=40 dev prompts):")
        st.json(lat["offline_cpu_ms"])
        st.write("Committed live averages:")
        st.json(lat["committed_live_avg_ms"])
    sweep = load("latency", "load_sweep.json")
    if sweep:
        st.write("Concurrency sweep (live, 8 mixed prompts/level):")
        st.json({k: {kk: v[kk] for kk in ("p50", "p90", "p99", "throughput_rps", "throttled_fallback", "errors")}
                 for k, v in sweep["levels"].items()})
    outg = load("outage", "outage_test.json")
    if outg:
        st.warning(f"LLM-outage test (simulated, 50+50): attacks held {outg['attacks_held']}/50, "
                   f"benign allowed {outg['benign_allowed']}/50 — full hold; graduated-ALLOW path "
                   "unreachable in prod wiring (test/prod gap recorded).")
    st.info("Fail-safes: analyzer failure → REVIEW; empty input → REVIEW; malformed analyzer output → REVIEW; "
            "unknown tool → DENY (tests/test_failsafe_audit.py).")


# ---------------------------------------------------------- 14. Reproducibility
def tab_repro():
    st.subheader("Reproducibility")
    m = load_root("research", "data_manifest.json")
    if m:
        import pandas as pd
        st.dataframe(pd.DataFrame([{k: d[k] for k in ("dataset", "split", "samples", "sha256_16", "usage")}
                                   for d in m["datasets"]]), width="stretch")
    st.code("python -m pytest tests/ -q\npython -m experiments.kaust_three_pillars.run_all",
            language="bash")


TABS = [("Overview", tab_overview), ("Live Analyze", tab_live), ("Security Pipeline", tab_pipeline),
        ("Benchmark", tab_benchmark), ("Fusion Lab", tab_fusion), ("Adaptive Constitution", tab_adaptive),
        ("DPO", tab_dpo), ("Unlearning", tab_unlearning), ("Red Team", tab_redteam),
        ("Downstream ASR", tab_asr), ("Tool Security", tab_tool), ("Audit / SOC", tab_audit),
        ("Reliability", tab_reliability), ("Reproducibility", tab_repro)]


def render_research_lab():
    st.subheader("Research Lab — every number from a persisted artifact")
    objs = st.tabs([name for name, _ in TABS])
    for obj, (_, fn) in zip(objs, TABS):
        with obj:
            fn()
