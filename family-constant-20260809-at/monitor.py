#!/usr/bin/env python3
"""Aggregates all 4 shards' result.json into decision.json once complete.

Per-arm logic:
  transition: per-run in_window_accuracy > transition_threshold (bb's
    bimodality-corrected signal). Control arm uses aggregate recall > 0.8.
  d_collapse: among transitioned runs, pool per-distance accuracies; the
    largest d with pooled acc >= 0.8 is d_collapse; a clean collapse requires
    a larger observed d with pooled acc <= chance_ceiling (0.15).
  alpha = d_collapse / W.
Gates G0-G4 evaluated exactly as pre-registered in campaign.json. No gate
amendment; this monitor only READS results and applies the frozen gates.
"""
import json, math, pathlib

R = pathlib.Path(__file__).resolve().parent
m = json.load(open(R / "campaign.json"))
G = m["preregistered_gate"]
TR = G["transition_threshold_in_window"]
CHANCE = G["chance_ceiling"]
MINTR = G["min_transitions_per_arm"]

def load_rows():
    rows = []
    for sh in m["shards"]:
        p = R / sh["id"] / "result.json"
        if not p.exists():
            print(f"INCOMPLETE: have 0 of {expected_run_count() or '?'} expected "
                  f"result rows — {sh['id']}/result.json does not exist yet; "
                  f"refusing to score (decision.json NOT written)")
            return None
        d = json.load(open(p))
        rows.extend(d["results"])
    return rows

def expected_run_count():
    """Authoritative denominator from the sealed shards manifest:
    one run per (seed, arm) pair. Returns None (never a guess) if the
    manifest is missing the fields needed to compute it."""
    try:
        return sum(len(sh["seeds"]) * len(sh["arms"]) for sh in m["shards"])
    except (KeyError, TypeError):
        return None

# Completeness precondition (added 2026-08-09 after the 14:22Z premature
# verdict — Hani 15:30Z NOTICE). run_at.py writes each shard's result.json
# INCREMENTALLY per seed, so "all 4 result.jsons exist" does NOT mean the
# campaign is finished (it fired at 7/28). Refuse to score until every
# manifest run has a result row; write decision.json atomically only after
# this check passes. This is the 4th false-"finished" artifact class in this
# program (bc x2 INCOMPLETE_FAILED, false a01 outage, this one); the same
# guard belongs in every future campaign monitor, not just this copy.
def completeness_check(rows):
    exp = expected_run_count()
    got = len(rows) if rows else 0
    if exp is None:
        print("INCOMPLETE: expected run count could not be derived from "
              "campaign.json's shards manifest (missing seeds/arms) — "
              "refusing to score rather than guess (decision.json NOT written)")
        return False
    if got < exp:
        print(f"INCOMPLETE: have {got} of {exp} expected result rows — "
              f"refusing to score (decision.json NOT written)")
        return False
    return True


def transitioned(rows, arm_pred, ctrl=False):
    out = []
    for r in rows:
        if not arm_pred(r):
            continue
        if ctrl:
            if r.get("recall", 0) > 0.8:
                out.append(r)
        else:
            if r.get("in_window_accuracy", 0) > TR:
                out.append(r)
    return out

def pool_per_distance(runs):
    """average per-distance accuracy across runs (simple mean of per-run acc)."""
    acc = {}
    for r in runs:
        for d, a in r["per_distance"].items():
            acc.setdefault(int(d), []).append(a)
    return {d: sum(v) / len(v) for d, v in acc.items()}

def collapse_alpha(runs, W):
    pd = pool_per_distance(runs)
    ds = sorted(pd)
    intact = [d for d in ds if pd[d] >= 0.8]
    if not intact:
        return None, None, pd
    d_col = max(intact)
    collapsed_above = [d for d in ds if d > d_col and pd[d] <= CHANCE]
    clean = len(collapsed_above) > 0
    alpha = d_col / W
    return (d_col if clean else None), alpha, pd

def arm_rows(rows, family=None, n_layers=None, arm_name=None):
    def pred(r):
        if arm_name:
            return r.get("arm") == arm_name
        if family:
            return r.get("family") == family and (n_layers is None or r.get("n_layers") == n_layers)
        return False
    return [r for r in rows if pred(r)]

def main():
    # Sealed-verdict guard: decision.json is never clobbered once written.
    if (R / "decision.json").exists():
        print("REFUSING: decision.json already exists — verdicts are sealed, "
              "not overwritten (exiting without scoring)")
        return
    rows = load_rows()
    if rows is None:
        return
    if not completeness_check(rows):
        return
    W = m["shards"][0]["window"]  # fixed W=14 on all candidate shards
    out = {"campaign": m["campaign"], "status": "COMPLETE", "window": W,
           "n_results": len(rows), "n_expected": expected_run_count()}

    # G0 control
    ctrl = transitioned(rows, lambda r: r.get("arm") == "transformer_full", ctrl=True)
    n_ctrl_total = len([r for r in rows if r.get("arm") == "transformer_full"])
    g0 = len(ctrl) >= 12
    out["control"] = {"n_transitioned": len(ctrl), "n_total": n_ctrl_total, "G0_pass": g0}

    arms = {}
    # anchor gla L8
    gla = transitioned(rows, lambda r: r.get("family") == "gla" and r.get("n_layers") == 8)
    dc, alpha, pd = collapse_alpha(gla, W)
    g1 = (dc is not None) and (dc in (W - 2, W))  # collapse at window edge within resolution
    arms["gla_win14_L8"] = {"n_transitioned": len(gla), "d_collapse": dc,
                            "alpha": alpha, "per_distance": pd, "G1_pass": g1}
    # plain depth sweep
    plain_alphas = {}
    for L in (4, 8, 12):
        pr = transitioned(rows, lambda r, L=L: r.get("family") == "plain" and r.get("n_layers") == L)
        dc, alpha, pd = collapse_alpha(pr, W)
        plain_alphas[L] = alpha
        arms[f"plain_win14_L{L}"] = {"n_transitioned": len(pr), "d_collapse": dc,
                                     "alpha": alpha, "per_distance": pd}
    # G2 plain alpha (L8 reference)
    p8 = arms["plain_win14_L8"]
    g2 = (p8["n_transitioned"] >= MINTR and p8["d_collapse"] is not None
          and p8["alpha"] is not None and 1.5 <= p8["alpha"] <= 3.0
          and alpha_gt(p8["alpha"], arms["gla_win14_L8"]["alpha"]))
    # G3 depth ordering
    have = [plain_alphas[L] for L in (4, 8, 12) if plain_alphas[L] is not None]
    g3 = len(have) == 3 and have[0] <= have[1] <= have[2]

    out["arms"] = arms
    out["gates"] = {"G0": g0, "G1": g1, "G2": g2, "G3": g3}

    if not g0:
        verdict = "INSTRUMENT_SUSPECT"
    elif g1 and g2:
        verdict = "FAMILY_CONSTANT_CONFIRMED"
    elif g1 and not g2 and p8["d_collapse"] is None and p8["n_transitioned"] >= MINTR:
        verdict = "ALPHA_NOT_STABLE"
    elif g1 and p8["alpha"] is not None and abs(p8["alpha"] - 1.0) <= (2.0 / W):
        verdict = "PLAIN_REACH_IS_WINDOW"
    elif p8["n_transitioned"] < MINTR or arms["gla_win14_L8"]["n_transitioned"] < MINTR:
        verdict = "UNDERPOWERED"
    else:
        verdict = "ALPHA_NOT_STABLE"
    out["verdict"] = verdict
    # atomic write: tmp + os.replace so no consumer ever reads a partial file
    tmp = R / "decision.json.tmp"
    tmp.write_text(json.dumps(out, indent=2) + "\n")
    import os
    os.replace(tmp, R / "decision.json")
    print("VERDICT", verdict)

def alpha_gt(a, b):
    return a is not None and b is not None and a > b

if __name__ == "__main__":
    main()
