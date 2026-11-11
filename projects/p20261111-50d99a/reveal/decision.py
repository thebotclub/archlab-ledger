#!/usr/bin/env python3
"""ArchLab sealed decision script (generated). Inputs: <results_dir> <attempts.json>.
Prints one JSON object. The verdict is mechanical: every prediction must hold for SUPPORTED, and a sealed
positive control (if any) must reach its threshold or the instrument is suspect."""
import json, pathlib, statistics, sys

PREDICTIONS = json.loads('[{"aggregate": "mean", "criterion": null, "id": "p1", "metric": "accuracy", "op": "<", "threshold": 0.9}]')
POSITIVE_CONTROL = json.loads('{"aggregate": "mean", "criterion": null, "metric": "accuracy", "op": ">=", "threshold": 0.95}')
MIN_VALID_SEEDS = 3
MIN_VALID_POSITIVE = 2

def agg(kind, vals, criterion):
    if kind == "mean": return statistics.fmean(vals)
    if kind == "median": return statistics.median(vals)
    if kind == "min": return min(vals)
    if kind == "max": return max(vals)
    c = criterion
    return {"count_ge": sum(v >= c for v in vals), "count_le": sum(v <= c for v in vals),
            "count_gt": sum(v > c for v in vals), "count_lt": sum(v < c for v in vals)}[kind]

def holds(x, op, t):
    return {"<": x < t, "<=": x <= t, ">": x > t, ">=": x >= t, "==": x == t, "!=": x != t}[op]

res = [json.loads(p.read_text()) for p in sorted(pathlib.Path(sys.argv[1]).glob("*/result.json"))]
attempts = json.load(open(sys.argv[2]))
def valid_for(arm):
    return [r for r in res if r.get("arm", "main") == arm and r.get("status", "ok") == "ok" and isinstance(r.get("metrics"), dict)]
valid = valid_for("main")
out = {"n_results": len(res), "n_valid": len(valid), "n_attempts": len(attempts),
       "min_valid_seeds": MIN_VALID_SEEDS, "predictions": [], "positive_control": None}
def finish(verdict, reason=None):
    out["verdict"] = verdict
    if reason: out["reason"] = reason
    print(json.dumps(out)); sys.exit(0)
if POSITIVE_CONTROL:
    pv = valid_for("positive_control")
    pc = POSITIVE_CONTROL
    vals = [float(r["metrics"][pc["metric"]]) for r in pv if pc["metric"] in r["metrics"]]
    rec = {"metric": pc["metric"], "aggregate": pc.get("aggregate", "mean"), "criterion": pc.get("criterion"),
           "op": pc["op"], "threshold": pc["threshold"], "per_seed": vals, "n_valid": len(vals),
           "min_valid": MIN_VALID_POSITIVE}
    out["positive_control"] = rec
    if len(vals) < MIN_VALID_POSITIVE:
        finish("INSTRUMENT_SUSPECT", f"positive control: only {len(vals)} valid seeds; sealed minimum is {MIN_VALID_POSITIVE}")
    rec["value"] = agg(rec["aggregate"], vals, rec["criterion"])
    rec["holds"] = holds(rec["value"], pc["op"], pc["threshold"])
    if not rec["holds"]:
        finish("INSTRUMENT_SUSPECT", "positive control did not reach the predicted regime: the instrument "
               "could not have shown the effect, so a null result is not evidence")
if len(valid) < MIN_VALID_SEEDS:
    finish("INCONCLUSIVE", f"only {len(valid)} valid seeds; sealed minimum is {MIN_VALID_SEEDS}")
all_hold = True
for p in PREDICTIONS:
    vals = [float(r["metrics"][p["metric"]]) for r in valid if p["metric"] in r["metrics"]]
    if len(vals) < MIN_VALID_SEEDS:
        finish("INSTRUMENT_SUSPECT", f"metric {p['metric']} missing from results")
    value = agg(p["aggregate"], vals, p.get("criterion"))
    ok = holds(value, p["op"], p["threshold"])
    all_hold &= ok
    out["predictions"].append({"id": p["id"], "metric": p["metric"], "aggregate": p["aggregate"],
                               "criterion": p.get("criterion"), "op": p["op"], "threshold": p["threshold"],
                               "value": value, "per_seed": vals, "holds": ok})
finish("SUPPORTED" if all_hold else "REFUTED")
