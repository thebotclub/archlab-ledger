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

def fisher_one_sided(st, gl, n):
    # P(stable transitions >= st) under hypergeometric with margins n/n, total transitions T
    T = st + gl
    denom = math.comb(2 * n, n)
    p = 0.0
    for k in range(st, min(T, n) + 1):
        if T - k > n:
            continue
        p += math.comb(T, k) * math.comb(2 * n - T, n - k) / denom
    return p

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
        out = {"campaign": R.name, "status": "INCOMPLETE_FAILED", "claim_eligible": True,
               "gate_result": "FAIL", "failures": failures}
    elif len(rows) == 2 * len(m["train_seeds"]):
        gla = [r for r in rows if r["arm"] == "gla"]
        st = [r for r in rows if r["arm"] == "stablegla"]
        gla.sort(key=lambda r: r["init_seed"])
        st.sort(key=lambda r: r["init_seed"])
        n = len(m["train_seeds"])
        st_tr = sum(1 for r in st if r["recall"] > THR)
        gl_tr = sum(1 for r in gla if r["recall"] > THR)
        deltas = [s_["recall"] - g_["recall"] for s_, g_ in zip(st, gla)]
        pf = fisher_one_sided(st_tr, gl_tr, n)
        gates = {
            "finite_complete_pairs": len(gla) == n and len(st) == n,
            "stablegla_transitions_ge_8": st_tr >= g["stablegla_transitions_min"],
            "gla_transitions_le_1": gl_tr <= g["gla_transitions_max"],
            "fisher_exact_one_sided_p_le_0_005": pf <= g["fisher_exact_one_sided_alpha"],
            "worst_pair_ge_minus_0_10": min(deltas) >= g["worst_pair_delta_min"],
        }
        out = {"campaign": R.name, "stage": m["stage"], "claim_eligible": True,
               "panel": m["panel"], "budget": m["budget"],
               "stablegla_transitions": st_tr, "gla_transitions": gl_tr, "n_pairs": n,
               "fisher_exact_one_sided_p": pf,
               "stablegla_recalls": [round(r["recall"], 4) for r in st],
               "gla_recalls": [round(r["recall"], 4) for r in gla],
               "pair_deltas": [round(d, 4) for d in deltas],
               "gates": gates,
               "status": "PASS" if all(gates.values()) else "FAIL",
               "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    else:
        time.sleep(30)
        continue
    tmp = R / "decision.json.tmp"
    tmp.write_text(json.dumps(out, indent=2) + "\n")
    os.replace(tmp, R / "decision.json")
    break
