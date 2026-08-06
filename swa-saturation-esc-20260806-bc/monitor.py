#!/usr/bin/env python3
"""Aggregates all 4 shards' result.json into decision.json once complete.
Same transition/saturation criteria as bb's monitor (control: recall>0.8;
windowed: in_window_accuracy>0.8; ceiling tolerance +-0.05 on aggregate
recall among transitioned runs only). Control-anomaly rule identical to
bb's: CONTROL_CONFIRMED requires every transitioned control run at
recall>=0.95. Verdicts (this rung only; the pooled bb+bc interpretation is
written by the operator into PAPER-NOTE.md at verdict):
  ESCALATION_SATURATES_GENERIC -- control confirmed AND every escalated
    window arm confirms saturation.
  ESCALATION_FAMILY_SPECIFIC -- control confirmed AND at least one
    escalated window arm has >=3 transitioned runs with <60% of them within
    +-0.05 of predicted ceiling.
  ESCALATION_CONTROL_ANOMALOUS -- control transitioned but not all
    transitioned runs >=0.95 (bb's anomaly reproduces at 2x budget).
  ESCALATION_UNDERPOWERED -- control <3 transitions or an escalated window
    arm still <3 in-window transitions at 6e16.
"""
import json, math, os, pathlib, time

R = pathlib.Path(__file__).resolve().parent
m = json.load(open(R / "campaign.json"))
THR = m["preregistered_gate"]["transition_recall_threshold"]
TOL = m["preregistered_gate"]["ceiling_tolerance"]
MIN_TR = m["preregistered_gate"]["min_transitions_per_arm"]


def alive(p):
    try:
        os.kill(int(p.read_text()), 0)
        return True
    except Exception:
        return False


while True:
    all_rows, failures = [], []
    for s in m["shards"]:
        d = R / s["id"]
        f = d / "result.json"
        expect_n = len(s["arms"]) * len(s["seeds"])
        if f.exists():
            try:
                r = json.load(open(f))["results"]
                if len(r) == expect_n:
                    all_rows += r
                elif not alive(d / "pid"):
                    failures.append(s["id"] + ":partial-result")
            except Exception as e:
                failures.append(s["id"] + ":invalid:" + type(e).__name__)
        elif not alive(d / "pid"):
            failures.append(s["id"] + ":exited-without-result")
    total_expect = sum(len(s["arms"]) * len(s["seeds"]) for s in m["shards"])
    if failures:
        out = {"campaign": R.name, "status": "INCOMPLETE_FAILED",
               "gate_result": "FAIL", "failures": failures}
    elif len(all_rows) == total_expect:
        control_rows = [r for r in all_rows if r["arm"] == "transformer_full"]
        control_transitions = sum(1 for r in control_rows if r["recall"] > THR)
        anomalous = [r["seed"] for r in control_rows
                     if r["recall"] > THR and r["recall"] < 0.95]
        control_status = ("CONTROL_UNDERPOWERED" if control_transitions < MIN_TR
                          else ("CONTROL_ANOMALOUS" if anomalous
                                else "CONTROL_CONFIRMED"))
        arms = {}
        for s in m["shards"]:
            for arm_name in s["arms"]:
                if arm_name == "transformer_full":
                    continue
                cand_rows = [r for r in all_rows if r["arm"] == arm_name]
                transitioned = [r for r in cand_rows
                                if r["in_window_accuracy"] > THR]
                n_tr = len(transitioned)
                ceiling = s["predicted_ceiling"]
                confirmed = [r for r in transitioned
                             if abs(r["recall"] - ceiling) <= TOL]
                if n_tr < MIN_TR:
                    status = "STILL_UNDERPOWERED_AT_6E16"
                elif len(confirmed) >= math.ceil(0.6 * n_tr):
                    status = "SATURATION_CONFIRMED"
                else:
                    status = "SATURATION_NOT_CONFIRMED"
                arms[arm_name] = {
                    "window": s["window"], "predicted_ceiling": ceiling,
                    "n_seeds": len(cand_rows),
                    "n_transitioned_in_window": n_tr,
                    "n_ceiling_confirmed": len(confirmed),
                    "status": status,
                    "recalls": [round(r["recall"], 4) for r in cand_rows],
                    "in_window_accuracies": [round(r["in_window_accuracy"], 4)
                                             for r in cand_rows],
                    "out_of_window_accuracies": [round(r["out_of_window_accuracy"], 4)
                                                 for r in cand_rows],
                }
        if control_status == "CONTROL_UNDERPOWERED":
            verdict = "ESCALATION_UNDERPOWERED"
        elif control_status == "CONTROL_ANOMALOUS":
            verdict = "ESCALATION_CONTROL_ANOMALOUS"
        elif any(a["status"] == "STILL_UNDERPOWERED_AT_6E16"
                 for a in arms.values()):
            verdict = "ESCALATION_UNDERPOWERED"
        elif any(a["status"] == "SATURATION_NOT_CONFIRMED"
                 for a in arms.values()):
            verdict = "ESCALATION_FAMILY_SPECIFIC"
        else:
            verdict = "ESCALATION_SATURATES_GENERIC"
        out = {"campaign": R.name, "stage": m["stage"],
               "parent_campaign": m["parent_campaign"],
               "panel": m["panel"]["id"], "budget": m["budget"],
               "control_transitions": control_transitions,
               "control_status": control_status,
               "control_anomalous_seeds": anomalous,
               "arms": arms, "verdict": verdict, "status": "COMPLETE",
               "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                              time.gmtime())}
    else:
        time.sleep(60)
        continue
    tmp = R / "decision.json.tmp"
    tmp.write_text(json.dumps(out, indent=2) + "\n")
    os.replace(tmp, R / "decision.json")
    break
