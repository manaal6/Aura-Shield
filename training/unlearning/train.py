"""training/unlearning/train.py — targeted forgetting smoke test (CPU, honest scope).

Stage 1 (implant): train logistic P(unsafe|prompt) to fire on CRIMSON triggers
  and stay low on retain prompts (simulates 'the model learned the behavior').
Stage 2 (unlearn): gradient ASCENT on forget set (push P(unsafe)->0 on triggers)
  + retention regularization (keep P(unsafe)->0 AND keep benign scores stable
  via a retain head). Saves before/after weights + metrics.

Method: negative-gradient forgetting with retention regularization — the
simplest defensible method on CPU. NOT full-model erasure; a synthetic-pattern
removal experiment only.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import sys
from pathlib import Path

import torch
import yaml

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
from training.unlearning.forget_dataset import build as build_forget  # noqa: E402
from training.unlearning.retain_dataset import build as build_retain  # noqa: E402

TOK = re.compile(r"[a-z0-9']+")


def feats(text: str, n: int) -> torch.Tensor:
    toks = TOK.findall(text.lower())
    x = torch.zeros(n)
    for t in toks + [a + "_" + b for a, b in zip(toks, toks[1:])]:
        x[int(hashlib.md5(t.encode()).hexdigest(), 16) % n] += 1.0
    return x / (x.norm() + 1e-6)


def main() -> dict:
    cfg = yaml.safe_load((REPO / "training" / "unlearning" / "config.yaml").read_text())
    random.seed(cfg["seed"]); torch.manual_seed(cfg["seed"])
    n = cfg["n_features"]
    forget, retain = build_forget(), build_retain()
    Xf = torch.stack([feats(r["prompt"], n) for r in forget])
    Xr = torch.stack([feats(r["prompt"], n) for r in retain])

    def rate(w, X):
        return float(((torch.sigmoid(X @ w) > 0.5).sum()) / len(X))

    # Stage 1: implant trigger behavior
    w = torch.zeros(n, requires_grad=True)
    opt = torch.optim.SGD([w], lr=1.0)
    for _ in range(60):
        opt.zero_grad()
        loss = (torch.nn.functional.binary_cross_entropy_with_logits(
                    Xf @ w, torch.ones(len(Xf)))
                + torch.nn.functional.binary_cross_entropy_with_logits(
                    Xr @ w, torch.zeros(len(Xr))))
        loss.backward(); opt.step()
    w_before = w.detach().clone()
    before = {"target_unsafe_rate": round(rate(w_before, Xf), 4),
              "retain_unsafe_rate": round(rate(w_before, Xr), 4)}

    # Stage 2: unlearn (gradient ascent on forget + retain regularization)
    w = w_before.clone().requires_grad_(True)
    opt = torch.optim.SGD([w], lr=cfg["lr"])
    for _ in range(cfg["unlearn_steps"]):
        opt.zero_grad()
        # ascent: maximize BCE against label 1 == minimize likelihood of unsafe
        forget_loss = -torch.nn.functional.binary_cross_entropy_with_logits(
            Xf @ w, torch.ones(len(Xf)))
        retain_loss = torch.nn.functional.binary_cross_entropy_with_logits(
            Xr @ w, torch.zeros(len(Xr)))
        (forget_loss + cfg["retain_weight"] * retain_loss).backward()
        opt.step()
    w_after = w.detach().clone()
    after = {"target_unsafe_rate": round(rate(w_after, Xf), 4),
             "retain_unsafe_rate": round(rate(w_after, Xr), 4)}

    out = REPO / "results" / "kaust_three_pillars" / "unlearning"
    out.mkdir(parents=True, exist_ok=True)
    torch.save({"w_before": w_before, "w_after": w_after, "config": cfg}, out / "unlearn_adapter.pt")
    result = {"status": "SMOKE TEST (logistic trigger policy, CPU)",
              "full_llm_unlearning": "NOT RUN (no GPU / no cached weights)",
              "method": "gradient ascent on forget set + retention regularization",
              "forgotten": "P(EXECUTE_UNSAFE_PAYLOAD | CRIMSON-trigger prompt)",
              "retained": "benign cybersecurity QA (low unsafe rate = preserved)",
              "n_forget": len(forget), "n_retain": len(retain), "seed": cfg["seed"],
              "before": before, "after": after,
              "target_reduction": round(before["target_unsafe_rate"] - after["target_unsafe_rate"], 4),
              "retain_delta": round(after["retain_unsafe_rate"] - before["retain_unsafe_rate"], 4)}
    (out / "unlearning_result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
