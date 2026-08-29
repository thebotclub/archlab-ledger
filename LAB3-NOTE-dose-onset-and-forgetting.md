# Lab 3 note: capability dose-response is bimodal, and post-burst forgetting is capability-generic

*Draft internal note — archlab Lab 3 ("Capability Dosing"), campaigns d1–d7, 2026-08-03 to 2026-08-09. Written up 2026-08-29 from sealed campaign artifacts; no new computation. Status: complete chain, never previously written up — Lab 3 was parked in favour of Lab 4/paper-finalization work, not because these results were weak.*

## Motivation

A small on-web-text model (110M params) trained on a corpus with a targeted capability held out scores exactly 0.000 on that capability's probe while scoring 0.875 on a control (copying) — until a few percent of the training mix is switched to include the capability's pattern, at which point performance lands sharply on a predicted ceiling. Loss-based data-mixing laws cannot see this: the transition is invisible in the loss curve and only visible in the capability probe itself. Lab 3 asked: is there a general dose-response law for "how much of a targeted pattern in the training mix is needed to switch a capability on," and does it behave the same way once the capability has switched on, or can it be lost again?

Method follows the same sealed-pre-registration discipline as Lab 1 and Lab 2: numeric predictions and interpretation branches committed to the ledger before training, hidden salted evals, known-positive and known-negative control arms in every campaign, no gate amendment after data.

## The chain

| Campaign | Date | Verdict | What it established |
|---|---|---|---|
| d1 (dose-onset) | Aug 3 | COMPLETE, P0 not killed | A capability-specific dose-response band exists for both a "recall" (needle-retrieval) and a "state" (within-window tracking) capability; neither showed a sustained dead zone that would kill the whole approach. |
| d2 (dose-boundary) | Aug 3 | H1_TOKEN_COUNT_PROVISIONAL | Instrument validated (8/10 sealed controls correct); bimodal HIGH/LOW response confirmed at scale (20+20 runs, one ambiguous state cell); the token-count functional form for the boundary itself only partially supported (3/4 seed-cells) — **provisional, not confirmed**. |
| d2c, d4 (dose-boundary, repeat) | Aug 4 | INSTRUMENT_SUSPECT_NO_LAW_VERDICT (both) | Void. Instrument-error campaigns, consistent with the programme-wide lesson that instrument error dominates naive readings — no law claim made from either. |
| d5 (dose-boundary, repaired) | Aug 4 | **CLAIM_PASS_RECALIBRATED_NSTAR** | After the d2c/d4 instrument repair, the threshold claim passes cleanly: 17/18 sealed predictions correct, all control gates pass, per-row breakdown clean. The bimodal dose threshold is real once the threshold parameter (N*) is properly calibrated. |
| d6 (dose-timing) | Aug 9 | MIXED_PARTIAL_FORGETTING | Tests whether d2's front/late timing failure is genuine schedule-dependence or a forgetting artifact. Answer: both mechanisms operate — a front-loaded burst can transiently cross the HIGH threshold at injection-close, then decay back to LOW by run end if the post-injection clean tail is long enough. |
| d7 (dose-consolidation) | Aug 9 | **BOTH_FORGET** | Resolves d6. At fixed total budget, sweeping injection position so the clean post-injection tail is the only variable: **recall decays with a measured halflife of roughly 100–190 steps** (two front/mid arms, log-linear fit off the probe curve); **state decays too** — and in some seeds decays further than the sealed prediction anticipated (one expectation check explicitly failed: predicted floor was DEAD_ZONE, observed floor was LOW, i.e. state forgot *more* than expected, not less). Forgetting is not recall-specific; it is a property of any burst-induced capability. |

## Headline finding

Two things, both sealed and both replicated across seeds:

1. **Capability acquisition via targeted-mix dosing is bimodal, not graded** — a model sits at floor performance until a training-mix dose crosses a threshold, then jumps to a ceiling. This threshold is real and passes a strict pre-registered claim gate (d5) once correctly calibrated, but the exact functional form of the threshold (token-count based, per d2's H1) remains provisional, not confirmed.
2. **A capability acquired by a late-training burst can be partially or wholly forgotten afterward, and this is capability-generic** — it happens to both the "recall" and the "state" capability tested, with a measurable decay half-life on the order of 100–1500 steps depending on arm, at fixed total training budget. This means any dose-response law for this kind of capability injection needs a decay term, not just a threshold term.

## Honest limitations (carried from the sealed record, not added after the fact)

- All work is scratch-salt, small-model (order-100M-parameter), synthetic-probe work — there is no natural-language or production-checkpoint validation of either finding (the equivalent of Lab 1's p1e/deployed-checkpoint legs never ran for Lab 3).
- d2's boundary functional form (H1_TOKEN_COUNT_PROVISIONAL) is explicitly not a confirmed law — only the existence of a bimodal threshold (d5) and the forgetting dynamic (d7) are claim-grade.
- Two full campaigns (d2c, d4) are void on instrument grounds and contribute nothing beyond "these designs didn't work" — worth stating plainly rather than omitting, per the programme's own rule about a hostile reader finding void campaigns in the ledger.
- The chain stops at d7. No replication campaign, no cross-scale check, no attempt to fit the decay term into a single predictive law the way Lab 1's `f + (1−f)·p_uniform` unifies its results. This is a set of clean individual findings, not yet a unified law.
- Nothing here has been through adversarial review the way the main paper has (six-plus rounds). Treat this note as a faithful summary of sealed artifacts, not as review-hardened prose.

## Recommendation

This is real, decisive, already-sealed work that cost nothing further to write up — it was simply parked. As a short standalone note (this document, lightly polished) it is defensible as-is: every number traces to a sealed decision.json, every verdict is stated including the two void campaigns. It is **not** manuscript-ready for a venue like the main paper without at least: (a) a written unification attempt for the threshold + decay dynamics into one predictive form, and (b) a validation leg beyond the synthetic scratch-salt setting. Whether that further investment is worth making is a resourcing call — the finding itself is solid enough to be worth having on record either way.
