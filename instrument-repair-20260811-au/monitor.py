#!/usr/bin/env python3
"""STAGE A monitor -- instrument-repair-20260811-au.

Completeness-precondition discipline (Hani 15:30Z NOTICE, at lesson): derives
the expected run count from campaign.json's pilot seed list, REFUSES to score
until every seed's result.json exists with 1 result row, and writes
decision.json ATOMICALLY. Reports the oracle gate outcome (the headline),
measured p_chance, elimination margin, and the pilot transition count.

Boundary/censoring discipline (directive hard limits): any d_collapse/alpha
readout emits a censoring status and inequalities, never bare floats. For
this pilot the registered readout is the transition count only; alpha
analysis is Stage B's, not Stage A's.
"""
import json
import os
import pathlib
import time

ROOT = pathlib.Path("/home/hani/archlab-runs/instrument-repair-20260811-au")
CAMPAIGN = json.loads((ROOT / "campaign.json").read_text())
SEEDS = CAMPAIGN["pilot"]["seeds"]
EXPECTED = len(SEEDS)
OUT = ROOT / "decision.json"


def load_results():
    rows = []
    for seed in SEEDS:
        p = ROOT / f"shard_seed{seed}" / "result.json"
        if not p.exists():
            return None
        payload = json.loads(p.read_text())
        res = payload.get("results", [])
        if len(res) != 1:                      # one run per seed, by manifest
            return None
        rows.append(res[0])
    return rows


def main():
    oracle = json.loads((ROOT / "oracle_report.json").read_text())
    rows = load_results()
    if rows is None:
        have = [s for s in SEEDS
                if (ROOT / f"shard_seed{s}" / "result.json").exists()]
        print(f"{time.strftime('%H:%M:%SZ', time.gmtime())} waiting: "
              f"{len(have)}/{EXPECTED} seeds done {have}", flush=True)
        return

    transitions = sum(1 for r in rows if r["recall"] > 0.8)
    per_seed = {str(r["seed"]): round(r["recall"], 4) for r in rows}
    g0a = oracle["verdict"] == "PASS"
    decision = {
        "campaign": "instrument-repair-20260811-au",
        "stage": "A (instrument repair; claim-ineligible, scratch salt)",
        "completeness_check": f"{len(rows)}=={EXPECTED} from campaign.json seeds",
        "elimination_margin": CAMPAIGN["panel"]["elimination_margin"],
        "measured_p_chance": oracle["measured_p_chance"],
        "p_chance_used": oracle["p_chance_used"],
        "oracle_threshold": oracle["threshold"],
        "oracle_stratum_accuracy": oracle["oracle_stratum_accuracy"],
        "G0a_oracle": {"pass": g0a, "breaches": oracle["breaches"]},
        "pilot": {"seeds": SEEDS, "per_seed_recall": per_seed,
                  "transitions": transitions, "gate": ">= 3/6",
                  "A4_gate_pass": transitions >= 3},
        "censoring": {
            "status": "NOT_MEASURED",
            "note": "d_collapse/alpha are Stage B readouts; this pilot reports "
                    "transition counts only. Receptive field L*(W-1)+1 = 53 at "
                    "L=4,W=14: any collapse claim beyond d=52 would be "
                    "RIGHT_CENSORED on this instrument -- stated here so no "
                    "future reader derives a float alpha from this pilot.",
            "alpha_measurable_range": "none registered for Stage A",
        },
        "headline": ("G0a_oracle " + oracle["verdict"] +
                     (f" -- measured p_chance {oracle['measured_p_chance']:.4f}, "
                      f"threshold {oracle['threshold']:.4f}; "
                      f"pilot {transitions}/6 transitions" if g0a else
                      " -- battery REJECTED before training")),
        "decided_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(decision, indent=1) + "\n")
    os.replace(tmp, OUT)
    print(f"decision written: {decision['headline']}", flush=True)


if __name__ == "__main__":
    main()
