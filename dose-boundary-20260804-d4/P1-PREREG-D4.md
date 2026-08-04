# P1-PREREG-D4 — dose-boundary-20260804-d4

**STATUS: SEALED 2026-08-04 (operator).** Dose-law analogue of Lab 2's
campaign `ap` (`~/archlab-runs/stablegla-lawtest-20260730-ap`): tests the
already-provisional H1(token-count) law's NUMERIC predictive power on
genuinely unseen cells, rather than re-fitting it. Authorized by Hani's
2026-08-04T14:45Z inbox instruction ("design and launch the sealed H1
(token-count) claim campaign — the dose-law analogue of campaign ap ...
pre-register NUMERIC N* predictions for unseen (dose, budget) cells computed
from the d2/d2c fits, BOTH capabilities, fresh seeds, salted evals,
controls-first, predictions committed to the public ledger BEFORE training").

## Why this exists

d2 (2 budget points, H1 3/4 vs H0f 2/4 — thin) and d2c (3rd budget point,
quarter, H1 4/4 vs H0f 0/4 — clean) both support H1(token-count, alpha~1)
over H0f(fraction, alpha=0), but every discriminator so far has scored the
law by BRACKETING (does d* fall inside a predicted range at an
already-partially-tested budget). Campaign `ap`'s pattern for Lab 2's
window-provisioning law was different and stronger: compute a NUMERIC
predicted value from the established fit and test it against CELLS NEVER
BEFORE EVALUATED AT ANY BUDGET. This campaign does the dose-law equivalent:
derive N* = d*_full x C0 (a fitted absolute-token-count threshold, in
dose-fraction x steps units since batch/block are fixed across all Lab 3
campaigns) from d2/d2c's own point estimates, predict d*(C) = N*/C at a
**brand-new eighth compute budget (C0/8 = 650 steps, never tested by d1,
d2, or d2c)**, and pre-register the resulting HIGH/LOW class at specific
doses chosen so H1 and H0f's predictions diverge.

## Reused instrument (no fresh seal of the corpus/battery/pools)

Byte-identical to d2/d2c: `models.py`/`data_dose.py`/`eval_d1.py`/
`train_d1.py`/`queue_runner_multi.py` (sha256-verified against d2c's
`campaign.json.harness_sha256` before use), `eval_salt.txt` (sha256 of the
stripped value verified against d2's `eval_salt_sha256`, asserted in
`setup_campaign_d4.py`), `needle_pool.npy`/`state_pool.npy`/
`battery_manifest.json` (byte-identical copies of d2's, sha matches recorded
in `campaign.json`). This is a continuation of the same sealed measurement
lineage, not an independent replication — same analytic bands
(recall_high/low, state_high/low, unchanged from d1/d2/d2c), same
already-validated controls (d2's `controls.ok` PASS). `controls.ok` in this
dir documents that inheritance explicitly, same precedent as d2's
half-budget row and d2c's quarter-budget row (neither ran a fresh
known-positive/negative barrier at their new budget either).

**What IS new at this budget**: 12 "agree" cells (see below) where H1 and
H0f predict the SAME class — these function as this row's own
floor/ceiling sanity check specifically for the eighth-budget point, scored
as `instrument_validity` in `decision.json` before any law verdict is read
(p1b/p2f/d1 precedent: never read a law off an unverified instrument).

## Alpha-fit inputs (from `dose-boundary-20260803-d2/analysis/alpha_fit_20260804.txt`, NOT re-derived here)

| capability/lr | d*_full (geometric-mid bracket) | N* = d*_full x 5200 |
|---|---|---|
| recall / lr=3e-3 | 2.00% (bracket (1%,4%]) | 104.0 |
| recall / lr=1e-3 | 2.828% (bracket (2%,4%]) | 147.08 |
| state / lr=1e-3 | 0.3162% (bracket (0.2%,0.5%]) | 16.44 |

Predicted d* at the eighth budget (C_eighth = 650 steps):

| capability/lr | H1 (token-count): N*/650 | H0f (fraction): unchanged |
|---|---|---|
| recall / lr=3e-3 | **16.00%** | 2.00% |
| recall / lr=1e-3 | **22.63%** | 2.83% |
| state / lr=1e-3 | **2.53%** | 0.32% |

## Cells (26 runs, all steps=650=C0/8, uniform schedule)

Per (capability, lr) row, 4 doses x 2 fresh seeds {3006, 3007} (verified
unused against `~/archlab-ledger/` — Lab 3 range 3000-3999; consumed so far:
d1 3000/3001, d2/d2c 3002-3005, cs1 3900/3901):

- **recall/lr3e-3**: doses {1%, 4%, 8%, 24%}. 1% agrees-LOW, 24% agrees-HIGH
  (floor/ceiling checks); 4% and 8% are DIVERGENT (H1 predicts LOW since
  below 16%, H0f predicts HIGH since above 2%) — 8% additionally cross-checks
  d2c's own quarter-budget 8% cell (which was LOW) one compute-halving
  further down.
- **recall/lr1e-3**: doses {1%, 8%, 16%, 32%}. 1% agrees-LOW, 32%
  agrees-HIGH; 8% and 16% DIVERGENT.
- **state/lr1e-3**: doses {0.1%, 1%, 2%, 5%}. 0.1% agrees-LOW, 5%
  agrees-HIGH; 1% and 2% DIVERGENT.
- **none-control** (2 runs): dose 0%, floor check shared across capabilities.

Total: 3 rows x 4 doses x 2 seeds (24) + 2 none-control = 26 runs.

## Sealed predictions

See `sealed_predictions.json` (this dir): `divergent_cells` (12 seed-cells,
the actual H1-vs-H0f discriminator), `agree_cells_instrument_check` (12
seed-cells, both hypotheses concur — a miss here means the eighth-budget
instrument itself is suspect, not that the law is wrong), `none_control_run_ids`.

## Gate (pre-registered)

- **Instrument validity**: agree-cells (12) + none-control (2) = 14
  seed-cells classify as predicted; `instrument_valid` requires >=10/14
  correct AND all results present. If false: `INSTRUMENT_SUSPECT_NO_LAW_VERDICT`,
  no law verdict is read (p2f precedent).
- **Law verdict** (only read if instrument_valid): of the 12 divergent
  seed-cells, H1 wins `H1_TOKEN_COUNT_CONFIRMED_EIGHTH_BUDGET` if H1_matches
  >=9/12 AND strictly more than H0f_matches; H0f wins symmetrically
  (`H0F_FRACTION_CONFIRMED_EIGHTH_BUDGET`); else
  `INDETERMINATE_AT_EIGHTH_BUDGET`.

## What is NOT claimed

No new architecture claim, no P2 scale/interference claim (suffix `d3`,
charter-reserved, separate Hani go-ahead). This campaign tests the numeric
predictive power of the already-provisional H1 law on unseen cells — it is
the confirmatory step that would let the write-up state the law as
predictive rather than merely fit-consistent, same role `ap` played for
Lab 2's window-provisioning law.

## Sealing record

1. Verified byte-identical reuse of eval_salt.txt (sha256 8fc93dbe...) and
   all 5 harness .py files against d2c's sealed `campaign.json` shas — all
   MATCH (see tick's Decision Log for raw hashes).
2. Verified 3006/3007 unused against `~/archlab-ledger/dose-*` campaign
   records before assignment.
3. This file + sealed_predictions.json + runs.json + campaign.json sealed via
   `archlab-ledger-sync.py` commit+push BEFORE `queue_runner_multi.py` starts
   any run; commit sha recorded in `campaign.json.sealed_commit_sha`.
