# P0-PREREG — dose-onset-20260803-d1 (Lab 3 kill test)

Sealed at launch, before the first training run of this campaign starts.
This text is FINAL: it is not edited after launch, whatever the data does.
Operator: Lab 3 build agent (interactive-session dispatched) 2026-08-03.
Charter: ~/archlab3/LAB3-CHARTER.md (P0 section). Fresh 4-byte eval salt in
eval_salt.txt (sha256 in campaign.json); batteries are hidden salted evals
built from val.bin, which the training stream never touches.

## Question

Is capability onset BIMODAL in training-mix dose? Per-seed final performance
on the salted eval must land near the analytic ceiling or near chance —
sustained graded intermediates mean the dosing law has no phase boundary to
map, and Lab 3 dies here.

## Instrument

- One boring fixed architecture for ALL arms (charter bans architecture
  comparison): 6-layer softmax transformer (AAAAAA), d=384, heads=6,
  hidden=1024, RoPE, SwiGLU, tied embeddings, vocab 32000 → 22,909,824
  params. Sliding attention window W=256 (import-time D1_WINDOW, asserted in
  every process — p1d lesson).
- Base stream: FineWeb-Edu sample-10BT, Llama-2 tokenized (Lab 2's corpus,
  read-only; train.bin sha 52ac343a05163caa8f139584a2b37e9cbca91bff41d0daa02aba56ad9f1cafa7).
- Injection: full-row task-format examples at exact fraction d of training
  rows (= fraction of tokens; Bresenham accounting, achieved fraction
  recorded per run). Formats: p1c/p1d needle-retrieval; mod-5 state trace.
- Budget per run: 5200 steps x batch 32 x block 1024 = 170,393,600 tokens
  (~= 1.7e16 FLOPs by the 6N + 12*L*T*d convention). Sized from measured
  0.66 s/step on the V100 so ~20 runs finish inside ~20 h on GPU 3, while
  keeping >~2x margin over the only onset datum available (p1c: needle/kv
  onset between 58M and 124M tokens at 10% dose, 110M params).
- Precision: fp32 master weights, fp16 autocast + GradScaler (V100 fast
  path); run aborts if >200 scaler-skipped steps.
- Seeds (Lab 3 range 3000-3999): init_seed = data_seed ∈ {3000, 3001},
  paired across every arm. Pool salts 3100 (needle), 3101 (state).
  Smoke-test-only seed 3999 (never used in campaign runs).

## Capabilities and analytic bands (declared BEFORE launch)

recall (windowed needle retrieval), scored on the 1024-probe stratified
battery (32 distance strata from p1d, 32/stratum):
- f(W=256) = 15/32 = 0.46875 by construction; p_chance = 1/65 = 0.015385.
- ceiling = f + (1-f)*p_chance = 0.476923 (the proven plateau law; its
  validity at W for trained multi-layer models is p1d's sealed G3/G5 result,
  re-validated here by the 8% known-positive landing in the HIGH band).
- HIGH band:  recall_acc >= ceiling - 0.10 = 0.376923
- LOW band:   recall_acc <= p_chance + 0.05 = 0.065385
- DEAD ZONE:  (0.065385, 0.376923) exclusive.

state (mod-5 running-state trace), scored over all 40 supervised state
positions x 512 rows:
- ceiling = 1.0, chance = 0.2.
- HIGH band:  state_acc >= 0.90
- LOW band:   state_acc <= 0.30
- DEAD ZONE:  (0.30, 0.90) exclusive.

"Sustained" in the dead zone = the run's salted-eval reading for its trained
capability is in the dead zone BOTH at the probe nearest 80% of budget
(step 4160) AND at the final read. (A final-only dead-zone value could be a
transition caught mid-flight; a sustained one cannot.)

## Arms (20 runs, all on GPU 3, CUDA_VISIBLE_DEVICES=3, sequential)

Dose grid (uniform schedule, LR 1e-3): d ∈ {0%, 0.5%, 2%, 8%} x seeds
{3000, 3001} x capabilities {recall, state}. The two 0% runs are shared
between capabilities (no injection → one training run scored on both
batteries): 14 runs.
Timing arm (recall, d=2%, LR 1e-3): schedules {front-loaded-20%,
late-20%} x 2 seeds = 4 runs; the uniform cells are shared with the dose
grid (dedupe, per charter).
LR mini-sweep (recall, d=2%, uniform): LR 3e-3 x 2 seeds = 2 runs; the
1e-3 member of the sweep is the dose-grid cell itself. (Charter allows 2-4;
2 chosen because the grid must fit one shared V100 — see Deviations.)

## Controls — evaluated FIRST, before any grid run starts

Queue order enforces: the six control runs (0% x2 seeds; recall-8% x2;
state-8% x2) complete and are gated by monitor.py before any other run may
begin.
- Known-negative: BOTH 0% runs must be in the LOW band on BOTH capabilities.
- Known-positive: for EACH capability, at least one 8% seed must reach the
  HIGH band (8% is 4x the private-anomaly dose that switched recall on; if
  neither seed transitions, the instrument/budget cannot see onset at all).
If either control fails: monitor writes INSTRUMENT-BROKEN.md + STOP,
decision.json status INSTRUMENT_BROKEN, the grid does not run, and NOTHING
in this campaign is interpreted as evidence about the dosing law.

## Pre-registered P0 gate (the kill rule)

Evaluated over the uniform-schedule dose-grid runs of each capability
(d ∈ {0.5%, 2%, 8%} x 2 seeds = 6 runs per capability; the LR-3e-3 and
timing runs are excluded from the kill gate).

- P0 KILL (Lab 3 dies): for EITHER capability, >= 2 of its 6 grid runs are
  SUSTAINED in the dead zone. Write the null, stop the program.
- AMBIGUOUS: exactly 1 of 6 sustained-dead for a capability → not a kill;
  P0 must be extended with 2 more seeds at that dose before any P1 work.
- P0 PASS (bimodality survives): 0 of 6 sustained-dead per capability, and
  every HIGH-band run sits within 0.10 of its analytic ceiling — the
  distance-to-ceiling instrument works and P1 (boundary map) may be charted.
Runs that fail to complete are reported and excluded, but a capability needs
>= 5 completed grid runs for its gate to be evaluable; otherwise P0 is
INCOMPLETE, not passed.

## Pre-registered timing-arm question (descriptive, never gates P0)

At fixed 2% dose on recall, compare {front, uniform, late} x 2 seeds:
- Transition indicator: final recall_acc in HIGH band.
- Onset cost: cumulative injected rows at the first probe step whose
  recall_acc >= 0.376923 (linear interpolation not attempted; probe grid is
  the resolution).
Outcomes and their pre-declared meanings:
- Schedule-invariant (same transition pattern across schedules per seed):
  dose collapses toward a scalar total → simplifies P1 design.
- Late-20% transitions where uniform/front do not, or at fewer cumulative
  injected rows: late injection is cheaper → prioritise the
  capability-injection-into-checkpoints spin-off in the P1 brief.
- Front-loaded cheaper: curriculum-order effect → P1 must control schedule
  as a nuisance variable.
Two seeds cannot certify any of these; the timing arm OUTPUTS A HYPOTHESIS
for P1, never a claim.

## LR mini-sweep interpretation (pre-registered)

If the 2%-dose outcome differs between LR 1e-3 and 3e-3 (transition vs
sustained-dead or vs LOW), then dose-onset is LR-confounded at this scale
and NO single-LR reading of the dose grid may be promoted to P1 without an
LR-crossed design (the w/x/as/au lesson). If both LRs agree, LR 1e-3
readings stand.

## What is NOT claimed

No claim about H1 vs H2 (that is P1). No architecture claim. No claim from
the timing arm beyond hypothesis generation. Single scale (23M), single
window (W=256), needle content words shared between train pool and battery
(held out in filler/placement/combination, not vocabulary — p1d's stated
limitation, inherited).
