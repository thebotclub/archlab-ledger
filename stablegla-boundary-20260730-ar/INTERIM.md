# ar interim (4/6 cells): effective reach EXCEEDS the nominal window

Panel: every retrieval distance is exactly 160 (verified: min=max=160).
Implemented predicate 0 <= i-j < W, so direct attention reaches W-1.

  W=156 (direct 155): 1/6   0.086 0.063 0.178 0.065 0.096 1.000
  W=158 (direct 157): 6/6   all 1.000
  W=160 (direct 159): 5/6
  W=161 (direct 160): 2/6   0.818 0.572 0.303 0.150 0.123 1.000
  W=162, W=164: pending

## Verdict against the pre-registration
BOTH pre-registered conventions are falsified. The strict convention predicted
transitions only for W>=161; the inclusive convention predicted W>=160. W=158
transitioned 6/6 at a retrieval distance of 160 -- three tokens beyond its
direct reach of 157. The third registered hypothesis, depth relay (effective
reach > W), is the one supported.

## Caveat recorded honestly
The rates are non-monotonic in W (6/6 at 158 but 2/6 at 161). These cells sit
near the compute-gated transition threshold where per-seed outcomes are bimodal
and the rate carries real variance at n=6; Fisher between 6/6 and 2/6 is only
p~0.06. So the ORDERING of rates across nearby W is not established by this
campaign. What IS established, and does not depend on rates, is the existence
claim: a window whose direct reach is strictly less than the retrieval distance
achieved full recall in 6 of 6 seeds. Effective reach exceeds W.

## Consequences
1. The provisioning law must be stated over EFFECTIVE reach, not the nominal
   window. The v3.2 patent definition of "effective retrieval reach" (added
   this morning from the p1b boundary observation) is now empirically supported
   rather than merely hypothesised.
2. p1b's failed W=512 cell is explained by the same effect (26/128 examples at
   distance exactly 512, one token past direct reach, answered anyway).
3. The practical provisioning rule becomes CONSERVATIVE: choose W from the
   workload distance distribution using the strict convention, and treat any
   extra reach as margin rather than budget. Quantifying how far the relay
   extends (and its dependence on depth) needs a further campaign: vary blocks
   (e.g. 4 vs 8 vs 12) at fixed W and fixed distance, with rates estimated at
   n>=16 per cell to overcome the variance seen here.
