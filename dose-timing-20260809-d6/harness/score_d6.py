#!/usr/bin/env python3
"""d6 -- timing-schedule follow-up scorer (one-shot; run by monitor.py once
all runs/*.result.json exist and controls.ok is present).

Successor to d2's timing arm (uniform/front/late at 8% recall/lr1e-3/5200).
Question: is the front/late failure a genuine schedule-dependence of onset,
or a budget-halt/forgetting artifact (transiently induced then forgotten)?
Arms A (decay-tail sweep) / B (stronger front dose) / C (mid-loaded).

Bands identical to score_d5.py/aggregate_d2.py (same sealed instrument,
byte-identical eval_salt/battery, sha256-verified by setup_campaign_d6.py).
Probe-curve shape classification reads the per-run probe_curve; the
injection-end read uses each run's registered `extra_probes` (c+1 = the
schedule's burst close, pinned in runs.json + campaign.json). Writes
decision.json in the campaign dir.
"""
import glob
import json
import os
import sys

CAMP = sys.argv[1]
B = {"recall_high": 0.376923076923, "recall_low": 0.065384615385,
     "state_high": 0.90, "state_low": 0.30}


def classify(value, high, low):
    if value >= high:
        return "HIGH"
    if value <= low:
        return "LOW"
    return "DEAD_ZONE"


def load(camp):
    results = {}
    for p in sorted(glob.glob(os.path.join(camp, "runs", "*.result.json"))):
        r = json.load(open(p))
        results[r["run_id"]] = r
    return results


def cap_metric(cap):
    return "recall_acc" if cap == "recall" else "state_acc"


def cap_bands(cap):
    return (B["recall_high"], B["recall_low"]) if cap == "recall" \
        else (B["state_high"], B["state_low"])


def probe_map(run):
    """step -> capability accuracy for this run's capability."""
    m = cap_metric(run["capability"])
    return {int(p["step"]): float(p.get(m, 0.0)) for p in run.get("probe_curve", [])}


def inj_end_step(run):
    """The schedule's burst-CLOSE step (c = round(0.2*steps)); uniform None.
    front closes at c; mid closes at steps//2; late closes at `steps`."""
    sched = run.get("schedule")
    steps = run["steps"]
    c = max(1, int(round(0.2 * steps)))
    if sched == "front":
        return c
    if sched == "mid":
        return steps // 2
    if sched == "late":
        return steps
    return None


def inj_start_step(run):
    """The schedule's burst-START step (injection begins here)."""
    sched = run.get("schedule")
    steps = run["steps"]
    c = max(1, int(round(0.2 * steps)))
    if sched == "front":
        return 0
    if sched == "mid":
        return max(0, steps // 2 - c)
    if sched == "late":
        return steps - c
    return None


def probe_at(run, step):
    """Accuracy at the probe closest to `step` (registered extra_probes put one
    within a couple steps of every injection end)."""
    pm = probe_map(run)
    if not pm:
        return None
    best = min(pm, key=lambda s: abs(s - step))
    return pm[best]


def classify_shape(run):
    """PEAK_THEN_DECAY / FLAT_NEVER_RISES / MONOTONIC_RISE / SUSTAINED_FROM_INJ_END.

    peak = max accuracy over probes up to and including the injection-end read.
    final = accuracy at the last probe.
    """
    high, low = cap_bands(run["capability"])
    c = inj_end_step(run)
    pm = probe_map(run)
    if not pm:
        return {"shape": "NO_PROBES"}
    final = pm[max(pm)]
    if c is None:                       # uniform: no burst close to anchor on
        upto = pm
    else:
        st = inj_start_step(run)
        upto = {s: v for s, v in pm.items() if st <= s <= c + 5}
    peak = max(upto.values()) if upto else 0.0
    if peak >= high and final <= low:
        shape = "PEAK_THEN_DECAY"
    elif peak >= high and final >= high:
        shape = "SUSTAINED_FROM_INJ_END"
    elif final >= high:
        shape = "MONOTONIC_RISE"
    elif peak <= low and final <= low:
        shape = "FLAT_NEVER_RISES"
    else:
        shape = "PARTIAL_OR_AMBIGUOUS"
    return {"shape": shape, "peak_upto_inj_end": peak, "final": final,
            "peak_class": classify(peak, high, low),
            "final_class": classify(final, high, low)}


def main():
    results = load(CAMP)
    sealed = json.load(open(os.path.join(CAMP, "sealed_predictions.json")))
    n_planned = len(json.load(open(os.path.join(CAMP, "runs.json"))))
    out = {"status": None, "n_results": len(results), "n_planned": n_planned}

    def cls(rid):
        r = results[rid]
        hi, lo = cap_bands(r["capability"])
        return classify(r["final_eval"][cap_metric(r["capability"])], hi, lo)

    # ---- controls (unconditional, sealed) ----
    ctrl = {}
    for rid in sealed["controls"]["none"]:
        ctrl[rid] = {"predicted": "LOW", "observed": cls(rid),
                     "correct": cls(rid) == "LOW"}
    for rid in sealed["controls"]["positive"]:
        ctrl[rid] = {"predicted": "HIGH", "observed": cls(rid),
                     "correct": cls(rid) == "HIGH"}
    controls_pass = all(v["correct"] for v in ctrl.values())
    out["controls"] = {"detail": ctrl, "pass": controls_pass}

    # ---- arms: per-run shape + final class + inj_end read ----
    arms = {}
    for arm, rids in sealed["arms"].items():
        arms[arm] = {}
        for rid in rids:
            r = results[rid]
            sh = classify_shape(r)
            c = inj_end_step(r)
            arms[arm][rid] = {
                "schedule": r["schedule"], "dose": r["dose"],
                "steps": r["steps"], "seed": r["init_seed"],
                "inj_end_step": c,
                "acc_at_inj_end": (probe_at(r, c + 1) if c is not None else None),
                **sh,
            }
    out["arm_runs"] = arms

    # ---- pre-registered expectation checks (numeric, sealed) ----
    # Each check compares OBSERVED (peak_class, final_class) per seed against
    # the sealed predictions in sealed_predictions.json. Predictions are the
    # d2-evidence-based forgetting-artifact hypothesis; per-check the sealed
    # alternative (genuine-timing) is recorded too so the verdict can branch.

    def cell(arm, dose, steps):
        """(peak_class, final_class) per seed for a (arm,dose,steps) cell."""
        out_rows = []
        for rid in sealed["arms"][arm]:
            r = results[rid]
            if abs(r["dose"] - dose) < 1e-9 and r["steps"] == steps:
                sh = classify_shape(r)
                out_rows.append((sh["peak_class"], sh["final_class"]))
        return out_rows

    P = sealed["cell_predictions"]   # cellkey -> {"peak":..,"final":..}
    checks = {}

    def score_cell(arm, dose, steps, check_id, meaning):
        obs = cell(arm, dose, steps)
        key = f"{arm}_d{dose}_b{steps}"
        pred = P[key]
        ok = bool(obs) and all(
            pc in pred["peak"] and fc in pred["final"] for (pc, fc) in obs)
        checks[check_id] = {"cell": key, "observed": obs,
                            "predicted": pred, "pass": ok, "meaning": meaning}
        return obs

    # Decay-tail sweep (Arm A) at front/8%: forgetting predicts the inj_end
    # read is tail-invariant AND the final never IMPROVES with a longer tail.
    score_cell("A", 0.08, 650,  "A_0x", "front 8% 0x tail (5200-step dose in "
               "130-step burst): peak==final==LOW (no room to consolidate)")
    score_cell("A", 0.08, 5200, "A_1x", "replicates d2 front@5200: peak LOW/"
               "DEAD_ZONE (transient), final LOW both seeds")
    score_cell("A", 0.08, 10400, "A_2x", "front 8% 2x tail: inj_end read same "
               "as 1x (tail-invariant), final LOW (more decay, not less)")
    score_cell("A", 0.08, 20800, "A_4x", "front 8% 4x tail: inj_end read same "
               "as 1x, final LOW (most decay)")

    # Stronger front dose (Arm B) at 5200: under pure recency/decay a 2x dose
    # still decays (final LOW); it does NOT reliably rescue to HIGH.
    score_cell("B", 0.08, 5200, "B_8", "replicates d2 front 8% @5200 final LOW")
    score_cell("B", 0.16, 5200, "B_16", "front 16% @5200: final NOT reliably "
               "HIGH (decays); >=1 seed non-HIGH")

    # Mid-loaded (Arm C) at 5200: separates recency-to-end from absolute
    # position. Forgetting predicts mid is intermediate (>=1 seed non-LOW).
    score_cell("C", 0.08, 5200, "C_8", "mid 8% @5200: intermediate between "
               "front(LOW) and late(HIGH-capable); >=1 seed DEAD_ZONE/HIGH")
    # Late reference at 5200 (d2 seed 3003 went HIGH): recency to end helps.
    score_cell("late_ref", 0.08, 5200, "LATE_8", "late 8% @5200: recency to "
               "end -> >=1 seed reaches HIGH final (replicates d2 late split)")

    # Uniform reference at 5200 (the d2 HIGH cell, schedule-invariance anchor).
    score_cell("uniform_ref", 0.08, 5200, "UNI_8", "uniform 8% @5200: HIGH "
               "final both seeds (replicates d2 known-positive)")

    # ---- derived forgetting-vs-timing discriminators ----
    # (1) inj_end tail-invariance across the A sweep (0x/1x/2x/4x).
    a_peak_classes = [checks[k]["observed"] for k in ("A_0x", "A_1x", "A_2x", "A_4x")]
    peaks_flat = all(
        len({pc for (pc, _) in cellobs}) <= 1 and
        all(pc == a_peak_classes[0][0][0] for (pc, _) in cellobs)
        for cellobs in a_peak_classes if cellobs) if all(a_peak_classes) else False
    # (2) final never improves with longer tail.
    finals_low_at_0x = all(fc == "LOW" for (_, fc) in checks["A_0x"]["observed"]) \
        if checks["A_0x"]["observed"] else False
    finals_nonimproving = all(
        all(fc == "LOW" for (_, fc) in checks[k]["observed"])
        for k in ("A_1x", "A_2x", "A_4x") if checks[k]["observed"])
    # (3) transient exists (some inj_end read non-LOW).
    transient = any(d["peak_class"] in ("HIGH", "DEAD_ZONE")
                    for arm in arms for d in arms[arm].values())
    # (4) mid intermediate; (5) front16 not reliably HIGH.
    mid_intermediate = checks["C_8"]["pass"]
    front16_not_high = checks["B_16"]["pass"]

    out["expectation_checks"] = checks
    out["n_checks_pass"] = sum(1 for v in checks.values() if v["pass"])
    out["n_checks"] = len(checks)
    out["derived"] = {
        "inj_end_tail_invariant": peaks_flat,
        "final_never_improves_with_tail": finals_low_at_0x and finals_nonimproving,
        "transient_signature_present": transient,
        "mid_intermediate": mid_intermediate,
        "front16_not_reliably_HIGH": front16_not_high,
    }

    # ---- verdict ----
    if len(results) < n_planned:
        verdict = "PENDING"
    elif not controls_pass:
        verdict = "VOID_CONTROLS_FAILED"
    else:
        dv = out["derived"]
        forgetting = (dv["inj_end_tail_invariant"]
                      and dv["final_never_improves_with_tail"]
                      and dv["transient_signature_present"]
                      and dv["mid_intermediate"])
        genuine_timing = ((not dv["transient_signature_present"])
                          and dv["front16_not_reliably_HIGH"]
                          and not dv["mid_intermediate"])
        if forgetting:
            verdict = "SCHEDULE_IS_FORGETTING_ARTIFACT"
        elif genuine_timing:
            verdict = "SCHEDULE_DEPENDENCE_GENUINE"
        elif dv["final_never_improves_with_tail"] or dv["mid_intermediate"]:
            verdict = "MIXED_PARTIAL_FORGETTING"
        else:
            verdict = "INDETERMINATE"
    out["verdict"] = verdict

    with open(os.path.join(CAMP, "decision.json.tmp"), "w") as f:
        json.dump(out, f, indent=2)
    os.replace(os.path.join(CAMP, "decision.json.tmp"),
               os.path.join(CAMP, "decision.json"))
    print(json.dumps({"verdict": verdict, "n_results": len(results),
                      "n_planned": n_planned, "n_checks_pass": n_pass},
                     indent=2))


if __name__ == "__main__":
    main()
