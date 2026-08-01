#!/usr/bin/env python3
import json, os, pathlib, time
R = pathlib.Path(__file__).resolve().parent
m = json.load(open(R / "campaign.json"))
THR = m["preregistered_gate"]["crossing_criterion"]

def alive(p):
    try:
        os.kill(int(p.read_text()), 0)
        return True
    except Exception:
        return False

while True:
    rows, failures = [], []
    for s in m["shards"]:
        d = R / s["id"]
        f = d / "result.json"
        if f.exists():
            try:
                r = json.load(open(f))["results"]
                if len(r) == len(s["seeds"]):
                    rows += r
                elif not alive(d / "pid"):
                    failures.append(s["id"] + ":partial-result")
            except Exception as e:
                failures.append(s["id"] + ":invalid:" + type(e).__name__)
        elif not alive(d / "pid"):
            failures.append(s["id"] + ":exited-without-result")
    if failures:
        out = {"campaign": R.name, "status": "INCOMPLETE_FAILED", "failures": failures}
    elif len(rows) == len(m["seeds"]):
        rows.sort(key=lambda r: r["init_seed"])
        n_cross = sum(1 for r in rows if r["recall"] > THR)
        steps = None
        for r in rows:
            for line in r.get("training_log", []):
                if "/" in str(line):
                    tail = str(line).split("step ")[-1].split()[0]
                    if "/" in tail:
                        steps = tail.split("/")[-1]
        verdict = "NULL_IS_STEP_BOUNDED" if n_cross >= 1 else "NULL_SURVIVES_STEP_MATCH"
        out = {"campaign": R.name, "stage": m["stage"], "panel": m["panel"],
               "budget": m["budget"], "n_runs": len(rows),
               "steps_per_run": steps,
               "transformer_transitions": n_cross,
               "transformer_recalls": [round(r["recall"], 4) for r in rows],
               "transformer_final_losses": [r["final_loss"] for r in rows],
               "max_recall": round(max(r["recall"] for r in rows), 4),
               "verdict": verdict,
               "verdict_means": m["preregistered_gate"][
                   "transitions_ge_1_means" if n_cross >= 1 else "transitions_eq_0_means"],
               "status": "COMPLETE",
               "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    else:
        time.sleep(120)
        continue
    tmp = R / "decision.json.tmp"
    tmp.write_text(json.dumps(out, indent=2) + "\n")
    os.replace(tmp, R / "decision.json")
    break
