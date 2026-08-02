#!/usr/bin/env python3
"""Mechanical evaluation of p2d results against the pre-registered gates and
frozen predictions in ~/archlab2-runs/prv-lawtransfer-20260802-p2d/campaign.json.
No amendments. Predictions and strata partitions are read verbatim from
campaign.json (fixed 2026-08-02 00:40Z, before any p2d probe was scored) --
this script does not compute or refit anything, only compares.
"""
import json, math, os, time

OUT = os.path.expanduser("~/archlab-p2d")
CAMP_DIR = os.path.expanduser("~/archlab2-runs/prv-lawtransfer-20260802-p2d")
CAMPAIGN = json.load(open(os.path.join(CAMP_DIR, "campaign.json")))

ARM_TAGS = {
    "phi3": "arm_phi3",
    "mistral_v01": "arm_mistral_v01",
    "phi3_w1024": "arm_phi3_w1024",
    "mistral_nowindow": "arm_mistral_nowindow",
}
WINDOWED = {"phi3", "mistral_v01", "phi3_w1024"}  # arm4 is the nowindow counterfactual


def eval_arm(tag):
    pred_key = ARM_TAGS[tag]
    pred = CAMPAIGN["frozen_predictions"][pred_key]
    d = json.load(open(os.path.join(OUT, f"p2d_{tag}.json")))
    rb = {int(k): v for k, v in d["recall_by_distance_strict"].items()}
    n_completed = len(rb)
    n_target = len(pred["in_strata"]) + len(pred["out_strata"])

    # G0: capability, strict recall >= 0.90 at every completed stratum d <= 256
    near = [k for k in rb if k <= 256]
    g0 = bool(near) and all(rb[k] >= 0.90 for k in near)

    # G1: structural, read straight off run_p2d.py's own mask probe
    g1r = d["G1_enforcement"]
    if tag in WINDOWED:
        w_minus_1 = d["window_used"] - 1
        g1_pass = ("error" not in g1r
                    and g1r.get("builder") == "create_sliding_window_causal_mask"
                    and g1r.get("max_attendable_distance") == w_minus_1)
    else:
        n_probe = d["window_used"] + 128
        g1_pass = ("error" not in g1r
                    and g1r.get("builder") == "create_causal_mask"
                    and g1r.get("max_attendable_distance") == n_probe - 1)
    void = None if g1_pass else "G1 structural check did not demonstrate the pre-registered mask behaviour"

    # GP: per-stratum |observed-predicted| <= 0.05 on >= K of N completed strata
    per_stratum = {}
    hits = 0
    for k in pred["in_strata"]:
        if k in rb:
            err = abs(rb[k] - pred["pred_in"])
            per_stratum[k] = {"observed": rb[k], "predicted": pred["pred_in"], "abs_err": round(err, 4)}
            hits += err <= 0.05
    if pred["out_strata"]:
        for k in pred["out_strata"]:
            if k in rb:
                err = abs(rb[k] - pred["pred_out"])
                per_stratum[k] = {"observed": rb[k], "predicted": pred["pred_out"], "abs_err": round(err, 4)}
                hits += err <= 0.05
    K = math.ceil(20.0 / 24.0 * n_completed) if n_completed < n_target else 20
    gp_pass = hits >= K

    # GB: boundary location
    if tag in WINDOWED:
        in_completed = [k for k in pred["in_strata"] if k in rb]
        out_completed = [k for k in pred["out_strata"] if k in rb]
        in_ok = bool(in_completed) and all(rb[k] >= 0.90 for k in in_completed)
        if out_completed:
            first_out = min(out_completed)
            out_ok = rb[first_out] <= pred["pred_out"] + 0.10
        else:
            out_ok = None  # boundary strata not reached -> INCONCLUSIVE, handled below
        gb_pass = in_ok and (out_ok is True)
        gb_evaluable = bool(in_completed) and bool(out_completed)
    else:
        all_completed = [k for k in pred["in_strata"] if k in rb]
        gb_pass = bool(all_completed) and all(rb[k] >= 0.90 for k in all_completed)
        gb_evaluable = bool(all_completed)

    truncated = d.get("truncated_at_stratum")
    inconclusive = (not g0) or (truncated is not None and not gb_evaluable)

    return {
        "model": d["model"], "tag": tag, "window_used": d["window_used"],
        "config_sliding_window": d["config_sliding_window"],
        "G0_capability": {"pass": g0},
        "G1_structural": {"pass": g1_pass, **g1r},
        "GP_prediction": {"pass": gp_pass, "hits": hits, "K_required": K,
                           "n_completed_strata": n_completed, "per_stratum": per_stratum},
        "GB_boundary": {"pass": gb_pass, "evaluable": gb_evaluable},
        "truncated_at_stratum": truncated,
        "inconclusive": inconclusive,
        "pass_if": bool(g0 and g1_pass and gp_pass and gb_pass and not inconclusive),
        "void": void,
    }


def main():
    arms = {ARM_TAGS[t]: eval_arm(t) for t in ARM_TAGS}
    a1, a2, a3 = arms["arm_phi3"], arms["arm_mistral_v01"], arms["arm_phi3_w1024"]
    a4 = arms["arm_mistral_nowindow"]

    if a4["GB_boundary"]["pass"] is False and not a4["inconclusive"]:
        # arm4 predicts recall>=0.90 everywhere; a cliff surviving mask removal
        # is a confound per campaign.json's interpretation_fixed_in_advance.
        outcome = "CONFOUND_ALERT: arm4 (window disabled) shows a cliff -- interpretation of arms 1-3 suspended, notify Hani"
    elif not (a1["pass_if"] and a2["pass_if"]):
        outcome = "PREDICTIONS_DO_NOT_HOLD: p2c characterization does not survive fresh draws; p2b LAW_DOES_NOT_TRANSFER stands unhedged"
    elif a3["pass_if"]:
        outcome = "LAW_ARITHMETIC_TRANSFERS: frozen predictions hold on deployed checkpoints, including an unseen boundary"
    else:
        outcome = "TRANSFERS_ON_FITTED_BOUNDARIES_ONLY: arms 1-2 pass, arm 3 (unseen boundary) fails"

    decision = {
        "campaign": "prv-lawtransfer-20260802-p2d",
        "aggregated_by": "aggregate_p2d.py, mechanical evaluation of pre-registered gates + frozen predictions in campaign.json; no amendments",
        "arms": arms,
        "campaign_outcome": outcome,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    tmp = os.path.join(CAMP_DIR, ".decision.tmp")
    with open(tmp, "w") as fh:
        json.dump(decision, fh, indent=1)
    os.replace(tmp, os.path.join(CAMP_DIR, "decision.json"))
    print(f"decision.json written: {outcome}")


if __name__ == "__main__":
    main()
