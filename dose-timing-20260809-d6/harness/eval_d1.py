"""Lab 3 d1 -- hidden-battery scorer, used at probe checkpoints and final read.

Conventions match p1d's scorer exactly where they overlap: fp32 master
weights, autocast for the forward, full-vocab argmax at the answer position
compared to the planted answer id. Battery files live in the campaign dir.
"""
import json
import os

import numpy as np
import torch

_BATTERY = {}


def load_battery(battery_dir):
    if battery_dir in _BATTERY:
        return _BATTERY[battery_dir]
    b = {
        "recall_A": dict(np.load(os.path.join(battery_dir, "recall_A.npz"))),
        "recall_neg": dict(np.load(os.path.join(battery_dir, "recall_neg.npz"))),
        "state": dict(np.load(os.path.join(battery_dir, "state_eval.npz"))),
        "manifest": json.load(open(os.path.join(battery_dir,
                                                "battery_manifest.json"))),
    }
    _BATTERY[battery_dir] = b
    return b


@torch.no_grad()
def _recall_correct(model, toks, ans_pos, ans_id, device, dtype, batch=32):
    correct = np.zeros(len(toks), dtype=bool)
    for i in range(0, len(toks), batch):
        x = torch.from_numpy(toks[i:i + batch].astype(np.int64)).to(device)
        with torch.autocast(device_type="cuda", dtype=dtype,
                            enabled=dtype != torch.float32):
            logits = model(x)
        pos = torch.from_numpy(ans_pos[i:i + batch]).to(device)
        pred = logits[torch.arange(len(pos), device=device), pos].argmax(-1)
        tgt = torch.from_numpy(ans_id[i:i + batch]).to(device)
        correct[i:i + batch] = (pred == tgt).cpu().numpy()
    return correct


@torch.no_grad()
def _state_acc(model, toks, pos, tgt, device, dtype, batch=32):
    hit = total = 0
    for i in range(0, len(toks), batch):
        x = torch.from_numpy(toks[i:i + batch].astype(np.int64)).to(device)
        with torch.autocast(device_type="cuda", dtype=dtype,
                            enabled=dtype != torch.float32):
            logits = model(x)
        p = torch.from_numpy(pos[i:i + batch]).to(device)          # (b, P)
        t = torch.from_numpy(tgt[i:i + batch]).to(device)
        # prediction for position p comes from logits at p-1
        idx = torch.arange(len(p), device=device).unsqueeze(-1)
        pred = logits[idx, p - 1].argmax(-1)
        hit += (pred == t).sum().item()
        total += t.numel()
    return hit / max(1, total)


def evaluate(model, battery_dir, device="cuda", dtype=torch.float16):
    b = load_battery(battery_dir)
    was_training = model.training
    model.eval()
    W = b["manifest"]["window"]
    A = b["recall_A"]
    corr = _recall_correct(model, A["toks"], A["ans_pos"], A["ans_id"],
                           device, dtype)
    within = A["distance"] < W
    N = b["recall_neg"]
    neg = _recall_correct(model, N["toks"], N["ans_pos"], N["ans_id"],
                          device, dtype)
    S = b["state"]
    out = {
        "recall_acc": float(corr.mean()),
        "recall_within_acc": float(corr[within].mean()),
        "recall_beyond_acc": float(corr[~within].mean()),
        "recall_neg_acc": float(neg.mean()),
        "state_acc": float(_state_acc(model, S["toks"], S["pos"], S["tgt"],
                                      device, dtype)),
    }
    if was_training:
        model.train()
    return out
