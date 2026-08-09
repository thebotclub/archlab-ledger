#!/bin/bash
cd /home/hani/archlab-runs/family-constant-20260809-at
while true; do
  n=$(ls shard*/result.json 2>/dev/null | wc -l)
  if [ "$n" -ge 4 ]; then
    /home/hani/archlab/.venv/bin/python monitor.py >> monitor.log 2>&1
    echo "$(date -u +%FT%TZ) decision written" >> monitor.log
    break
  fi
  sleep 300
done
