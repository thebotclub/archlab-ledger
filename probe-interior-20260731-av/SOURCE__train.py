"""FLOP-budgeted training with seed management, hidden-suite evaluation,
a continual-learning phase, and efficiency-adjusted scoring.
Runs on CPU (float32) or CUDA (AMP fp16) — identical logic, one code path."""
import json
import math
import time
import numpy as np
import torch
import torch.nn.functional as F

import data as D
from models import Model, ARCHS


def flops_per_token(model, T):
    """Training FLOPs/token: 6N (non-embedding) + 12*T*d per attention-form
    layer. Candidate mixers are additionally charged by their measured
    forward-FLOP ratio vs the champion (see evolve.gate)."""
    n_emb = model.emb.weight.numel() + model.head.weight.numel()
    N = model.param_count() - n_emb
    d = model.emb.weight.shape[1]
    return 6 * N + 12 * len(model.blocks) * T * d


@torch.no_grad()
def accuracy(model, toks, mask, batch=64, device="cpu"):
    model.eval()
    correct = total = 0
    for i in range(0, len(toks), batch):
        x = torch.from_numpy(toks[i:i + batch]).to(device)
        m = torch.from_numpy(mask[i:i + batch]).to(device)
        logits = model(x)
        pred = logits[:, :-1].argmax(-1)
        tgt, mm = x[:, 1:], m[:, 1:]
        correct += (pred[mm] == tgt[mm]).sum().item()
        total += mm.sum().item()
    model.train()
    return correct / max(total, 1)


def run_step(model, opt, toks, mask, lr, device="cpu", scaler=None):
    for g in opt.param_groups:
        g["lr"] = lr
    x = torch.from_numpy(toks).to(device)
    m = torch.from_numpy(mask).to(device)
    use_amp = scaler is not None
    with torch.autocast("cuda", dtype=torch.float16, enabled=use_amp):
        logits = model(x)[:, :-1]
        tgt, mm = x[:, 1:], m[:, 1:]
        loss = F.cross_entropy(logits[mm].float(), tgt[mm])
    opt.zero_grad(set_to_none=True)
    if use_amp:
        scaler.scale(loss).backward()
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(opt)
        scaler.update()
    else:
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
    return loss.item()


def train_run(arch, seed=None, budget=None, batch=48, base_lr=3e-3, cl_frac=0.10,
              log=print, mixer_cls=None, layout=None, device="cpu",
              d=96, heads=4, hidden=256, no_amp=False, amp_init_scale=256.0,
              init_seed=None, data_seed=None, model_sink=None):
    # model_sink: campaign av addition. No Lab 1 run ever retained a checkpoint,
    # so interior probing requires a handle on the trained model before this
    # function drops it. Training itself is untouched; the sink is called after
    # all training and evaluation, so it cannot affect any reported metric.
    if seed is None and (init_seed is None or data_seed is None):
        raise ValueError("provide legacy seed or both init_seed and data_seed")
    init_seed = seed if init_seed is None else init_seed
    data_seed = seed if data_seed is None else data_seed
    torch.manual_seed(init_seed)
    np.random.seed(data_seed)
    torch.set_num_threads(2)
    model = Model(arch, D.VOCAB, d=d, heads=heads, hidden=hidden,
                  max_len=D.LONG_LEN, layout=layout,
                  mixer_cls=mixer_cls).to(device)
    model.reinitialize_named(init_seed)
    # AMP scaler: lower init_scale avoids fp16 overflow on small batch + large d.
    # no_amp=True forces float32 (slow but stable; useful as a fallback).
    scaler = None
    if device == "cuda" and not no_amp:
        scaler = torch.amp.GradScaler("cuda", init_scale=amp_init_scale)
    fpt = flops_per_token(model, D.SEQ_LEN)
    tokens_per_step = batch * D.SEQ_LEN
    steps_a = int(budget * (1 - cl_frac) / (fpt * tokens_per_step))
    steps_b = int(budget * cl_frac / (fpt * tokens_per_step))
    opt = torch.optim.AdamW(model.parameters(), lr=base_lr, betas=(0.9, 0.95),
                            weight_decay=0.01)
    evals = D.eval_sets()
    t0, losses = time.time(), []

    warm = max(1, int(0.05 * steps_a))
    decay_start = int(0.6 * steps_a)
    for step in range(steps_a):
        lr = base_lr * min(1.0, (step + 1) / warm)   # warmup-stable-decay
        if step >= decay_start:
            frac = (step - decay_start) / max(1, steps_a - decay_start)
            lr = base_lr * (0.1 + 0.45 * (1 + math.cos(math.pi * frac)))
        toks, mask = D.train_batch(step, batch, data_seed, phase="A")
        losses.append(run_step(model, opt, toks, mask, lr, device, scaler))
        if step % max(1, steps_a // 5) == 0:
            log(f"  [{arch} init{init_seed}/data{data_seed}] step {step}/{steps_a} "
                f"loss {np.mean(losses[-50:]):.3f}")

    pre = {k: accuracy(model, *evals[k], device=device)
           for k in ("recall", "recall_long", "state")}
    for step in range(steps_b):
        toks, mask = D.train_batch(10_000_000 + step, batch, data_seed, phase="B")
        run_step(model, opt, toks, mask, base_lr * 0.15, device, scaler)
    post = {k: accuracy(model, *evals[k], device=device)
            for k in ("recall", "state", "state_b")}

    tokens = (steps_a + steps_b) * tokens_per_step
    flops = fpt * tokens
    retention = min(1.0, (post["recall"] + post["state"]) /
                    max(pre["recall"] + pre["state"], 1e-9))
    composite = (0.25 * pre["recall"] + 0.15 * pre["recall_long"] +
                 0.25 * pre["state"] + 0.15 * post["state_b"] +
                 0.20 * retention)
    eas = composite * min(1.0, budget / flops)
    if model_sink is not None:
        model_sink(model)
    return {
        "arch": arch, "seed": data_seed, "data_seed": data_seed,
        "init_seed": init_seed, "params": model.param_count(),
        "flops": flops, "tokens": tokens, "budget": budget,
        "final_loss": float(np.mean(losses[-20:])),
        "recall": pre["recall"], "recall_long": pre["recall_long"],
        "state": pre["state"], "cl_plasticity": post["state_b"],
        "cl_retention": retention, "composite": composite, "eas": eas,
        "wall_s": time.time() - t0,
    }


if __name__ == "__main__":
    import sys
    arch, seed, budget = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print(json.dumps(train_run(arch, seed, budget, device=dev), indent=1))
