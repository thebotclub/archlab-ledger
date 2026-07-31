# p1b evidence-retention gap — disclosure

**Written 2026-07-31 10:30 UTC, after the fact, by audit rather than by the
campaign's own reporting.** Recorded here because the numbers in `decision.json`
are cited in the executive summary and are candidates for the paper, and a reader
must be able to see what raw evidence does and does not still exist behind them.

## What happened

p1b's four cells ran on two rented instances. The instances were deleted at
2026-07-31 04:41 UTC, ~1 minute before `decision.json` was written at 04:42 UTC.
Per-cell `result.json` files were not collected to hub first.

State of the raw evidence on hub today:

| cell | raw result.json on hub | probe_curve retained |
|---|---|---|
| w128 | yes, 5,974 bytes | **yes — full curve** |
| w256 | present but **0 bytes** | no |
| w512 | **absent** | no |
| w1024 | **absent** | no |

The instances are deleted, so the three missing/empty files are unrecoverable.
No raw training logs (`law_w*.log`) for p1b survive on hub either.

## What this does and does not mean

**It does not mean the reported numbers are wrong.** `decision.json` is detailed,
internally consistent, and was written in good faith while the instances were
still reachable; its per-cell maxima, steps, and root-cause analysis read as an
accurate transcription. The GATE_NOT_MET verdict is unaffected — the positive
control failed by an order of magnitude in all four cells, far outside any
transcription-error range.

**It does mean that for three of four cells the numbers are transcriptions, not
artifacts.** They cannot be independently re-derived, recomputed at a different
checkpoint, or checked against the probe curve. For a lab whose stated value is
"pre-registered, tamper-evident, honest", that is a real gap and it belongs in
the methods section, not in a comment.

## Contributing cause: the ledger never archived Lab 2 results

`archlab-ledger-sync.py` globbed `result.json` and `*/result.json`. Lab 1 shards
results as `<cell>/result.json` and matched. Lab 2 writes them flat at campaign
root as `<tag>.result.json` and matched **neither** pattern. Consequence: no Lab 2
campaign (p1a, p1b, p1c) had any observational evidence in the ledger — only
pre-registrations. The ledger proved what was promised and nothing about what was
observed, which is the exact failure its own source comment warns against.

Fixed 2026-07-31 10:2x UTC; both filename shapes are now globbed, and p1b's
surviving w128 result is archived (w256 is archived as the 0-byte file it is).

## Fixed going forward

`p1c_collect_teardown.py` (cron, every 10 min) inverts the order that caused
this: it collects each cell's `result.json` and training log to hub, verifies the
local copy's sha256 against the instance's original, checks the file parses and
carries a non-empty `probe_curve` at the pre-registered step count, and **only
then** issues any DELETE. Any partial, empty, corrupt, or short result blocks
teardown and raises a Telegram alert instead. The gate was tested against the
live instance across six cases including the exact 0-byte condition that lost
p1b's w256; all six behaved correctly.

## Recommended disposition

1. Cite p1b's w128 numbers as artifact-backed; cite w256/w512/w1024 as
   transcription-backed, and say so in the methods section.
2. Do not quietly drop p1b now that p1c supersedes it. p1b stays in the record as
   GATE_NOT_MET with this retention gap attached.
3. If any p1b cell's numbers are load-bearing for a paper claim, re-derive them
   from p1c's retained artifacts instead — p1c re-tests the same pre-registration
   on a fixed instrument, with evidence retention now enforced.
