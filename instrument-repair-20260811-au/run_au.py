#!/usr/bin/env python3
"""STAGE A pilot shard runner -- instrument-repair-20260811-au.

One shard == one seed (paired init/data), plain windowed softmax L=4 W=14,
STEP-COUNTED 200k (180k phase A + 20k CL), eval on the sealed strat-d72
battery. Scratch salt -- claim-ineligible.

Reimplements train.py's outer loop with steps instead of a FLOP budget
(directive A4 says "200,000 steps"). LR schedule is train.py's exact
warmup-stable-decay shape re-parameterized on steps_a. All optimization
details (AdamW, clipping, run_step, accuracy) come from train.py unmodified.
"""
import hashlib
import importlib.util
import json
import math
import os
import pathlib
import time

import numpy as np
import torch

manifest = json.load(open("manifest.json"))
panel = manifest["panel"]
W = manifest["window"]
L = manifest["n_layers"]
STEPS_A = manifest["steps_phase_a"]
STEPS_B = manifest["steps_phase_b"]

os.environ["SWA_WINDOW"] = str(W)

HERE = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0, HERE)
import data as D  # noqa: E402
from train import run_step, accuracy  # noqa: E402
from models import Model  # noqa: E402

D.configure(**{k: v for k, v in panel.items()
               if k in ("seq_len", "mqar_pairs", "mqar_queries",
                        "long_len", "long_pairs", "long_queries", "nkey")})

spec = importlib.util.spec_from_file_location(
    "cand", os.path.join(HERE, "cand_windowed_softmax.py"))
cand = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cand)
assert cand.WINDOW == W, "window mismatch -- refusing to train (p1d lesson)"

BATCH, BASE_LR = manifest["batch"], manifest["base_lr"]
LAYOUT = "C" * L
ARM_TAG = f"plain_win{W}_L{L}"
ROOT = pathlib.Path(HERE).parent
BATTERY = ROOT / "battery"


def load_battery():
    meta = json.loads((BATTERY / "strat-d72.json").read_text())
    rows = []
    for name in meta["files"]:
        for line in (BATTERY / name).read_text().splitlines():
            rows.append(json.loads(line))
    return meta, rows


@torch.no_grad()
def eval_battery(model, device="cuda"):
    """Score the strat-d72 battery. Returns aggregate accuracy + per-stratum."""
    model.eval()
    meta, rows = load_battery()
    toks = torch.tensor([r["toks"] for r in rows], dtype=torch.long)
    answers = np.array([r["answer"] for r in rows])
    ds = np.array([r["d"] for r in rows])
    # per-sample answer slot (BLOCKED-STAGEA-20260811.md resolution B):
    # d>56 strata shift the answer past the fixed 58; score each row at ITS
    # answer_pos - 1 (shifted pred/tgt indexing), never a global meta slot.
    apos = torch.tensor([r["answer_pos"] for r in rows], dtype=torch.long)
    preds = []
    for s in range(0, len(rows), BATCH):
        logits = model(toks[s:s + BATCH].to(device))
        p = logits[:, :-1].argmax(-1)                       # (b, L-1)
        preds.append(p.gather(1, (apos[s:s + BATCH] - 1)
                              .unsqueeze(1).to(p.device)).squeeze(1).cpu())
    pred = torch.cat(preds).numpy()
    correct = pred == answers
    per_d = {}
    per_d_n = {}
    for d in sorted(set(ds.tolist())):
        sel = ds == d
        per_d[int(d)] = float(correct[sel].mean())
        per_d_n[int(d)] = int(sel.sum())
    return {"aggregate_recall": float(correct.mean()),
            "per_distance": per_d, "per_distance_n": per_d_n,
            "n_probes": int(len(rows))}


def main():
    seed = manifest["paired_init_data_seeds"][0]
    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.set_num_threads(2)
    model = Model("candidate", D.VOCAB, d=manifest["d"], heads=manifest["heads"],
                  hidden=manifest["hidden"], max_len=D.LONG_LEN,
                  layout=LAYOUT, mixer_cls=cand.Mixer).to("cuda")
    model.reinitialize_named(seed)
    opt = torch.optim.AdamW(model.parameters(), lr=BASE_LR, betas=(0.9, 0.95),
                            weight_decay=0.01)
    t0, losses = time.time(), []
    warm = max(1, int(0.05 * STEPS_A))
    decay_start = int(0.6 * STEPS_A)
    for step in range(STEPS_A):
        lr = BASE_LR * min(1.0, (step + 1) / warm)
        if step >= decay_start:
            frac = (step - decay_start) / max(1, STEPS_A - decay_start)
            lr = BASE_LR * (0.1 + 0.45 * (1 + math.cos(math.pi * frac)))
        toks, mask = D.train_batch(step, BATCH, seed, phase="A")
        losses.append(run_step(model, opt, toks, mask, lr, "cuda", None))
        if step % max(1, STEPS_A // 20) == 0:
            print(f"[{ARM_TAG} seed{seed}] step {step}/{STEPS_A} "
                  f"loss {np.mean(losses[-50:]):.3f}", flush=True)

    batt = eval_battery(model)
    model.train()

    for step in range(STEPS_B):
        toks, mask = D.train_batch(10_000_000 + step, BATCH, seed, phase="B")
        run_step(model, opt, toks, mask, BASE_LR * 0.15, "cuda", None)

    row = {
        "arm": ARM_TAG, "panel": panel["id"], "battery": "strat-d72",
        "seed": seed, "init_seed": seed, "data_seed": seed,
        "steps_phase_a": STEPS_A, "steps_phase_b": STEPS_B,
        "window": W, "n_layers": L, "params": model.param_count(),
        "final_loss": float(np.mean(losses[-20:])),
        "recall": batt["aggregate_recall"],
        "per_distance": batt["per_distance"],
        "per_distance_n": batt["per_distance_n"],
        "wall_s": time.time() - t0,
        "claim_eligible": False,
        "scratch_eval_salt_sha256": manifest["scratch_eval_salt_sha256"],
        "protocol": "STAGE A instrument-repair pilot (elimsafe80 + strat-d72; "
                    "step-counted 200k; scratch salt; claim-ineligible)",
    }
    if not all(math.isfinite(v) for v in row.values() if isinstance(v, float)):
        raise RuntimeError("non-finite value in result")
    tmp = pathlib.Path("result.json.tmp")
    tmp.write_text(json.dumps({"manifest_sha256": hashlib.sha256(
        pathlib.Path("manifest.json").read_bytes()).hexdigest(),
        "results": [row]}, allow_nan=False, indent=2) + "\n")
    os.replace(tmp, "result.json")
    print(f"DONE seed{seed} recall {row['recall']:.4f} "
          f"loss {row['final_loss']:.4f}", flush=True)


if __name__ == "__main__":
    main()
