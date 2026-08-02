# SUCCESSOR-DIRECTIVE — for the operator (p2 lineage owner)

Written 2026-08-02 ~00:25Z by the interactive session, within the grace
window of p2c's decision.json (00:09:43Z), under COORDINATION.md rule 6:
this is a directive, not a launch — the lineage stays yours.
Authority: Hani approved the full 2026-08-02 review recommendations
("go ahead with all your recommendations") this session.

## Context you already have

p2c's mechanical aggregation stands unamended: G0/G1/G2a pass both arms,
G2b/G2c fail both arms, G3 passes but is FITTED. The 2026-08-02 independent
methodology review ruled that a fitted calibration cannot be quoted as a
pre-registered prediction — p2c is instrument characterization. p2b's
LAW_DOES_NOT_TRANSFER therefore stands for the strict step-to-chance form,
while boundary location + in-window saturation are confirmed on deployed
checkpoints, and the residual means the law under-promises (provisioning by
it is conservative — the commercially survivable branch).

## Directive: design and run p2d as the pre-registered transfer test

Purpose: earn (or definitively refuse) the sentence "the law's arithmetic
transfers to deployed checkpoints" with predictions that are fixed BEFORE
any new probe is scored, using p2c's fitted instrument as the frozen basis.

Design constraints (from the methodology review; bind them in campaign.json):
1. Freeze the instrument exactly as p2c ran it (value-token anchor, exact
   digit-boundary scoring, structural G1, BOS, decorrelated filler). No
   further fitting of any kind.
2. Predictions computed from p2c's FITTED boundary + measured chance floor +
   an explicit residual term: predict per-stratum recall = 1.0 for d < b,
   r_resid for d > b, with r_resid pre-registered from p2c's pooled far-field
   (phi3 ~0.028, mistral ~0.024 — recompute from the artifacts, don't trust
   this note) with a pre-registered tolerance (suggest ±0.05 as elsewhere).
3. FRESH evaluation draws: new salt, new filler sampling, new probe
   positions — same models, same W. The thing being tested is the
   prediction, not the instrument.
4. Optionally add one UNSEEN model as arm 3 (e.g. Qwen2.5-7B if it has a
   config sliding window, else a third seen-family checkpoint at a different
   W) — an unseen-model pass is worth more than both re-runs combined.
5. Gates: per-stratum |obs − pred| ≤ tol on ≥ K/N strata (pre-register K),
   plus the boundary-location gate re-affirmed. Interpretation fixed in
   advance for pass / fail-high / fail-low, as p2b did.
6. Eval-only, local GPUs, no spend. Ledger-sync the campaign dir at
   creation (harness copies included, per COORDINATION.md rule 4).

Naming: next free suffix — check ~/.archlab-suffix-claims/ (being seeded
today) AND both runs trees; p2d expected free.

## Also binding on Lab 2 Phase 2 (for when p1e passes)

Hani has ratified the P2 gate restructure: PRIMARY gate = certification
(pre-registered prediction error ≤ tolerance on the converted checkpoint);
folklore-per-byte comparison SECONDARY; sweep-cost-avoided reported as the
commercial number. Llama-3.2-1B is REQUIRED alongside Qwen3-0.6B for any
external claim; evaluation must include a real RULER subset; deliverables
include released checkpoints + a runnable eval harness. This supersedes the
"beat folklore" primary in LAB2-CHARTER.md — noted there too.
