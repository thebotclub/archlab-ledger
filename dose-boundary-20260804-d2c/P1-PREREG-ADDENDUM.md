# P1-PREREG-ADDENDUM — dose-boundary-20260804-d2c

**STATUS: SEALED 2026-08-04 (operator).** Addendum to `dose-boundary-20260803-d2`
(P1-PREREG.md, sealed commit 767c388048a6ee4d8311cd7d8ed0505166b51a0d).
Binding as of the ledger-sync commit sha recorded in this dir's `campaign.json`
(`sealed_commit_sha`) -- sealed BEFORE any run in this addendum's `runs.json`
started training. Authorized by Hani's 2026-08-04 10:45Z inbox instruction
("take (a) NOW -- the 3rd-budget row on the idle GPUs is $0 ... if the
prereg's ambiguity rule requires extension seeds for the state sustained-dead
cell, fold those into the same launch").

## Why this exists

d2's own `analysis/alpha_fit_20260804.txt` (written by the operator/interactive
session after d2's decision.json landed) flagged two open loose ends:
1. The H1(alpha=1)-vs-H0f(alpha=0) alpha fit rests on only 2 budget points
   (full C0=5200, half C0/2=2600) with wide brackets; a 3rd point would pin
   alpha properly. The Lab 3 charter's own original P1 spec called for
   **3 compute budgets** (LAB3-CHARTER.md line 50); d2 implemented 2. This
   addendum completes P1 to the charter's original spec -- it is NOT a P2
   scale/interference campaign (P2 is reserved for suffix d3 per the charter's
   own namespace table), it is P1's own budget axis finished.
2. `bimodality_recheck.state.ambiguous = true` (exactly 1 sustained-dead-zone
   run in the full-budget state grid: `st_d0p5_lr3e3_u_s3003`, DEAD_ZONE while
   its paired seed `s3002` was HIGH at the identical dose/lr/schedule/budget).
   d2's own kill-reopen rule triggers at >=2 sustained-dead grid runs; this is
   a single-run result sitting exactly one seed below that line, not
   comfortably either resolved or triggered.

## Reused instrument (no fresh seal of the corpus/battery/pools)

Byte-identical to d2: `models.py`/`data_dose.py`/`eval_d1.py`/`train_d1.py`
(sha256-verified against d2's `campaign.json.harness_sha256` before use),
`eval_salt.txt` (sha256 of the stripped value verified against
`eval_salt_sha256`), `needle_pool.npy`/`state_pool.npy`/`battery_manifest.json`
(sha256-verified against d2's `injection_pools.manifest.file_sha256` /
`battery_manifest_sha256`). This is a continuation of d2's own measurement,
not an independent replication -- same analytic bands, same controls already
validated by d2's own `controls.ok` (PASS, recorded in d2/decision.json).
`controls.ok` in this dir documents that inheritance explicitly rather than
re-deriving a fresh controls barrier for a budget point (quarter) that,
like d2's own half-budget row, was never separately control-validated either
(precedent: d2's half-budget grid ran under the SAME full-budget-derived
controls.ok, no half-budget-specific known-positive/negative pair).

## Cells (10 runs, all sequential-safe / no cross-run dependency)

**Quarter-budget discriminator (8 runs, steps=1300 = C0/4):** recall/lr3e-3
dose {2,4,8}% x seed {3002,3003} (6 runs) + recall/lr1e-3 dose 4% x seed
{3002,3003} (2 runs). Same doses/seeds as d2's half-budget row, one more
compute-halving down.

**State ambiguity extension (2 runs, steps=5200 = C0, full budget):**
state/dose0.5%/lr3e-3/uniform x NEW seeds {3004, 3005} (both freshly drawn,
verified unused against `~/archlab-ledger/` -- Lab 3 range 3000-3999; d1 used
3000/3001, cs1 3900/3901, d2 3002/3003, this addendum's quarter-budget cells
reuse 3002/3003, extension cells use 3004/3005).

## Sealed predictions

See `sealed_predictions.json` (this dir) -- H1/H0f match-sets for the 4
strict-gate quarter-budget seed-cells (recall/lr3e-3 doses 2%/4%), 2
descriptive-only cells (recall/lr3e-3 dose 8%; recall/lr1e-3 dose 4%), and the
pre-registered interpretation rule for the state extension (no directional
prediction -- a bimodality confirmation, not a law test; the rule specifies
exactly what counts as re-triggering d2's own kill-reopen condition).

## Gate (pre-registered)

- Alpha refit: three budget points (full/half/quarter) fit to H2's
  `d* . C^alpha = k`; report alongside d2's existing 2-point fit.
- Law verdict: hypothesis matching >=3/4 on the strict-gate cells wins
  PROVISIONALLY (unchanged threshold from d2). If neither reaches 3/4:
  INDETERMINATE_AT_THREE_BUDGETS is now a **terminal** call for the P1
  boundary-map lineage -- no further budget row without a fresh Hani/charter
  decision (this addendum is the one deferred loose end d2's analysis
  flagged, not an open-ended series).
- State ambiguity: per the `pre_registered_interpretation` in
  `sealed_predictions.json` -- >=1 new sustained-dead seed re-trips d2's own
  kill-reopen rule (report immediately, do not proceed to further
  interpretation); 0 new sustained-dead seeds resolves the ambiguity as noise,
  d2's verdict stands unchanged.

## What is NOT claimed

No new architecture claim, no P2 scale/interference claim (that is a separate,
larger, charter-gated campaign under suffix `d3`, requiring its own Hani
go-ahead per the same precedent as Lab 2's P2). This addendum only tightens
d2's own already-sealed P1 measurement.

## Sealing record

1. Verified byte-identical reuse of eval_salt.txt, needle_pool.npy,
   state_pool.npy, battery_manifest.json, and all 4 harness .py files against
   d2's sealed `campaign.json` shas (sha256 diff, all MATCH, see tick's
   Decision Log for the raw hashes).
2. Verified 3004/3005 unused against `~/archlab-ledger/dose-*` campaign
   records before assignment.
3. This file + sealed_predictions.json + runs.json + campaign.json sealed via
   `archlab-ledger-sync.py` commit+push BEFORE `queue_runner_multi.py` starts
   any run; commit sha recorded in `campaign.json.sealed_commit_sha`.
