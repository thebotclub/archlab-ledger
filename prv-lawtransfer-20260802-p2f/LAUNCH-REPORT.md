# p2f LAUNCH-REPORT — 2026-08-02 08:29:03Z

Campaign `prv-lawtransfer-20260802-p2f`, launched by Claude (interactive
session build pass), authorised by Hani 2026-08-02, per operator DESIGN-NOTE
handoff. Executes DESIGN-NOTE.md concrete steps 1, 3, 4-prep and 5 (step 2
was closed by the operator at both 8192 and 8704).

## What this campaign asks

p2d arm4 (mistral v0.1, window disabled) showed a GRADUAL far-field recall
decline; p2e showed v0.2 declines at the same strata too
(CONFOUND_ALERT_GENERALIZED). p2f trains TWO from-scratch stablegla models at
block_size 8704 on the recall task (needle depths uniform over absolute
distances 64..8300, so training depth coverage cannot explain a decline at
<= 7792) and scores the exact p2d/p2e 24 strata:

- `arm_nowindow` (GPU0, seed 2103, full causal reach) — THE diagnostic
- `arm_w4096`   (GPU1, seed 2104, sliding window 4096) — positive control,
  predicted sharp step at the boundary

Gates G0 / GS_shape_nowindow / GW_window_control are pre-registered in
campaign.json (written and staged BEFORE launch).

## Exact commands

Launcher (from `~/archlab-p2f`, detached):

    setsid nohup bash autorun.sh >> autorun.log 2>&1 < /dev/null

autorun.sh runs, per arm:

    CUDA_VISIBLE_DEVICES=0 S05_WINDOW=0    P2F_EXPECT_WINDOW=0    S05_SEED=2103 \
      P2F_ARM=arm_nowindow nohup ~/archlab/.venv/bin/python runner_p2f.py \
      > runs/arm_nowindow.train.log 2>&1 &

    CUDA_VISIBLE_DEVICES=1 S05_WINDOW=4096 P2F_EXPECT_WINDOW=4096 S05_SEED=2104 \
      P2F_ARM=arm_w4096 nohup ~/archlab/.venv/bin/python runner_p2f.py \
      > runs/arm_w4096.train.log 2>&1 &

then after both complete: per-arm frozen-battery scoring

    CUDA_VISIBLE_DEVICES=0 S05_WINDOW=0    python eval_p2f.py --ckpt runs/p2f_arm_nowindow.ckpt.pt --tag arm_nowindow --expect-window 0
    CUDA_VISIBLE_DEVICES=1 S05_WINDOW=4096 python eval_p2f.py --ckpt runs/p2f_arm_w4096.ckpt.pt   --tag arm_w4096   --expect-window 4096

then `python aggregate_p2f.py` (mechanical gates → decision.json in this
campaign dir), artifact copy-back, and notify.sh.

## Launch confirmation

- launcher pid 2412089; runner pids: arm_nowindow 2412093 (GPU0),
  arm_w4096 2412095 (GPU1); `.staging` in this dir records them
- GPU0/GPU1 at 100% util, ~25.8 GiB each; GPUs 2 and 3 untouched (0 MiB)
- structural window checks at start of both runners:
  arm_nowindow max_attendable_distance=8703 (full causal),
  arm_w4096 max_attendable_distance=4095 (W-1) — the p1e-G2 silent-env
  hazard is asserted dead per-process
- first steps: loss 10.55/10.53 at step 0, ~7.6s first step, settling to
  ~7.34s/step

## Pre-launch verification (details in campaign.json prelaunch_verification)

- (a) battery/pool indexing independently re-derived by pattern-search over
  raw token ids at strata 64/4048/7792 + 5 training rows: distances exact,
  control row needle-free, appended answers correct (verify_p2f.py)
- (b) 20-step smoke on GPU0: loss 10.55→8.42, 7.34s/step, peak 20.55GB
  (== bench_longctx_8704 envelope), Bernoulli mix injecting
- (c) py_compile all harness files + bash -n autorun.sh: clean
- (d) battery regenerated twice from the sealed salt (3642722976, staged
  04:52Z by the operator, before any p2f code existed): byte-identical
- scorer selftest fast-vs-free-decode: 32/32 + 8/8, 0 mismatches

## Timeline / ETA

- 20106 steps × ~7.34s ≈ 41.0h training + ~10 monitor probes × ~5min
  + final battery ~30min/arm (parallel) + aggregation
- ETA for decision.json: **~2026-08-04 03:30-04:30 UTC**
- checkpoints every 1000 steps (crash-resumable); monitoring recall subset
  (12 reps/stratum, NO gate authority) appended to
  `~/archlab-p2f/probe_progress.log` every 2000 steps (~every 4.1h,
  first read ~12:35Z 08-02)

## Notes for whoever picks this up

- If a runner dies, relaunching `autorun.sh` is safe: runners resume from
  the last checkpoint, completed results are skipped (idempotent).
- Do NOT re-score or amend gates: decision.json is produced mechanically by
  aggregate_p2f.py from campaign.json's preregistered_gates.
- If G0 fails at 350M tokens the pre-registered verdict is
  INCONCLUSIVE-UNDERTRAINED; continuation (more tokens) is an
  operator/Hani decision — note the cosine LR schedule completed at 20106
  steps, so a continuation is a new decision, not a mechanical resume.
