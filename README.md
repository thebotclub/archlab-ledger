# archlab-ledger — the evidence ledger for the window-provisioning paper

This repository is the append-only pre-registration and results ledger behind
*"Provisioning Recall: Windowed Attention Saturates Its Window, and How Much It
Will Recall Can Be Predicted Before Any Training Result Exists"* ([ARXIV-LINK]).
If you arrived from the paper's Reproducibility section: this is the artifact it
points at, and everything below is written for the reader who intends to check
the claims rather than take them.

Each top-level directory is one campaign. A campaign's manifest
(`campaign.json`) is written and committed **before** its results exist; its
decision (`decision.json`) is a mechanical evaluation of pre-registered gates
against the raw result files sitting next to it. Commit timestamps on this
repository provide external ordering. Nothing is ever amended in place:
corrections are dated addenda, refuted claims stay in the record with their
refutations, and voided campaigns keep their directories.

Tooling derived from these results: [recallkit.ai](https://recallkit.ai)
(`pip install recallkit-ai`).

## The honest inception disclosure, first

External timestamping does not cover the whole record, and you should know
exactly where the seam is — the paper states this in its Reproducibility
section and this README mirrors it rather than softening it:

- **This repository was created 2026-07-30T03:26Z — mid-way through campaign
  `ap`'s training run.** From that point on — every campaign sealed after
  inception, `aq` onward (first `aq` commit 2026-07-30T05:00Z), including the
  `aw`/`ax` falsification ladder, `az`, `p1c`'s mid-training addendum, `p1d`,
  `p1e` and the `p2` series — manifests are committed contemporaneously by a
  20-minute cron, and their commit timestamps establish pre-registration
  ordering externally. (An earlier revision of this README enumerated this
  span as "`az` onward"; that understated it — the commit history shows `aq`
  through `ay` committed contemporaneously as well.)
- **Campaigns sealed before that date (`m` through `ao`, and the a–j era) were
  backfilled en masse at repository creation.** Their pre-registration ordering
  rests on internally consistent manifests, hashes and file mtimes, attested
  only by the machine that produced the results.
- For campaign `ap` specifically — the pre-registered out-of-sample law test —
  the predictions entered this repository in the inception commit
  (`bdd3720`, 2026-07-30T03:26:31Z): 31 minutes **after** its training started
  and 13 minutes **before** its first result artifact. The paper's abstract
  says "before any training result existed", not "before training", for
  exactly this reason.

If your threat model requires external timestamps for everything, the
externally-ordered portion of the record (everything from 2026-07-30T03:26Z
onward) includes the law test `ap`'s results, the sealed FoX-Pro claim
campaign `aq`, the `aw`/`ax` falsification ladder, the step-matched
transformer control `az`, the natural-language leg (`p1c`–`p1e`), and the
entire deployed-checkpoint series (`p2a`–`p2f`).

## Anatomy of a campaign directory

| File | What it is |
|---|---|
| `campaign.json` | The pre-registration: numeric predictions and/or gates, seeds, panels, budgets, the sealed hidden-eval salt (as a SHA-256), `registered_utc`, and a `claim_eligible` flag. Written before launch. |
| `decision.json` | The mechanical gate evaluation, written at completion: per-arm outcomes and a status string (`PASS`, `FAIL`, `GATE_NOT_MET`, `LAW_DOES_NOT_TRANSFER`, `CONFOUND_ALERT`, …). Failures are recorded as failures; no decision has ever been amended in place. |
| `gate_evaluation.json` | Where present, the per-cell gate arithmetic (predicted vs observed, absolute error, confirms true/false). |
| `SOURCE__*.py` | The harness sources (`data.py`, `models.py`, `train.py`, …) copied verbatim into the campaign directory at launch. This became structural policy after a harness source was lost to a working-directory collision (see the `p2b` VOID entry below). |
| `<shard>__manifest.json`, `<shard>__result.json`, `<shard>__run.log` | Per-shard raw evidence: the seeds run, per-run hidden-eval recall and losses, and the full training log. Lab-2 campaigns use `<arm>.result.json` naming instead. |
| `monitor.py`, `gpu*_chain.sh`, `*.log` | The execution machinery, kept because "what actually ran" is part of the evidence. |
| `VOID.md` | Present only in voided campaigns; states why, in full. |

`preregistrations/` holds standalone pre-registration documents that precede
their campaigns (e.g. the p1d needle battery, the p2a scale test).

## Verify a sealed claim end-to-end: campaign `ap` in 5 steps

`stablegla-lawtest-20260730-ap` is the paper's §4.1 out-of-sample test: eight
numeric recall ceilings predicted from task geometry alone, sealed before any
training result existed. To check it, from a clone of this repo:

**1. Read the pre-registration.**
`stablegla-lawtest-20260730-ap/campaign.json` contains the eight predicted
ceilings under `preregistered_predictions` (e.g. `g1_w96`:
`in_window_fraction` 0.344255, `predicted_ceiling` 0.385239), the gates under
`preregistered_gates` (`registered_utc: 2026-07-30T02:55:04Z`; each cell
confirms if the max observed recall over its 6 seeds is within ±0.05 of the
prediction; pass requires ≥6 of 8 including the f=1 trivial control), the seed
assignments per shard, and the sealed development-salt hash.

**2. Establish the ordering externally.**
```
git log --diff-filter=A --format='%H %aI' -- stablegla-lawtest-20260730-ap/campaign.json
```
The manifest enters at commit `bdd3720`, 2026-07-30T03:26:31Z (the inception
commit — see the disclosure above for what that does and does not attest).
The same command on any result file shows it arriving later. For any
post-inception campaign this step gives fully contemporaneous ordering.

**3. Recompute the predictions yourself.**
Each ceiling is pure arithmetic on the manifest's own numbers:
`predicted_ceiling = f + (1 − f)/16`. For `g1_w96`:
0.344255 + 0.655745/16 = 0.385239. Nothing about the model enters; a
prediction you can recompute from the pre-registration cannot have been fitted
to the results.

**4. Read the raw evidence and take the maxima yourself.**
The eight `*__result.json` files hold all 48 runs' hidden-eval recalls (the
same numbers are echoed per-arm in `decision.json` — e.g. `g1_w96` recalls
[0.0629, 0.0619, 0.3854, 0.0777, 0.3872, 0.3842]: three seeds at the ~0.0625
chance floor, three at the ceiling, which is the paper's §4.4 bimodality in
the raw data). Take the max per cell. The `*__run.log` files show the full
training trajectories, and `SOURCE__*.py` is the exact harness that produced
them.

**5. Re-evaluate the gate mechanically.**
Compare your per-cell maxima against `gate_evaluation.json` (predicted vs
`observed_max`, `abs_error`, `confirms`) and against `decision.json` (status
`LAWTEST_COMPLETE`). All eight cells confirm with absolute errors of
0.0010–0.0047 — an order of magnitude inside the ±0.05 tolerance. Everything
in the decision should be derivable by you from steps 1 and 4; if it is not,
that is a finding, and we would like to hear about it.

The same five steps work on any campaign here; only the file names of step 4
vary. For the paper's pooled transformer counts, the released
`recount_transformer_corpus.py` (shipped with the paper's audit trail) is the
single source of truth and recomputes them from these artifacts.

## Naming: the suffix is the lineage

Directories are named `<topic>-<YYYYMMDD>-<suffix>`. **The suffix, not the
date or the topic string, is the campaign's identity and its unit of
ownership.** Single letters run chronologically through the synthetic program
(`a` … `z`, then `aa`, `ab`, …): `a`–`j` are the pre-assay-repair era
(enumerated in the paper's Appendix C; nothing from it is cited as evidence,
nothing from it was deleted), `k` onward is the frozen-suite era, and the nine
sealed claim campaigns are `m, q, r, t, u, ag, aj, ak, am`. Prefixed suffixes
are the Lab-2 lineages: `p1a → p1e` is the natural-language law-transfer
chain, `p2a → p2f` the deployed-checkpoint chain, `pr1` a mechanism probe.
Consecutive suffixes within a lineage are repair chains: each successor's
manifest documents the faults of its predecessor's instrument, and no
predecessor's gate is ever amended — `p2b`'s pre-registered
`LAW_DOES_NOT_TRANSFER` stands in its `decision.json` even though the
instrument that produced it was later itself corrected.

## The two VOID campaigns are part of the record

- **`prv-lawtransfer-20260802-p2b`** — a name-collision campaign. An
  interactive session registered a campaign under a suffix the autonomous
  operator was already running, inherited a known instrument fault, and
  overwrote the operator's harness source in a shared working directory. It
  was halted and voided; `VOID.md` states what was damaged, plainly — and
  itself contains a dated correction, because the first version of the void
  note made a false claim ("no result file was written") that checking
  falsified. The resolution (suffix = ownership; sources copied into campaign
  directories at launch) is recorded there too.
- **`stablegla-mechanism-20260725-i`** — an empty directory: a
  registered-then-abandoned placeholder whose suffix collides with
  `stablegla-compute-threshold-20260725-i`. Disclosed in the paper alongside
  the two cross-campaign seed collisions, and left in place.

Both stay because an append-only ledger that quietly dropped its
embarrassments would not be worth the name.

## Pointers

- Paper: [ARXIV-LINK] — see its §3.4 (sealed protocol), §3.6 (the autonomous
  protocol), Appendix C (superseded campaigns), and Reproducibility (whose
  inception wording this README mirrors).
- Tooling: [recallkit.ai](https://recallkit.ai) — `pip install recallkit-ai`.
  `provision.py` reproduces campaign `p1d`'s sealed predictions to float
  error; the probe reproduces the `p2c`/`p2d` instrument.
- Competing interests: THE BOT CLUB PTY LTD has filed AU provisional patent
  applications (2026906694, 2026906768) covering the provisioning method; the
  paper discloses the same.
