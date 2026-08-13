# Stage A pilot (campaign `au`) — TERMINAL RECORD, 2026-08-13

**Gate A4 (>= 3/6 transitions): FAILED. 0 transitions in 4 valid runs.**
Stage B is NOT unblocked and must not be sealed or launched on this panel.

## Result

| seed | status | recall | final loss |
|---|---|---|---|
| 3980 | valid | 0.0183 | 0.8485 |
| 3981 | valid | 0.0156 | 0.8497 |
| 3982 | valid | 0.0271 | 0.8539 |
| 3983 | valid | 0.0218 | 0.8506 |
| 3984 | **INVALID** | — | harness path bug, never trained |
| 3985 | **INVALID** | — | harness path bug, never trained |

The decisive number is not the aggregate but the **in-window** recall: **0.0069** at
d <= W = 14, against 0.0183 out-of-window. The model did not learn the task at all — this is
not "learned but could not reach far", it is noise, and out-window scoring slightly *above*
in-window is what noise looks like. The repaired `elimsafe80` panel is elimination-safe and
**unlearnable** by a 4-layer 7.2M-parameter model at 200k steps.

The gate outcome does not depend on the two invalid runs: even had both transitioned, 2/6 < 3/6.

## Two defects found, both recorded rather than papered over

**D1 — harness path bug (cost 2 of 6 runs).** Seeds 3984/3985 died on
`FileNotFoundError: /home/hani/archlab-runs/battery/strat-d72.json` — the path is missing the
campaign-directory component; the battery lives at
`~/archlab-runs/instrument-repair-20260811-au/battery/`. The four completed runs read the correct
battery (`panel: elimsafe80, battery: strat-d72` recorded in their `result.json`), so the floor
finding stands on valid data. **Fix the launcher before any re-run.**

**D2 — the completeness monitor waits forever for runs that can never arrive.** `monitor.py`
polled `waiting: 4/6 seeds done` every 5 minutes for **15+ hours** after seeds 3984/3985 had
already died. The completeness gate is correct and is the fix for the `at` premature-verdict
incident — but it checks only whether results are *present*, never whether the missing ones are
still *possible*. Because the monitor process stayed alive, the operator reported the campaign as
`running`, so a terminal campaign presented as healthy and in progress.

This is a distinct failure shape from the ones already on record. The programme's rule is "an
all-clear must be able to return not-clear"; this is a **wait that can never end**. A completeness
gate needs a liveness check on what it is waiting for:

> If an expected run has no live worker AND its log ends in an error, it is DEAD, not pending.
> Report INCOMPLETE-TERMINAL and stop. Never wait on a corpse.

Monitor stopped 2026-08-13T00:0xZ by the interactive session; `monitor.pid` 2087740 killed,
`wave1-relaunch.pid` and `wave2-launcher.pid` were already dead.

## Consequence for Stage B

Stage B as designed would floor on every arm and return a second INSTRUMENT_SUSPECT. The pilot
did exactly its job: ~7h of compute prevented ~68h of it.

**The underlying tension is the finding.** Elimination-safety requires
`pairs - queries + 1 >= NVAL`, i.e. >= 23 pairs at 8 queries. Going from 8 pairs (easy48, which
transitions to recall 1.0) to 28 pairs (elimsafe80) made the task unlearnable. Making the panel
honest made it impossible. Those two requirements are in direct conflict on this ladder, and that
is a design problem, not a tuning problem.

One untested route out: the confound exists because queries are drawn **without** replacement, so
the final answer is inferable by elimination. Drawing **with** replacement breaks the bijection and
may permit a small pair count — possibly restoring an 8-pair panel that is both learnable and
elimination-safe. **Not verified. Needs a senior ruling before any build**, given both prior panel
designs carried non-obvious flaws.
