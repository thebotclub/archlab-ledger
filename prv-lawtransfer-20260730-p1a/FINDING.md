# p1a HALTED after ~50 min — the measurement instrument lacks dynamic range

## What was checked (before spending a day of cloud time)
Probe accuracies of the ALREADY-TRAINED S0.5 transformer checkpoint
(110M params, 2.5B tokens, step 78126), scored on CPU, unrestricted attention:

  kv_acc             = 0.0078   (distances <= 27 tokens)
  needle_acc         = 0.0000   (distances 30-915 tokens)
  induction_acc      = 0.0208
  copying_acc        = 0.8750   (distances = 7 tokens, EVERY example)
  state_tracking_acc = 0.1250

An independent re-implementation of the scorer reproduced kv 0/32, and decoded
examples confirm both tasks are well-posed
("Fact: yellow is Monday. ... Question: What is yellow? Answer:" -> Monday).
So this is not a scorer bug: it is a capability result.

## Why this halts the experiment
The law needs a task that is BOTH long-distance (so the window discriminates)
AND learnable at this scale. The battery has neither in one family:
  - needle has the distance range (30-915) but is unlearnable here (0.000);
  - copying is learnable (0.875) but every retrieval distance is 7 tokens, so
    every candidate window covers it and all predicted ceilings are 1.0.
Running the four cells to completion would very likely have triggered the
pre-registered PREREQUISITE gate ("if the W=1024 cell does not reach 0.50
needle accuracy the run is INCONCLUSIVE ON COMPUTE, not a refutation") after
~24h and ~$100. Halted at ~50 min (~$5) instead. Both instances STOPPED.

## The scientific finding to keep (worth reporting)
A compute-optimal 110M transformer trained on 2.5B tokens of natural text does
NOT acquire in-context key-value or needle retrieval (0.008 / 0.000) while it
does acquire local copying (0.875). Note that a naive induction head predicts
the token that FOLLOWED the key ("is"), not the value, so key-value retrieval
requires a strictly harder circuit. This is independent evidence, on real text
at 110M scale, for the program's central thesis that retrieval is compute-gated
rather than emerging with generic language competence.

## Redesign for p1b (the actual fix)
The toy-scale campaigns TRAINED on the retrieval task and evaluated on a
held-out salted panel. The natural-text analogue must do the same: mix
needle-format examples generated from the TRAIN split (with a salt distinct
from the frozen evaluation battery) into the training stream, so the model
learns the task FORMAT, and the window then determines whether retrieval is
POSSIBLE. Zero-shot emergence of the format from pure language modelling was
an unstated and, as measured above, false assumption in the original design.
The pre-registered needle predictions (0.2154 / 0.2231 / 0.4154 / 1.0) are
derived from panel geometry alone and therefore REMAIN VALID UNCHANGED for
p1b; only the training recipe changes.
