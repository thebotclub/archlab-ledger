#!/usr/bin/env bash
# permval16 depth escalation pv2 — L=6/W=14, 4 seeds, one per V100.
# Standing ruling: depth before steps (PERMVAL16-DESIGN-20260813.md line 201).
# Receptive field L*(W-1)+1 = 79, covering the whole 32-76 distance band.
# Claim-ineligible learnability probe, scratch salt, $0 local.
set -eu
D="$HOME/archlab-runs/permval16-probe-20260817-pv2"
PY="$HOME/archlab/.venv/bin/python"
cd "$D"
i=0
for seed in 3990 3991 3992 3993; do
  CUDA_VISIBLE_DEVICES=$i setsid nohup "$PY" run_probe.py "$seed" \
      > "$D/launch_${seed}.log" 2>&1 < /dev/null &
  echo "launched seed=$seed on gpu=$i pid=$!"
  i=$((i+1))
done
