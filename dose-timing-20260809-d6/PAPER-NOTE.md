# PAPER-NOTE — dose-timing-20260809-d6 (timing-schedule follow-up)

Successor to d2's timing arm. Question: is d2's front/late failure at 8%
recall/lr1e-3/5200 a **genuine schedule-dependence** of capability onset, or a
**budget-halt/forgetting artifact** (transiently induced, then forgotten over
the post-injection clean tail)? Design per d2/analysis/
TIMING-FOLLOWUP-DESIGN-NOTE-20260804.md (Hani 2026-08-04T14:45Z); launched per
Hani 2026-08-09 ~04:20Z (Lab 3 gets the idle V100s).

Design: arms A (decay-tail sweep — front 8% at budgets 650/5200/10400/20800,
same absolute dose, tails 0x/1x/2x/4x), B (stronger front 16% @5200), C
(mid-loaded 8% @5200), plus late/uniform references at 5200. Same sealed
instrument as d2..d5 (byte-identical eval salt + battery + injection pools).
One additive harness change: a probe exactly at each schedule's
injection-window close (extra_probes, sha-pinned), plus a new "mid" schedule.

Copy-edit the matching paragraph into the paper at verdict.

## If SCHEDULE_IS_FORGETTING_ARTIFACT
The d2 timing result is a budget-halt artifact, not a new axis of the dosing
law. Front-loaded dosing transiently induces the capability (a non-LOW read at
the injection-window close, invariant to tail length) but the capability
decays over the post-injection clean tail; the final read is LOW regardless of
tail length, and a mid-loaded schedule lands intermediate between front and
late. Onset remains a function of cumulative dose; only recency-to-end-of-
training modulates whether an induced transition survives to measurement.
Dosing charts (P3) should report dose-vs-onset with a consolidation-window
caveat, not a third schedule axis.

## If SCHEDULE_DEPENDENCE_GENUINE
The d2 timing result is genuine schedule-dependence: front-loaded dosing never
transiently crosses threshold at any tail length (all injection-close reads
LOW), doubling the front dose to 16% still fails to induce a HIGH transition,
and a mid-loaded schedule fails identically to front. WHEN task-relevant data
arrives during training changes whether the capability can be induced at all —
schedule is a genuine third axis of the provisioning law, and the P3 dosing
chart must be parameterized by it.

## If MIXED_PARTIAL_FORGETTING
Both mechanisms operate: front-loaded dosing is partly a forgetting artifact
(final decays with tail, or mid lands intermediate) but the full forgetting
conjunction does not hold (e.g. the injection-close read is itself
tail-dependent, or no clean transient is observed). Report the per-arm
probe-curve shapes; the boundary between schedule-dependence and forgetting
is itself dose- and budget-dependent.

## If INDETERMINATE
The data refute the forgetting hypothesis in at least one load-bearing cell
(e.g. a longer clean tail IMPROVES the front-loaded final read, which no
forgetting mechanism predicts). Report the observed shapes; a new mechanism
(e.g. distributed-repetition spacing effects) is implicated and needs a
freshly pre-registered design.
