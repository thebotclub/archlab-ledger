#!/usr/bin/env python3
"""Lab 3 d6 -- timing-schedule follow-up, successor to d2's timing arm.

Per Hani 2026-08-09 ~04:20Z directive: Lab 3 gets the idle local V100s; the
operator owns choosing the next dosing question from the closed d1..d5/cs1
record. The record points here: d2's timing arm (uniform/front/late at 8%
recall/lr1e-3/5200) found uniform transitions 2/2, front fails 2/2, late
splits 1/2 -- the campaign's most interesting new physics (onset boundary is
not purely a function of cumulative dose). TIMING-FOLLOWUP-DESIGN-NOTE-
20260804.md (written per Hani 2026-08-04T14:45Z, "design note only, do not
launch yet") proposed arms A/B/C to separate genuine schedule-dependence from
a budget-halt/forgetting artifact. d4/d5 (law recalibration) are COMPLETE and
P2/p2g are on cloud, so capacity has now cleared; this is that design, sealed
and launched.

Reuses d2..d5's sealed instrument (eval_salt + battery + injection pools)
byte-for-byte (sha256-verified below against d2/d5 campaign.json before
sealing) -- continuation-of-sealed-lineage precedent (d2c/d4/d5). ONE additive
harness change: per-run `extra_probes` in runs.json place a read exactly at
each schedule's injection-window close (the default geomspace probes miss it),
and a new "mid" schedule (Arm C); both registered and sha-pinned below.

Usage: setup_campaign_d6.py <campaign_dir>
"""
import hashlib
import json
import os
import shutil
import sys

HARNESS = os.path.dirname(os.path.abspath(__file__))
PY = "/home/hani/archlab/.venv/bin/python"
D2 = "/home/hani/archlab3-runs/dose-boundary-20260803-d2"
D5 = "/home/hani/archlab3-runs/dose-boundary-20260804-d5"

CAMP = sys.argv[1]
BATCH, BLOCK = 32, 1024
LR1 = 1e-3
SEEDS = [3074, 3075]                  # fresh, next free in Lab 3's 3000s
N_WORKERS = 4                          # all 4 idle V100s (Lab 1/2 want none now)

assert os.path.isdir(os.path.expanduser("~/.archlab-suffix-claims/d6")), \
    "suffix d6 lockfile claim missing"
os.makedirs(CAMP, exist_ok=False)

# ---- reuse d2's sealed salt + pools + battery byte-for-byte ----
shutil.copy(os.path.join(D2, "eval_salt.txt"), os.path.join(CAMP, "eval_salt.txt"))
shutil.copytree(os.path.join(D2, "battery"), os.path.join(CAMP, "battery"))
salt = open(os.path.join(CAMP, "eval_salt.txt")).read().strip()
salt_sha = hashlib.sha256(salt.encode()).hexdigest()

d2_camp = json.load(open(os.path.join(D2, "campaign.json")))
d5_camp = json.load(open(os.path.join(D5, "campaign.json")))
assert salt_sha == d2_camp["eval_salt_sha256"] == d5_camp["eval_salt_sha256"], \
    "salt mismatch vs d2/d5 -- refusing to seal"

RECALL_CEILING = d2_camp["battery_predictions"]["recall_ceiling"]   # 0.476923...
HIGH, LOW = "HIGH", "LOW"


def c_for(steps):
    return max(1, int(round(0.2 * steps)))


def extra_probes(schedule, steps):
    """Place a read exactly at the injection-window close (peak anchor)."""
    c = c_for(steps)
    if schedule == "front":
        return sorted({c, c + 1})
    if schedule == "mid":
        m = steps // 2
        return sorted({m, m + 1})
    if schedule == "late":
        return sorted({steps - 1})           # closes at end == final read
    return []                                # uniform: default probes suffice


runs = []


def add(run_id, group, cap, dose, sched, lr, seed, steps):
    runs.append({
        "run_id": run_id, "group": group, "capability": cap, "dose": dose,
        "schedule": sched, "lr": lr, "seed": seed, "steps": steps,
        "batch": BATCH, "block": BLOCK,
        "extra_probes": extra_probes(sched, steps),
        "worker": 0,
    })


# ---- controls (4): none (floor) + uniform-8% known-positive (d2 HIGH) ----
for s in SEEDS:
    add(f"none_d0_u_s{s}", "control", "none", 0.0, "uniform", LR1, s, 5200)
    add(f"uni_d8_b5200_s{s}", "control", "recall", 0.08, "uniform", LR1, s, 5200)

# ---- Arm A: decay-tail sweep, front 8%, tails {0x,1x,2x,4x} ----
for steps in (650, 5200, 10400, 20800):
    for s in SEEDS:
        add(f"frA_d8_b{steps}_s{s}", "A", "recall", 0.08, "front", LR1, s, steps)

# ---- Arm B: stronger front dose at 5200 ----
for dose, dtag in ((0.08, "8"), (0.16, "16")):
    for s in SEEDS:
        add(f"frB_d{dtag}_b5200_s{s}", "B", "recall", dose, "front", LR1, s, 5200)

# ---- Arm C: mid-loaded 8% at 5200 ----
for s in SEEDS:
    add(f"midC_d8_b5200_s{s}", "C", "recall", 0.08, "mid", LR1, s, 5200)

# ---- late reference at 5200 (d2's split cell) ----
for s in SEEDS:
    add(f"late_d8_b5200_s{s}", "late_ref", "recall", 0.08, "late", LR1, s, 5200)

assert len(runs) == 4 + 8 + 4 + 2 + 2 == 20, f"expected 20 runs, built {len(runs)}"
assert len({r["run_id"] for r in runs}) == 20, "duplicate run_id"

with open(os.path.join(CAMP, "runs.json"), "w") as f:
    json.dump(runs, f, indent=1)


def cellkey(arm, dose, steps):
    return f"{arm}_d{dose}_b{steps}"


# ---- sealed cell predictions (d2-evidence-based forgetting hypothesis) ----
# peak = class at the injection-end read; final = class at the last probe.
# Prediction = the d2-observed behaviour extended by the forgetting
# (budget-halt) hypothesis; each cell's sealed alternative is the genuine-
# timing branch. Numeric basis: recall ceiling 0.477 (HIGH >= 0.377),
# LOW <= 0.065 (p_chance+0.05), DEAD_ZONE between.
cell_predictions = {
    # Arm A decay-tail sweep. d2 front@5200 (1x): peak LOW/DEAD_ZONE (0.0225
    # max), final LOW. Forgetting predicts the inj_end read is tail-invariant
    # (set by exposure, not by what follows) and final never improves with a
    # longer clean tail.
    cellkey("A", 0.08, 650):   {"peak": [LOW, "DEAD_ZONE"], "final": [LOW]},
    cellkey("A", 0.08, 5200):  {"peak": [LOW, "DEAD_ZONE"], "final": [LOW]},
    cellkey("A", 0.08, 10400): {"peak": [LOW, "DEAD_ZONE"], "final": [LOW]},
    cellkey("A", 0.08, 20800): {"peak": [LOW, "DEAD_ZONE"], "final": [LOW]},
    # Arm B stronger front. Forgetting: doubling dose still decays -> final
    # NOT reliably HIGH (>=1 seed non-HIGH). peak may be higher (DEAD_ZONE).
    cellkey("B", 0.08, 5200):  {"peak": [LOW, "DEAD_ZONE"], "final": [LOW]},
    cellkey("B", 0.16, 5200):  {"peak": [LOW, "DEAD_ZONE", HIGH],
                                "final": [LOW, "DEAD_ZONE"]},
    # Arm C mid. Forgetting: mid is intermediate (recency to end helps) ->
    # >=1 seed reaches DEAD_ZONE/HIGH final (NOT uniformly LOW like front).
    cellkey("C", 0.08, 5200):  {"peak": [LOW, "DEAD_ZONE", HIGH],
                                "final": ["DEAD_ZONE", HIGH]},
    # late reference: d2 late split 1/2 HIGH (recency to end helps) -> >=1 HIGH.
    cellkey("late_ref", 0.08, 5200): {"peak": [LOW, "DEAD_ZONE", HIGH],
                                      "final": [LOW, HIGH]},
    # uniform known-positive (control + schedule-invariance anchor): d2 2/2 HIGH.
    cellkey("uniform_ref", 0.08, 5200): {"peak": [HIGH], "final": [HIGH]},
}

sealed = {
    "sealed_utc_note": "binding once ledger-committed+pushed before any cell "
        "in this campaign trains; scored by score_d6.py. Successor to d2's "
        "timing arm per Hani 2026-08-09 ~04:20Z (Lab 3 gets the idle V100s; "
        "operator owns the next dosing question). Design from d2/analysis/"
        "TIMING-FOLLOWUP-DESIGN-NOTE-20260804.md (Hani 2026-08-04T14:45Z). "
        "Question: is d2's front/late failure at 8% a genuine schedule-"
        "dependence of onset, or a budget-halt/forgetting artifact "
        "(transiently induced then forgotten)?",
    "reused_instrument": "byte-identical eval_salt.txt/battery/injection-pools "
        "to d2..d5 (sha256-verified above before sealing); continuation of the "
        "same sealed measurement, not a fresh independent replication. ONE "
        "additive harness change: per-run extra_probes place a read exactly at "
        "each schedule's injection-window close (pinned in runs.json + "
        "campaign.json), plus a new 'mid' schedule (Arm C); default behaviour "
        "for uniform/front/late is byte-identical to the d2..d5 instrument.",
    "parent": "dose-boundary-20260803-d2 (COMPLETE; timing arm: uniform 2/2 "
        "HIGH, front 2/2 LOW with a 0.0225-then-0 transient, late split 1/2)",
    "thresholds": {"recall_high": 0.376923076923, "recall_low": 0.065384615385,
                   "recall_ceiling": RECALL_CEILING},
    "controls": {
        "none": [f"none_d0_u_s{s}" for s in SEEDS],
        "positive": [f"uni_d8_b5200_s{s}" for s in SEEDS],
    },
    "arms": {
        "A": [f"frA_d8_b{st}_s{s}" for st in (650, 5200, 10400, 20800)
              for s in SEEDS],
        "B": [f"frB_d{dt}_b5200_s{s}" for dt in ("8", "16") for s in SEEDS],
        "C": [f"midC_d8_b5200_s{s}" for s in SEEDS],
        "late_ref": [f"late_d8_b5200_s{s}" for s in SEEDS],
        "uniform_ref": [f"uni_d8_b5200_s{s}" for s in SEEDS],
    },
    "cell_predictions": cell_predictions,
    "gates": {
        "G_controls": "both none LOW AND both uniform-8% HIGH, else VOID "
            "(do not read anything else).",
        "verdicts": {
            "SCHEDULE_IS_FORGETTING_ARTIFACT": "inj_end read tail-invariant "
                "across Arm A AND final never improves with a longer tail AND "
                "a transient signature exists AND mid is intermediate.",
            "SCHEDULE_DEPENDENCE_GENUINE": "NO transient anywhere (all inj_end "
                "reads LOW) AND front-16% still fails to reach HIGH AND mid is "
                "NOT intermediate (uniformly LOW like front).",
            "MIXED_PARTIAL_FORGETTING": "final decays with tail OR mid "
                "intermediate, but not the full forgetting conjunction.",
            "INDETERMINATE": "none of the above (e.g. a longer tail IMPROVES "
                "the front final -- would refute the forgetting hypothesis).",
        },
        "no_efficacy_stopping": True, "no_gate_amendment_after_data": True,
    },
}
with open(os.path.join(CAMP, "sealed_predictions.json"), "w") as f:
    json.dump(sealed, f, indent=2)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


with open(os.path.join(CAMP, "controls.ok"), "w") as f:
    json.dump({
        "inherited_from": "dose-boundary-20260803-d2/controls.ok (via d2c/d4/d5 "
                          "continuation precedent)",
        "note": "Same sealed instrument, byte-identical salt/pools/battery "
                "(sha256-verified above). This campaign's own controls (none "
                "LOW + uniform-8% HIGH) are sealed in sealed_predictions.json "
                "and scored in decision.json before any verdict is read.",
        "d2_controls_pass": True,
    }, f, indent=2)

harness_files = ["models.py", "data_dose.py", "eval_d1.py", "train_d1.py",
                 "queue_runner_multi.py", "monitor.py", "score_d6.py",
                 "setup_campaign_d6.py"]
campaign = {
    "campaign": os.path.basename(CAMP.rstrip("/")),
    "lab": "Lab 3 -- The Capability Dosing Lab",
    "stage": "P1 timing-schedule follow-up: is d2's front/late failure at 8% "
             "genuine schedule-dependence or a budget-halt/forgetting artifact "
             "(arms A decay-tail sweep / B stronger front / C mid-loaded)",
    "parent": "dose-boundary-20260803-d2 (timing arm) + d2/analysis/"
              "TIMING-FOLLOWUP-DESIGN-NOTE-20260804.md",
    "charter": "~/archlab3/LAB3-CHARTER.md",
    "operator": "hub headless operator, 2026-08-09 (Hani ~04:20Z directive: "
                "Lab 3 gets the idle V100s; operator owns the next dosing "
                "question from the closed d1..d5 record)",
    "claim_eligible": True,
    "prereg": "sealed_predictions.json (this dir) + ledger mirror "
              "~/archlab-ledger/dose-timing-20260809-d6/",
    "eval_salt_sha256": salt_sha,
    "corpus": d2_camp["corpus"],
    "model": d2_camp["model"],
    "pool_salts": d2_camp["pool_salts"],
    "injection_pools": d2_camp["injection_pools"],
    "battery_manifest_sha256": sha(os.path.join(CAMP, "battery", "battery_manifest.json")),
    "battery_predictions": d2_camp["battery_predictions"],
    "budget_per_run": {"batch": BATCH, "block_size": BLOCK,
                       "steps_list": sorted({r["steps"] for r in runs})},
    "dose_semantics": d2_camp["dose_semantics"],
    "schedules": ["uniform", "front", "mid", "late"],
    "extra_probes_note": "per-run extra_probes in runs.json place a read at "
                         "each schedule's injection-window close; additive "
                         "only, default probes unchanged",
    "disk_policy": d2_camp["disk_policy"],
    "scratch_ckpt_dir": "/dev/shm/archlab-d6-ckpt",
    "gpu": "all 4 idle local V100s (Lab 1 closed, p2g on cloud); "
           "claim-file queue_runner_multi.py",
    "n_runs": len(runs),
    "n_workers": N_WORKERS,
    "seeds_used": SEEDS,
    "smoke_seed": 3998,
    "python": PY,
    "harness_files": harness_files,
    "harness_sha256": {fn: sha(os.path.join(HARNESS, fn)) for fn in harness_files
                        if os.path.exists(os.path.join(HARNESS, fn))},
    "coordination": "suffix d6 claimed via ~/.archlab-suffix-claims/d6; "
                    "working dir ~/archlab-d6; reuses d2's sealed instrument "
                    "byte-for-byte (see sealed_predictions.json)",
    "sealed_predictions_sha256": sha(os.path.join(CAMP, "sealed_predictions.json")),
}
with open(os.path.join(CAMP, "campaign.json"), "w") as f:
    json.dump(campaign, f, indent=2)

print(json.dumps({
    "salt_sha256": salt_sha, "n_runs": len(runs),
    "n_cells": len(cell_predictions),
    "harness_changed": {fn: campaign["harness_sha256"][fn][:12]
                        for fn in ("train_d1.py", "data_dose.py")},
}, indent=2))
