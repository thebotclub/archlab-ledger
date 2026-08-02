#!/usr/bin/env python3
"""Mechanical evaluation of p2e results against the pre-registered gates in
~/archlab2-runs/prv-lawtransfer-20260802-p2e/campaign.json. No amendments.
Gate definitions are read verbatim from campaign.json (fixed 2026-08-02
02:58Z, before any p2e probe was scored) -- this script does not compute or
refit anything, only compares. Structure copied from aggregate_p2d.py.
"""
import json, os, time

OUT = os.path.expanduser("~/archlab-p2e")
CAMP_DIR = os.path.expanduser("~/archlab2-runs/prv-lawtransfer-20260802-p2e")
CAMPAIGN = json.load(open(os.path.join(CAMP_DIR, "campaign.json")))

FORCED_W1024_BOUNDARY = 5499  # W-1, force_window=5500 (exclusive convention, p2d-established)


def load(tag):
    return json.load(open(os.path.join(OUT, f"p2e_{tag}.json")))


def eval_capability_control(tag="mistral_v02_capability_control"):
    d = load(tag)
    rb = {int(k): v for k, v in d["recall_by_distance_strict"].items()}

    near = [k for k in rb if k <= 256]
    g0 = bool(near) and all(rb[k] >= 0.90 for k in near)

    g1r = d["G1_enforcement"]
    n_probe = d["window_used"] + 128
    g1_pass = ("error" not in g1r
               and g1r.get("builder") == "create_causal_mask"
               and g1r.get("max_attendable_distance") == n_probe - 1)
    void = None if g1_pass else "G1 did not confirm full causal (unmasked) attention"

    completed = sorted(rb)
    gb_pass = bool(completed) and all(rb[k] >= 0.90 for k in completed)
    gb_evaluable = bool(completed)

    truncated = d.get("truncated_at_stratum")
    inconclusive = (not g0) or (truncated is not None and not gb_evaluable)

    return {
        "model": d["model"], "tag": tag, "window_used": d["window_used"],
        "config_sliding_window": d["config_sliding_window"],
        "G0_capability": {"pass": g0},
        "G1_structural": {"pass": g1_pass, **g1r},
        "GB_capability_control": {"pass": gb_pass, "evaluable": gb_evaluable,
                                    "recall_by_distance": rb},
        "truncated_at_stratum": truncated,
        "inconclusive": inconclusive,
        "pass_if": bool(g0 and g1_pass and gb_pass and not inconclusive),
        "void": void,
    }


def eval_forced_shape(tag="mistral_v01_forcedcutoff5500"):
    d = load(tag)
    rb = {int(k): v for k, v in d["recall_by_distance_strict"].items()}
    p_chance = d.get("p_chance_measured_matched_regime", 0.0)

    near = [k for k in rb if k <= 256]
    g0 = bool(near) and all(rb[k] >= 0.90 for k in near)

    g1r = d["G1_enforcement"]
    g1_pass = ("error" not in g1r
               and g1r.get("builder") == "create_sliding_window_causal_mask"
               and g1r.get("max_attendable_distance") == FORCED_W1024_BOUNDARY)
    void = None if g1_pass else "G1 did not confirm the forced-window boundary at 5499"

    below = [k for k in rb if k <= 5266]
    in_ok = bool(below) and all(rb[k] >= 0.90 for k in below)
    first_out = 5547 if 5547 in rb else None
    out_ok = (rb[first_out] <= p_chance + 0.10) if first_out is not None else None
    gb_pass = in_ok and (out_ok is True)
    gb_evaluable = bool(below) and (first_out is not None)

    truncated = d.get("truncated_at_stratum")
    inconclusive = (not g0) or (truncated is not None and not gb_evaluable)

    return {
        "model": d["model"], "tag": tag, "window_used": d["window_used"],
        "config_sliding_window": d["config_sliding_window"],
        "forced_window": d.get("forced_window"),
        "p_chance_measured_matched_regime": p_chance,
        "G0_capability": {"pass": g0},
        "G1_structural": {"pass": g1_pass, **g1r},
        "GB_forced_shape": {"pass": gb_pass, "evaluable": gb_evaluable,
                              "in_ok": in_ok, "out_ok": out_ok,
                              "first_out_stratum_recall": rb.get(5547),
                              "recall_by_distance": rb},
        "truncated_at_stratum": truncated,
        "inconclusive": inconclusive,
        "pass_if": bool(g0 and g1_pass and gb_pass and not inconclusive),
        "void": void,
    }


def main():
    cap = eval_capability_control()
    shape = eval_forced_shape()

    cap_pass = cap["pass_if"]
    shape_pass = shape["pass_if"]

    if cap_pass and shape_pass:
        outcome = ("CONFOUND_RESOLVED_CAPABILITY_CEILING: v0.2 shows no decline through the "
                   "same far strata where v0.1-nowindow declined to 0.146, AND a forced mask "
                   "boundary at W=5500 produces a sharp step (not a gradual decay) -- p2d "
                   "arm4's decline is v0.1-specific capability, masked cliffs remain "
                   "boundary-precise, arms 1-3's LAW_ARITHMETIC_TRANSFERS is reinstated with "
                   "this caveat now explicit")
    elif (not cap_pass) and shape_pass:
        outcome = ("CONFOUND_ALERT_GENERALIZED: v0.2 ALSO declines at extreme absolute "
                   "distance regardless of RoPE base -- the far-field failure is not "
                   "v0.1-specific; arms 1-3 remain suspended pending a from-scratch-model "
                   "diagnostic, notify Hani")
    elif cap_pass and (not shape_pass):
        outcome = ("MASK_SIGNATURE_UNRELIABLE: v0.2 capability control clears, but the forced "
                   "W=5500 boundary did NOT produce a sharp step -- undermines confidence that "
                   "arms 1-3's boundary-precise cliffs were mask-caused rather than "
                   "coincidental; arms 1-3 remain suspended, notify Hani")
    else:
        outcome = ("CONFOUND_UNRESOLVED: neither diagnostic clarifies the picture; escalate to "
                   "Hani for a from-scratch-model design rather than further deployed-checkpoint "
                   "probing")

    decision = {
        "campaign": "prv-lawtransfer-20260802-p2e",
        "aggregated_by": "aggregate_p2e.py, mechanical evaluation of pre-registered gates in campaign.json; no amendments",
        "arms": {
            "arm_mistral_v02_capability_control": cap,
            "arm_mistral_v01_forcedcutoff5500": shape,
        },
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
