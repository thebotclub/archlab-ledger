#!/bin/bash
# p2e finisher: cap arm was already running when the shape-arm G1 bug was
# found and fixed (2026-08-02 ~03:05Z); this launches the fixed shape arm
# and waits for BOTH result files before aggregating, since the original
# autorun.sh wrapper was killed along with the buggy shape-arm process.
set -u
cd ~/archlab-p2e
LOCK=~/archlab-p2e/.finish.lock
exec 9>"$LOCK"
flock -n 9 || { echo "another autorun holds the lock"; exit 1; }

PY=~/archlab/.venv/bin/python
LOG=~/archlab-p2e/autorun.log
ts() { date -u +"[%H:%M:%SZ]"; }
export PYTORCH_ALLOC_CONF=expandable_segments:True

{
  echo "$(ts) p2e finish.sh start (pid $$) -- cap arm already running, launching fixed shape arm"

  CUDA_VISIBLE_DEVICES=1 $PY run_p2e.py --model mistralai/Mistral-7B-Instruct-v0.1 \
    --window 4096 --force-window 5500 --max-context 8192 --reps 48 --gpu 0 --tag mistral_v01_forcedcutoff5500 \
    >>"$LOG.mistral_v01_forcedcutoff5500" 2>&1 &
  PID_SHAPE=$!
  echo "$(ts) launched fixed shape arm: mistral_v01_forcedcutoff5500=$PID_SHAPE"

  ok=1
  wait $PID_SHAPE || { echo "$(ts) TERMINAL: mistral_v01_forcedcutoff5500 FAILED"; ok=0; }

  # cap arm (pid 1627897) is not a child of this shell; poll for it instead of wait.
  while kill -0 1627897 2>/dev/null; do sleep 15; done
  if [ ! -f "$HOME/archlab-p2e/p2e_mistral_v02_capability_control.json" ]; then
    echo "$(ts) TERMINAL: mistral_v02_capability_control exited without a result file (FAILED)"
    ok=0
  fi

  if [ "$ok" = "1" ]; then
    echo "$(ts) both arms OK"
    $PY aggregate_p2e.py && echo "$(ts) aggregation OK" || echo "$(ts) TERMINAL: aggregation FAILED"
  else
    echo "$(ts) TERMINAL: one or more arms failed, not aggregating"
  fi
  echo "$(ts) TERMINAL: runs_complete"
} >>"$LOG" 2>&1
