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

---

# CORRECTION APPENDED 2026-08-01 — the diagnosis above is wrong, and the wrong diagnosis is the more comfortable one

**Nothing above has been altered.** The original addendum, its timestamp and its
reasoning stand as written. What follows corrects its *diagnosis*, changes no
gate, and does not touch p1c's verdict, which remains GATE_NOT_MET as
pre-registered.

## What the addendum claimed

That the ordering gate could not resolve w128 vs w256 because the predicted gap
(0.007692) is smaller than the battery's resolution (1/128 = 0.0078125) — i.e.
a **statistical power** problem, remediable by a larger battery, with ~23,000
probes per cell quoted for half-gap resolution.

## What is actually true

The predicted gap is not small. **It is exactly zero**, and the battery cannot
test the w128/w256 relation at any sample size.

Measured directly from the frozen battery (`~/archlab-s05/data/probes/needle.npz`):

```
planted-needle distance support: {110, 263, 311, 512, 714, 797, 915}
probes with planted-needle distance in [128, 256):   0
f(128) = f(256) = 0.187500        -> predicted gap  0.000000
f(128)=0.203125, f(256)=0.210938  -> predicted gap  0.007812   (nearest-token measure)
probes where a filler token sits nearer than the planted needle:  7 of 128
```

The pre-registered `needle_in_window_fraction` values (0.203125, 0.210938) were
computed by taking retrieval distance to be the distance to the **nearest
occurrence of the answer token anywhere in the context**. That is not the
retrieval distance. It is the distance to whichever copy of that word happened
to appear in the fineweb-edu filler. Measured properly — distance from the
question to the value token that was actually *planted* — every probe sits at
one of five fixed depths, the distribution has **no support whatsoever between
128 and 256**, and the law therefore predicts w128 and w256 to be identical.

The entire 0.007692 is manufactured by **one probe (example 6)** whose planted
needle is at distance 714 but which contains the answer word coincidentally in
its filler at distance 214. That probe is answered *incorrectly in both cells*,
as it must be: recovering it would require reading a bare word out of prose with
no `K is V` binding while the real needle is out of window.

The observed 0.0078 "inversion" is likewise not an inversion. Exactly one probe
differs between the two cells — **example 96, at distance 714** — which is far
outside both windows and is chance noise at p_chance = 1/65.

**So: a phantom prediction, and an unrelated chance flip. Neither quantity has
anything to do with the window-provisioning law, and the w128-vs-w256 ordering
comparison was never tested — in p1c, and retroactively in p1b, whose ordering
"pass" this addendum had already retired as a coin flip.**

## Why the correction matters practically, not just for the record

The addendum's diagnosis directly generated a proposed follow-up: re-score the
retained checkpoints against ~23,000 probes drawn from the same distance
distribution. Because total sequence length is pinned at 1023 and depths are
five fixed values, that distribution is **deterministic** — raising n replicates
the same five distances forever and f(128) = f(256) at every n. A 23,000-probe
run would have measured a gap of ≈0 against a mis-derived prediction of ≈0.0017
with a paired standard error near 0.001, and reported **a well-powered,
publishable, entirely spurious refutation of our own law** — caused start to
finish by a bug in how we measure distance. That is a materially worse outcome
than the GATE_NOT_MET we already have, and we were one campaign away from it.

## Two further errors in the quoted sample size, recorded so they are not repeated

Even taken on its own terms, the ~23,000 figure was wrong twice:

1. **It specifies ~52% power without saying so.** "SE = half the gap" is z = 2.0
   against a two-sided α=0.05 critical value of 1.96, giving power Φ(0.04) ≈
   **51.6%** — a coin flip, which is precisely the defect the addendum set out
   to eliminate. No α or power was stated anywhere in it. Properly powered on
   the same unpaired model: n ≈ 45,376 (80%) or 60,743 (90%).
2. **It ignores the paired structure, inflating n by ~22×.** One battery scored
   on four models is McNemar on discordant pairs, not two independent
   proportions. Measured discordance between w128 and w256 is **1 probe in 128**
   (p_d = 0.0078), giving a paired SE of 0.0078 against the unpaired 0.0517 —
   ratio 6.62, n-inflation 43.8. The correct McNemar n for the claimed effect
   would have been **~1,032**, not 23,000.

Neither error would have mattered, because the effect is zero. They are recorded
because the next power calculation this programme writes must state α and power
explicitly and must respect pairing.

## What replaces it

Not a bigger battery on the same grid — no n works. A **redesigned distance
distribution**, stratified across the full range with mass deliberately placed
between the tested windows, so that f(W) is exact and known before scoring and
the predicted adjacent-window gaps are ~0.22–0.28 instead of ~0. Under that
design the ordering question is resolvable at roughly 200 probes, and a
per-stratum step-function gate becomes available, which is a mechanism claim
rather than an aggregate-calibration claim.

This is a strictly *harder* test of the law, not an easier one: the current
battery's predictions (0.22/0.22/0.42/1.00) are satisfied by any model that
recalls only recent needles, whereas a stratified grid predicts a step function
at the window boundary that a recency model cannot produce. The redesign is
therefore not battery-shopping — but the guards must be explicit anyway: weights
frozen and sha256-recorded, battery salt hashed and sealed, and all predictions
committed before a single score is computed.

## Instrument defects to fix before that campaign

1. **Record the needle's value-token position at generation time** (`needle_pos`
   in the .npz) and define distance as `ans_pos - needle_pos`. Never infer
   distance by post-hoc token search. Root cause of everything above.
2. **Reject-and-resample any probe whose answer or key token appears in the
   filler.** Currently 7 of 128 (5.5%) are contaminated, and in 5 of those the
   filler copy is nearer than the needle. This also closes a copying shortcut.
3. **Decouple distance from depth by varying sequence length.** `gen_needle`
   always emits L = 1023 with `ans_pos = 1022`, so within any single cell depth
   and distance are perfectly confounded and "gated by window" cannot be
   distinguished from "gated by recency". Only the cross-cell manipulation of W
   currently breaks that tie.
4. **Add a negative control** (needle absent, key never bound) to measure
   p_chance rather than assume 1/65. Existing data is consistent with the
   assumption — pooled far-out-of-window accuracy was 3/206 = 0.0146 against
   0.0154 expected — but it should be measured.

*Correction authored 2026-08-01 after an independent design review. The measured
figures above were reproduced from the frozen battery artifacts and are
recomputable by anyone with `needle.npz`.*
