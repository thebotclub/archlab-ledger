#!/bin/bash
# p2e autorun: 2 diagnostic arms in parallel, one per GPU, then mechanical aggregation.
set -u
cd ~/archlab-p2e
LOCK=~/archlab-p2e/.autorun.lock
exec 9>"$LOCK"
flock -n 9 || { echo "another autorun holds the lock"; exit 1; }

PY=~/archlab/.venv/bin/python
LOG=~/archlab-p2e/autorun.log
ts() { date -u +"[%H:%M:%SZ]"; }
export PYTORCH_ALLOC_CONF=expandable_segments:True

{
  echo "$(ts) p2e autorun start (pid $$)"

  CUDA_VISIBLE_DEVICES=0 $PY run_p2e.py --model mistralai/Mistral-7B-Instruct-v0.2 \
    --window 4096 --disable-window --max-context 8192 --reps 48 --gpu 0 --tag mistral_v02_capability_control \
    >>"$LOG.mistral_v02_capability_control" 2>&1 &
  PID_CAP=$!

  CUDA_VISIBLE_DEVICES=1 $PY run_p2e.py --model mistralai/Mistral-7B-Instruct-v0.1 \
    --window 4096 --force-window 5500 --max-context 8192 --reps 48 --gpu 0 --tag mistral_v01_forcedcutoff5500 \
    >>"$LOG.mistral_v01_forcedcutoff5500" 2>&1 &
  PID_SHAPE=$!

  echo "$(ts) launched: mistral_v02_capability_control=$PID_CAP mistral_v01_forcedcutoff5500=$PID_SHAPE"

  ok=1
  wait $PID_CAP    || { echo "$(ts) TERMINAL: mistral_v02_capability_control FAILED"; ok=0; }
  wait $PID_SHAPE  || { echo "$(ts) TERMINAL: mistral_v01_forcedcutoff5500 FAILED"; ok=0; }

  if [ "$ok" = "1" ]; then
    echo "$(ts) both arms OK"
    $PY aggregate_p2e.py && echo "$(ts) aggregation OK" || echo "$(ts) TERMINAL: aggregation FAILED"
  else
    echo "$(ts) TERMINAL: one or more arms failed, not aggregating"
  fi
  echo "$(ts) TERMINAL: runs_complete"
} >>"$LOG" 2>&1
