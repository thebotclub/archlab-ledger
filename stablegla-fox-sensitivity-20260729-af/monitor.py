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
    done, failures, arms = 0, [], {}
    for s in m["shards"]:
        d = R / s["id"]
        f = d / "result.json"
        if f.exists():
            try:
                rows = json.load(open(f))["results"]
                if len(rows) == len(s["seeds"]):
                    done += 1
                    arms[s["id"]] = {"transitions": sum(1 for r in rows if r["recall"] > THR),
                                     "n": len(rows),
                                     "recalls": [round(r["recall"], 4) for r in rows]}
                elif not alive(d / "pid"):
                    failures.append(s["id"] + ":partial-result")
            except Exception as e:
                failures.append(s["id"] + ":invalid:" + type(e).__name__)
        elif not alive(d / "pid"):
            failures.append(s["id"] + ":exited-without-result")
    if failures:
        out = {"campaign": R.name, "status": "INCOMPLETE_FAILED", "failures": failures, "arms": arms}
    elif done == len(m["shards"]):
        total = sum(v["transitions"] for v in arms.values())
        out = {"campaign": R.name, "stage": m["stage"], "claim_eligible": False,
               "reference": m["reference"], "arms": arms,
               "fox_sensitivity_total": f"{total}/{sum(v['n'] for v in arms.values())}",
               "status": "FOX_SENSITIVITY_ROUND1_COMPLETE",
               "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    else:
        time.sleep(30)
        continue
    tmp = R / "decision.json.tmp"
    tmp.write_text(json.dumps(out, indent=2) + "\n")
    os.replace(tmp, R / "decision.json")
    break
