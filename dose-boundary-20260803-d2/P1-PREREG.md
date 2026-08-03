# P1-PREREG — dose-boundary-20260803-d2 (Lab 3 P1: LR-crossed dose boundary map)

**STATUS: SEALED 2026-08-03 ~22:20Z (operator, fresh-eyes re-verification pass
following the 17:15Z draft).** Binding as of the ledger-sync commit whose sha
is recorded in campaign.json's `sealed_commit_sha` field (external timestamp =
GitHub push, per archlab-ledger-sync.py's own doc comment) — sealed BEFORE any
run in runs.json started training. Cell list, sealed predictions, and the
dose/run-count arithmetic were independently re-derived from
setup_campaign_d2.py's output this tick and matched this document exactly
(64 runs, group counts control=6/grid=36/half=18/timing=4; see verification
note at the end).

## Question

Map the dose boundary d*(capability, lr, budget) and discriminate:
- **H1** (token-count law, alpha=1): d* x T = N* — the absolute number of
  injected tokens at onset is budget-invariant.
- **H0f** (fraction law, alpha=0): d* itself is budget-invariant.
- **H2** (general): d* x T^alpha = k, alpha fit once >=2 budgets exist.
P0 (d1) ran a single budget, so these are indistinguishable there; d2's
half-budget row is the discriminator. Pre-fit brackets from P0 data:
`fit_p0_brackets.json` (recall/lr1e-3 d* in (2%,8%] at C0; recall/lr3e-3
d* ~= 2% at C0 (seed-split at exactly 2%); state/lr1e-3 d* < 0.5% at C0).

## Instrument (cloned from d1, changes listed)

Identical to d1 (P0-PREREG.md): 22.9M-param 6-layer windowed transformer
(W=256 asserted), FineWeb-Edu/Llama-2 corpus (same sha), fp16+GradScaler,
Bresenham dose accounting, salted hidden batteries from val.bin.
Changes from d1:
- FRESH 4-byte eval salt drawn at seal time: sha256
  8fc93dbeefd5bd4cd905d342c207eaf95745bc1d3585160d3917a7bf1bfe1477
  (raw value in campaign dir's eval_salt.txt, not reproduced here).
- Fresh seeds: **3002, 3003** (Lab 3 range 3000-3999; d1 used 3000/3001,
  cs1 used 3900/3901 — reverified free against ~/archlab-ledger this tick).
- Two budgets: **C0 = 5200 steps** (170.39M tokens, = d1) and
  **C0/2 = 2600 steps** (85.20M tokens). Same batch 32 x block 1024.
- Same analytic bands as P0-PREREG (recall HIGH >= 0.376923, LOW <= 0.065385;
  state HIGH >= 0.90, LOW <= 0.30; sustained = 80%-of-budget probe AND final
  read both in-zone; for half-budget runs the 80% point is step 2080).
- Smoke-test-only seed 3999 (never used in any campaign run) — structural
  GPU 3 smoke test (window-mask + dose-accountant checks, d1's own
  smoke_test.py, unmodified) run and PASSED this tick before sealing.

## Cells

**Recall grid (full budget):** dose {0.5, 1, 2, 4, 8}% x lr {1e-3, 3e-3} x
seeds {3002, 3003} = 20 runs.
**State grid (full budget):** dose {0.1, 0.2, 0.5, 1, 2}% x lr {1e-3, 3e-3} x
seeds {3002, 3003} = 20 runs.
  DEVIATION from SUCCESSOR-DIRECTIVE's literal {0.5..8}% ladder, documented
  here per protocol: P0 showed d*_state < 0.5% (0.5% already HIGH both seeds),
  so the directive ladder would return 20 HIGH cells and zero boundary
  information; the state ladder is shifted x5 down, staying inside the
  charter's P1 range (0.1%-10%). Same 5-rung log-spaced shape.
**Half-budget row (the H1/H0f discriminator):**
  recall: dose {2, 4, 8}% x lr {1e-3, 3e-3} x seeds {3002, 3003} = 12 runs.
  state: dose {0.1, 0.2, 0.5}% x lr 1e-3 x seeds {3002, 3003} = 6 runs.
**Timing rerun (descriptive, never gates):** recall, dose 8%, lr 1e-3
(a KNOWN-transitioning dose, fixing d1's sub-threshold placement),
schedules {front-20%, late-20%} x seeds {3002, 3003} = 4 runs; uniform
member shared with the grid.
**Zero-dose controls:** 0% x seeds {3002, 3003}, scored on both batteries
= 2 runs.
**Total: 64 runs** (control 6 + grid 36 + half 18 + timing 4), sequential on
GPU 3. 46 full-budget-equivalent runs + 18 half-budget runs (0.5 equivalent
each) = **55.0 full-equivalents** at d1's measured ~1h/full-run pacing =>
ETA **~2.3 days** from launch (corrects the draft's rough "~58" estimate to
the value setup_campaign_d2.py actually computes from runs.json).

## Controls-first barrier (clone of d1's queue_runner/monitor gate)

Controls run first; monitor.py writes controls.ok only if ALL pass, else
INSTRUMENT-BROKEN.md + STOP and nothing is interpreted:
- Known-negative: both 0% runs LOW on both capabilities.
- Known-positive recall: recall 8%/lr1e-3 (both seeds) — at least one HIGH.
- Known-positive state: state 2%/lr1e-3 (both seeds) — at least one HIGH.
(All four known-positive cells are grid cells, deduped as in d1.)

## Sealed held-out predictions (THE gate; class predictions from P0 only)

Sealed before ANY d2 cell trains. Each is a band-class prediction for a
fresh-salt/fresh-seed cell; "correct" = BOTH seeds land in the predicted
class (boundary cells excluded from sealing where P0 marks them unknown).

Full-budget replication predictions (10):
| cell | prediction | basis |
|---|---|---|
| recall 0.5% lr1e-3 | LOW  | P0 direct |
| recall 1%   lr1e-3 | LOW  | below P0's LOW 2% |
| recall 2%   lr1e-3 | LOW  | P0 direct |
| recall 8%   lr1e-3 | HIGH | P0 direct (known-positive) |
| recall 0.5% lr3e-3 | LOW  | 4x below the lr3e-3 boundary (~2%) |
| recall 4%   lr3e-3 | HIGH | 2x above the lr3e-3 boundary |
| recall 8%   lr3e-3 | HIGH | 4x above |
| state 0.5% lr1e-3  | HIGH | P0 direct |
| state 1%   lr1e-3  | HIGH | above P0's HIGH 0.5% |
| state 2%   lr1e-3  | HIGH | P0 direct (known-positive) |
NOT sealed (genuinely unknown, they ARE the measurement): recall 4% lr1e-3;
recall 1%/2% lr3e-3; state 0.1%/0.2% (both lrs); all state lr3e-3 cells.

Half-budget discriminating predictions — sealed CONDITIONALLY per hypothesis
(the gate scores which hypothesis's column wins, not a single row):
| cell (half budget) | H1 (alpha=1) predicts | H0f (alpha=0) predicts |
|---|---|---|
| recall 2% lr3e-3 | LOW/DEAD (d* doubles to ~4%) | boundary (seed-split or HIGH) |
| recall 4% lr3e-3 | boundary | HIGH |
| recall 8% lr3e-3 | HIGH | HIGH (non-discriminating) |
| recall 4% lr1e-3 | LOW (d* in (4,16]%) | unknown (bracket spans) |

**GATE (pre-registered):**
- Instrument-validity: >= 8/10 sealed replication predictions correct
  (both-seed criterion). Below that, the fresh-salt instrument disagrees
  with P0 and NO law verdict may be read from this campaign.
- Law verdict (only if instrument-valid): the H1-vs-H0f columns are scored
  on the discriminating half-budget recall/lr3e-3 cells; the hypothesis
  whose predicted classes match observed classes on >= 3/4 seed-cells at
  2% and 4% wins PROVISIONALLY; alpha is then fit (H2) across both budgets
  and reported with the boundary map. If neither column reaches 3/4, verdict
  is INDETERMINATE_AT_TWO_BUDGETS and P2 must add a third budget.
- Bimodality re-check: any capability showing >= 2 sustained-dead-zone runs
  among its full-budget uniform grid cells re-opens the P0 kill question
  (report immediately, do not proceed to fits).

## What is NOT claimed
No architecture claim. Timing rerun outputs hypotheses only. Single scale
(23M) and single window (W=256); scale transfer is P2. State/lr3e-3 and
sub-0.5%-state cells are exploratory (no sealed prediction).

## Sealing record (this tick, 2026-08-03 ~21:56Z-22:20Z)

1. Fresh-eyes re-verification: independently diffed aggregate_d1.py vs
   aggregate_d2.py (the two-budget/sealed-prediction/H1-H0f-scoring additions
   are the only substantive change; control-gate and probe-band logic is an
   unmodified clone), confirmed train_d1.py/data_dose.py/gen_pools.py/
   gen_eval_battery.py/models.py carry no residual d1-specific hardcoding
   that would silently misconfigure d2, and confirmed the D1_WINDOW env var
   is set from campaign.json (not left at the models.py default of 0) before
   every training subprocess imports models.py. Cross-checked
   setup_campaign_d2.py's runs.json generator cell-by-cell against this
   document's Cells section (64/64 match) and sealed_predictions.json against
   the Sealed held-out predictions tables above (10 full-budget + the 4
   half-budget H1/H0f rows, exact match).
2. GPU 3 smoke test (structural: window-mask correctness + Bresenham dose
   accountant, d1's own unmodified smoke_test.py) run pinned to GPU 3 this
   tick: PASS (window mask beyond-window delta=0.0, within-window
   delta=0.0131; dose accountant exact at 0.5%/2%/8% x uniform/front/late).
3. Campaign assembled via setup_campaign_d2.py: fresh salt drawn, hidden
   batteries generated (recall_A/recall_neg/state_eval), runs.json (64,
   controls first), sealed_predictions.json, campaign.json all written to
   ~/archlab3-runs/dose-boundary-20260803-d2/.
4. This file replaces the DRAFT and is the sealing artifact; the seal event
   itself is the archlab-ledger-sync.py commit+push that mirrors this file
   (and the rest of the campaign dir) to
   ~/archlab-ledger/dose-boundary-20260803-d2/P1-PREREG.md (same convention
   d1's P0-PREREG.md used — no separate `preregistrations/` subdir file for
   Lab 3 campaigns, since ledger-sync mirrors the whole campaign directory).
   Commit sha recorded in campaign.json's `sealed_commit_sha` immediately
   after the sync runs, before queue_runner starts.
