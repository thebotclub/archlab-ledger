#!/usr/bin/env python3
import json, os, pathlib, time
R = pathlib.Path(__file__).resolve().parent
m = json.load(open(R / "campaign.json"))
g = m["preregistered_gates"]
THR = g["crossing_criterion"]

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
    elif len(rows) == 2 * len(m["replicated_seeds"]):
        tr = sorted([r for r in rows if r["arm"] == "transformer"], key=lambda r: r["init_seed"])
        st = sorted([r for r in rows if r["arm"] == "stablegla"], key=lambda r: r["init_seed"])
        tr_cross = [r["recall"] > THR for r in tr]
        n_cross = sum(tr_cross)

        if n_cross == len(tr):
            rep = "REPLICATED"
        elif n_cross == 0:
            rep = "FAILED_TO_REPLICATE"
        else:
            rep = "PARTIAL_SEED_FRAGILE"

        # Probe calibration is asked ONLY of transformers that actually crossed.
        chance = tr[0].get("probe_chance", 0.0625)
        valid = [r for r in tr
                 if abs(r.get("probe_shuffled_control", 9) - chance) <= 0.02]
        crossing_valid = [r for r in valid if r["recall"] > THR]
        if not crossing_valid:
            calib = "NOT_ASSESSABLE_NO_VALID_CROSSING_TRANSFORMER"
        elif min(r["probe_best"] for r in crossing_valid) >= 0.50:
            calib = "PROBE_VALIDATED_WITHIN_ARCHITECTURE"
        elif max(r["probe_best"] for r in crossing_valid) <= chance + 0.02:
            calib = "PROBE_ARCHITECTURE_BIASED_AV_NEEDS_REQUALIFYING"
        else:
            calib = "INDETERMINATE"

        out = {"campaign": R.name, "stage": m["stage"], "panel": m["panel"],
               "budget": m["budget"],
               "replicated_seeds": m["replicated_seeds"],
               "transformer_recalls": [round(r["recall"], 4) for r in tr],
               "transformer_final_losses": [r["final_loss"] for r in tr],
               "stablegla_recalls": [round(r["recall"], 4) for r in st],
               "transformer_crossings": f"{n_cross}/{len(tr)}",
               "replication_verdict": rep,
               "ax_observed": m["what_ax_observed"],
               "probe_chance": chance,
               "probe_best_by_seed": {str(r["init_seed"]): round(r["probe_best"], 4) for r in tr},
               "probe_shuffled_by_seed": {str(r["init_seed"]): round(r.get("probe_shuffled_control", -1), 4) for r in tr},
               "probe_best_candidate_by_seed": {str(r["init_seed"]): round(r["probe_best"], 4) for r in st},
               "probe_models_excluded_as_leaking": [r["init_seed"] for r in tr if r not in valid],
               "probe_calibration_verdict": calib,
               "status": "COMPLETE",
               "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    else:
        time.sleep(60)
        continue
    tmp = R / "decision.json.tmp"
    tmp.write_text(json.dumps(out, indent=2) + "\n")
    os.replace(tmp, R / "decision.json")
    break
