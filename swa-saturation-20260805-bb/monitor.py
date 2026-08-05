#!/usr/bin/env python3
"""Aggregates all 4 shards' result.json into decision.json once complete.
Transition criterion: control arm uses aggregate recall>0.8 (standard, matches
every other sealed campaign); windowed candidate arms use in_window_accuracy>0.8
(the directive's own bimodality-corrected signal -- aggregate recall is capped
by predicted_ceiling for narrow windows even on a fully-transitioned run, so it
cannot by itself distinguish "transitioned but window-capped" from "never
transitioned"). Saturation is read ONLY from transitioned runs, comparing
aggregate recall against predicted_ceiling +-0.05, per ap's own sealed
plateau-law gate convention.
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
        expect_n = 2 * len(s["seeds"])
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
    total_expect = sum(2 * len(s["seeds"]) for s in m["shards"])
    if failures:
        out = {"campaign": R.name, "status": "INCOMPLETE_FAILED",
               "gate_result": "FAIL", "failures": failures}
    elif len(all_rows) == total_expect:
        control_rows = [r for r in all_rows if r["arm"] == "transformer_full"]
        control_transitions = sum(1 for r in control_rows if r["recall"] > THR)
        control_status = ("CONTROL_UNDERPOWERED_ESCALATE_6E16"
                           if control_transitions < MIN_TR else
                           ("CONTROL_CONFIRMED"
                            if all(r["recall"] >= 0.95 for r in control_rows
                                   if r["recall"] > THR) else "CONTROL_ANOMALOUS"))
        arms = {}
        for s in m["shards"]:
            w = s["window"]
            arm_name = f"transformer_win{w}"
            cand_rows = [r for r in all_rows if r["arm"] == arm_name]
            transitioned = [r for r in cand_rows if r["in_window_accuracy"] > THR]
            n_tr = len(transitioned)
            ceiling = s["predicted_ceiling"]
            confirmed = [r for r in transitioned
                         if abs(r["recall"] - ceiling) <= TOL]
            if n_tr < MIN_TR:
                status = "UNDERPOWERED_ESCALATE_6E16"
            elif len(confirmed) >= math.ceil(0.6 * n_tr):
                status = "SATURATION_CONFIRMED"
            else:
                status = "SATURATION_NOT_CONFIRMED"
            arms[arm_name] = {
                "window": w, "predicted_ceiling": ceiling,
                "n_seeds": len(cand_rows),
                "n_transitioned_in_window": n_tr,
                "n_ceiling_confirmed": len(confirmed),
                "status": status,
                "recalls": [round(r["recall"], 4) for r in cand_rows],
                "in_window_accuracies": [round(r["in_window_accuracy"], 4) for r in cand_rows],
                "out_of_window_accuracies": [round(r["out_of_window_accuracy"], 4) for r in cand_rows],
            }
        if control_status != "CONTROL_CONFIRMED":
            verdict = "UNDERPOWERED" if control_status == "CONTROL_UNDERPOWERED_ESCALATE_6E16" else "CONTROL_ANOMALOUS_INCONCLUSIVE"
        elif any(a["status"] == "UNDERPOWERED_ESCALATE_6E16" for a in arms.values()):
            verdict = "UNDERPOWERED"
        elif any(a["status"] == "SATURATION_NOT_CONFIRMED" for a in arms.values()):
            verdict = "FAMILY_SPECIFIC"
        elif all(a["status"] == "SATURATION_CONFIRMED" for a in arms.values()):
            verdict = "SATURATES_GENERIC"
        else:
            verdict = "UNDERPOWERED"
        out = {"campaign": R.name, "stage": m["stage"], "panel": m["panel"]["id"],
               "budget": m["budget"], "control_transitions": control_transitions,
               "control_status": control_status, "arms": arms,
               "verdict": verdict, "status": "COMPLETE",
               "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    else:
        time.sleep(60)
        continue
    tmp = R / "decision.json.tmp"
    tmp.write_text(json.dumps(out, indent=2) + "\n")
    os.replace(tmp, R / "decision.json")
    break
