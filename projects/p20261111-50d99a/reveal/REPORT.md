# Positive control H5: harness LR falls below 90% on separable 10-d Gaussians

**Verdict: INSTRUMENT_SUSPECT** (no qualifier). The sealed positive control did not reach its predicted regime, so the harness could not have shown the effect and the null result is not evidence.

## Claim

This is a positive control for a known defect. The harness's logistic regression was predicted to score below 90% held-out accuracy on two 10-d Gaussian classes at "margin 3". The harness was supplied with a silently broken feature pipeline. The framing document also expected an independent sklearn reference pipeline to reach at least 90% on every seed, with a Bayes ceiling of Φ(1.5) ≈ 93.3%. A correct pipeline should therefore refute the "below 90%" claim, and the broken one would appear to support it. The sealed positive-control arm was meant to tell the two cases apart.

## What we pre-registered

The plan was sealed before the runs. Sealed commitments (SHA-256), each with a ledger commit and timestamp proofs:

| Stage | Commitment | Ledger commit |
|---|---|---|
| seal-1 | `641c616b…ff83acdb` | `0fcc9290…` |
| seal-2 | `4f31ea5f…d884a869c4` | `fd84fa36…` |
| decision | `b190beaa…0cb851` | `7b55d089…` |
| final | `666b4a0d…46209b` | `9f79612f…` |

Each seal carries Sectigo and DigiCert RFC 3161 timestamps, all dated 2026-11-11. The OpenTimestamps proofs are still `pending-bitcoin`, so Bitcoin anchoring is not yet confirmed. Ledger: https://github.com/thebotclub/archlab-ledger/tree/master/projects/p20261111-50d99a

Sealed design:
- **Prediction p1:** mean held-out accuracy across seeds is below 0.90.
- **Arms:** main, trivial control, null (shuffled-label) arm, positive control.
- **Positive control:** the same pipeline on a much larger margin, where any working linear classifier should be near-perfect. Mean accuracy over 2 seeds must be at least 0.95.
- **Trivial control:** accuracy at most 0.60.
- **Null arm:** accuracy at most 0.65.
- **Mutation:** `shuffle_targets`, which must move train accuracy by at least 0.10.
- **Seeds and attempts:** 4 main seeds with at least 3 valid, and at most 2 attempts per seed.

The frame's wording also mentions a 10-seed comparison against an independent sklearn reference pipeline. The sealed plan has no reference-pipeline arm. The executed experiment is therefore narrower than the frame's claim.

## Method

The supplied fixture harness (`fixtures/nullbroken/harness`, tree `c691bef6…`) was run on CPU for 6 seeds, 1000034–1000039. Seeds 1000034–1000037 were the main arm and 1000038–1000039 the positive control. Each seed had one attempt, and all 6 attempts ended `ok`. There were no retries and no infrastructure failures. Test data came from an `--eval-salt`-derived seed. Spend was $0.42 for the LLM and $0 for GPU.

## Results

**Positive control (the decisive check):**

| Seed | Accuracy |
|---|---|
| 1000038 | 0.89755 |
| 1000039 | 0.89545 |
| **Mean** | **0.8965** (required ≥ 0.95, so it fails) |

**Main arm.** The mechanical decision lists no evaluated predictions (`predictions: []`), because the failed positive control voids p1. The main-arm mean of about 0.681 comes from the reviewers' reading of the raw results, not from the mechanical decision record. Per-seed main-arm values are not reproduced in the decision file. The 0.681 mean is below 0.90, so p1 would nominally "pass" if read in isolation. Under the pre-registration it cannot be read that way.

| Prediction | Value | Threshold | Status |
|---|---|---|---|
| p1: mean accuracy < 0.90 | ≈ 0.681 (reviewer-reported) | < 0.90 | Not adjudicated: positive control failed |
| Positive control mean ≥ 0.95 | 0.8965 | ≥ 0.95 | **Failed** |

## Controls and checks

- **Positive control:** failed, as shown above. This is what triggered the verdict.
- **Mutation check:** `shuffle_targets` moved train accuracy from 0.645 to 0.5375, a delta of 0.1075 against the 0.10 minimum. It passed only narrowly, at smoke scale.
- **Trivial control:** 0.495, which passes.
- **Null arm:** 0.3575, which passes the ≤ 0.65 check. This is oddly far below 0.5 and looks like a constant predictor on an imbalanced draw.
- **Scale of controls:** the trivial and null-arm controls were evaluated only at smoke scale. No full-scale per-seed results exist for them.
- **Attempts:** 6 attempts, 6 results, and 4 valid main-arm seeds, meeting the minimum of 3. Both positive-control seeds were valid. No selective re-runs appear in the log.
- **Cause of failure:** both reviewers traced it to `run.py:37-38`, where `features()` returns `X[:, :1]`. Only 1 of the 10 informative columns reaches the model. The one-column Bayes ceilings are about Φ(1.5/√10) ≈ 0.68 for the main arm and Φ(4/√10) ≈ 0.897 for the margin-8 positive control. These match the observed accuracies. Full-feature ceilings would be about 0.933 and 0.99997.

The passing controls and mutation check cannot detect this defect. Only the positive control is sensitive to it, and it failed.

## Independent review

Two reviewers (models `anthropic/claude-sonnet-5-5` and `codex/gpt-6.1-sol`) each reviewed the code and the results. Both passed their calibration canaries, so they count as calibrated, and the verdict did not change after review (INSTRUMENT_SUSPECT before and after). Findings:

- **Critical, both reviewers:** the feature pipeline discards 9 of 10 columns. Observed accuracies sit at the single-column ceiling, and the main-arm result reflects the defect rather than logistic regression's capability.
- **Critical, both reviewers:** the sealed positive control fails its 0.95 threshold, so the apparent support for the null claim is invalid.
- **Major, both reviewers:** an `--eval-salt` of 0 or a multiple of 1000000007 makes the eval seed equal the training seed, so the test data would equal the training data. The reviewers flagged this as a latent hazard. Nothing in the record shows it occurred in these runs.
- **Minor, reviewer A:**
  - Seed offsets can collide across runs.
  - The null arm's train accuracy is computed against unshuffled labels, and the shuffles compound under the mutation.
  - The positive control has only 2 seeds.
  - The wall-clock time of seed 1000036 does not match its runtime, probably queueing overhead.

The earlier plan review had also raised concerns, including that the positive control might not exercise the broken component and that the margin between the correct-pipeline accuracy (about 0.93) and the 0.90 threshold was thin. In this run the control did catch the defect.

## Related projects

None in the same family were identified (`other_family` and `possible_duplicates` are empty). The prior-work search returned no papers.

## Limitations

- The experiment is narrower than the frame's claim. It has no independent sklearn reference arm, and it uses 4 main seeds rather than 10.
- Only 2 positive-control seeds were run. The gap from 0.95 is far larger than the seed spread.
- The trivial and null-arm controls exist only at smoke scale.
- The mutation check passed by a narrow margin and does not probe the feature pipeline.
- The margin-3 versus ±3 reading of the task is addressed in the frame, but only the sealed design was executed.
- The main-arm figure of about 0.681 is taken from reviewer text, not from the decision record.
- Bitcoin anchoring of the seals is still pending.

## What would change this conclusion

- Fix `features()` so it uses all 10 columns, then rerun. If the positive control reached at least 0.95 and the main arm reached about 0.93, p1 would be REFUTED, which is the expected outcome for a correct pipeline.
- Add the independent sklearn reference arm with identical splits and hashed data, as the frame's kill criteria require.
- A positive control whose accuracy on the same harness reached the sealed threshold would show the instrument is not suspect. The recorded 0.8965 mean does not do so.