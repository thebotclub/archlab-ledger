#!/usr/bin/env python3
import json, os, pathlib, time
R = pathlib.Path(__file__).resolve().parent
m = json.load(open(R / "campaign.json"))
g = m["preregistered_gates"]
THR = g["transition_recall_threshold"]
PARTIAL = g["partial_learning_threshold"]


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

    if total_transitions >= 1:
        outcome = "AQ_CONTROL_REFUTED"
    elif global_max > PARTIAL:
        outcome = "AQ_CONTROL_WEAKENED"
    else:
        outcome = "AQ_CONTROL_UPHELD"

    # meta-gate: is the LR axis bracketed at each budget?
    unbracketed = []
    for budget_tag, prefix in (("3e15", "s1_"), ("1.2e16", "s2_")):
        axis = {cid: c for cid, c in cells.items() if cid.startswith(prefix)}
        if axis:
            best = max(axis.items(), key=lambda kv: kv[1]["mean_recall"])
            lowest_lr = min(c["base_lr"] for c in axis.values())
            if best[1]["base_lr"] == lowest_lr:
                unbracketed.append({"budget": budget_tag, "argmax_cell": best[0],
                                    "argmax_lr": best[1]["base_lr"],
                                    "mean_recall": best[1]["mean_recall"]})

    # harness positive controls -- BOTH must pass (preregistered_gates)
    def _pc(cell_id, ref, label):
        c = cells.get(cell_id)
        d = round(abs(c["mean_recall"] - ref), 4) if c else None
        return {"cell": cell_id, "reference_mean": ref, "reference_source": label,
                "observed_mean": c["mean_recall"] if c else None,
                "abs_delta": d, "tolerance": 0.05,
                "passed": bool(d is not None and d <= 0.05)}

    pcs = [
        _pc("s2_lr1em3_replication", m["aq_reference_grid"]["lr1p2e16_1em3"],
            "aq lr1p2e16_1em3"),
        _pc("s1_lr3em4", m["aq_reference_grid"]["_w_campaign_3e15"]["lr3e-4"],
            "campaign w lr3e-4 @3e15"),
    ]
    pc_ok = all(x["passed"] for x in pcs)

    out = {
        "campaign": R.name, "stage": m["stage"], "audits": m["audits"],
        "claim_eligible": False,
        "cells": cells,
        "total_transitions": total_transitions,
        "global_max_recall": global_max,
        "chance_recall": m["chance_recall"],
        "outcome": outcome,
        "outcome_meaning": g["outcomes"][outcome],
        "harness_positive_controls": pcs,
        "harness_positive_controls_all_passed": pc_ok,
        "meta_gate_sweep_unbracketed": {
            "triggered": bool(unbracketed), "detail": unbracketed,
            "consequence": ("A further downward LR extension is REQUIRED before publication."
                            if unbracketed else "LR axis is bracketed at both budgets."),
        },
        "reportable": pc_ok,
        "reportable_note": ("" if pc_ok else "HARNESS POSITIVE CONTROL FAILED -- the outcome "
                            "above must NOT be reported until the disagreement with the "
                            "program's prior runs is explained."),
        "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

tmp = R / "decision.json.tmp"
tmp.write_text(json.dumps(out, indent=2) + "\n")
os.replace(tmp, R / "decision.json")
print(json.dumps(out, indent=2))
