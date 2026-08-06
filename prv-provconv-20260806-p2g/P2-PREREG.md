# P2-PREREG — prv-provconv-20260806-p2g (Lab 2 Phase 2, Qwen pilot)

Status: FINAL REGISTRATION TEXT, 2026-08-06 ~04:45Z (operator). Sealed when
the ledger commit containing this file + the campaign mirror lands, BEFORE
any conversion training starts. Every previously signed item is FROZEN and
copied verbatim; every blank is now filled — by the SENIOR-SIGNOFF
(2026-08-05), by the D8 BINDING DECISION (2026-08-06, senior reviewer
delegated by Hani), or by the operator's PRE-SEAL decisions (D2/D3/D4,
2026-08-04/05). No discretion remains.

Sources of truth (all on hub, all mirrored to the ledger):
- `~/archlab2/p2-prep-20260803/P2-PREREG-SKELETON.md` (SIGNATURE RECORD)
- `~/archlab2/p2-prep-20260803/SENIOR-SIGNOFF-20260805.md` (4 blanks signed,
  scoping text; 7 flagged defects D1–D7)
- `~/archlab-p2g/D8-SENIOR-DECISION-20260806.md` (A1 window decision,
  binding, executed verbatim)
- `~/archlab-p2g/PRE-SEAL-DECISIONS-20260804.md` (D2/D3/D4/D8-discovery)

## Campaign identity
- Name: `prv-provconv-20260806-p2g`. Suffix p2g claimed 2026-08-04
  (`~/.archlab-suffix-claims/p2g`). Working dir `~/archlab-p2g/`; the
  campaign dir `~/archlab2-runs/prv-provconv-20260806-p2g/` is created at
  seal and receives campaign.json + the harness archive (rule 4).
- Cloud: IBM spot, p1e-proven shape (2xL40S), P2 CLOUD RULE: bootstrap
  asserts driver+headers — never assume the image path. Quote-before-create;
  spend_check-gated; evidence-gated collect+teardown (p1c pattern).

## FROZEN primary gate (Hani-signed 2026-08-04 — never amended after data)
Per certified cell (A1, A4 — see Certification-cell designation below):
freeze predicted recall BEFORE conversion completes; pass iff
|observed − predicted| ≤ **T_agg = 0.03** aggregate AND per-stratum
|observed − predicted| ≤ 0.05 on **≥ 20 of 24 strata**.
n accounting (D8, registered): n_agg = 9600 pooled scored retrievals over
the 4 certification primaries (2400/task), ~400/stratum pooled — D4's
≥100/stratum floor is cleared BY POOLING (per-task realized minima ≥ 369,
verified in the sealed battery's S26/S27 verify); the frozen n ≥ 2048 floor
is met 4.7×. Boundary convention b = W inclusive for the converted module
(p1d G6/p1e G7 precedent).

Certification set = the 4 primaries (`niah_single_1`, `niah_single_2`,
`niah_single_3`, `niah_multikey_1`) per RULER-SUBSET.md; the 4 secondaries
(`niah_multikey_2/3`, `niah_multiquery`, `niah_multivalue`) are reported
descriptively only (prevents the 8-way multiple-comparisons problem).

## Sealed predictions (recomputed from sealed battery 779038744, f = k/24
over the 24 strata, pooled primaries)
- p_chance_pooled = **8.333333e-08** (3 numbers-valued primaries @ 1/9e6;
  1 uuid primary ~0; D8 binding figures).
- **A1 (W=1024): f = 4/24 = 0.16666667 → predicted aggregate recall
  0.16666674.** Per-stratum predictions: strata {92, 152, 280, 536} = 1.0;
  the other 20 strata = 8.333333e-08.
- **A4 (W=512): f = 3/24 = 0.12500000 → predicted aggregate recall
  0.12500007.** Per-stratum: {92, 152, 280} = 1.0; other 21 = 8.333333e-08.
- A2/A3: NO law prediction (full-attention layers ⇒ no in-window bound);
  reported descriptively.
- Stratum membership at scoring: a scored retrieval belongs to the stratum
  its realized distance clusters at (generator clusters items at the stratum
  points with tolerance drift ±essay 2/noise 6/needle 12 — the realized
  support in the manifest).
- D4 exclusion rule (operator, pre-registered 2026-08-05): any
  (task, stratum) cell with REALIZED count < 100 is excluded from that
  task's evaluable-strata tally and flagged `instrument_caution: low_n`;
  if fewer than 20/24 evaluable strata remain for a task, that task's
  contribution is INSTRUMENT_SUSPECT, reported as such, never forced.

## Arms (final — D8 2026-08-06, no blanks)
| Arm | Definition | Role |
|---|---|---|
| A1 | declared **W=1024**, all 28 layers converted, n_full=0 | CERTIFICATION CELL (headline) |
| A2 | folklore 3:1 @ W=1024 (10 full layers: 0,3,…,27) | secondary-gate comparator |
| A3 | folklore 6:1 @ W=1024 (5 full layers: 0,6,12,18,24) | secondary-gate comparator |
| A4 | all 28 layers @ W=512, n_full=0 | CERTIFICATION CELL (co-registered) |
| A5 | random placement — **SKIPPED, STRUCTURALLY DEGENERATE** | seed registered, unused |

A1 is a DECLARED window: NO inversion is performed, target_recall is NOT
USED, `law_provision()` is not called (D8). Rejected alternatives, verbatim
from the binding record: W=512 makes A1 bit-identical to A4 (one arm, two
labels); W=2048 masks nothing at the frozen KILL seqlen 2048 (vacuous kill
gate) plus training-seqlen cost and 8–256-token decay half-lives risk the
in-window premise; telemetry inversion provisions on one distribution and
certifies on another (declined on merits — signature 4 NOT overridden).
W=1024 binds r_in ≥ 0.82. A5's skip fires the pre-registered D2 rule
(A1 n_full=0 ⇒ no non-trivial placement exists); its placement seed (2106)
is registered fresh and UNUSED, honoring signature 4.

## SECONDARY gate (arithmetic FROZEN PRE-DATA at L=8192/bf16, D8)
KV-state bytes: full-attention layer = L·2·8·128·2 B = 32.00 MiB;
windowed layer = W·2·8·128·2 B (W/1024 × 32 MiB).
- A1 = 112.00 MiB, A2 = 392.00, A3 = 252.00, A4 = 56.00, base = 896.00.
- A1 beats A2 on recall-per-byte iff obs(A2) < 0.5833333; beats A3 iff
  obs(A3) < 0.3750000 (same recall-per-byte break-evens; A1 recall
  conservative at its own predicted 0.16666674).
- Comparators = A2/A3 ONLY. A4 is reported, not gated.
- REGISTERED PRE-DATA (verbatim D8): A1 is arithmetically guaranteed to
  LOSE to A4 on recall-per-byte if both certify (f/W decreasing on this
  ladder) — instrument property, not law failure; stated now so it cannot
  be spun later.

## CONTROLS / KILL gates
- **KILL(i) random-placement comparator: NOT EVALUABLE** — the comparator
  does not exist (A5 skipped). Must NEVER be reported as satisfied/passed
  (D8 wording, verbatim).
- **KILL(ii) held-out LM loss: Δ ≤ 0.10 NATS vs unconverted base** (held-out
  FineWeb-Edu tail, seqlen 2048, measured post full registered budget;
  SENIOR-SIGNOFF signature 1 verbatim). Scope = certified arm **A1 only**;
  all other arms report descriptively (signature-1 scoping text, verbatim).
  ALSO report A1 LM loss at **seqlen 8192** (where windowing actually
  bites) — reporting only, non-gating (D8).
- **KILL(iii) G2-style reproduction gate**: before scoring any converted
  arm, battery on unconverted base == battery on no-op-initialized converted
  model, bit-identical logits (verify_noop_qwen3.py already PASS on real
  weights; rerun per-arm at score time).
- **KILL(iv) no efficacy stopping** — all arms run to the registered token
  budget.

## Certification-cell designation (D8, verbatim)
The certification verdict is adjudicated on **A1**; A4 is co-registered.
A4-pass/A1-fail (or reverse) = **PARTIAL CERTIFICATION**, both stated,
NEVER collapsed.

## What the pilot DOES and DOES NOT isolate (registered stated limitation,
verbatim D8)
- DOES: law placement vs folklore placement at matched W+budget (A1 vs
  A2/A3); law prediction vs observation at two independently trained
  windows (A1, A4).
- DOES NOT: law-chosen vs arbitrary W — no deployment distribution to
  invert against; any such claim here would be unfalsifiable decoration.
- Inversion moves to teardown narrative with telemetry, labelled
  NON-CERTIFIED. P3 follow-on named: draw certification strata FROM the
  deployment distribution so provisioning input == measurement distribution
  — the only falsifiable inversion design.

## Substrate & instrument
- Qwen3-0.6B-**Base**, pinned rev `da87bfb608c14b7cf20ba1ce41287e8de496c0cd`;
  28 layers, hidden 1024, 16Q/8KV heads (GQA groups=2), head_dim 128
  decoupled, QK-norm, RoPE theta 1e6, tied embeddings, vocab 151,936, bf16.
- Conversion module: `build/qwen3_windowed_decay_attention.py` (B1;
  B2 no-op bit-identical + liveness + window-mask PASS on real weights).
- Trainers: `build/attention_transfer.py` (stage 1, per-layer MSE vs frozen
  teacher, joint) + `build/lora_recovery.py` (stage 2, peft LoRA). D6
  checkpoint/resume round-trip exercised for BOTH trainers with real SIGKILL
  mid-run (S29, PASS).
- Certification battery: `data/sealed_battery_779038744/`, salt 779038744,
  8 tasks × 2400 items + 128 negatives, 24 strata {92,152,280,536,1048,
  1536,2024,2072,2472,2872,3272,3672,4072,4120,4502,4885,5268,5650,6032,
  6415,6798,7180,7562,7945}, guard bands at ALL SIX grid points {128,256,
  512,1024,2048,4096} (guard 16, edge-padded 24). S26/S27 verify PASS, 0
  failures; train-pool collision reject armed (D7). **D3 step 4 FIRES:
  both registered windows (1024, 512) are guard-banded grid points ⇒ the
  sealed battery is used AS-IS, no regeneration.** Battery sha256s recorded
  in campaign.json.
- Transfer corpus (D8 blocking step 1, executed): regenerated at
  **block=2048** (conversion_training_seqlen = 2048 REGISTERED — must exceed
  max W or the mask is inert). Same source slice, salts, and generation
  path as the block-1024 smoke corpus (bin bit-identical, sha verified);
  needle/kv pools re-rolled at block 2048 under the same salts. New
  sha256s recorded in campaign.json. B3/B4 smokes re-run at the new block:
  smoke_real_transfer.py PASS, smoke_lora_tiny.py PASS (result shas in
  campaign.json).

## Training recipe (identical across arms, both stages)
- Conversion token budget: **500M tokens per arm, TOTAL across
  attention-transfer + LoRA stages** (SENIOR-SIGNOFF signature 2 verbatim);
  stage split registered here, identical across all arms and both targets:
  **300M attention-transfer / 200M LoRA** (60/40, matching the S28 dry-run
  split used for the D5 end-to-end scoring proof).
- conversion_training_seqlen = 2048 (REGISTERED, D8).
- Corpus mix: FineWeb-Edu slice (re-tokenized Qwen3, block 2048) + needle
  0.10 + kv 0.10 (S05 data.py convention); LoRA rank/steps, optimizer, LR
  schedule per the D5-proven S28 configs (identical across arms).
- Seeds: Lab 2 21xx block — consumed through 2104. **A-arms training seed:
  2105** (one seed per arm, pilot; second seed only on PASS, mirroring
  p1d→p1e). A5 placement seed 2106 registered, UNUSED. Next free after
  this campaign: 2107.

## Sweep-cost accounting (D8 verbatim)
- Grid = SIX points {128,256,512,1024,2048,4096}; law path = 1× C_conv.
- Teardown MUST state both counterfactuals (signature 3 verbatim): full
  sweep = (|grid|−1) × C_conv = 5× C_conv, binary search = 2× C_conv —
  never headline only the full-sweep figure.
- Teardown must state: the pilot ran 4 conversions of which 3 are controls
  a practitioner would not pay (D8 verbatim).

## New required reporting (D8 verbatim — all three, non-gating)
1. Error decomposition r_in/r_out per cell (p1d's r_out ≈ 0.02 alone eats
   ~0.017 of the 0.03 budget — cancelling errors must be visible).
2. Per-stratum tally split in-window vs out-of-window.
3. Descriptive re-window ladder off the A1 checkpoint at
   W ∈ {128, 256, 512, 2048, 4096}, 2400 retrievals, non-gating, CAP $15 —
   skip if the quote exceeds.

## Residual risks (carried to teardown, D8 verbatim)
- A1 may LOSE the secondary gate if folklore arms' full-attention layers
  retain recall — real result, registered pre-data, must not be
  reinterpreted after.
- The pilot headline is narrower than charter: it certifies the ceiling AT
  A DECLARED W and placement-vs-folklore, NOT the law choosing W. Say so in
  the abstract.

## Pre-launch checklist (final state at seal)
- [x] B1 module + B2 no-op/liveness/mask on real weights (2026-08-04)
- [x] B3 attention-transfer trainer + CPU smoke PASS (S15)
- [x] B4 LoRA recovery + smoke PASS (S17)
- [x] B5 arm/placement configs + runner
- [x] E1 sealed battery 779038744, all-6-grid-point guard bands, verify PASS
- [x] E2 scorer; D5 converted+trained end-to-end scoring proof (S28, PASS)
- [x] D6 checkpoint/resume round-trip both trainers (S29, PASS)
- [x] D7 train-pool collision reject (S25)
- [x] D2/D3/D4 pre-registered (2026-08-04/05); D2 fires (A5 skipped)
- [x] O1 cloud orchestration adapted from p1e (create/bootstrap/collect-
      teardown; bootstrap asserts driver+headers)
- [x] D8 blocking step 1: corpus regenerated at block=2048 + B3/B4 re-smoke
      PASS + new sha256s (2026-08-06)
- [x] D8 blocking step 2: all knock-ons applied (this document; arm configs;
      placements.py; STATUS.md/DESIGN-NOTE.md syncs)
- [ ] D8 blocking step 3: ledger seal → quote-before-create → Qwen pilot
      launch (this tick, in order)

## Explicit non-actions at seal
- NO cloud instance created yet, NO spend. Quote-before-create records
  first; spend_check gate; evidence-gated collection before any DELETE.
- Llama-3.2-1B arm untouched (second by signed order, only if Qwen
  certification adjudicates; HF token needs a fresh live check first).
