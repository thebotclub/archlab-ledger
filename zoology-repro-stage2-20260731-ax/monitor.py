#!/usr/bin/env python3
import json, math, os, pathlib, time
R = pathlib.Path(__file__).resolve().parent
m = json.load(open(R / "campaign.json"))
g = m["preregistered_gate"]
THR = g["transition_recall_threshold"]

def alive(p):
    try:
        os.kill(int(p.read_text()), 0)
        return True
    except Exception:
        return False

def mcnemar_exact_one_sided(b, c):
    # b = transformer-cross/stablegla-not, c = stablegla-cross/transformer-not (discordant counts)
    n = b + c
    if n == 0:
        return 1.0
    denom = 2 ** n
    p = sum(math.comb(n, k) for k in range(0, min(b, c) + 1)) / denom
    return min(1.0, p)

while True:
    rows, failures = [], []
    for s in m["shards"]:
        d = R / s["id"]
        f = d / "result.json"
        if f.exists():
            try:
                r = json.load(open(f))["results"]
                if len(r) == 2 * len(s["seeds"]):
                    rows += r
                elif not alive(d / "pid"):
                    failures.append(s["id"] + ":partial-result")
            except Exception as e:
                failures.append(s["id"] + ":invalid:" + type(e).__name__)
        elif not alive(d / "pid"):
            failures.append(s["id"] + ":exited-without-result")
    if failures:
        out = {"campaign": R.name, "status": "INCOMPLETE_FAILED", "failures": failures}
    elif len(rows) == 2 * len(m["paired_seeds"]):
        tr = [r for r in rows if r["arm"] == "transformer"]
        st = [r for r in rows if r["arm"] == "stablegla"]
        tr.sort(key=lambda r: r["init_seed"])
        st.sort(key=lambda r: r["init_seed"])
        n = len(m["paired_seeds"])
        tr_cross = [r["recall"] > THR for r in tr]
        st_cross = [r["recall"] > THR for r in st]
        tr_n = sum(tr_cross)
        st_n = sum(st_cross)
        b = sum(1 for t, s_ in zip(tr_cross, st_cross) if t and not s_)
        c = sum(1 for t, s_ in zip(tr_cross, st_cross) if s_ and not t)
        pf = mcnemar_exact_one_sided(b, c)
        candidate_control_pass = st_n >= g["candidate_control_transitions_min"]
        if tr_n >= 1:
            verdict = "HARNESS_VALIDATED_NO_ESCALATION"
        elif candidate_control_pass:
            verdict = "ESCALATE_STAGE3"
        else:
            verdict = "INCONCLUSIVE_PANEL_BROKEN"
        out = {"campaign": R.name, "stage": m["stage"], "panel": m["panel"],
               "budget": m["budget"], "n_pairs": n,
               "transformer_transitions": tr_n, "stablegla_transitions": st_n,
               "candidate_control_pass": candidate_control_pass,
               "mcnemar_exact_one_sided_p": pf,
               "transformer_recalls": [round(r["recall"], 4) for r in tr],
               "stablegla_recalls": [round(r["recall"], 4) for r in st],
               "verdict": verdict,
               "status": "COMPLETE",
               "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    else:
        time.sleep(60)
        continue
    tmp = R / "decision.json.tmp"
    tmp.write_text(json.dumps(out, indent=2) + "\n")
    os.replace(tmp, R / "decision.json")
    break
