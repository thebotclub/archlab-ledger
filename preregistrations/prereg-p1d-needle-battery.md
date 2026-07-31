# Pre-registration — p1d: enlarged needle battery
### Written 2026-07-31, before p1c has finished. No result from it is known.

## Why

The window-provisioning law asserts recall is non-decreasing in W. Preprint
limitation 8 withdraws the W=128 vs W=256 comparison because the instrument
cannot resolve it: predicted ceilings 0.2154 and 0.2231 differ by 0.0077, while
the 128-question battery resolves 1/128 = 0.0078 per question and the standard
error of the difference at p≈0.22 is 0.052 — about seven times the effect.

This campaign restores that comparison by enlarging the battery until the
difference is resolvable. It is evaluation-only: **no training**, no new model,
no cloud spend beyond what p1c already incurred.

## Method

Against p1c's four retained checkpoints (W ∈ {128, 256, 512, 1024}), collected
to hub and sha256-verified before teardown:

1. Generate **N = 24,000 needle probes per cell** from the frozen battery
   generator with a NEW salt, disjoint from p1c's evaluation salt. Sizing: for
   the standard error of the difference between two proportions at p≈0.22 to
   reach half the predicted gap (0.00385), n = 2·p(1−p)/SE² ≈ 23,000. 24,000 is
   the next round number above that.
2. Score each checkpoint on the enlarged battery at the checkpoint that p1c's
   own decision identifies as best, using the identical scoring code.
3. Report observed recall per cell with exact binomial confidence intervals.

## Pre-registered predictions

Derived from panel geometry alone, exactly as p1c's were, and unchanged from it:

| cell | predicted ceiling |
|---|---|
| W=128 | 0.2154 |
| W=256 | 0.2231 |
| W=512 | 0.4154 (strict) / 0.6154 (inclusive) |
| W=1024 | 1.0000 |

**Primary gate.** The ordering W=128 ≤ W=256 is tested at n=24,000. With that
battery the standard error of the difference is ≈0.0038, so the predicted
0.0077 gap is a ~2σ effect and the test is meaningful for the first time.

- **Confirms** if observed W=256 − W=128 is positive and the 95% CI on the
  difference excludes zero.
- **Refutes** if the difference is negative with its CI excluding zero. This
  would contradict the law's monotonicity and must be reported as a refutation,
  not as noise.
- **Indeterminate** if the CI spans zero — meaning even 24,000 probes cannot
  resolve it, and the ordering claim stays withdrawn permanently rather than
  being retried at larger n.

**Secondary.** The W=512 cell discriminates the strict (<W) from the inclusive
(≤W) boundary convention. At n=24,000 the two predictions (0.4154 vs 0.6154) are
separated by ~52 standard errors, so this cell decides the convention outright.
That is the question campaign p1c was told would need its own dedicated test;
this is it.

## Stop conditions

- If p1c is INCONCLUSIVE on compute grounds (its W=1024 prerequisite fails),
  this campaign does not run — there is no validated instrument to enlarge.
- If any checkpoint fails its sha256 on load, that cell is excluded and reported
  as excluded, not silently dropped.

## Cost

Zero cloud spend. Evaluation-only on local hardware against retained weights.
