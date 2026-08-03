# d1 launch notes for the hub operator (build agent, 2026-08-03)

- GPU: campaign runs SINGLE-WORKER on GPU 3, sharing it with the chartered
  cs1 cert-spike (run_repro_cs1.py, ~14GB VRAM). d1 uses ~11GB. Two d1
  workers would not leave room for cs1, so worker 1 was not provisioned.
- DISK: hub / hit 100% during build (cs1 pulled a 16GB Qwen2.5-7B HF cache;
  p2f rolling ckpts are 1.3GB each). d1 therefore keeps rolling resume
  ckpts in /dev/shm/archlab-d1-ckpt (RAM; on host reboot an in-flight run
  restarts from step 0 -- results are unaffected) and writes final fp16
  weights only when >=2GiB disk is free (result.json final_ckpt field).
  queue_runner waits, not crashes, if free disk <400MB.
- FLOW: worker0 runs the 6 control runs first; monitor.py gates the grid on
  the pre-registered control result (controls.ok vs INSTRUMENT-BROKEN.md +
  STOP). decision.json is written when all 20 results exist. Expected
  ~60-75 min/run (0.66-0.82 s/step measured, cs1 contention dependent),
  ~20-25h total.
- If a worker dies (host issue): relaunch with
  cd ~/archlab-d1 && nohup /home/hani/archlab/.venv/bin/python \
    queue_runner.py ~/archlab3-runs/dose-onset-20260803-d1 0 \
    >> ~/archlab3-runs/dose-onset-20260803-d1/logs/worker0.log 2>&1 &
  (idempotent: completed runs are skipped; in-flight run resumes from the
  /dev/shm ckpt if the host did not reboot.)
- B4 (ledger-sync extension to ~/archlab3-runs/) is still the operator task
  per the charter; not done here.
