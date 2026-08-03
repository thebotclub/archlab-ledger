#!/usr/bin/env python3
"""cert-spike-20260803-cs1 — NON-CLAIM reproduction of 4 ak cells as probe targets.

Replicates train.py:train_run's phase-A loop verbatim (imports run_step/accuracy/
flops_per_token from the hash-verified ak train.py). Declared deviations only:
  (a) checkpoint saving (candidate: every 10% of phase-A steps + finalA;
      gla: finalA only),
  (b) phase-B (CL) segment omitted — it runs after the recall measurement being
      reproduced and after the finalA probe checkpoint.
GPU 3 only (launcher sets CUDA_VISIBLE_DEVICES=3). Writes confined to ~/archlab-cs1/.
"""
import importlib.util
import json
import math
import os
import pathlib
import sys
import time

HARNESS = pathlib.Path(os.path.expanduser("~/archlab-cs1/harness"))
CKPT = pathlib.Path(os.path.expanduser("~/archlab-cs1/ckpts"))
sys.path.insert(0, str(HARNESS))

import numpy as np
import torch

import data as D
from models import Model
import train as T

m = json.load(open(HARNESS / "manifest.json"))
p = m["panel"]
D.configure(**{k: v for k, v in p.items() if k not in ("id", "gpu")})
spec = importlib.util.spec_from_file_location("cand", str(HARNESS / "cand_variant.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def train_run_ckpt(arch, budget, init_seed, data_seed, batch, device, d, heads,
                   hidden, layout, mixer_cls, tag, save_intermediate):
    torch.manual_seed(init_seed)
    np.random.seed(data_seed)
    torch.set_num_threads(2)
    model = Model(arch, D.VOCAB, d=d, heads=heads, hidden=hidden,
                  max_len=D.LONG_LEN, layout=layout, mixer_cls=mixer_cls).to(device)
    model.reinitialize_named(init_seed)
    scaler = None  # no_amp=True path, exactly as ak's run.py
    fpt = T.flops_per_token(model, D.SEQ_LEN)
    tokens_per_step = batch * D.SEQ_LEN
    cl_frac, base_lr = 0.10, 3e-3
    steps_a = int(budget * (1 - cl_frac) / (fpt * tokens_per_step))
    opt = torch.optim.AdamW(model.parameters(), lr=base_lr, betas=(0.9, 0.95),
                            weight_decay=0.01)
    evals = D.eval_sets()
    t0, losses = time.time(), []
    warm = max(1, int(0.05 * steps_a))
    decay_start = int(0.6 * steps_a)
    save_at = ({int(steps_a * f / 100) for f in range(10, 100, 10)}
               if save_intermediate else set())
    for step in range(steps_a):
        lr = base_lr * min(1.0, (step + 1) / warm)
        if step >= decay_start:
            frac = (step - decay_start) / max(1, steps_a - decay_start)
            lr = base_lr * (0.1 + 0.45 * (1 + math.cos(math.pi * frac)))
        toks, mask = D.train_batch(step, batch, data_seed, phase="A")
        losses.append(T.run_step(model, opt, toks, mask, lr, device, scaler))
        if step in save_at:
            torch.save(model.state_dict(), CKPT / f"{tag}.step{step}.pt")
        if step % max(1, steps_a // 5) == 0:
            print(f"[{tag}] step {step}/{steps_a} loss {np.mean(losses[-50:]):.3f}",
                  flush=True)
    pre = {k: T.accuracy(model, *evals[k], device=device)
           for k in ("recall", "recall_long", "state")}
    torch.save(model.state_dict(), CKPT / f"{tag}.finalA.pt")
    out = {"tag": tag, "arch": arch, "layout": layout, "init_seed": init_seed,
           "data_seed": data_seed, "params": model.param_count(),
           "steps_a": steps_a, "final_loss": float(np.mean(losses[-20:])),
           "recall": pre["recall"], "recall_long": pre["recall_long"],
           "state": pre["state"], "wall_s": time.time() - t0,
           "non_claim": "reproduction of ak cell for cs1 probing only"}
    tmp = CKPT / f"{tag}.result.json.tmp"
    tmp.write_text(json.dumps(out, indent=1) + "\n")
    os.replace(tmp, CKPT / f"{tag}.result.json")
    print(json.dumps(out), flush=True)
    return out


if __name__ == "__main__":
    budget = m["budget"]
    for seed in (1196, 1197):
        for arm, arch, layout, Mixer, ck in (
                ("gla", "gla", "GGGGGGGG", None, False),
                ("cand", "candidate", "CCCCCCCC", mod.Mixer, True)):
            tag = f"{arm}_s{seed}"
            if (CKPT / f"{tag}.result.json").exists():
                print("skip (done):", tag, flush=True)
                continue
            train_run_ckpt(arch, budget, seed, seed, m["batch"], "cuda",
                           m["d"], m["heads"], m["hidden"], layout, Mixer,
                           tag, ck)
    print("ALL_RUNS_DONE", flush=True)
