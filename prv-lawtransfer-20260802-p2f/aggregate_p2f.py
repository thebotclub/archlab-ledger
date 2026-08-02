"""p2f aggregation: mechanical evaluation of the pre-registered gates in
campaign.json against the two arms' frozen-battery eval outputs. No
amendments -- mirrors aggregate_p2c/p2e style. Writes decision.json into the
campaign dir.

Usage: python aggregate_p2f.py
Reads:  runs/p2f_arm_nowindow.eval.json, runs/p2f_arm_w4096.eval.json,
        runs/p2f_arm_nowindow.result.json, runs/p2f_arm_w4096.result.json
Writes: ~/archlab2-runs/prv-lawtransfer-20260802-p2f/decision.json
"""
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CAMPAIGN_DIR = os.path.expanduser("~/archlab2-runs/prv-lawtransfer-20260802-p2f")

NEAR = [64, 101, 161, 255, 404, 641, 1016, 1611]        # G0 strata (<=1611)
FAR = [4048, 4144, 4425, 4705, 4986, 5266, 5547, 5828,  # GS strata (4048->7792)
       6108, 6389, 6670, 6950, 7231, 7511, 7792]
W_IN = [64, 101, 161, 255, 404, 641, 1016, 1611, 2553, 4048]   # GW in-window
W_OUT = [4144, 4425, 4705, 4986, 5266, 5547, 5828, 6108, 6389,
         6670, 6950, 7231, 7511, 7792]                          # GW out


def _ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(xs, ys):
    rx, ry = _ranks(xs), _ranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = sum((a - mx) ** 2 for a in rx) ** 0.5
    dy = sum((b - my) ** 2 for b in ry) ** 0.5
    if dx == 0 or dy == 0:
        return None  # degenerate (e.g. all recalls identical): rho undefined
    return num / (dx * dy)


def load(tag):
    ev = json.load(open(f"{HERE}/runs/p2f_{tag}.eval.json"))
    res_path = f"{HERE}/runs/p2f_{tag}.result.json"
    res = json.load(open(res_path)) if os.path.exists(res_path) else {}
    return ev, res


def main():
    campaign = json.load(open(f"{CAMPAIGN_DIR}/campaign.json"))
    arms = {}

    # --- arm_nowindow ---------------------------------------------------
    ev, res = load("arm_nowindow")
    rec = {int(k): v for k, v in ev["recall_by_distance_strict"].items()}
    g0 = all(rec.get(s, 0.0) >= 0.90 for s in NEAR)
    far_rec = [rec.get(s, 0.0) for s in FAR]
    rho = spearman(FAR, far_rec)
    if all(v >= 0.90 for v in far_rec):
        shape = "FLAT"
    elif rho is not None and rho < -0.7 and rec.get(7792, 1.0) < 0.5:
        shape = "DECLINING"
    else:
        shape = "MIXED"
    arms["arm_nowindow"] = {
        "seed": res.get("init_seed"), "window": 0,
        "structural_window_check": ev.get("structural_window_check"),
        "G0_capability": {"pass": g0,
                          "per_stratum": {str(s): rec.get(s) for s in NEAR}},
        "GS_shape_nowindow": {"classification": shape,
                              "spearman_rho_far": rho,
                              "final_stratum_recall": rec.get(7792),
                              "per_stratum": {str(s): rec.get(s) for s in FAR}},
        "recall_by_distance": {str(k): rec[k] for k in sorted(rec)},
        "p_chance": ev.get("p_chance_measured_matched_regime"),
        "final_train_loss": res.get("final_train_loss"),
        "tokens": res.get("tokens"), "mix_totals": res.get("mix_totals"),
    }

    # --- arm_w4096 ------------------------------------------------------
    ev_w, res_w = load("arm_w4096")
    rec_w = {int(k): v for k, v in ev_w["recall_by_distance_strict"].items()}
    p_chance = ev_w.get("p_chance_measured_matched_regime") or 0.0
    gw_in = all(rec_w.get(s, 0.0) >= 0.90 for s in W_IN)
    gw_out = all(rec_w.get(s, 1.0) <= p_chance + 0.05 for s in W_OUT)
    gw = gw_in and gw_out
    g0_w = all(rec_w.get(s, 0.0) >= 0.90 for s in NEAR)
    arms["arm_w4096"] = {
        "seed": res_w.get("init_seed"), "window": 4096,
        "structural_window_check": ev_w.get("structural_window_check"),
        "G0_capability": {"pass": g0_w,
                          "per_stratum": {str(s): rec_w.get(s) for s in NEAR}},
        "GW_window_control": {"pass": gw, "in_ok": gw_in, "out_ok": gw_out,
                              "p_chance": p_chance,
                              "per_stratum_in": {str(s): rec_w.get(s) for s in W_IN},
                              "per_stratum_out": {str(s): rec_w.get(s) for s in W_OUT}},
        "recall_by_distance": {str(k): rec_w[k] for k in sorted(rec_w)},
        "final_train_loss": res_w.get("final_train_loss"),
        "tokens": res_w.get("tokens"), "mix_totals": res_w.get("mix_totals"),
    }

    # --- campaign outcome, per campaign.json's fixed precedence ----------
    if not gw:
        outcome = ("INSTRUMENT_SUSPECT: GW_window_control failed -- the "
                   "positive-control arm did not reproduce a sharp step at "
                   "W=4096 at this scale, so the whole campaign is "
                   "instrument-suspect; no GS claim is made. Shapes reported "
                   "for diagnosis only.")
    elif not g0:
        outcome = ("INCONCLUSIVE_UNDERTRAINED: arm_nowindow failed "
                   "G0_capability at 350M tokens -- not a confirmation of "
                   "decline; continuation decision goes to the operator/Hani "
                   "per the staged-budget pre-registration.")
    elif shape == "FLAT":
        outcome = ("FLAT: the from-scratch no-window model holds recall "
                   ">=0.90 at every far stratum through 7792 -- p2d arm4's "
                   "gradual far-field decline is a pretrained-checkpoint "
                   "property, NOT fundamental; the p2d/p2e suspension of "
                   "LAW_ARITHMETIC_TRANSFERS is resolvable in the law's "
                   "favor with the residual attributed to checkpoint "
                   "long-context capability.")
    elif shape == "DECLINING":
        outcome = ("DECLINING: the far-field decline generalizes to "
                   "from-scratch training on the recall task; the law's "
                   "far-field account needs an explicit capability-decay "
                   "term; the p2d/p2e suspension stands.")
    else:
        outcome = "MIXED: shape reported, no claim."

    decision = {
        "campaign": "prv-lawtransfer-20260802-p2f",
        "aggregated_by": "aggregate_p2f.py, mechanical evaluation of "
                         "pre-registered gates in campaign.json; no amendments",
        "gates_source": campaign.get("preregistered_gates"),
        "arms": arms,
        "campaign_outcome": outcome,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    out = f"{CAMPAIGN_DIR}/decision.json"
    with open(out + ".tmp", "w") as f:
        json.dump(decision, f, indent=1)
    os.replace(out + ".tmp", out)
    print(json.dumps({"campaign_outcome": outcome,
                      "GS": arms["arm_nowindow"]["GS_shape_nowindow"]["classification"],
                      "G0_nowindow": g0, "GW": gw}, indent=1))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
