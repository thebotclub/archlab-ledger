# QUARANTINED PREMATURE VERDICT — 2026-08-09 (Hani session)

`decision.json` was moved to `decision.json.PREMATURE-QUARANTINED-20260809T1422Z`.

## Why
monitor.py fired at 14:22Z while the campaign was still training and scored
PARTIAL data as if it were final. The file it wrote claimed:

    "status": "COMPLETE"
    "verdict": "INSTRUMENT_SUSPECT"
    gates G0-G3 all False, every arm n_transitioned = 0

At the moment it fired, only a handful of result rows existed out of 44 expected.

**CORRECTION 2026-08-09 15:58Z:** this note originally said "4 of 24". The 24 was
WRONG. The expected count is **44**, confirmed independently three ways during
verification: campaign.json's shard manifest (16+16+4+8), each shard's own
manifest.json as read by the trainer, and run_at.py's row-generation logic. The
operator's own ticks had separately quoted both 6/24 and 6/28, so the wrong
denominator was circulating in several places. The fixed monitor derives 44 from
the manifest rather than from any written-down number. The
control arm read 1/3 transitioned, which is not a G0 failure — it is an empty
sample. NONE of those gate readings are meaningful and NO family claim can be
drawn from that file.

## Status
The campaign is STILL RUNNING and healthy: 4/4 shard workers alive, GPUs 45-94%,
sealed predictions and gates (campaign.json, ledger commit 3ba41c07) UNTOUCHED
and still binding. This quarantine changes no gate, no prediction, and no
threshold — it removes a false artifact, nothing else.

## Why it was moved rather than deleted
It is evidence of a harness defect and must survive for audit. It was moved
rather than left in place because `decision.json` is the file every downstream
consumer treats as the campaign's verdict — the research-vault ledger reads it
directly and had already begun publishing this campaign as COMPLETE /
INSTRUMENT_SUSPECT, which is false.

## What must happen
When all 24 runs have landed, re-run monitor.py manually against the COMPLETE
result set to produce the real decision.json. Do not reuse or edit the
quarantined file. Do not create `.handled` for it.

## Root cause to fix
monitor.py scored on elapsed time / worker state rather than on a completeness
check. It must refuse to score until the expected result count is present, and
must write decision.json atomically only after that check passes.

**FIXED 2026-08-09:** a completeness precondition and a
never-overwrite-an-existing-verdict guard are now in this campaign's monitor.py
(pre-edit backup: monitor.py.bak-precompleteness-20260809T1531Z) and in the four
Lab 3 lineage monitors that clone forward into new campaigns. Independently
verified: the fixed monitor refuses on this live campaign with
"INCOMPLETE: have 8 of 44 expected result rows -- refusing to score" and writes
nothing. Note monitor_loop.sh is one-shot and has already exited, so the real
re-score must be triggered manually once all 44 rows land. This is the
fourth premature/false "finished" artifact in this program (bc x2
INCOMPLETE_FAILED, the false a01 outage, this one) — the pattern is a
supervision layer that reports conclusions from unverified state.
