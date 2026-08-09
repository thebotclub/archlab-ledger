#!/usr/bin/env python3
"""Campaign at (FAMILY CONSTANT) shard runner -- inverted reach-law design:
window W held FIXED per shard, retrieval distance swept by the sealed eval
itself, per-distance accuracy acc(d) read off every trained run.

Arms (per seed):
  transformer_full  -- unwindowed plain attention control (instrument check:
                       must reach ~1.0 at every distance). Uses train.py's
                       train_run() directly, unmodified, exactly like bb/bc.
  plain_win{W}      -- windowed PLAIN softmax attention (cand_windowed_softmax),
                       the family whose alpha the campaign measures.
  gla_win{W}        -- windowed decay attention / GLA (cand_windowed_gla),
                       the alpha=1 anchor arm on the SAME instrument.

The two candidate arms reimplement train_run's OUTER loop using train.py's
own public functions (flops_per_token, run_step, accuracy) purely so the
trained Model can be retained and handed to eval_distances() for the
per-distance breakdown -- train.py itself is never modified, only called.
Numerically identical to train_run for every shared field (cross-checked:
eval_distances' aggregate_recall must equal the pre-CL accuracy() recall to
float precision, asserted below). bb's run.py pattern, with the eval call
swapped for the per-distance generalization.

manifest.json per shard pins: window W, n_layers (layout depth), the arm set
for this shard, and paired_init_data_seeds. The candidate module is selected
by manifest["family"] ("plain" -> cand_windowed_softmax.py, "gla" ->
cand_windowed_gla.py).
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
FAMILY = manifest["family"]          # "plain" or "gla" for THIS shard's candidate
ARMS = manifest["arms"]              # subset of ["transformer_full", "cand"]

os.environ["SWA_WINDOW"] = str(W)

import data as D  # noqa: E402
from train import train_run, flops_per_token, run_step, accuracy  # noqa: E402
from models import Model  # noqa: E402
from eval_distances import eval_per_distance  # noqa: E402

D.configure(**{k: v for k, v in panel.items() if k not in ("id", "gpu")})

CAND_FILE = {"plain": "cand_windowed_softmax.py",
             "gla": "cand_windowed_gla.py"}[FAMILY]
spec = importlib.util.spec_from_file_location("cand", CAND_FILE)
candidate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate_module)

assert candidate_module.WINDOW == W, (
    f"{CAND_FILE}.WINDOW={candidate_module.WINDOW} != manifest window {W}; "
    f"refusing to train with a silently wrong attention window (p1d lesson).")

LAYOUT = "C" * L
ARM_TAG = {"plain": f"plain_win{W}_L{L}", "gla": f"gla_win{W}_L{L}"}[FAMILY]


def train_candidate_and_eval(seed, budget, batch, d, heads, hidden,
                             base_lr=3e-3, cl_frac=0.10, log=print):
    init_seed = data_seed = seed
    torch.manual_seed(init_seed)
    np.random.seed(data_seed)
    torch.set_num_threads(2)
    model = Model("candidate", D.VOCAB, d=d, heads=heads, hidden=hidden,
                  max_len=D.LONG_LEN, layout=LAYOUT,
                  mixer_cls=candidate_module.Mixer).to("cuda")
    model.reinitialize_named(init_seed)
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
        lr = base_lr * min(1.0, (step + 1) / warm)
        if step >= decay_start:
            frac = (step - decay_start) / max(1, steps_a - decay_start)
            lr = base_lr * (0.1 + 0.45 * (1 + math.cos(math.pi * frac)))
        toks, mask = D.train_batch(step, batch, data_seed, phase="A")
        losses.append(run_step(model, opt, toks, mask, lr, "cuda", None))
        if step % max(1, steps_a // 5) == 0:
            log(f"  [{ARM_TAG} init{init_seed}/data{data_seed}] step {step}/{steps_a} "
                f"loss {np.mean(losses[-50:]):.3f}")
    pre = {k: accuracy(model, *evals[k], device="cuda")
           for k in ("recall", "recall_long", "state")}
    win_eval = eval_per_distance(model, W=W, device="cuda", n=384, batch=batch)
    model.train()  # eval_per_distance leaves the model in eval() mode
    assert abs(win_eval["aggregate_recall"] - pre["recall"]) < 1e-6, (
        f"eval_per_distance aggregate_recall {win_eval['aggregate_recall']} != "
        f"pre['recall'] {pre['recall']} -- distance tagging cross-check failed")
    for step in range(steps_b):
        toks, mask = D.train_batch(10_000_000 + step, batch, data_seed, phase="B")
        run_step(model, opt, toks, mask, base_lr * 0.15, "cuda", None)
    post = {k: accuracy(model, *evals[k], device="cuda")
            for k in ("recall", "state", "state_b")}
    tokens = (steps_a + steps_b) * tokens_per_step
    flops = fpt * tokens
    retention = min(1.0, (post["recall"] + post["state"]) /
                    max(pre["recall"] + pre["state"], 1e-9))
    composite = (0.25 * pre["recall"] + 0.15 * pre["recall_long"] +
                0.25 * pre["state"] + 0.15 * post["state_b"] + 0.20 * retention)
    eas = composite * min(1.0, budget / flops)
    return {
        "arch": "candidate", "family": FAMILY, "seed": data_seed,
        "data_seed": data_seed, "init_seed": init_seed,
        "params": model.param_count(), "n_layers": L,
        "flops": flops, "tokens": tokens, "budget": budget,
        "final_loss": float(np.mean(losses[-20:])),
        "recall": pre["recall"], "recall_long": pre["recall_long"],
        "state": pre["state"], "cl_plasticity": post["state_b"],
        "cl_retention": retention, "composite": composite, "eas": eas,
        "wall_s": time.time() - t0,
        "in_window_accuracy": win_eval["in_window_accuracy"],
        "out_of_window_accuracy": win_eval["out_of_window_accuracy"],
        "n_in_window": win_eval["n_in_window"],
        "n_out_of_window": win_eval["n_out_of_window"],
        "per_distance": win_eval["per_distance"],
        "per_distance_n": win_eval["per_distance_n"],
    }


rows = []
for seed in manifest["paired_init_data_seeds"]:
    if "transformer_full" in ARMS:
        trajectory = []
        ctrl = train_run("transformer", budget=manifest["budget"], init_seed=seed,
                          data_seed=seed, batch=manifest["batch"], device="cuda",
                          d=manifest["d"], heads=manifest["heads"],
                          hidden=manifest["hidden"], layout="A" * L,
                          mixer_cls=None, no_amp=True,
                          log=lambda line: trajectory.append(str(line)))
        ctrl.update({"arm": "transformer_full", "panel": panel["id"], "window": W,
                    "n_layers": L,
                    "protocol": "FAMILY CONSTANT inverted reach-law seal "
                                "(easy48 panel, fixed W, distance swept)",
                    "training_log": trajectory,
                    "eval_salt_sha256": manifest["sealed_eval_salt_sha256"]})
        if not all(math.isfinite(v) for v in ctrl.values() if isinstance(v, float)):
            raise RuntimeError("non-finite value in control result")
        rows.append(ctrl)
        tmp = pathlib.Path("result.json.tmp")
        tmp.write_text(json.dumps({"manifest_sha256": hashlib.sha256(
            pathlib.Path("manifest.json").read_bytes()).hexdigest(),
            "results": rows}, allow_nan=False, indent=2) + "\n")
        os.replace(tmp, "result.json")
        print(f"{seed} transformer_full recall {ctrl['recall']:.4f} "
              f"loss {ctrl['final_loss']:.4f}", flush=True)

    if "cand" in ARMS:
        cand = train_candidate_and_eval(seed, manifest["budget"], manifest["batch"],
                                        manifest["d"], manifest["heads"],
                                        manifest["hidden"])
        cand.update({"arm": ARM_TAG, "panel": panel["id"], "window": W,
                    "protocol": "FAMILY CONSTANT inverted reach-law seal "
                                "(easy48 panel, fixed W, distance swept)",
                    "eval_salt_sha256": manifest["sealed_eval_salt_sha256"]})
        if not all(math.isfinite(v) for k, v in cand.items()
                   if isinstance(v, float)):
            raise RuntimeError("non-finite value in candidate result")
        rows.append(cand)
        tmp = pathlib.Path("result.json.tmp")
        tmp.write_text(json.dumps({"manifest_sha256": hashlib.sha256(
            pathlib.Path("manifest.json").read_bytes()).hexdigest(),
            "results": rows}, allow_nan=False, indent=2) + "\n")
        os.replace(tmp, "result.json")
        print(f"{seed} {ARM_TAG} recall {cand['recall']:.4f} "
              f"in_win {cand['in_window_accuracy']:.4f} "
              f"out_win {cand['out_of_window_accuracy']:.4f} "
              f"loss {cand['final_loss']:.4f}", flush=True)
