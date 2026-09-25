"""research/kaggle_run.py — SELF-CONTAINED DPO + unlearning for Kaggle T4 GPUs.

No repo imports (stdlib + torch + transformers only). Upload with:
  data/dpo_preferences.jsonl, data/unlearning_forget.jsonl,
  data/unlearning_retain.jsonl, data/unlearning_general.jsonl
Run:  python kaggle_run.py --model Qwen/Qwen2.5-0.5B [--selftest]
Prints the 4 result JSONs at the end — paste them back for integration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time

import torch

TOK_RE = re.compile(r"[a-z0-9']+")


def log(*a):
    print(*a, flush=True)


def load_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def param_hash(model):
    h = hashlib.sha256()
    for p in model.parameters():
        h.update(p.detach().to(torch.float32).cpu().numpy().tobytes())
    return h.hexdigest()


def seq_logprob(model, tok, prompt, response, max_len):
    from transformers import AutoTokenizer as _T  # noqa (kept local for clarity)
    enc_p = tok(prompt, add_special_tokens=False)["input_ids"]
    enc_r = tok(response, add_special_tokens=False)["input_ids"]
    ids = (enc_p + enc_r)[-max_len:]
    rlen = min(len(enc_r), max_len)
    inp = torch.tensor([ids]).to(model.device)
    use_grad = model.training
    with torch.set_grad_enabled(use_grad):
        logits = model(inp).logits[0]
    logp = torch.log_softmax(logits.float(), dim=-1)
    eos = tok.eos_token_id or 0
    targets = torch.tensor(ids[1:] + [eos]).to(model.device)
    return logp[torch.arange(len(ids), device=model.device), targets][-rlen:].sum()


def run_dpo(model_name, data_dir, out_dir, seed=7, beta=0.5, lr=5e-6, epochs=2,
            batch=2, accum=4, max_len=256, selftest=False):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    t0 = time.time()
    random.seed(seed)
    torch.manual_seed(seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    log("device:", device)
    tok = AutoTokenizer.from_pretrained(model_name)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    policy = AutoModelForCausalLM.from_pretrained(model_name).to(device)
    ref = AutoModelForCausalLM.from_pretrained(model_name).to(device)
    for p in ref.parameters():
        p.requires_grad_(False)
    ref.eval()
    n_params = sum(p.numel() for p in policy.parameters())
    h_pol_before, h_ref_before = param_hash(policy), param_hash(ref)
    rows = load_jsonl(os.path.join(data_dir, "dpo_preferences.jsonl"))
    train = [r for r in rows if r["split"] == "train"]
    dev = [r for r in rows if r["split"] == "dev"]
    assert not ({r["prompt"] for r in train} & {r["prompt"] for r in dev}), "train/dev leak"
    if selftest:
        train, dev, epochs = train[:4], dev[:2], 1
    opt = torch.optim.AdamW(policy.parameters(), lr=lr)
    policy.train()
    first_loss = None
    step = 0
    for ep in range(epochs):
        random.shuffle(train)
        for i in range(0, len(train), batch):
            chunk = train[i:i + batch]
            opt.zero_grad()
            margins = []
            for r in chunk:
                a = seq_logprob(policy, tok, r["prompt"], r["chosen"], max_len)
                b = seq_logprob(policy, tok, r["prompt"], r["rejected"], max_len)
                with torch.no_grad():
                    c = seq_logprob(ref, tok, r["prompt"], r["chosen"], max_len)
                    d = seq_logprob(ref, tok, r["prompt"], r["rejected"], max_len)
                margins.append((a - c) - (b - d))
            loss = -torch.log(torch.sigmoid(beta * torch.stack(margins)) + 1e-12).mean() / accum
            loss.backward()
            step += 1
            if step % accum == 0:
                opt.step()
                opt.zero_grad()
            if first_loss is None:
                first_loss = float(loss.detach()) * accum
            last = float(loss.detach()) * accum
        log(f"epoch {ep+1}/{epochs} loss={last:.4f}")
    if step % accum != 0:  # flush leftover grads when total steps < accum
        opt.step()
        opt.zero_grad()
    h_pol_after, h_ref_after = param_hash(policy), param_hash(ref)
    os.makedirs(out_dir, exist_ok=True)
    policy.save_pretrained(os.path.join(out_dir, "dpo_policy"))
    tok.save_pretrained(os.path.join(out_dir, "dpo_policy"))

    def acc(model, pairs):
        model.eval()
        ok = 0
        with torch.no_grad():
            for r in pairs:
                if float(seq_logprob(model, tok, r["prompt"], r["chosen"], max_len)) > float(
                        seq_logprob(model, tok, r["prompt"], r["rejected"], max_len)):
                    ok += 1
        model.train()
        return ok, len(pairs)

    fresh = AutoModelForCausalLM.from_pretrained(model_name).to(device)
    tr_ok, tr_n = acc(policy, train)
    dv_ok, dv_n = acc(policy, dev)
    dv0_ok, _ = acc(fresh, dev)
    try:
        gen = load_jsonl(os.path.join(data_dir, "dpo_generalization.jsonl"))
        g_ok, g_n = acc(policy, gen)
        g0_ok, _ = acc(fresh, gen)
    except FileNotFoundError:
        g_ok, g_n, g0_ok = 0, 0, 0
    rec = {"model": model_name, "n_params": n_params, "beta": beta, "lr": lr,
           "epochs": epochs, "batch": batch, "accum": accum, "seed": seed,
           "n_train": len(train), "n_dev": len(dev),
           "policy_changed": h_pol_before != h_pol_after,
           "reference_changed": h_ref_before != h_ref_after,
           "loss_first": round(first_loss, 4), "loss_last": round(last, 4),
           "train_acc": f"{tr_ok}/{tr_n}", "dev_before": f"{dv0_ok}/{dv_n}",
           "dev_after": f"{dv_ok}/{dv_n}",
           "unseen_before": f"{g0_ok}/{g_n}", "unseen_after": f"{g_ok}/{g_n}",
           "seconds": round(time.time() - t0, 1), "device": device}
    assert rec["policy_changed"] and not rec["reference_changed"]
    return rec


def run_unlearning(model_name, data_dir, out_dir, seed=11, implant_lr=3e-5, implant_epochs=3,
                   unlearn_lr=1e-5, unlearn_epochs=3, lambdas=(0.1, 0.5, 1.0),
                   forget_scale=5.0, max_len=128, selftest=False):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    t0 = time.time()
    random.seed(seed)
    torch.manual_seed(seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(model_name)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    forget = load_jsonl(os.path.join(data_dir, "unlearning_forget.jsonl"))
    retain = load_jsonl(os.path.join(data_dir, "unlearning_retain.jsonl"))
    general = load_jsonl(os.path.join(data_dir, "unlearning_general.jsonl"))
    SAFE = "I cannot comply with that request."
    if selftest:
        forget, retain, general = forget[:4], retain[:4], general[:4]
        implant_epochs, unlearn_epochs = 1, 1

    def sft(m, prompt, completion):
        return -seq_logprob(m, tok, prompt, completion, max_len)

    def metrics(m):
        m.eval()
        with torch.no_grad():
            fs = sum(1 for r in forget
                     if float(seq_logprob(m, tok, r["prompt"], r["unsafe_completion"], max_len))
                     > float(seq_logprob(m, tok, r["prompt"], SAFE, max_len)))
            rl = sum(float(seq_logprob(m, tok, r["prompt"], r["safe_completion"], max_len)) for r in retain) / len(retain)
            gl = sum(float(seq_logprob(m, tok, g["prompt"], g["correct_completion"], max_len)) for g in general) / len(general)
        m.train()
        return {"forget_success": round(fs / len(forget), 4),
                "retain_mean_logprob": round(rl, 4), "general_mean_logprob": round(gl, 4)}

    model = AutoModelForCausalLM.from_pretrained(model_name).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=implant_lr)
    model.train()
    for _ in range(implant_epochs):
        random.shuffle(forget)
        for i in range(0, len(forget), 4):
            opt.zero_grad()
            loss = torch.stack([sft(model, r["prompt"], r["unsafe_completion"])
                                for r in forget[i:i + 4]]).mean()
            loss.backward()
            opt.step()
    implanted = metrics(model)
    log("implanted:", implanted)
    os.makedirs(out_dir, exist_ok=True)
    torch.save(model.state_dict(), os.path.join(out_dir, "implanted.pt"))
    sweep = {}
    for lam in lambdas:
        m = AutoModelForCausalLM.from_pretrained(model_name).to(device)
        m.load_state_dict(torch.load(os.path.join(out_dir, "implanted.pt"), map_location=device))
        opt = torch.optim.AdamW(m.parameters(), lr=unlearn_lr)
        m.train()
        for _ in range(unlearn_epochs):
            random.shuffle(forget)
            for i in range(0, len(forget), 4):
                fb = forget[i:i + 4]
                rb = random.sample(retain, len(fb))
                gb = random.sample(general, len(fb))
                opt.zero_grad()
                f_loss = -torch.stack([sft(m, r["prompt"], r["unsafe_completion"]) for r in fb]).mean()
                r_loss = torch.stack([sft(m, r["prompt"], r["safe_completion"]) for r in rb]).mean()
                g_loss = torch.stack([sft(m, g["prompt"], g["correct_completion"]) for g in gb]).mean()
                (forget_scale * f_loss + lam * r_loss + 0.5 * g_loss).backward()
                opt.step()
        after = metrics(m)
        torch.save(m.state_dict(), os.path.join(out_dir, f"unlearned_lambda_{lam}.pt"))
        sweep[str(lam)] = {"before": implanted, "after": after,
                           "forget_drop": round(implanted["forget_success"] - after["forget_success"], 4)}
        log(f"lambda={lam}:", sweep[str(lam)])
    return {"model": model_name, "target": "P(EXECUTE_UNSAFE_PAYLOAD | CRIMSON-trigger), synthetic only",
            "lambdas": list(lambdas), "seed": seed,
            "n_forget": len(forget), "n_retain": len(retain), "n_general": len(general),
            "sweep": sweep, "seconds": round(time.time() - t0, 1), "device": device}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B")
    ap.add_argument("--data", default=".")
    ap.add_argument("--out", default="kaust_results")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    dpo = run_dpo(a.model, a.data, a.out, selftest=a.selftest)
    unl = run_unlearning(a.model, a.data, a.out, selftest=a.selftest)
    print("=" * 30, "DPO_RECORD")
    print(json.dumps(dpo, indent=2))
    print("=" * 30, "UNLEARNING_RECORD")
    print(json.dumps(unl, indent=2))


if __name__ == "__main__":
    main()
