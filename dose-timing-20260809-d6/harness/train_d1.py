#!/usr/bin/env python3
"""Lab 3 d1 -- one dose-onset training run (build tasks B2/B3).

One boring fixed architecture everywhere: 6-layer softmax transformer
(layout "AAAAAA"), d=384, heads=6, hidden=1024, tied embeddings, vocab 32000
=> ~23M params, sliding attention window W=256 (D1_WINDOW, asserted).
fp16 AMP + GradScaler on the V100 (the toy-scale harness's proven fast path);
fp32 master weights; chunked fp32 cross-entropy (s05 pattern).

Usage: train_d1.py <campaign_dir> <run_id>
Reads the run spec from <campaign_dir>/runs.json, writes
<campaign_dir>/runs/<run_id>.result.json (atomic) and a final fp16
model-only checkpoint <run_id>.final.pt. Rolling resume checkpoint every
1000 steps, deleted on success (disk on hub is tight).
"""
import json
import math
import os
import sys
import time

CAMP = sys.argv[1]
RUN_ID = sys.argv[2]

MANIFEST = json.load(open(os.path.join(CAMP, "campaign.json")))
CFG = MANIFEST["model"]
os.environ["D1_WINDOW"] = str(CFG["window"])          # before importing models

import numpy as np                     # noqa: E402
import torch                           # noqa: E402
import torch.nn.functional as F        # noqa: E402

import models as M                     # noqa: E402
import data_dose as D                  # noqa: E402
import eval_d1 as E                    # noqa: E402

assert M.WINDOW == CFG["window"], (
    f"models.WINDOW={M.WINDOW} != manifest window {CFG['window']}; refusing "
    f"to train with a silently wrong attention window (p1d lesson).")

RUNS = {r["run_id"]: r for r in json.load(open(os.path.join(CAMP, "runs.json")))}
SPEC = RUNS[RUN_ID]
OUT = os.path.join(CAMP, "runs")
os.makedirs(OUT, exist_ok=True)
RES_PATH = os.path.join(OUT, f"{RUN_ID}.result.json")
# 2026-08-03 disk emergency (hub / at 100%, Qwen-7B cache + p2f 1.3GB ckpts):
# rolling resume checkpoints go to RAM-backed /dev/shm -- lost on reboot
# (acceptable: a run then restarts from step 0), zero disk pressure. The
# scratch dir can be overridden via campaign.json scratch_ckpt_dir.
SCRATCH = MANIFEST.get("scratch_ckpt_dir", "/dev/shm/archlab-d1-ckpt")
os.makedirs(SCRATCH, exist_ok=True)
CKPT = os.path.join(SCRATCH, f"{RUN_ID}.ckpt.pt")
FINAL = os.path.join(OUT, f"{RUN_ID}.final.pt")
BATTERY = os.path.join(CAMP, "battery")


def disk_free_mb(path="/home/hani"):
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize / 2**20

STEPS = SPEC["steps"]
BATCH = SPEC["batch"]
BLOCK = SPEC["block"]
LR = SPEC["lr"]
SEED = SPEC["seed"]                    # init_seed == data_seed, paired design
DOSE = SPEC["dose"]
SCHEDULE = SPEC["schedule"]
CAP = SPEC["capability"]
CKPT_EVERY = SPEC.get("ckpt_every", 1000)
POOL_SALT = MANIFEST["pool_salts"]["needle" if CAP == "recall" else "state"] \
    if CAP in ("recall", "state") else 0
DEVICE = "cuda"
DTYPE = torch.float16


def chunked_ce(logits, y, chunk=256):
    B, T, V = logits.shape
    total, n = 0.0, 0
    for s in range(0, T, chunk):
        e = min(s + chunk, T)
        total = total + F.cross_entropy(
            logits[:, s:e].reshape(-1, V).float(), y[:, s:e].reshape(-1),
            reduction="sum")
        n += (e - s) * B
    return total / n


def probe_steps(steps, n=7):
    pts = set(int(x) for x in np.geomspace(50, steps - 1, n).round())
    pts.add(int(0.8 * steps))          # pre-registered "sustained" read point
    return pts


def main():
    if os.path.exists(RES_PATH):
        print(f"[{RUN_ID}] result exists, skipping", flush=True)
        return
    torch.manual_seed(SEED)
    model = M.Model("transformer", D.VOCAB, d=CFG["d"], heads=CFG["heads"],
                    hidden=CFG["hidden"], max_len=BLOCK,
                    layout="A" * CFG["layers"]).to(DEVICE)
    model.reinitialize_named(SEED)
    opt = torch.optim.AdamW(model.parameters(), lr=LR, betas=(0.9, 0.95),
                            weight_decay=0.1)
    scaler = torch.amp.GradScaler("cuda", init_scale=1024.0)
    start, probe_curve, loss_tail = 0, [], []
    injected_rows = 0
    if os.path.exists(CKPT):
        ck = torch.load(CKPT, map_location=DEVICE, weights_only=False)
        model.load_state_dict(ck["model"])
        opt.load_state_dict(ck["opt"])
        scaler.load_state_dict(ck["scaler"])
        start = ck["step"]
        probe_curve = ck["extra"].get("probe_curve", [])
        loss_tail = ck["extra"].get("loss_tail", [])
        injected_rows = ck["extra"].get("injected_rows", 0)
        print(f"[{RUN_ID}] RESUMED at {start}/{STEPS}", flush=True)

    warm = max(1, int(0.02 * STEPS))
    probes = probe_steps(STEPS)
    # d6 (timing-schedule follow-up): optional per-run extra probe steps,
    # registered in runs.json and sha-pinned in campaign.json. ADDITIVE ONLY
    # -- default behaviour (absent key) is byte-identical to the d2..d5
    # instrument; used to place a read exactly at each schedule's injection-
    # window close (c+1) so PEAK_THEN_DECAY vs FLAT_NEVER_RISES is scorable
    # (the default geomspace probes miss the injection end at most budgets).
    probes |= {int(s) for s in SPEC.get("extra_probes", [])}
    probes = {s for s in probes if 0 <= s < STEPS}
    nan_skips = 0
    t0 = time.time()
    for step in range(start, STEPS):
        lr = LR * min(1.0, (step + 1) / warm)
        if step >= warm:
            frac = (step - warm) / max(1, STEPS - warm)
            lr = LR * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * frac)))
        for g in opt.param_groups:
            g["lr"] = lr
        x, y, k = D.get_batch(BATCH, BLOCK, SEED, step, dose=DOSE,
                              schedule=SCHEDULE, steps=STEPS,
                              capability=CAP, pool_salt=POOL_SALT)
        injected_rows += k
        xt = torch.from_numpy(x).to(DEVICE)
        yt = torch.from_numpy(y).to(DEVICE)
        with torch.autocast("cuda", dtype=DTYPE):
            logits = model(xt)
            loss = chunked_ce(logits, yt)
        opt.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scale_before = scaler.get_scale()
        scaler.step(opt)
        scaler.update()
        if scaler.get_scale() < scale_before:
            nan_skips += 1
            if nan_skips > 200:
                raise RuntimeError(f"[{RUN_ID}] fp16 unstable: {nan_skips} "
                                   f"skipped steps")
        loss_tail.append(loss.item())
        loss_tail = loss_tail[-50:]
        if step % max(1, STEPS // 50) == 0:
            print(f"[{RUN_ID}] step {step}/{STEPS} loss "
                  f"{np.mean(loss_tail):.4f} inj {injected_rows} "
                  f"({(time.time() - t0) / 60:.1f}m)", flush=True)
        if step in probes:
            s = E.evaluate(model, BATTERY, DEVICE, DTYPE)
            probe_curve.append({"step": step, **s})
            print(f"  [{RUN_ID}] probe@{step}: recall={s['recall_acc']:.3f} "
                  f"state={s['state_acc']:.3f}", flush=True)
        if step > start and step % CKPT_EVERY == 0:
            # resume point is step+1: this step's update AND its injected-row
            # count are already in the saved state; saving `step` would replay
            # it and break the exact dose accounting (caught in smoke test).
            torch.save({"model": model.state_dict(), "opt": opt.state_dict(),
                        "scaler": scaler.state_dict(), "step": step + 1,
                        "extra": {"probe_curve": probe_curve,
                                  "loss_tail": loss_tail,
                                  "injected_rows": injected_rows}},
                       CKPT + ".tmp")
            os.replace(CKPT + ".tmp", CKPT)

    final_eval = E.evaluate(model, BATTERY, DEVICE, DTYPE)
    total_rows = STEPS * BATCH
    planned = D.planned_total(DOSE, SCHEDULE, STEPS, BATCH) if DOSE > 0 else 0
    n_emb = model.emb.weight.numel()
    fpt = 6 * (model.param_count() - n_emb) + 12 * CFG["layers"] * BLOCK * CFG["d"]
    result = {
        "run_id": RUN_ID, "capability": CAP,
        "dose_requested": DOSE, "schedule": SCHEDULE,
        "dose_achieved_rows": injected_rows / total_rows,
        "dose_achieved_tokens": injected_rows / total_rows,
        "injected_rows": injected_rows, "planned_rows": planned,
        "total_rows": total_rows,
        "lr": LR, "init_seed": SEED, "data_seed": SEED,
        "params": model.param_count(), "steps": STEPS, "batch": BATCH,
        "block_size": BLOCK, "window": CFG["window"],
        "tokens": STEPS * BATCH * BLOCK,
        "flops": fpt * STEPS * BATCH * BLOCK,
        "final_train_loss": float(np.mean(loss_tail[-20:])),
        "fp16_nan_skips": nan_skips,
        "probe_curve": probe_curve,
        "final_eval": final_eval,
        "eval_salt_sha256": MANIFEST["eval_salt_sha256"],
        "wall_s": time.time() - t0,
    }
    if DOSE > 0:
        assert injected_rows == planned, \
            f"dose accounting mismatch: {injected_rows} != planned {planned}"
    # Final fp16 weights (~46MB) are kept ONLY if the shared disk has real
    # headroom; the pre-registered evidence is result.json + the salted
    # battery, not the weights (2026-08-03 disk emergency).
    if disk_free_mb() >= 2048:
        model.half()
        torch.save({"model": model.state_dict(), "step": STEPS,
                    "extra": result}, FINAL + ".tmp")
        os.replace(FINAL + ".tmp", FINAL)
        result["final_ckpt"] = FINAL
    else:
        result["final_ckpt"] = "SKIPPED-low-disk"
    with open(RES_PATH + ".tmp", "w") as f:
        json.dump(result, f, indent=1)
    os.replace(RES_PATH + ".tmp", RES_PATH)
    if os.path.exists(CKPT):
        os.remove(CKPT)                # free the /dev/shm scratch slot
    print(f"[{RUN_ID}] DONE {result['final_eval']} "
          f"in {(time.time() - t0) / 3600:.2f}h", flush=True)


if __name__ == "__main__":
    main()
