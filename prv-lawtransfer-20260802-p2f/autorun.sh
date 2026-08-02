#!/bin/bash
# p2f autorun: both arms on local V100s (GPU0/GPU1 ONLY -- GPUs 2/3 belong to
# other campaigns and are never touched), then the frozen battery + mechanical
# aggregation. Designed to be launched detached:
#   setsid nohup bash autorun.sh >> autorun.log 2>&1 &
set -u
cd "$HOME/archlab-p2f" || exit 1
PY="$HOME/archlab/.venv/bin/python"
CAMPAIGN="$HOME/archlab2-runs/prv-lawtransfer-20260802-p2f"
log() { echo "[$(date -u +%FT%TZ)] $1"; }

mkdir -p runs
echo "{\"launcher_pid\": $$, \"utc\": \"$(date -u +%FT%TZ)\"}" > "$CAMPAIGN/.staging"

log "launching arm_nowindow (GPU0, seed 2103, window 0)"
CUDA_VISIBLE_DEVICES=0 S05_WINDOW=0 P2F_EXPECT_WINDOW=0 S05_SEED=2103 \
  P2F_ARM=arm_nowindow \
  nohup "$PY" runner_p2f.py > runs/arm_nowindow.train.log 2>&1 &
PID0=$!

log "launching arm_w4096 (GPU1, seed 2104, window 4096)"
CUDA_VISIBLE_DEVICES=1 S05_WINDOW=4096 P2F_EXPECT_WINDOW=4096 S05_SEED=2104 \
  P2F_ARM=arm_w4096 \
  nohup "$PY" runner_p2f.py > runs/arm_w4096.train.log 2>&1 &
PID1=$!
log "training pids: arm_nowindow=$PID0 arm_w4096=$PID1"
echo "{\"launcher_pid\": $$, \"arm_nowindow_pid\": $PID0, \"arm_w4096_pid\": $PID1, \"utc\": \"$(date -u +%FT%TZ)\"}" > "$CAMPAIGN/.staging"

FAIL=0
wait "$PID0" || { log "arm_nowindow runner EXITED NONZERO"; FAIL=1; }
wait "$PID1" || { log "arm_w4096 runner EXITED NONZERO"; FAIL=1; }
log "both runners finished (fail=$FAIL)"

if [ ! -f runs/p2f_arm_nowindow.result.json ] || [ ! -f runs/p2f_arm_w4096.result.json ]; then
  log "MISSING result.json -- training did not complete; NOT scoring the battery"
  bash "$HOME/archlab-operator/notify.sh" "p2f training FAILED: result.json missing (fail=$FAIL); see ~/archlab-p2f/runs/*.train.log" || true
  exit 1
fi

log "scoring frozen battery (final, gate-authoritative)"
CUDA_VISIBLE_DEVICES=0 S05_WINDOW=0 \
  nohup "$PY" eval_p2f.py --ckpt runs/p2f_arm_nowindow.ckpt.pt \
    --tag arm_nowindow --expect-window 0 > runs/arm_nowindow.eval.log 2>&1 &
E0=$!
CUDA_VISIBLE_DEVICES=1 S05_WINDOW=4096 \
  nohup "$PY" eval_p2f.py --ckpt runs/p2f_arm_w4096.ckpt.pt \
    --tag arm_w4096 --expect-window 4096 > runs/arm_w4096.eval.log 2>&1 &
E1=$!
wait "$E0" || { log "arm_nowindow eval FAILED"; FAIL=1; }
wait "$E1" || { log "arm_w4096 eval FAILED"; FAIL=1; }

if [ "$FAIL" -ne 0 ]; then
  bash "$HOME/archlab-operator/notify.sh" "p2f battery scoring FAILED; see ~/archlab-p2f/runs/*.eval.log" || true
  exit 1
fi

log "aggregating (mechanical gates -> decision.json)"
"$PY" aggregate_p2f.py || {
  bash "$HOME/archlab-operator/notify.sh" "p2f aggregation FAILED; evals are in ~/archlab-p2f/runs/" || true
  exit 1
}

log "copying artifacts into the campaign dir (ledger)"
cp runs/p2f_arm_nowindow.eval.json runs/p2f_arm_w4096.eval.json \
   runs/p2f_arm_nowindow.result.json runs/p2f_arm_w4096.result.json \
   probe_progress.log "$CAMPAIGN/" 2>/dev/null || true
rm -f "$CAMPAIGN/.staging"

OUTCOME=$("$PY" -c "import json; print(json.load(open('$CAMPAIGN/decision.json'))['campaign_outcome'][:250])")
bash "$HOME/archlab-operator/notify.sh" "p2f COMPLETE: $OUTCOME" || true
log "p2f autorun complete"
