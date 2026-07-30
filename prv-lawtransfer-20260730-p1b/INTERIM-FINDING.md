# p1b interim: the pre-registered prediction FAILED for the W=512 cell.
# Recorded 2026-07-30 10:35 UTC, at ~10% of training, BEFORE the run finished.

## Status against the pre-registration (no retroactive rewriting)
At checkpoint 7560/73243:
  W=128 : predicted 0.2154 | observed 0.008  (still rising; not yet assessable)
  W=256 : predicted 0.2231 | observed 0.203  (within tolerance)
  W=512 : predicted 0.4154 | observed 0.594  (|err| 0.179 >> 0.05 tolerance -> FAILS)
  W=1024: predicted 1.0000 | observed 1.000  (exact)
The pre-registered gate for the W=512 cell is FAILED. That stands on the record
regardless of the explanation below.

## Identified cause (post-hoc, therefore NOT a pass)
The needle retrieval distances are discrete clusters:
  30:1, 56:1, 101:1, 110:23, 214:1, 311:25, 512:26, 714:24, 898:1, 915:25
A cluster of 26/128 examples sits at distance EXACTLY 512, i.e. exactly on the
W=512 window. The implemented predicate is (i - j) < W, so direct attention
reaches at most W-1 = 511 tokens: that cluster is ONE TOKEN outside direct
reach, and the pre-registered prediction used f(distance < W) = 0.4062.
Scoring the same cell with f(distance <= W) = 0.6094 gives a predicted ceiling
of 0.6154 against an observed 0.594 -- an error of 0.021, inside tolerance.
Only the W=512 cell can discriminate between the two conventions (no cluster
lies near 128, 256 or 1024), so a single cell decides it, which is exactly why
this must be re-tested rather than asserted.

## Mechanism hypothesis (to be tested, not claimed)
Stacked windowed attention has an effective reach greater than a single
window: the token immediately preceding the query has its own W-wide window
reaching one token further back, and depth relays that information forward.
This predicts effective reach slightly exceeding W, which is what the boundary
cluster shows, while NOT predicting unbounded reach (the W=256 cell sits on
its single-hop prediction, with its nearest cluster 55 tokens beyond the
window -- too far for a reliable one-hop relay).

## Required follow-up (pre-registered, before any claim is made)
Campaign p1c: build a probe set whose retrieval distances are placed
deliberately at W-2, W-1, W, W+1, W+2 and at W + delta for several delta, and
pre-register predictions under BOTH conventions plus a depth-relay form.
Vary depth (e.g. 6 vs 12 blocks) at fixed W to test the relay explanation
directly. Only that campaign can establish the corrected boundary rule.

## Consequence for the patent specification (ACTION REQUIRED BEFORE FILING)
The v3.1 Statements of Invention already recite the fraction of distances
"not exceeding" the candidate width (the <= convention, which the data
supports). However the Detailed Description's Table 2 defines f as distances
"strictly less than W". These are inconsistent, and the inconsistency is now
known to be material at the boundary. Fix the Table 2 wording to match the
claim, and add a sentence recording that the effective reach of a stacked
windowed layer may slightly exceed W. Do not file until this is corrected.
