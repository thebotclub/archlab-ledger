#!/bin/bash
# p2d autorun: 4 arms in parallel, one per GPU, then mechanical aggregation.
set -u
cd ~/archlab-p2d
LOCK=~/archlab-p2d/.autorun.lock
exec 9>"$LOCK"
flock -n 9 || { echo "another autorun holds the lock"; exit 1; }

PY=~/archlab/.venv/bin/python
LOG=~/archlab-p2d/autorun.log
ts() { date -u +"[%H:%M:%SZ]"; }
export PYTORCH_ALLOC_CONF=expandable_segments:True

{
  echo "$(ts) p2d autorun start (pid $$)"

  CUDA_VISIBLE_DEVICES=0 $PY run_p2d.py --model microsoft/Phi-3-mini-4k-instruct \
    --window 2047 --max-context 4096 --reps 48 --gpu 0 --tag phi3 \
    >>"$LOG.phi3" 2>&1 &
  PID_PHI3=$!

  CUDA_VISIBLE_DEVICES=1 $PY run_p2d.py --model mistralai/Mistral-7B-Instruct-v0.1 \
    --window 4096 --max-context 8192 --reps 48 --gpu 0 --tag mistral_v01 \
    >>"$LOG.mistral_v01" 2>&1 &
  PID_MISTRAL=$!

  CUDA_VISIBLE_DEVICES=2 $PY run_p2d.py --model microsoft/Phi-3-mini-4k-instruct \
    --window 1024 --force-window 1024 --max-context 4096 --reps 48 --gpu 0 --tag phi3_w1024 \
    >>"$LOG.phi3_w1024" 2>&1 &
  PID_W1024=$!

  CUDA_VISIBLE_DEVICES=3 $PY run_p2d.py --model mistralai/Mistral-7B-Instruct-v0.1 \
    --window 4096 --disable-window --max-context 8192 --reps 48 --gpu 0 --tag mistral_nowindow \
    >>"$LOG.mistral_nowindow" 2>&1 &
  PID_NOWINDOW=$!

  echo "$(ts) launched: phi3=$PID_PHI3 mistral_v01=$PID_MISTRAL phi3_w1024=$PID_W1024 mistral_nowindow=$PID_NOWINDOW"

  ok=1
  wait $PID_PHI3       || { echo "$(ts) TERMINAL: phi3 FAILED"; ok=0; }
  wait $PID_MISTRAL    || { echo "$(ts) TERMINAL: mistral_v01 FAILED"; ok=0; }
  wait $PID_W1024      || { echo "$(ts) TERMINAL: phi3_w1024 FAILED"; ok=0; }
  wait $PID_NOWINDOW   || { echo "$(ts) TERMINAL: mistral_nowindow FAILED"; ok=0; }

  if [ "$ok" = "1" ]; then
    echo "$(ts) all 4 arms OK"
    $PY aggregate_p2d.py && echo "$(ts) aggregation OK" || echo "$(ts) TERMINAL: aggregation FAILED"
  else
    echo "$(ts) TERMINAL: one or more arms failed, not aggregating"
  fi
  echo "$(ts) TERMINAL: runs_complete"
} >>"$LOG" 2>&1
