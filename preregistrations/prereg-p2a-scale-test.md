# Pre-registration — p2a: does the law predict recall in a model we did not train?
### Written 2026-07-31, before p1c has finished. No result is known.

## Why this is the experiment that matters

Every validation of the window-provisioning law so far shares two weaknesses:

1. **Scale.** 7M-parameter models on synthetic MQAR, plus one 110M run on
   natural text.
2. **Naturalness.** Campaign p1a established that a model trained on ordinary
   web text scores **0%** on long-distance retrieval unless the retrieval format
   is explicitly trained. Every subsequent validation therefore *injects* a
   retrieval task into natural language rather than measuring retrieval as it
   naturally arises.

So the honest current status is: the law predicts recall for a task we
construct, in models we train. That is not yet a claim anyone should buy or
build on, and it is the first thing both a referee and a commercial
counterparty will press.

This campaign tests the law where it would actually be used: **an existing
open-weights model, which we did not train, on a recognised long-context
retrieval benchmark, with the prediction made before the measurement.**

## Method

1. **Choose an open checkpoint** in the 1–8B range with published weights and a
   documented context length. Record the exact revision hash before anything
   else.
2. **Measure the benchmark's retrieval-distance distribution** — the empirical
   distribution of distances between where a fact is stated and where it is
   queried — directly from the benchmark data, not from any model.
3. **Compute f(W)** = fraction of retrieval distances strictly below W, for a
   ladder of windows W, and the predicted ceiling
   `recall(W) = f(W) + (1 − f(W))·p_chance`, with `p_chance` derived from the
   benchmark's answer space.
4. **Seal the predictions** into this ledger, timestamped, before running any
   model.
5. **Apply windowed attention** at each W to the frozen checkpoint (band mask,
   the same implementation verified in p1c against an independent reference
   mask) and measure benchmark recall. No finetuning in the primary arm.
6. **Report predicted vs observed per window.**

## Pre-registered gates

- **Prerequisite.** The unwindowed model must score ≥ 0.50 on the benchmark's
  retrieval task. If it does not, the model cannot do the task at all and the
  run is INCONCLUSIVE about the law — the same prerequisite logic as p1c.
- **Confirms** if observed recall is within ±0.10 of prediction in ≥ 3 of 4
  windows.
- **Refutes** if ≥ 2 windows miss by more than 0.10 in a consistent direction.
  A refutation here matters far more than any confirmation so far, because this
  is the only test conducted on retrieval that occurs naturally, at a scale and
  in a model the field recognises. **A refutation must be published, and it
  invalidates the commercial thesis as currently stated.**
- **Secondary (finetuned arm, only if the primary is inconclusive on
  prerequisite grounds):** repeat with light retrieval-format finetuning. This
  arm is explicitly weaker evidence, because it reintroduces the injected-task
  caveat, and must be labelled as such wherever it is reported.

## Why the prediction is falsifiable

The predicted ceilings come from benchmark geometry alone — distances measured
from the data — with no free parameters fitted to the model, and they are sealed
before the model runs. There is no path by which a wrong law produces right
numbers here.

## Gating and cost

This is Lab 2 Phase 2, whose funding is conditioned on the law-transfer gate
(p1c). **It does not launch until p1c passes as pre-registered.** If p1c fails
its gate, this campaign is reconsidered rather than launched, because it would
be building on an uncorroborated instrument.

Estimated cost: inference-dominated, no pretraining. Hundreds of dollars against
the approved $3,000 Lab 2 envelope. Quote-before-create applies, and a ledger
line is written at provision time — not retroactively, as happened with p1c.
