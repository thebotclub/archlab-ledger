#!/bin/bash
# Lab 3 d6 -- campaign launch. Usage: launch.sh <campaign_dir>
set -euo pipefail
CAMP="$1"
HARNESS="$(cd "$(dirname "$0")" && pwd)"
PY=/home/hani/archlab/.venv/bin/python

# Preconditions (sealed protocol: prereg artifacts must exist pre-launch)
for f in sealed_predictions.json campaign.json eval_salt.txt runs.json; do
  [ -f "$CAMP/$f" ] || { echo "FATAL: $f missing"; exit 1; }
done

# All 4 local V100s must be idle (Lab 3 launches only on GPUs Lab 1/2 don't
# want). Any occupant on any GPU aborts.
for g in 0 1 2 3; do
  while read -r pid; do
    [ -z "$pid" ] && continue
    CMD=$(ps -o cmd= -p "$pid" || true)
    echo "FATAL: GPU $g occupied by process $pid: $CMD"; exit 1
  done < <(nvidia-smi --query-compute-apps=pid --format=csv,noheader -i "$g")
done

# Disk gate (rolling ckpts in /dev/shm; ~30MB of JSON/logs on /home/hani).
DFREE_KB=$(df --output=avail /home/hani | tail -1 | tr -d " ")
[ "$DFREE_KB" -ge 409600 ] || {
  echo "FATAL: only ${DFREE_KB}KB free on /home/hani (need >=400MB)"; exit 1; }

# /dev/shm capacity for 4 concurrent rolling checkpoints (~46MB fp32 master
# each, well under shm).
SHM_KB=$(df --output=avail /dev/shm | tail -1 | tr -d " ")
[ "$SHM_KB" -ge 1048576 ] || {
  echo "FATAL: only ${SHM_KB}KB free on /dev/shm (need >=1GB)"; exit 1; }

# COORDINATION.md rule 4: archive the executable harness in the campaign dir
mkdir -p "$CAMP/harness"
cp "$HARNESS"/*.py "$HARNESS"/launch.sh "$CAMP/harness/"
cp "$HARNESS"/pools/pools_manifest.json "$CAMP/harness/"

mkdir -p "$CAMP/logs" "$CAMP/runs"
cd "$HARNESS"

nohup "$PY" monitor.py "$CAMP" > "$CAMP/logs/monitor.log" 2>&1 &
echo "monitor pid $!"
for g in 0 1 2 3; do
  nohup "$PY" queue_runner_multi.py "$CAMP" "$g" \
    > "$CAMP/logs/worker$g.log" 2>&1 &
  echo "worker gpu$g pid $!"
done
echo "LAUNCHED $(date -u +%FT%TZ)"
