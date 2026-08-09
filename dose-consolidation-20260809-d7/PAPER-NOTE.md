# PAPER-NOTE — dose-consolidation-20260809-d7 (pre-written interpretation branches)

Successor to dose-timing-20260809-d6 (verdict MIXED_PARTIAL_FORGETTING). This note
is written BEFORE training and sealed alongside `sealed_predictions.json`. At
verdict, exactly one branch is copy-edited into the paper; the others are deleted.
No gate is amended after data.

## Background (what d6 established)

d6 tested whether d2's timing-arm failure (uniform 8% recall/lr1e-3 transitions
2/2, front fails 2/2, late splits 1/2) is genuine schedule-dependence or a
budget-halt/forgetting artifact. Result: BOTH mechanisms operate. Front 8%
transiently crosses the threshold when its clean post-injection tail is long
enough (HIGH at injection-close for both seeds at 2x/4x tails, acc_at_inj_end
0.466–0.483 vs HIGH ≥ 0.377) but decays to LOW by run end (final 0.0 at every
tail length). Mid-loaded lands HIGH-at-close; late never rises. The
schedule-vs-forgetting boundary is dose/budget-dependent.

## What d7 asks

Two questions d6 could not answer:

1. Is the post-injection decay a **budget-dependent forgetting law** — final
   accuracy a function of the clean post-injection tail — measurable as a decay
   constant off the per-run probe curves?
2. Is forgetting **recall-specific**, or does **state** forget too? (d6 was
   recall-only; the lineage contains no state timing data. d2's state lr3e-3
   d0p5 cell split HIGH/DEAD_ZONE across seeds — a hint state sits nearer onset
   and may share the transient.)

## Design

Decay-hold: total budget FIXED at 5200 steps, injection position swept
front/mid/late so the clean post-injection tail is the independent variable
(front tail 4160, mid 2600, late 0). Two arms × 3 positions × 2 seeds (3076/3077):

- **Arm R (recall):** 8% at 5200 — the d6 anchor dose.
- **Arm S (state):** 2% at 5200 — strongly supra-threshold under uniform
  (d2 st_d2_lr1e3 = 1.0/1.0 HIGH; state d* ≈ 0.2–0.5%).

Controls (6, sealed): none floor (LOW), recall uniform-8% (HIGH, d2/d6
known-positive), state uniform-2% (HIGH, d2 known-positive). All reuse the
d2..d6 sealed instrument byte-for-byte (sha256-verified salt/battery/pools);
no harness change beyond d6's additive extra_probes.

Numeric decay constants are read off probe curves: a log-linear fit of
capability accuracy vs clean-tail steps after injection close (k > 0 = decaying,
halflife = ln2/k).

## Interpretation branches (pick exactly one at verdict)

### Branch 1 — RECALL_FORGETS_STATE_CONSOLIDATES
Recall front final decays to LOW with a measurable probe-curve decay constant,
while state front/mid/late all stay HIGH final. **Reading: post-induction
forgetting is capability-specific.** Recall (needle retrieval) is forgotten
across a clean tail at a budget-dependent rate; state (within-window tracking)
consolidates and persists. The dose-onset law's forgetting term is not a generic
property of injected capability — it acts on the retrieval pathway. This
sharpened the d6 MIXED verdict into a capability-resolved mechanism.

### Branch 2 — BOTH_FORGET
Recall front AND state front both decay (final LOW/DEAD_ZONE). **Reading:
forgetting is capability-generic.** Any burst-induced capability decays across a
subsequent clean tail regardless of type; the d6 transient is one instance of a
general post-injection decay law. The dose-onset law needs a decay term that
applies to all injected capabilities.

### Branch 3 — NEITHER_FORGETS
Recall front AND state front both stay HIGH final. **Reading: d6's decay was a
tail-length onset effect, not post-induction forgetting.** At the d6 anchor dose
a front burst that crosses threshold does NOT then decay when the budget is held
at 5200 — meaning d6's LOW finals reflected the longer-budget arms' onset
dynamics, not a forgetting process. The consolidation hypothesis wins; no decay
term is needed at this budget.

### Branch 4 — INDETERMINATE
Mixed within a capability (a seed split the sealed bands cannot resolve), or a
control failure (VOID). **Reading: the instrument lacks resolution at this
dose/budget for a clean forgetting-law read; a finer position sweep or an
extension-seed addendum is owed before any claim.**

## Provenance

- Sealed: `sealed_predictions.json` + `campaign.json` (this dir), ledger mirror
  `~/archlab-ledger/dose-consolidation-20260809-d7/`, committed BEFORE training.
- Instrument: byte-identical to d2..d6 (eval_salt sha256 8fc93dbe…, battery,
  injection pools); sha256-verified against d2/d5 campaign.json at setup.
- Seeds 3076/3077 (fresh, next free in Lab 3's 3000-range ledger).
- No efficacy stopping; no gate amendment after data; controls scored before any
  verdict is read.
