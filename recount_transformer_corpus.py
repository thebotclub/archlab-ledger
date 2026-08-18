#!/usr/bin/env python3
"""Recount the transformer null corpus from run artifacts.

Single source of truth for every transformer count quoted in the preprint and
the executive summary. Earlier drafts quoted 88, 168 and 172 at various points;
those were hand-maintained and did not reconcile. Run this instead of counting
by hand, and cite its output.

The headline claim is scoped to the hard MQAR panel family (pairs80, p80x384).
Campaigns aw/ax use the easy48 panel and are the pre-registered falsification
ladder, NOT part of the null corpus -- they are reported separately.
"""
import collections
import glob
import json
import os
import re

PANEL_FAMILY = ("pairs80", "p80x384")
LADDER_CAMPAIGNS = {"zoology-repro-20260731-aw", "zoology-repro-stage2-20260731-ax"}
CROSSING_CRITERION = 0.8  # pre-registered: recall > 0.8


def lr_from_arm(arm):
    """Recover base_lr from arm names like `lr6e15_3em3` (budget 6e15, lr 3e-3).

    Campaign aq names its escalated arms this way and records the rate nowhere
    else. The trailing token is <mantissa>em<exp> meaning mantissa x 10^-exp.
    """
    if not isinstance(arm, str):
        return None
    match = re.search(r"_(\d+)em(\d+)$", arm)
    if not match:
        return None
    return float(match.group(1)) * (10 ** -int(match.group(2)))


def campaign_base_lr(runs_root, campaign, _cache={}):
    """Fall back to the campaign's pre-registration when a runner omits the LR.

    Not every runner writes lr/base_lr into result.json -- campaign az does not.
    campaign.json does record it, sometimes as prose ("3e-3 (harness default in
    train.py -- deliberately NOT overridden)"), so parse a leading float out of
    whatever is there rather than requiring a bare number.
    """
    if campaign in _cache:
        return _cache[campaign]
    value = None
    path = os.path.join(runs_root, campaign, "campaign.json")
    try:
        raw = json.load(open(path)).get("base_lr")
        if isinstance(raw, (int, float)):
            value = float(raw)
        elif isinstance(raw, str):
            match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", raw)
            if match:
                value = float(match.group())
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        value = None
    _cache[campaign] = value
    return value


def load_transformer_runs(runs_root):
    pattern = os.path.join(runs_root, "*", "**", "result.json")
    for path in glob.glob(pattern, recursive=True):
        campaign = path.split(os.sep + "archlab-runs" + os.sep)[1].split(os.sep)[0]
        try:
            payload = json.load(open(path))
        except (json.JSONDecodeError, OSError):
            continue
        for run in payload.get("results", []):
            if run.get("arch") != "transformer":
                continue
            lr = run.get("lr") or run.get("base_lr")
            lr_source = "result.json"
            if not lr:
                lr = lr_from_arm(run.get("arm"))
                lr_source = "arm-name" if lr else lr_source
            if not lr:
                lr = campaign_base_lr(runs_root, campaign)
                lr_source = "campaign.json" if lr else "UNRECORDED"
            yield dict(
                campaign=campaign,
                seed=run.get("seed"),
                panel=run.get("panel"),
                budget=run.get("budget"),
                lr=lr,
                lr_source=lr_source,
                recall=run.get("recall") or 0.0,
            )


def summarize(label, runs):
    if not runs:
        print("\n== {}: no runs found".format(label))
        return
    budgets = [r["budget"] for r in runs if r["budget"]]
    lrs = sorted({r["lr"] for r in runs if r["lr"]})
    cells = {(r["panel"], r["budget"], r["lr"]) for r in runs}
    crossings = [r for r in runs if r["recall"] > CROSSING_CRITERION]
    panels = dict(collections.Counter(r["panel"] for r in runs))
    print("\n== {}".format(label))
    print("   runs:                {}".format(len(runs)))
    print("   distinct seeds:      {}".format(len({r["seed"] for r in runs})))
    print("   panels:              {}".format(panels))
    print("   budget span:         {:.3g} - {:.3g} FLOPs".format(min(budgets), max(budgets)))
    print("   learning rates:      {}".format(lrs))
    print("   panel x budget x lr: {} cells".format(len(cells)))
    for source, note in (("arm-name", "encoded in the arm name"),
                         ("campaign.json", "runner omitted it from result.json")):
        found = collections.Counter(r["campaign"] for r in runs
                                    if r.get("lr_source") == source)
        if found:
            print("   LR via {:<14} {} ({})".format(source + ":", dict(found), note))
    missing = collections.Counter(r["campaign"] for r in runs
                                  if r.get("lr_source") == "UNRECORDED")
    if missing:
        print("   *** LR UNRECORDED:    {} -- these runs are counted but their "
              "LR is not attributable; do not quote the LR list as complete"
              .format(dict(missing)))
    print("   crossings (>{}):    {}".format(CROSSING_CRITERION, len(crossings)))
    print("   max recall:          {:.4f}".format(max(r["recall"] for r in runs)))


def main():
    runs_root = os.path.expanduser("~/archlab-runs")
    all_runs = list(load_transformer_runs(runs_root))
    corpus = [r for r in all_runs
              if r["campaign"] not in LADDER_CAMPAIGNS and r["panel"] in PANEL_FAMILY]
    ladder = [r for r in all_runs if r["campaign"] in LADDER_CAMPAIGNS]
    other = [r for r in all_runs
             if r["campaign"] not in LADDER_CAMPAIGNS and r["panel"] not in PANEL_FAMILY]

    summarize("NULL CORPUS -- hard panel family (the headline claim)", corpus)
    print("   per-campaign:        {}".format(
        dict(collections.Counter(r["campaign"] for r in corpus))))
    summarize("FALSIFICATION LADDER aw/ax -- easy48 (reported separately)", ladder)
    summarize("OTHER PANELS -- early calibration, not in the headline claim", other)


if __name__ == "__main__":
    main()
