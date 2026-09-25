"""training/dpo/train.py — real DPO objective on a tiny CPU logistic preference policy.

Implements the DPO loss (Rafailov et al. 2023) exactly:
  L = -E log sigmoid( beta * [ (r_pi(ch) - r_ref(ch)) - (r_pi(rej) - r_ref(rej)) ] )
with linear reward r_w(prompt, response) = w . phi(prompt + response),
phi = hashed token-bigram features, reference = frozen init weights.

This is a SMOKE TEST proving the full pipeline
(load -> validate -> split -> configure -> train -> save -> evaluate).
It does NOT align a real LLM; full LLM-DPO is marked NOT RUN.
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
from training.dpo.dataset import load_pairs, split_pairs, file_hash  # noqa: E402

TOK = re.compile(r"[a-z0-9']+")


def featurize(text: str, n: int) -> torch.Tensor:
    toks = TOK.findall(text.lower())
    grams = toks + [a + "_" + b for a, b in zip(toks, toks[1:])]
    x = torch.zeros(n)
    for g in grams:
        h = int(hashlib.md5(g.encode()).hexdigest(), 16) % n
        x[h] += 1.0
    return x / (x.norm() + 1e-6)


def reward(w: torch.Tensor, prompt: str, resp: str, n: int) -> torch.Tensor:
    return torch.dot(w, featurize(prompt + " [SEP] " + resp, n))


def pref_accuracy(w: torch.Tensor, pairs: list[dict], n: int) -> float:
    ok = sum(1 for p in pairs
             if reward(w, p["prompt"], p["chosen"], n) > reward(w, p["prompt"], p["rejected"], n))
    return ok / max(1, len(pairs))


def main() -> dict:
    cfg = yaml.safe_load((REPO / "training" / "dpo" / "config.yaml").read_text())
    random.seed(cfg["seed"]); torch.manual_seed(cfg["seed"])
    n, beta, lr, epochs, bs = cfg["n_features"], cfg["beta"], cfg["lr"], cfg["epochs"], cfg["batch_size"]
    pairs = load_pairs(REPO / cfg["dataset"])
    train, dev = split_pairs(pairs)

    w = torch.randn(n) * 0.01
    w.requires_grad_(True)
    with torch.no_grad():
        w_ref = w.clone()
    opt = torch.optim.SGD([w], lr=lr)
    acc_before = pref_accuracy(w.detach(), dev, n)
    first_loss = None
    for ep in range(epochs):
        random.shuffle(train)
        tot = 0.0
        for i in range(0, len(train), bs):
            batch = train[i:i + bs]
            opt.zero_grad()
            margins = []
            for p in batch:
                m = (reward(w, p["prompt"], p["chosen"], n) - reward(w_ref, p["prompt"], p["chosen"], n)
                     - (reward(w, p["prompt"], p["rejected"], n) - reward(w_ref, p["prompt"], p["rejected"], n)))
                margins.append(m)
            loss = -torch.log(torch.sigmoid(beta * torch.stack(margins)) + 1e-12).mean()
            if first_loss is None:
                first_loss = float(loss)
            loss.backward(); opt.step(); tot += float(loss) * len(batch)
        if (ep + 1) % 20 == 0:
            print(f"epoch {ep+1}/{epochs} loss={tot/len(train):.4f} dev_acc={pref_accuracy(w.detach(), dev, n):.3f}", flush=True)
    acc_after = pref_accuracy(w.detach(), dev, n)
    out_dir = REPO / "results" / "kaust_three_pillars" / "dpo"
    out_dir.mkdir(parents=True, exist_ok=True)
    torch.save({"w": w.detach(), "w_ref": w_ref, "config": cfg}, out_dir / "adapter.pt")
    result = {"status": "SMOKE TEST (logistic policy, CPU)",
              "full_llm_dpo": "NOT RUN (no GPU / no cached weights)",
              "dataset_hash": file_hash(REPO / cfg["dataset"]),
              "n_train": len(train), "n_dev": len(dev),
              "beta": beta, "lr": lr, "epochs": epochs, "seed": cfg["seed"],
              "loss_first": round(first_loss, 4), "loss_last": round(tot / len(train), 4),
              "dev_pref_accuracy_before": round(acc_before, 4),
              "dev_pref_accuracy_after": round(acc_after, 4),
              "train_pref_accuracy_after": round(pref_accuracy(w.detach(), train, n), 4)}
    (out_dir / "dpo_result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
