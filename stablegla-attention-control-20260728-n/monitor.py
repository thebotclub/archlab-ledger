#!/usr/bin/env python3
import json, os, pathlib, time
R = pathlib.Path(__file__).resolve().parent
m = json.load(open(R / "campaign.json"))
THR = m["transition_recall_threshold"]

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
                if len(r) == len(m["arms"]) * len(s["seeds"]):
                    rows += r
                elif not alive(d / "pid"):
                    failures.append(s["id"] + ":partial-result")
            except Exception as e:
                failures.append(s["id"] + ":invalid:" + type(e).__name__)
        elif not alive(d / "pid"):
            failures.append(s["id"] + ":exited-without-result")
    if failures:
        out = {"campaign": R.name, "status": "INCOMPLETE_FAILED", "failures": failures}
    elif len(rows) == len(m["arms"]) * len(m["seeds"]):
        arms = {}
        for a, _, _ in m["arms"]:
            rs = sorted([r for r in rows if r["arm"] == a], key=lambda r: r["init_seed"])
            arms[a] = {"transitions": sum(1 for r in rs if r["recall"] > THR),
                       "n": len(rs),
                       "recalls": [round(r["recall"], 4) for r in rs],
                       "recall_mean": sum(r["recall"] for r in rs) / len(rs)}
        out = {"campaign": R.name, "stage": m["stage"], "claim_eligible": False,
               "panel": "pairs80", "budget": m["budget"], "arms": arms,
               "status": "CONTROL_AUDIT_COMPLETE",
               "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    else:
        time.sleep(30)
        continue
    tmp = R / "decision.json.tmp"
    tmp.write_text(json.dumps(out, indent=2) + "\n")
    os.replace(tmp, R / "decision.json")
    break
