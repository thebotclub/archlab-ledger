# p1e evaluation runbook — finishing the job when wave B lands

Campaign: `prv-lawtransfer-20260801-p1e` (multi-seed replication of the
window-provisioning law). Evaluation machinery lives in
`/home/hani/archlab-p1e-eval/` (built 2026-08-03).

## State as of 2026-08-03

- G2 reproduction (seed 2100 re-scored on the frozen p1d battery) — **DONE, exact
  match to p1d in all four cells**. Scoring path validated end-to-end.
- Wave A (seed 2101, 4 cells) — scored; `stablegla_s2101_w*.scores.json` in
  `/home/hani/archlab-p1e-eval/` and copied here.
- Wave B (seed 2102) — checkpoints not yet landed. `decision.json` is
  deliberately NOT emitted until all 12 cells exist (aggregate_p1e.py is
  idempotent and refuses to decide early).

## When wave B's 4 result/ckpt files land (stablegla_s2102_w*.ckpt.pt in this dir)

Run, in order (each scorer is ONE PROCESS PER CELL — never loop windows inside
one python process; models.py reads S05_WINDOW once at import; the scorer sets
and asserts it, and pins CUDA_VISIBLE_DEVICES=2 in-script):

```bash
PY=/home/hani/archlab/.venv/bin/python
EV=/home/hani/archlab-p1e-eval
P1E=/home/hani/archlab2-runs/prv-lawtransfer-20260801-p1e

cd $EV
for w in 128 256 512 1024; do
  $PY score_p1e.py $w $P1E/stablegla_s2102_w$w.ckpt.pt \
      stablegla_s2102_w$w.scores.json > score_s2102_w$w.log 2>&1
done

# copy scores into the campaign dir (ledger cron picks them up)
cp $EV/stablegla_s2102_w*.scores.json $P1E/

# mechanical G0–G6 verdict, thresholds verbatim from campaign.json
$PY aggregate_p1e.py
```

`aggregate_p1e.py` writes `decision.json` to `$EV` and copies it here. It
embeds the pre-registered gate text and interpretation strings verbatim; the
verdict mapping (LAW_REPLICATES_ACROSS_SEEDS / G6-only /
LAW_DOES_NOT_REPLICATE / VOID) is fixed in campaign.json
`interpretation_fixed_in_advance` and is not to be amended after seeing data.

## Notes

- ~4 min per cell on one V100; ~16 min for wave B total.
- The scorer verifies the frozen battery sha256s (campaign.json
  `battery_file_sha256`) before producing any number, and records the
  checkpoint sha256 in each scores.json.
- GPU policy at build time: GPU 2 only (0/1 live campaign, 3 another agent).
  If that reservation has changed, edit the `CUDA_VISIBLE_DEVICES` line at the
  top of `score_p1e.py` — it is the only GPU pin.
- If G2 ever stops reproducing (aggregate reports `G2_reproduction: false`),
  the run is VOID per prereg: instrument fault, no claim either way.
