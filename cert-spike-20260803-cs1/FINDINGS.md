# FINDINGS — cert-spike-20260803-cs1

**Verdict: MUNDANE-CONFIDENCE-ONLY (pre-registered reading). No Lab 4 brief
recommended on this evidence.** $0 spent. All thresholds below are quoted from
PREREG.md, which was installed before training and before any probe was fitted.

## What was run

- Lab 1 saved no checkpoints anywhere (all campaigns incl. sealed m/q/r/t/u/
  aj/ak/am/ag hold source+results only); Lab 2's 8 checkpoints are unsuitable
  (no floored model; correctness structurally window-determined). So the
  dispatch's reproduction fallback was used: 4 runs cloning sealed campaign ak
  exactly (p80x384@6e15, seeds 1196/1197, gla vs onorm_qknorm_win256).
- Reproduction was **bit-identical** to ak's result.json in all 4 cells
  (gla 0.06432/0.06107 floored; candidate 1.0/1.0 transitioned; final losses
  equal to full precision). Sanity gate PASSED.
- Training-time transition is sharp: s1196 recall 0.061->0.9985 between steps
  442->663; s1197 0.102->0.9998 between 663->884 (10%-granularity checkpoints).
  **No checkpoint fell in the pre-registered mid-transition band [0.20,0.95]**,
  so no mid cells (rule applied as written; the 0.102 checkpoint just misses).
- Probes: fresh panels P80/P96/P112/P128 (salt 3900, n=512 seqs, 40 queries),
  residual stream at query positions (emb + 8 blocks), split-by-sequence
  60/40 (seed 3901), class-weighted L2 logistic probes, single split.

## AUC table (test split; best layer per cell; full per-layer in results.json)

| model (state) | panel | recall | n_err | best layer AUC | conf-3feat AUC | raw margin | geometry* |
|---|---|---|---|---|---|---|---|
| gla_s1196 (floored) | P80 | 0.062 | 19206 | 0.494 | 0.509 | 0.511 | 0.519 |
| gla_s1196 | P96 | 0.063 | 19186 | 0.510 | 0.517 | 0.517 | 0.502 |
| gla_s1196 | P112 | 0.064 | 19171 | 0.537 | 0.516 | 0.489 | 0.500 |
| gla_s1196 | P128 | 0.063 | 19197 | 0.521 | 0.522 | 0.498 | 0.491 |
| gla_s1197 (floored) | P80 | 0.063 | 19193 | 0.516 | 0.511 | 0.474 | 0.523 |
| gla_s1197 | P96 | 0.065 | 19143 | 0.483 | 0.492 | 0.493 | 0.495 |
| gla_s1197 | P112 | 0.062 | 19211 | 0.503 | 0.501 | 0.500 | 0.491 |
| gla_s1197 | P128 | 0.063 | 19181 | 0.502 | 0.492 | 0.506 | 0.492 |
| cand_s1196 (transitioned) | P80 | 1.000 | 0 | UNDERPOWERED (0 errors) | - | - | - |
| cand_s1196 | P96 | 0.991 | 176 | 0.540 (L7) | 0.907 | 0.907 | 0.999 |
| cand_s1196 | P112 | 0.936 | 1312 | 0.693 (L8) | 0.890 | 0.890 | 0.997 |
| cand_s1196 | P128 | 0.850 | 3072 | 0.708 (L8) | 0.885 | 0.886 | 0.993 |
| cand_s1197 (transitioned) | P80 | 1.000 | 0 | UNDERPOWERED (0 errors) | - | - | - |
| cand_s1197 | P96 | 0.992 | 175 | 0.669 (L8) | 0.895 | 0.895 | 0.999 |
| cand_s1197 | P112 | 0.936 | 1319 | 0.845 (L8) | 0.866 | 0.866 | 0.997 |
| cand_s1197 | P128 | 0.849 | 3101 | 0.822 (L8) | 0.887 | 0.887 | 0.994 |

*geometry = descriptive covariate probe on [key-value distance, query index];
never a verdict input.

## Pre-registered readouts, applied

1. **Floored control: PASS.** All 72 layer-cells across both gla models and
   all four panels sit in [0.472, 0.537], inside the pre-registered band
   [0.35, 0.65]. Nothing to know, and the probe correctly finds nothing —
   the instrument does not hallucinate signal.
2. **Transitioned, DECODABLE (AUC >= 0.75):** met only by cand_s1197 at P112
   (0.845) and P128 (0.822). cand_s1196 peaks at 0.708 — below threshold.
3. **GENUINE INTERNAL SIGNAL (activation AUC >= confidence baseline + 0.10):
   met NOWHERE.** In every powered transitioned cell the activation probe is
   BELOW the output-confidence baseline (0.845 vs 0.866; 0.822 vs 0.887;
   0.708 vs 0.885). The pre-registered GENUINE verdict also required both
   seeds independently; neither clears it.
4. **DEAD (kill criterion, all layers <= 0.60 in every powered transitioned
   cell): not met** — above-chance decodability does exist above the
   capability transition and grows with depth (monotone toward L8).
5. **Verdict by pre-registered precedence: MUNDANE-CONFIDENCE-ONLY.**
   Whatever correctness information the residual stream carries at the query
   position is a strict subset of what the output logits already expose.

## Interpretation

- There IS an internal correlate of per-answer correctness that switches on
  with the capability transition (floored: flat ~0.5; transitioned: up to
  0.85, increasing with depth). But it never exceeds — indeed never reaches —
  the information already present in output confidence (max logprob/margin).
  On the charter's own terms this is the mundane outcome: self-knowledge here
  IS output confidence, not a separate internal signal, and there is no
  evidence of a second transition above the capability transition.
- The geometry covariate explains why: in the windowed transitioned
  architecture, correctness on harder panels is ~perfectly predicted
  (AUC 0.99+) by input geometry (queried key's distance vs the W=256 window).
  Errors are structural, and output confidence tracks them well (0.87-0.91).

## Honest caveats

1. **Error regime is structural, not idiosyncratic.** The transitioned
   architecture is windowed; harder panels create errors mainly by pushing
   keys out of the window. A metacognition probe on in-distribution,
   idiosyncratic errors was not possible: at recall 1.0 there are no errors,
   and no mid-transition checkpoint existed at 10% checkpoint granularity.
   The null is therefore established for the structural-error regime only.
2. cand P80 cells are UNDERPOWERED exactly as pre-registered (0 errors in
   20480 instances) — recall saturates at 1.0 above the transition.
3. Seed variance in decodability is material (peak 0.708 vs 0.845), though
   both seeds agree on the verdict (below confidence baseline).
4. Non-claim reproductions throughout; single pre-registered split; probes
   are linear — a nonlinear probe could in principle find more, but that
   comparison was not pre-registered and is not claimed.
5. Instrument fixes made after PREREG but before any probe result existed
   (logged): fp16->fp32 activation capture (GLA residual magnitudes overflow
   half precision), LBFGS->full-batch Adam (perfect-separation step-size
   overflow), standardized-feature clip at +/-30. Thresholds, split, panels,
   and readouts unchanged from PREREG.md.

## If anyone revisits this (requires a NEW charter per LAB3-CHARTER)

The one follow-up this data motivates: obtain a transitioned NON-windowed
model with idiosyncratic in-distribution errors (e.g. full stablegla from
campaign q's config, or denser checkpointing through the sharp transition
window steps 442-884) and re-ask whether activations beat confidence there.
This spike does not license that work.

## Artifacts

- Campaign dir: ~/archlab3-runs/cert-spike-20260803-cs1/ (campaign.json,
  PREREG.md, run_repro_cs1.py, probe_cs1.py, results.json, midscan.json,
  repro result JSONs, checkpoint sha256 manifest, this file).
- Working dir: ~/archlab-cs1/ (harness clone, checkpoints incl. finalA x4 and
  18 intermediates, logs, per-cell probe JSONs).
