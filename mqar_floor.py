#!/usr/bin/env python3
"""Bayes-optimal NO-RETRIEVAL accuracy ("cheat floor") for an MQAR panel.

WHY THIS EXISTS. Three generations of panel design were cleared by ARGUING
about what a no-retrieval strategy could do — first from a distinctness
assumption (the rule `pairs - queries + 1 >= NVAL`), then from a uniqueness
constraint, then from a hand-picked oracle set. All three arguments were wrong,
and each was found only after the panel had been used. This script replaces the
argument with a measured number. Run it for every panel BEFORE sealing, and
record the result in campaign.json.

THE MODEL. Values are drawn i.i.d. WITH replacement from an alphabet of size
NVAL (`data.py`: vals = rng.integers(0, NVAL, size=pairs)), so the values in a
sequence form a MULTISET. An adversary that never matches a key still knows the
whole context and which values earlier answers consumed, so its best guess for
the query at ordinal j is the MODE of the not-yet-asked pool:

    acc(j) = E[ max_x count_x(R_j) ] / |R_j| ,    |R_j| = pairs - j

The panel floor is the mean over the scored ordinals. Note this is strictly
above 1/NVAL for every finite pool: duplicates concentrate posterior mass.

    usage:  mqar_floor.py PAIRS QUERIES [NVAL] [--trials N]
            mqar_floor.py --table          # every panel in the programme
"""
import sys
import numpy as np


def floor_for(pairs, queries, nval=16, trials=40000, seed=12345):
    rng = np.random.default_rng(seed)
    accs = []
    for j in range(queries):
        pool = pairs - j
        if pool <= 0:
            break
        draws = rng.integers(0, nval, size=(trials, pool))
        counts = np.zeros((trials, nval), dtype=np.int32)
        for v in range(nval):
            counts[:, v] = (draws == v).sum(axis=1)
        accs.append((counts.max(axis=1) / pool).mean())
    return float(np.mean(accs))


PANELS = [
    ("easy48", 8, 8, "at, bb, bc"),
    ("elimsafe80", 28, 8, "au (abandoned)"),
    ("seq112 legacy", 32, 16, "c, e"),
    ("pairs80", 80, 40, "m, q, aj, ak, az, ap-g1, null corpus"),
    ("seq384", 64, 32, "ap-g2"),
    ("pairs48x448", 48, 24, "ap-g3"),
]


def main():
    args = sys.argv[1:]
    if "--table" in args or not args:
        print("Bayes no-retrieval floor, NVAL=16 (uniform guess = %.4f)\n" % (1 / 16))
        print("%-16s %-9s %-10s %s" % ("panel", "P/Q", "floor", "campaigns"))
        for name, p, q, who in PANELS:
            print("%-16s %-9s %-10.4f %s" % (name, "%d/%d" % (p, q), floor_for(p, q), who))
        print("\npermval16 (values a PERMUTATION, P=NVAL=16, ONE probe at ordinal 0):")
        print("  pool is a constant multiset, every value exactly once, nothing yet asked")
        print("  => modal count 1 / pool 16 = %.6f  == 1/NVAL exactly" % (1 / 16))
        print("  NB single-probe is load-bearing: at Q=8 the floor rises to ~0.083,")
        print("     which coincides with the legacy 0.0825 gate — a multi-probe")
        print("     permval16 panel would sit ON that gate and pass. Enforce Q=1.")
        return 0
    pairs, queries = int(args[0]), int(args[1])
    nval = int(args[2]) if len(args) > 2 and not args[2].startswith("--") else 16
    trials = 40000
    if "--trials" in args:
        trials = int(args[args.index("--trials") + 1])
    f = floor_for(pairs, queries, nval, trials)
    print("pairs=%d queries=%d NVAL=%d -> no-retrieval floor %.4f (uniform %.4f)"
          % (pairs, queries, nval, f, 1.0 / nval))
    return 0


if __name__ == "__main__":
    sys.exit(main())
