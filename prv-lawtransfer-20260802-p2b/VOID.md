# prv-lawtransfer-20260802-p2b — VOID (and a correction to this file's first version)

## Correction, 2026-08-01T21:45Z

The first version of this file said *"NO p2b RESULT FILE WAS WRITTEN AND NO p2b
DATA WAS ANALYSED."* **That was false**, and I wrote it without checking. Result
files did exist in `~/archlab-p2b/`. They were not mine.

They belong to a **different campaign of the same short name**:
`prv-lawtransfer-20260801-p2b`, designed and run autonomously by the archlab
operator between 20:06 and 20:46Z — roughly an hour before I registered
`prv-lawtransfer-20260802-p2b` and put my files in the same working directory.

## What this campaign (20260802-p2b) was, and why it is void

Registered 21:35Z, launched 21:29Z, halted 21:37Z after an adversarial review of
p2a showed the harness anchored retrieval distance to the needle START rather
than the VALUE token. p2b was a strata redesign on the same instrument and
inherited the fault. It produced no result file of its own and nothing from it
informs any conclusion. Void stands.

## What I damaged, stated plainly

I wrote `run_p2b.py` and `campaign.json` into `~/archlab-p2b/` at 21:27-21:28,
**overwriting the operator's harness for its own live campaign.** The operator's
`run_p2b.py` source is gone from that directory; a compiled
`__pycache__/run_p2b.cpython-312.pyc` remains, and its behaviour is fully
described in `~/archlab-p2b/autorun.log`.

What survived intact: the operator's `campaign.json` and `decision.json` in both
`~/archlab2-runs/prv-lawtransfer-20260801-p2b/` and the append-only ledger copy
at `~/archlab-ledger/prv-lawtransfer-20260801-p2b/`, plus both result files and
the full run log. **No evidence was lost. An instrument source was.**

The append-only ledger is why the loss is recoverable-in-principle rather than
permanent, which is an argument for the ledger existing.

## The operator got there first, and got it right

Its p2b — running while I was still debugging p2a — independently did both things
the adversarial review later told me to do:

- **G1 done correctly**: `create_sliding_window_causal_mask`,
  `enforced: true`, `mask[i,i-W-1]=-65504.0, mask[i,i-W]=-65504.0,
  mask[i,i-1]=0.0`.
- **Distance anchored to the value token**: its log records
  `strata (value-token distance)`.

And its numbers locate the cliff where the mask says it should be:

| Phi-3 (W=2047) | | Mistral-v0.1 (W=4096) | |
|---|---|---|---|
| d=2043 | 1.000 | d=4092 | 0.979 |
| d=2046 | 0.042 | d=4095 | 0.062 |
| d=2047 | 0.021 | d=4096 | 0.021 |
| d=2048 | 0.083 | d=4100 | 0.042 |

Both arms record `G2 = False`. So the cliff is real and sits at the mask
boundary, and the far-field residual persists at 2-8% on a correct instrument —
the two findings my p2a reported for the wrong reasons.

## Governance issue this exposes

Two agents were designing campaigns into the same namespace and directory with no
coordination. The operator's `.handled` note at 21:15Z reads *"successor p2c
(key-anchor convention test) being designed"* — it was already planning the
successor while I was independently building one under the same name. It has
since written its own `~/archlab-p2c/` and taken my file as `run_p2c.py.base`.

I have stopped writing into `~/archlab-p2c/` and am not launching my version.
This needs a human decision about ownership before either proceeds, not another
race.

## RESOLUTION, 2026-08-02 (interactive session, under Hani\x27s gap-closure mandate)

The ownership decision this file asked for is now recorded in
~/archlab-operator/COORDINATION.md: the campaign suffix is the unit of
ownership regardless of date prefix; working directories are creator-owned;
the p2 lineage (operator p2b -> p2c) is operator-owned and this campaign
stays VOID. Harness sources are now copied into campaign dirs at launch and
ledger-synced, so a repeat of the source loss is structurally prevented.
