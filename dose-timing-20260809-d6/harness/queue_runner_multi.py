#!/usr/bin/env python3
"""Lab 3 d2 -- claim-locked parallel run queue (scheduling-only change).

Usage: queue_runner_multi.py <campaign_dir> <gpu_id>

Same run semantics as queue_runner.py (controls barrier, disk rail, one
train_d1.py process per run); the only change is scheduling: any worker may
execute any pending run, coordinated by O_EXCL claim files in
<campaign_dir>/claims/. Authorized by Hani 2026-08-04T04:25Z inbox (GPUs
0/1/2 freed post-p1e/p2f); no change to runs, seeds, gates, or scoring --
per-run determinism depends only on the run's own seed, never on execution
order or GPU index (all 4 local V100s identical).
"""
import json
import os
import subprocess
import sys
import time

PY = "/home/hani/archlab/.venv/bin/python"
HARNESS = os.path.dirname(os.path.abspath(__file__))

CAMP = sys.argv[1]
GPU = sys.argv[2]
RUNS = json.load(open(os.path.join(CAMP, "runs.json")))
LOGS = os.path.join(CAMP, "logs")
CLAIMS = os.path.join(CAMP, "claims")
os.makedirs(LOGS, exist_ok=True)
os.makedirs(CLAIMS, exist_ok=True)


def stopped():
    return (os.path.exists(os.path.join(CAMP, "STOP"))
            or os.path.exists(os.path.join(CAMP, "INSTRUMENT-BROKEN.md")))


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def try_claim(rid):
    """Atomically claim rid. Returns True if this worker owns it."""
    path = os.path.join(CLAIMS, f"{rid}.claim")
    if os.path.exists(path):
        try:
            holder = int(open(path).read().split()[0])
        except (ValueError, IndexError, OSError):
            holder = None
        if holder and pid_alive(holder):
            return False
        # stale claim (holder dead, no result): atomic rename-aside so only
        # one worker gets to re-claim; the loser's rename raises and it skips
        try:
            os.rename(path, f"{path}.stale-{os.getpid()}")
        except OSError:
            return False
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    os.write(fd, f"{os.getpid()} gpu{GPU} {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n".encode())
    os.close(fd)
    return True


def wait_for_controls_ok():
    while True:
        if os.path.exists(os.path.join(CAMP, "controls.ok")):
            return True
        if stopped():
            return False
        time.sleep(60)


def main():
    env = dict(os.environ)
    env["CUDA_VISIBLE_DEVICES"] = GPU
    for spec in RUNS:
        rid = spec["run_id"]
        res = os.path.join(CAMP, "runs", f"{rid}.result.json")
        if os.path.exists(res):
            continue
        if stopped():
            print(f"[gpu{GPU}] STOP present, exiting", flush=True)
            return
        if spec["group"] != "control":
            if not wait_for_controls_ok():
                print(f"[gpu{GPU}] controls failed/STOP, exiting", flush=True)
                return
        if not try_claim(rid):
            continue
        if os.path.exists(res):
            continue
        while True:
            st = os.statvfs("/home/hani")
            free_mb = st.f_bavail * st.f_frsize / 2**20
            if free_mb >= 400:
                break
            print(f"[gpu{GPU}] only {free_mb:.0f}MB free on /, waiting "
                  f"before starting {rid}", flush=True)
            if stopped():
                return
            time.sleep(300)
        log = open(os.path.join(LOGS, f"{rid}.log"), "a")
        print(f"[gpu{GPU}] launching {rid}", flush=True)
        rc = subprocess.call([PY, os.path.join(HARNESS, "train_d1.py"),
                              CAMP, rid], stdout=log, stderr=subprocess.STDOUT,
                             env=env, cwd=HARNESS)
        log.close()
        if rc != 0:
            print(f"[gpu{GPU}] {rid} FAILED rc={rc}; releasing claim, "
                  f"continuing (monitor will see the hole)", flush=True)
            try:
                os.remove(os.path.join(CLAIMS, f"{rid}.claim"))
            except OSError:
                pass
    print(f"[gpu{GPU}] ALL DONE", flush=True)


if __name__ == "__main__":
    main()
