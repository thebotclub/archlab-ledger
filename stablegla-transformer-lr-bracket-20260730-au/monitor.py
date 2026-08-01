#!/usr/bin/env python3
import json, os, pathlib, time
R = pathlib.Path(__file__).resolve().parent
m = json.load(open(R / "campaign.json"))
g = m["preregistered_gates"]
THR = g["transition_recall_threshold"]
TOL = g["bracket_tolerance"]
REF = m["as_reference_grid"]["s1_lr1em4_mean"]

def alive(p):
    try:
        os.kill(int(p.read_text()), 0)
        return True
    except Exception:
        return False

def wait_for(shards):
    while True:
        rows_by_id, failures, done = {}, [], 0
        for s in shards:
            d = R / s["id"]
            f = d / "result.json"
            if f.exists():
                try:
                    r = json.load(open(f))["results"]
                    if len(r) == len(s["seeds"]):
                        rows_by_id[s["id"]] = r
                        done += 1
                    elif not alive(d / "pid"):
                        failures.append(s["id"] + ":partial-result")
                except Exception as e:
                    failures.append(s["id"] + ":invalid:" + type(e).__name__)
            elif not alive(d / "pid"):
                failures.append(s["id"] + ":exited-without-result")
        if failures:
            return None, failures
        if done == len(shards):
            return rows_by_id, None
        time.sleep(30)

rows_by_id, failures = wait_for(m["shards"])
if failures:
    out = {"campaign": R.name, "status": "INCOMPLETE_FAILED", "failures": failures}
else:
    cells = {}
    for s in m["shards"]:
        rs = rows_by_id[s["id"]]
        recalls = [r["recall"] for r in rs]
        cells[s["id"]] = {
            "base_lr": s["base_lr"], "budget": s["budget"], "n": len(rs),
            "transitions": sum(1 for v in recalls if v > THR),
            "max_recall": round(max(recalls), 4),
            "mean_recall": round(sum(recalls) / len(recalls), 4),
            "recalls": [round(v, 4) for v in recalls],
            "reference": s.get("reference", ""),
        }

    total_transitions = sum(c["transitions"] for c in cells.values())
    global_max = max(c["max_recall"] for c in cells.values())

    new_lr_cells = {cid: c for cid, c in cells.items() if cid != "s1_lr1em4_replication"}
    still_open = [cid for cid, c in new_lr_cells.items() if c["mean_recall"] >= REF + TOL]

    if total_transitions >= 1:
        outcome = "TRANSITION_AT_LOW_LR"
    elif still_open:
        outcome = "BRACKET_STILL_OPEN"
    else:
        outcome = "BRACKET_CLOSED"

    # harness positive control
    rep = cells.get("s1_lr1em4_replication")
    pc_delta = round(abs(rep["mean_recall"] - REF), 4) if rep else None
    pc_ok = (pc_delta is not None and pc_delta <= 0.05)

    out = {
        "campaign": R.name, "stage": m["stage"], "audits": m["audits"],
        "claim_eligible": False,
        "cells": cells,
        "total_transitions": total_transitions,
        "global_max_recall": global_max,
        "chance_recall": m["chance_recall"],
        "outcome": outcome,
        "outcome_meaning": g["outcomes"][outcome],
        "bracket_reference": {"s1_lr1em4_mean_as": REF, "tolerance": TOL, "still_open_cells": still_open},
        "harness_positive_control": {
            "cell": "s1_lr1em4_replication",
            "as_reference_mean": REF,
            "observed_mean": rep["mean_recall"] if rep else None,
            "abs_delta": pc_delta, "tolerance": 0.05, "passed": pc_ok,
        },
        "reportable": pc_ok,
        "reportable_note": ("" if pc_ok else "HARNESS POSITIVE CONTROL FAILED -- the outcome "
                            "above must NOT be reported until the disagreement with as is explained."),
        "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

tmp = R / "decision.json.tmp"
tmp.write_text(json.dumps(out, indent=2) + "\n")
os.replace(tmp, R / "decision.json")
print(json.dumps(out, indent=2))
