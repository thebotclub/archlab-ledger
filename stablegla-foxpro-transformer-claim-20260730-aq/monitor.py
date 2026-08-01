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
    T = st + gl
    denom = math.comb(2 * n, n)
    p = 0.0
    for k in range(st, min(T, n) + 1):
        if T - k > n:
            continue
        p += math.comb(T, k) * math.comb(2 * n - T, n - k) / denom
    return p

def wait_for(shards, expect_n):
    while True:
        rows_by_id, failures, total = {}, [], 0
        for s in shards:
            d = R / s["id"]
            f = d / "result.json"
            if f.exists():
                try:
                    r = json.load(open(f))["results"]
                    if len(r) == expect_n(s):
                        rows_by_id[s["id"]] = r
                        total += 1
                    elif not alive(d / "pid"):
                        failures.append(s["id"] + ":partial-result")
                except Exception as e:
                    failures.append(s["id"] + ":invalid:" + type(e).__name__)
            elif not alive(d / "pid"):
                failures.append(s["id"] + ":exited-without-result")
        if failures:
            return None, failures
        if total == len(shards):
            return rows_by_id, None
        time.sleep(30)

# --- phase 1: core sealed claim ---
core_rows, failures = wait_for(m["core_shards"], lambda s: 2 * len(s["seeds"]))
if failures:
    out = {"campaign": R.name, "status": "INCOMPLETE_FAILED", "claim_eligible": True,
           "gate_result": "FAIL", "phase": "core", "failures": failures}
    tmp = R / "decision.json.tmp"
    tmp.write_text(json.dumps(out, indent=2) + "\n")
    os.replace(tmp, R / "decision.json")
else:
    rows = [r for rs in core_rows.values() for r in rs]
    tr = [r for r in rows if r["arm"] == "transformer"]
    fx = [r for r in rows if r["arm"] == "foxpro"]
    tr.sort(key=lambda r: r["init_seed"]); fx.sort(key=lambda r: r["init_seed"])
    n = len(m["train_seeds"])
    fx_tr_ct = sum(1 for r in fx if r["recall"] > THR)
    tr_tr_ct = sum(1 for r in tr if r["recall"] > THR)
    deltas = [f_["recall"] - t_["recall"] for f_, t_ in zip(fx, tr)]
    pf = fisher_one_sided(fx_tr_ct, tr_tr_ct, n)
    gates = {
        "finite_complete_pairs": len(tr) == n and len(fx) == n,
        "foxpro_transitions_ge_10": fx_tr_ct >= g["foxpro_transitions_min"],
        "transformer_transitions_le_1": tr_tr_ct <= g["transformer_transitions_max"],
        "fisher_exact_one_sided_p_le_0_005": pf <= g["fisher_exact_one_sided_alpha"],
        "worst_pair_ge_minus_0_10": min(deltas) >= g["worst_pair_delta_min"],
    }
    out = {"campaign": R.name, "stage": m["stage"], "claim_eligible": True,
           "panel": m["panel"], "budget": m["budget"],
           "foxpro_transitions": fx_tr_ct, "transformer_transitions": tr_tr_ct, "n_pairs": n,
           "fisher_exact_one_sided_p": pf,
           "foxpro_recalls": [round(r["recall"], 4) for r in fx],
           "transformer_recalls": [round(r["recall"], 4) for r in tr],
           "pair_deltas": [round(d, 4) for d in deltas],
           "gates": gates,
           "status": "PASS" if all(gates.values()) else "FAIL",
           "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "note": "robustness grid + token-matched control still running; see robustness_decision.json"}
    tmp = R / "decision.json.tmp"
    tmp.write_text(json.dumps(out, indent=2) + "\n")
    os.replace(tmp, R / "decision.json")

# --- phase 2: robustness grid + token-matched control (non-claim, descriptive) ---
rob_rows, failures = wait_for(m["robustness_shards"], lambda s: len(s["seeds"]))
if failures:
    out2 = {"campaign": R.name, "status": "ROBUSTNESS_INCOMPLETE_FAILED", "failures": failures}
else:
    arms = {}
    for s in m["robustness_shards"]:
        rows = rob_rows[s["id"]]
        arms[s["id"]] = {"transitions": sum(1 for r in rows if r["recall"] > THR),
                         "n": len(rows), "budget": s["budget"], "base_lr": s.get("base_lr"),
                         "reference": s.get("reference", ""),
                         "recalls": [round(r["recall"], 4) for r in rows]}
    out2 = {"campaign": R.name, "stage": "robustness grid + token-matched control",
            "claim_eligible": False, "arms": arms, "status": "ROBUSTNESS_COMPLETE",
            "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
tmp2 = R / "robustness_decision.json.tmp"
tmp2.write_text(json.dumps(out2, indent=2) + "\n")
os.replace(tmp2, R / "robustness_decision.json")
