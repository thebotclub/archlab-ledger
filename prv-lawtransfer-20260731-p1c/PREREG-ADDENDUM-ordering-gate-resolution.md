# p1c pre-registration addendum — the ordering gate cannot resolve w128 vs w256

**Written 2026-07-31 ~10:30 UTC, while p1c is at step ~11,000 of 73,243 (15%).**
Best-checkpoint values are not known. The final outcome is not known. This note
is timestamped into the ledger now, before the data exists, precisely so it
cannot be mistaken for a post-hoc rescue of a failed gate.

**This addendum changes NO gate.** p1c will be scored exactly as pre-registered
in `campaign.json`. Nothing below alters `pass_if`, the tolerance, the
predictions, or the ordering rule.

## The defect

The pre-registered ordering gate requires observed needle accuracy to be
non-decreasing in W:

    w128 <= w256 <= w512 <= w1024

The pre-registered predicted ceilings for the first two cells are:

| cell | predicted ceiling |
|---|---|
| w128 | 0.215385 |
| w256 | 0.223077 |
| **predicted gap** | **0.007692** |

The frozen evaluation battery contains **128 needle questions**. Two consequences
follow, and both were fixed before this campaign launched — they are properties
of the instrument, not of the model:

1. **Discretization.** One question is worth 1/128 = 0.0078125 of accuracy. The
   entire predicted difference between w128 and w256 is *smaller than a single
   test question*. The gate asks the battery to resolve a difference it cannot
   represent.

2. **Sampling noise, which is the larger problem.** For a difference of two
   proportions at p ~ 0.22 with n = 128 per cell, the standard error of the
   difference is

       sqrt(2 * 0.219 * 0.781 / 128) = 0.0517

   That is **6.7 times the predicted gap of 0.0077**. The gate attempts to detect
   a 0.008 effect with an instrument whose noise is +/-0.05.

The w128/w256 ordering comparison is therefore a coin flip by construction. It
will pass or fail on which way one or two questions happen to land.

## This is already visible, and it already happened in p1b

At p1c's step-7560 probe the two cells read w128 = 0.203, w256 = 0.195 — an
inversion of 0.008, i.e. exactly one question, which would fail the ordering
gate. Early-checkpoint values are not the scored quantity, so this predicts
nothing about the final result; it is recorded only to show the failure mode is
live rather than hypothetical.

More importantly, look back at p1b. Its ordering gate **passed**:
observed_max = [0.2266, 0.2344, 0.6016, 1.0], so w128 <= w256 held by 0.0078 —
again exactly one question. p1b's ordering gate did not pass because the law
ordered the cells correctly; it passed because a coin landed heads. **That gate
result should not be cited as evidence in the paper.**

## Which comparisons the battery CAN resolve

Adjacent-cell ordering is only meaningful where the predicted gap exceeds roughly
2 standard errors (~0.10 at n = 128):

| comparison | predicted gap | resolvable at n=128? |
|---|---|---|
| w128 vs w256 | 0.008 | **NO** — noise is 6.7x the effect |
| w256 vs w512 | 0.192 | yes |
| w512 vs w1024 | 0.585 | yes |

So three of the four ordering relations the gate asserts are sound; one is not.

## How p1c will be scored, decided in advance

- p1c is scored **exactly as pre-registered**. No exception is carved out.
- If the ordering gate fails **solely** on the w128/w256 pair with an inversion of
  |delta| <= 2/128 = 0.0156, the campaign is reported as a **pre-registered FAIL**,
  with this timestamped note as the pre-existing explanation — the same handling
  p1b's w512 boundary-convention case received, and for the same reason: the lab
  reports what its gates say, then explains, rather than editing the gate.
- If it fails on any other pair, that is a substantive failure of the ordering
  prediction and must be treated as one.

## Pre-registered follow-up

To make the w128/w256 ordering claim testable at all, the needle battery must
grow. For the standard error of the difference to fall to half the predicted gap
(0.00385), holding p ~ 0.22:

    n = 2 * 0.219 * 0.781 / 0.00385^2 ~= 23,000 questions per cell

Even the weaker target of SE = gap requires ~5,800 per cell. This is cheap —
probes are evaluation-only, no retraining — and should be run against the
retained p1c checkpoints rather than as a new training campaign.

Until that runs, **the honest claim is that the law's ordering is confirmed
across resolvable window separations (w256 -> w512 -> w1024), and is untested
between w128 and w256.** The paper should say exactly that.
