# G3 evaluated — and why its failure is not informative about the law

Computed 2026-08-01, after p2a reported. Recorded here rather than folded into
p2a's decision.json, because p2a's decision recorded G3 as NOT EVALUATED and that
record should stand as written.

## Result as the gate was registered

Gate: `|observed − (f + (1−f)·p_chance)| ≤ 0.05`.

| arm | f | observed | predicted | error | verdict |
|---|---|---|---|---|---|
| phi3 | 0.667 | 0.7917 | 0.6667 | **+0.1250** | FAIL |
| mistral_v01 | 0.700 | 0.8042 | 0.7000 | **+0.1042** | FAIL |
| mistral_v02_nowindow | 0.700 | 0.9979 | 0.7000 | **+0.2979** | FAIL |
| gemma2_hybrid | 0.700 | 0.9354 | 0.7000 | **+0.2354** | FAIL |

**G3 fails on all four arms and is not amended.**

## Why that failure says almost nothing about the law

The law predicts a ceiling **for a workload**. p2a's probe set is not a workload:
its strata were deliberately clustered around W to resolve the boundary to within
a few tokens. Both terms of the gate are therefore design artifacts.

`f` is one. It is 0.667/0.700 because that is the ratio of strata we chose to put
inside versus outside the window, not because any traffic looks like that.

The out-of-window recall is the worse one. For phi3 it computes to 0.375, and the
reason is visible immediately:

| distance | recall | |
|---|---|---|
| 2048 | **1.000** | W+1 — still perfect |
| 2051 | **1.000** | W+4 — still perfect |
| 2063 | 0.042 | |
| 2111 | 0.042 | |
| 2303 | 0.042 | |
| 3072 | 0.125 | |

Mean over all six = 0.375. Mean over the four beyond W+16 = **0.0625**. The
"out-of-window recall" that made G3 fail is dominated by two strata that sit one
and four tokens past the window and have not fallen off the cliff yet — which is
the inclusive-boundary finding (G4), not a calibration result.

The two negative arms fail G3 for the trivial reason that they have no window, so
`f + (1−f)·p_chance` predicts 0.70 for a model that scores ~1.0 everywhere. That
was never a meaningful prediction for them.

## A trap in my own analysis, flagged rather than reported as a finding

I also computed a "refined" form, `f·r_in + (1−f)·r_out`, using the measured
in- and out-of-window recalls. It fits all four arms with error **exactly
0.0000**.

That is not a better model. It is an algebraic identity — the weighted mean of
two group means over the same partition reconstructs the aggregate by
construction. An error of exactly zero on four independent datasets is the
signature of a tautology, not of a discovery, and it must not be presented as
the law being "refined and now fitting".

## What is actually needed

A battery stratified across the full distance range rather than clustered at the
boundary — the shape p1d used (32 strata from 24 to 1000) and for exactly this
reason. Then `f` is a property of the battery's spread, out-of-window recall is
not dominated by two boundary points, and the arithmetic can be tested.

That is campaign **p2b**, pre-registered separately. G3 stays failed here.

## The far-field residual is smaller than p2a reported, and may be noise

p2a's decision quoted a residual of 0.083–0.125 as the reason G2 failed. Computed
over strata beyond W+16, phi3's mean is **0.0625** — i.e. 1.5 correct out of 24
per stratum. At n=24 the 95% interval on 1/24 spans roughly 0.001–0.21, so the
per-stratum figures cannot presently distinguish weak depth relay from scoring
noise. Note also that the residual does not decay with distance
(0.042, 0.042, 0.042, 0.125 at increasing distance), which is the opposite of
what a depth-relay account predicts.

p2b raises reps specifically so this is decidable.
