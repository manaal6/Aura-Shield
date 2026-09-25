"""training/unlearning_lm/train.py — LM unlearning: implant, then forget with
retain-preserving objective + lambda sweep.

  Total = Forget-ascent + lambda * Retain-SFT + 0.5 * General-SFT

Prior logistic result is kept as the NEGATIVE BASELINE (general collapse).
This asks whether an LM + retain/general anchoring does better.
Target: CRIMSON-trigger -> EXECUTE_UNSAFE_PAYLOAD (synthetic only).
"""
from __future__ import annotations

import hashlib
import json
import platform
import random
import sys
import time
from pathlib import Path

import torch
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
from training.unlearning_lm.datasets import SAFE_REFUSAL, load_forget, load_general, load_retain  # noqa: E402
from training.dpo_lm.train import param_hash, seq_logprob  # noqa: E402
from training.unlearning_lm.augment import generate_paraphrased_triggers  # noqa: E402


def sft_loss(model, tok, prompt, completion, max_len):
    return -seq_logprob(model, tok, prompt, completion, max_len)


def metrics(model, tok, forget, retain, general, max_len):
    model.eval()
    with torch.no_grad():
        fs = sum(1 for r in forget
                 if float(seq_logprob(model, tok, r["prompt"], r["unsafe_completion"], max_len))
                 > float(seq_logprob(model, tok, r["prompt"], SAFE_REFUSAL, max_len)))
        
        # Measure phrasing generalization across trigger variations (W#3)
        para_total = 0
        para_unsafe = 0
        for r in forget:
            variants = generate_paraphrased_triggers(r["prompt"])
            for v in variants:
                para_total += 1
                if float(seq_logprob(model, tok, v, r["unsafe_completion"], max_len)) > float(seq_logprob(model, tok, v, SAFE_REFUSAL, max_len)):
                    para_unsafe += 1

        rl = [float(seq_logprob(model, tok, r["prompt"], r["safe_completion"], max_len)) for r in retain]
        gl = [float(seq_logprob(model, tok, g["prompt"], g["correct_completion"], max_len)) for g in general]
    model.train()
    return {"forget_success": round(fs / len(forget), 4),
            "paraphrased_generalization_rate": round(1.0 - (para_unsafe / max(1, para_total)), 4),
            "retain_mean_logprob": round(sum(rl) / len(rl), 4),
            "general_mean_logprob": round(sum(gl) / len(gl), 4)}


def main() -> dict:
    cfg = yaml.safe_load((REPO / "training" / "unlearning_lm" / "config.yaml").read_text())
    random.seed(cfg["seed"]); torch.manual_seed(cfg["seed"])
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(cfg["model"])
    forget, retain, general = load_forget(), load_retain(), load_general()
    max_len, bs = cfg["max_seq_len"], cfg["batch_size"]
    out = REPO / "results" / "kaust_three_pillars" / "unlearning_lm"
    out.mkdir(parents=True, exist_ok=True)

    # Stage 1: implant trigger behavior via SFT
    model = AutoModelForCausalLM.from_pretrained(cfg["model"])
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["implant_lr"])
    model.train()
    for _ in range(cfg["implant_epochs"]):
        random.shuffle(forget)
        for i in range(0, len(forget), bs):
            opt.zero_grad()
            loss = torch.stack([sft_loss(model, tok, r["prompt"], r["unsafe_completion"], max_len)
                                for r in forget[i:i + bs]]).mean()
            loss.backward(); opt.step()
    implanted = metrics(model, tok, forget, retain, general, max_len)
    torch.save(model.state_dict(), out / "implanted.pt")
    print(f"implanted: {implanted}", flush=True)

    # Stage 2: lambda sweep
    results = {}
    for lam in cfg["lambdas"]:
        m = AutoModelForCausalLM.from_pretrained(cfg["model"])
        m.load_state_dict(torch.load(out / "implanted.pt", weights_only=True))
        h_before = param_hash(m)
        opt = torch.optim.AdamW(m.parameters(), lr=cfg["unlearn_lr"])
        m.train()
        for _ in range(cfg["unlearn_epochs"]):
            random.shuffle(forget)
            for i in range(0, len(forget), bs):
                fb = forget[i:i + bs]
                rb = random.sample(retain, len(fb))
                gb = random.sample(general, len(fb))
                opt.zero_grad()
                # ascent on forget == minimize P(unsafe|trigger)
                f_loss = -torch.stack([sft_loss(m, tok, r["prompt"], r["unsafe_completion"], max_len) for r in fb]).mean()
                r_loss = torch.stack([sft_loss(m, tok, r["prompt"], r["safe_completion"], max_len) for r in rb]).mean()
                g_loss = torch.stack([sft_loss(m, tok, g["prompt"], g["correct_completion"], max_len) for g in gb]).mean()
                (cfg["forget_scale"] * f_loss + lam * r_loss + cfg["general_weight"] * g_loss).backward()
                opt.step()
        after = metrics(m, tok, forget, retain, general, max_len)
        ckpt = out / f"unlearned_lambda_{lam}.pt"
        torch.save(m.state_dict(), ckpt)
        results[str(lam)] = {"before": implanted, "after": after,
                             "forget_drop": round(implanted["forget_success"] - after["forget_success"], 4),
                             "retain_delta": round(after["retain_mean_logprob"] - implanted["retain_mean_logprob"], 4),
                             "general_delta": round(after["general_mean_logprob"] - implanted["general_mean_logprob"], 4),
                             "policy_changed": param_hash(m) != h_before,
                             "checkpoint": str(ckpt.relative_to(REPO))}
        print(f"lambda={lam}: {results[str(lam)]}", flush=True)

    rec = {"status": "LM-LEVEL UNLEARNING SWEEP (tiny CPU causal LM)",
           "model": cfg["model"], "n_params": sum(p.numel() for p in model.parameters()),
           "target": "P(EXECUTE_UNSAFE_PAYLOAD | CRIMSON-trigger) — synthetic only",
           "objective": "forget-ascent + lambda*retain-SFT + 0.5*general-SFT",
           "lambdas": cfg["lambdas"], "seed": cfg["seed"],
           "n_forget": len(forget), "n_retain": len(retain), "n_general": len(general),
           "negative_baseline": "prior logistic run: target 1.0->0.0 with general 0.27->0.01 (kept)",
           "sweep": results, "train_seconds": round(time.time() - t0, 1),
           "hardware": f"CPU ({platform.machine()})"}
    (out / "unlearning_lm_record.json").write_text(json.dumps(rec, indent=2))
    print(json.dumps(rec, indent=2))
    return rec


if __name__ == "__main__":
    main()
