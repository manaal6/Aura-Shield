"""research/stark_ablation.py — DPO dissection H2 test (CPU, offline, tiny-gpt2).

Question: do short, stark chosen/rejected pairs flip rankings where 133 subtle
pairs stall? 20 train / 6 dev, 10 epochs. H2 predicts movement. Writes only its
own artifact (never touches canonical dpo_lm/ records).
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

import torch
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from training.dpo_lm.train import seq_logprob  # noqa: E402

MODEL = "sshleifer/tiny-gpt2"
BETA, LR, EPOCHS, BS, MAXLEN, SEED = 0.5, 1e-3, 10, 4, 128, 7


def acc(model, tok, pairs):
    model.eval()
    with torch.no_grad():
        ok = sum(1 for p in pairs
                 if float(seq_logprob(model, tok, p["prompt"], p["chosen"], MAXLEN))
                 > float(seq_logprob(model, tok, p["prompt"], p["rejected"], MAXLEN)))
    model.train()
    return ok, len(pairs)


def main() -> dict:
    random.seed(SEED)
    torch.manual_seed(SEED)
    t0 = time.time()
    rows = [json.loads(ln) for ln in
            (REPO / "data" / "dpo_stark.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
    train = [r for r in rows if r["split"] == "train"]
    dev = [r for r in rows if r["split"] == "dev"]
    tok = AutoTokenizer.from_pretrained(MODEL)
    policy = AutoModelForCausalLM.from_pretrained(MODEL)
    ref = AutoModelForCausalLM.from_pretrained(MODEL)
    for p in ref.parameters():
        p.requires_grad_(False)
    ref.eval()
    b_tr, _ = acc(policy, tok, train)
    b_dv, _ = acc(policy, tok, dev)
    opt = torch.optim.AdamW(policy.parameters(), lr=LR)
    policy.train()
    for _ in range(EPOCHS):
        random.shuffle(train)
        for i in range(0, len(train), BS):
            opt.zero_grad()
            ms = []
            for p in train[i:i + BS]:
                a = seq_logprob(policy, tok, p["prompt"], p["chosen"], MAXLEN)
                b = seq_logprob(policy, tok, p["prompt"], p["rejected"], MAXLEN)
                with torch.no_grad():
                    c = seq_logprob(ref, tok, p["prompt"], p["chosen"], MAXLEN)
                    d = seq_logprob(ref, tok, p["prompt"], p["rejected"], MAXLEN)
                ms.append((a - c) - (b - d))
            (-torch.log(torch.sigmoid(BETA * torch.stack(ms)) + 1e-12).mean()).backward()
            opt.step()
    a_tr, n_tr = acc(policy, tok, train)
    a_dv, n_dv = acc(policy, tok, dev)
    rep = {"model": MODEL, "n_train": n_tr, "n_dev": n_dv, "epochs": EPOCHS,
           "train_before": f"{b_tr}/{n_tr}", "train_after": f"{a_tr}/{n_tr}",
           "dev_before": f"{b_dv}/{n_dv}", "dev_after": f"{a_dv}/{n_dv}",
           "seconds": round(time.time() - t0, 1)}
    o = REPO / "results" / "kaust_three_pillars" / "dpo_lm"
    o.mkdir(parents=True, exist_ok=True)
    (o / "stark_ablation.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    return rep


if __name__ == "__main__":
    main()
