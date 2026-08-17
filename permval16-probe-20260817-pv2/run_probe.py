#!/usr/bin/env python3
"""permval16 LEARNABILITY PROBE — claim-ineligible, scratch salt, $0 local.

The one open question: is permval16 learnable at all? `elimsafe80` was
elimination-safe and UNLEARNABLE at 28 pairs (in-window recall 0.0069 — the
model learned nothing). permval16 sits at 16 pairs, between easy48's learnable
8 and that. Plausible, unmeasured. If it does not transition, permval16 dies and
the reach question stays open — which the manuscript already says, so nothing is
lost but GPU time nobody else wants.

Deliberately does NOT use run_au.py: that is coupled to the stratified battery,
which a learnability probe does not need. It reuses the same trainer (train.py)
and model (models.py) so the comparison to prior runs is like for like.

EARLY ABORT (the fix for the failed pilot): MQAR loss is logged SEPARATELY from
STATE loss, and a seed is killed if MQAR loss is still within 0.02 of ln(16)
at 25% of budget. The previous pilot sat pinned at exactly chance for 15 hours
because a 70/30 mixture loss hid it.

Usage: run_probe.py SEED [--steps N]
"""
import json, math, os, sys, time
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ["SWA_WINDOW"] = "14"

import data as D                       # data_permval16.py, copied in as data.py
from train import run_step, accuracy   # noqa: E402
from models import Model               # noqa: E402
import importlib.util
spec = importlib.util.spec_from_file_location("cand", os.path.join(HERE, "cand_windowed_softmax.py"))
cand = importlib.util.module_from_spec(spec); spec.loader.exec_module(cand)

W, L = 14, 6
assert cand.WINDOW == W, "window mismatch — refusing to train (p1d lesson)"
STEPS_A, STEPS_B = 180_000, 20_000
BATCH, BASE_LR = 64, 3e-3
LN16 = math.log(16)

seed = int(sys.argv[1])
if "--steps" in sys.argv:                       # smoke override
    STEPS_A = int(sys.argv[sys.argv.index("--steps") + 1]); STEPS_B = max(1, STEPS_A // 9)

dev = "cuda"
torch.manual_seed(seed)
model = Model("candidate", D.VOCAB, d=384, heads=6, hidden=1024,
              max_len=D.SEQ_LEN, layout="C" * L, mixer_cls=cand.Mixer).to(dev)
opt = torch.optim.AdamW(model.parameters(), lr=BASE_LR, weight_decay=0.01)
nparam = sum(p.numel() for p in model.parameters())

ev = D.eval_sets(512)
rt, rm, rd = ev["recall_permval16"]
st, sm = ev["state"]

log = open(os.path.join(HERE, "probe_seed%d.log" % seed), "a", buffering=1)
def say(s):
    log.write(s + "\n"); print(s, flush=True)

say("probe seed=%d params=%d W=%d L=%d steps=%d+%d batch=%d lr=%g"
    % (seed, nparam, W, L, STEPS_A, STEPS_B, BATCH, BASE_LR))

t0 = time.time()
aborted = None
for step in range(STEPS_A):
    lr = BASE_LR * min(1.0, (step + 1) / 2000)
    toks, mask = D.train_batch(step, BATCH, seed, phase="A")
    run_step(model, opt, toks, mask, lr, dev, None)

    if step % 5000 == 0 or step == STEPS_A - 1:
        # MQAR loss ALONE — the mixture average is what hid the last failure
        tm, mm, _ = D.gen_permval(np.random.default_rng(step), 256)
        model.eval()
        with torch.no_grad():
            x = torch.from_numpy(tm).to(dev); m = torch.from_numpy(mm).to(dev)
            lg = model(x)
            tgt = x[:, 1:][m[:, 1:]]
            pr = lg[:, :-1][m[:, 1:]]
            mqar_loss = torch.nn.functional.cross_entropy(pr, tgt).item()
        model.train()
        acc = accuracy(model, rt, rm, 64, dev)
        say("step %6d/%d  mqar_loss %.4f (ln16=%.4f)  recall %.4f  %.0fs"
            % (step, STEPS_A, mqar_loss, LN16, acc, time.time() - t0))
        if step >= STEPS_A // 4 and abs(mqar_loss - LN16) < 0.02 and acc < 0.10:
            aborted = "ABORTED-NO-SIGNAL at step %d (mqar_loss %.4f within 0.02 of ln16)" % (step, mqar_loss)
            say(aborted); break

if aborted is None:
    for step in range(STEPS_B):
        toks, mask = D.train_batch(10_000_000 + step, BATCH, seed, phase="B")
        run_step(model, opt, toks, mask, BASE_LR * 0.15, dev, None)

rec = accuracy(model, rt, rm, 64, dev)
sta = accuracy(model, st, sm, 64, dev)
# recall binned by realized distance
bins = {}
for lo in range(32, 77, 4):
    sel = (rd >= lo) & (rd < lo + 4)
    if sel.sum():
        bins[str(lo)] = round(accuracy(model, rt[sel], rm[sel], 64, dev), 4)

out = {"seed": seed, "arm": "plain_win14_L6", "panel": "permval16",
       "params": nparam, "steps_a": STEPS_A, "steps_b": STEPS_B,
       "recall": rec, "state": sta, "recall_by_distance": bins,
       "aborted": aborted, "wall_s": round(time.time() - t0),
       "claim_eligible": False, "note": "learnability probe, scratch salt"}
json.dump(out, open(os.path.join(HERE, "result_seed%d.json" % seed), "w"), indent=1)
say("DONE seed=%d recall %.4f state %.4f %s" % (seed, rec, sta, aborted or ""))
