#!/usr/bin/env python3
"""Lab 3 d6 -- campaign monitor (d2-pattern; scorer is score_d6.py).

Loop every 120s:
  1. Controls barrier: once all 4 control results exist (both none LOW +
     both uniform-8% HIGH, per sealed_predictions.json), write controls.ok
     (unblocks the grid in queue_runner_multi.py). On control failure write
     INSTRUMENT-BROKEN.md + STOP + decision.json (status INSTRUMENT_BROKEN)
     and exit -- the dose arms never start.
  2. When every planned run has a result (or the queue is stopped and no
     training process is alive), run score_d6.py to write decision.json
     (verdict from the sealed shape/final predictions) and exit. The hub
     operator takes over from decision.json.
"""
import json
import os
import subprocess
import sys
import time

CAMP = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
PY = "/home/hani/archlab/.venv/bin/python"

B = {"recall_high": 0.376923076923, "recall_low": 0.065384615385}


def classify(v):
    if v >= B["recall_high"]:
        return "HIGH"
    if v <= B["recall_low"]:
        return "LOW"
    return "DEAD_ZONE"


def write_json(path, obj):
    with open(path + ".tmp", "w") as f:
        json.dump(obj, f, indent=2)
    os.replace(path + ".tmp", path)


def training_alive():
    out = subprocess.run(["pgrep", "-f", "train_d1.py"],
                         capture_output=True, text=True)
    return bool(out.stdout.strip())


def results():
    out = {}
    rdir = os.path.join(CAMP, "runs")
    if os.path.isdir(rdir):
        for fn in os.listdir(rdir):
            if fn.endswith(".result.json"):
                try:
                    r = json.load(open(os.path.join(rdir, fn)))
                    out[r["run_id"]] = r
                except Exception:
                    pass
    return out


def controls_status(res, sealed):
    """(all_present, pass, detail) over the sealed control run ids."""
    detail = {}
    ok = True
    present = True
    for rid in sealed["controls"]["none"]:
        if rid not in res:
            present = False
            continue
        obs = classify(res[rid]["final_eval"]["recall_acc"])
        detail[rid] = {"predicted": "LOW", "observed": obs}
        ok = ok and obs == "LOW"
    for rid in sealed["controls"]["positive"]:
        if rid not in res:
            present = False
            continue
        obs = classify(res[rid]["final_eval"]["recall_acc"])
        detail[rid] = {"predicted": "HIGH", "observed": obs}
        ok = ok and obs == "HIGH"
    return present, ok, detail


def run_scorer():
    subprocess.call([PY, os.path.join(HERE, "score_d6.py"), CAMP])


def main():
    runs = json.load(open(os.path.join(CAMP, "runs.json")))
    sealed = json.load(open(os.path.join(CAMP, "sealed_predictions.json")))
    n_planned = len(runs)
    controls_ok = os.path.join(CAMP, "controls.ok")
    broken = os.path.join(CAMP, "INSTRUMENT-BROKEN.md")
    stop = os.path.join(CAMP, "STOP")
    decision = os.path.join(CAMP, "decision.json")
    # d6 ships a controls.ok (inherited-instrument note); remove it so the
    # controls barrier is genuinely re-evaluated on THIS campaign's fresh
    # control runs before the dose arms start.
    if os.path.exists(controls_ok) and not os.path.exists(
            os.path.join(CAMP, ".controls_judged")):
        os.remove(controls_ok)
    while True:
        res = results()
        present, cpass, cdetail = controls_status(res, sealed)
        if not os.path.exists(controls_ok) and not os.path.exists(broken) \
                and present:
            if cpass:
                write_json(controls_ok, {"pass": True, "detail": cdetail})
                open(os.path.join(CAMP, ".controls_judged"), "w").close()
                print("[monitor] controls PASS -> controls.ok", flush=True)
            else:
                with open(broken, "w") as f:
                    f.write("# INSTRUMENT-BROKEN -- d6 control gates failed\n\n"
                            "Sealed controls (none LOW + uniform-8%% HIGH) did "
                            "not pass; the dose arms are NOT interpretable.\n\n"
                            "```json\n" + json.dumps(cdetail, indent=2)
                            + "\n```\n")
                open(stop, "w").close()
                run_scorer()
                write_json(decision, {"status": "INSTRUMENT_BROKEN",
                                      "controls": cdetail})
                print("[monitor] controls FAIL -> STOP", flush=True)
                return
        n_done = len(res)
        if n_done >= n_planned:
            run_scorer()
            print(f"[monitor] all {n_done} runs done -> decision.json",
                  flush=True)
            return
        if (os.path.exists(stop) or os.path.exists(broken)) \
                and not training_alive():
            run_scorer()
            print("[monitor] stopped early -> decision.json", flush=True)
            return
        if not training_alive():
            time.sleep(120)
            if not training_alive():
                n2 = len(results())
                if n2 < n_planned:
                    run_scorer()
                    print("[monitor] no active runs, queue dead -> "
                          "decision.json", flush=True)
                    return
            continue
        time.sleep(120)


if __name__ == "__main__":
    main()
