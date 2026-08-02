# p2f — design note (suffix reserved, NOT launched as of 2026-08-02 ~05:00 UTC)

## Why this dir exists but has no campaign.json

p2e's decision.json (created 04:06:41Z) resolved to
`CONFOUND_ALERT_GENERALIZED`: Mistral-v0.2 (rope_theta 1e6, extended-context
training) ALSO fails GB_capability_control at the same far strata where
v0.1 declined — the far-field recall drop in p2d's arm4 is not a v0.1-
specific artifact. Per p2e/campaign.json's `interpretation_fixed_in_advance`,
this branch's pre-registered next step is explicit: *"Arms 1-3 remain
suspended pending a from-scratch-model diagnostic (p1d-style), notify Hani,
do not claim LAW_ARITHMETIC_TRANSFERS."* Not "another deployed-checkpoint
probe" — a genuinely from-scratch-trained model, so there is no RoPE-scaling
or emergent-capability confound left to argue about.

A prior invocation of this same tick (trigger: "p2e decision unhandled for
1401s", started 04:30Z, killed by the 1500s wrapper timeout ~04:55Z) got as
far as: verifying p2e's aggregation, writing p2e/.handled (04:35:05Z), then
claiming this suffix (`~/.archlab-suffix-claims/p2f`, 04:52:02Z) and staging
eval_salt.txt (3642722976) before running out of time. It did not reach
campaign.json. This tick (the direct continuation) chose NOT to complete a
rushed launch — see reasoning below — rather than blindly finishing the
in-progress claim.

## Why not launched this tick

A real "p1d-style" diagnostic needs an actual from-scratch TRAINED model,
not another frozen-checkpoint eval script edit (which is why p2b/c/d/e were
each tractable in a single ~20-30min tick: byte-identical harness copies,
only CLI args/salts changed). This is categorically different:

- The only existing from-scratch natural-text recall harness
  (`~/archlab-s05`, used by p1b/p1c/p1d) trains/evaluates at `block_size`
  1024–2048. The far-field decline under diagnosis lives at absolute
  distances 5547–7792 (p2e's stratification, inherited from p2d arm4) —
  4–8x beyond anything this harness has ever been run at.
- Scaling `block_size` that far is not a config-value change: S05-BUILD.md's
  own history (2026-07-30, item 6) shows `chunked_causal` OOM'd at the
  *current* 2048 scale and needed a multi-tick gradient-checkpointing
  rewrite, CPU-verified then GPU-scale-verified separately, before any real
  spend. The same discipline would need to repeat at ~4x the sequence
  length, with no guarantee the same fix's memory bound holds.
- The needle-probe battery (`probes_gen.py`) only has depth fractions
  0.1–0.9 of a 1024-token block; new depths reaching into the 5000–8000
  absolute-token range need a new frozen battery, a new sealed salt, and
  fresh verification (per this program's own repeated pattern of catching
  real scoring/indexing bugs on every new battery — S05-BUILD item 3's
  digit-marker bug, p2c's digit-boundary bug, p2e's G1 probe-sizing bug).
- Training to convergence at this new scale takes real wall-clock hours,
  not the ~1-2h eval-only runtimes of p2b–p2e.

Rushing this into the remaining budget of one headless tick carries the
same class of risk this program has repeatedly declined to take (see
OPERATOR.md's standing deferral of the "linear-time chunked StableGLA
kernel" rewrite for the identical reason: correctness-risk work needs
iteration room a single unsupervised tick doesn't have).

## Relevant evidence already in hand (not a substitute, but relevant)

p1d's own w1024 cell (`~/archlab2-runs/prv-lawtransfer-20260801-p1d/`,
a from-scratch stablegla model, seed 2100, effectively unwindowed at its
1024-token scale) shows recall ~1.0 with NO decline through its longest
tested distances (d=984, 1000; predicted_ceiling 1.0, all 32 strata inside
the window). That is *consistent with* "from-scratch models trained
end-to-end on the recall task don't show arm4's decay" — but it is not
scale-matched (1000 tokens vs 5500-7800) and the training regime differs
fundamentally from Mistral's general-purpose pretraining + zero-shot
in-context probe, so it cannot resolve CONFOUND_ALERT_GENERALIZED on its
own. Flagging it as context, not as a finished answer.

## Concrete next steps for whoever builds this (future tick or interactive session)

1. Extend `~/archlab-s05/models.py`/`data.py`/`probes_gen.py` to a much
   longer `block_size` (target: comfortably past 8192, so the diagnostic's
   distances are in-distribution, not extrapolated) — new corpus slice,
   new needle depths landing near 1000/2000/4000/5500/7000/7800 absolute
   tokens (mirroring p2d/p2e's exact stratification so results are directly
   comparable).
2. Re-run the GPU-scale memory/step-time verification
   (`bench_gpu_chunked.py`-style) BEFORE committing to a real training
   launch — do not assume the 2048-scale fix generalizes.
3. Train one no-window arm (transformer or stablegla, whichever is cheaper
   to converge) on the recall task at the new block_size to a real
   convergence checkpoint.
4. Probe recall vs. distance on the frozen checkpoint using the new needle
   battery; compare shape (sharp vs. gradual) against arm4/p2e's curves.
5. Pre-register gates before scoring, per this program's standard practice.

## Build progress

- 2026-08-02 ~06:00Z (operator tick): **Step 2 (GPU-scale memory/step-time
  verification at block_size=8192) DONE on hub GPU0** — `~/archlab-s05/
  bench_longctx.py`, results in `bench_longctx_result.json`. Findings:
  - stablegla @8192: FEASIBLE as-is — batch=2, peak 19.4GB, ~6.6s/step
    (chunked_causal + gradient checkpointing generalizes; the 2048-scale
    fix's memory bound holds at 4x).
  - transformer @8192 under bf16: OOM even at batch=1, INCLUDING in a clean
    process (not fragmentation). Root cause: V100 has no flash/mem-efficient
    SDP kernel for bf16, so F.scaled_dot_product_attention falls back to the
    math path and materializes the full (B,H,T,T) tensor (3GB alloc attempt).
  - Fix verified: forcing `SDPBackend.EFFICIENT_ATTENTION` + fp16 autocast
    makes transformer @8192 feasible — batch=2, peak 14.84GB, ~0.8s/step.
    Any p2f transformer arm on V100 must use fp16+efficient-attention (or run
    on cloud Ampere+ where bf16 flash kernels exist and this is moot).
  Step-times are V100-pessimistic (non-native bf16); L40S/A100 will be faster.
  Remaining steps: 1 (long-context corpus slice + needle battery at the
  p2d/p2e strata depths), 3 (train no-window arm to convergence), 4 (probe),
  5 (pre-register gates). Step 3's cheapest arm is now known: stablegla
  works unmodified; transformer needs the fp16/backend override.

- 2026-08-02 ~06:10Z (operator tick): **Step 1 prep (read-only, zero-risk) —
  computed and verified the exact target strata for the new needle battery.**
  Re-derived `strata_for(window=4096, max_context=8192)` from p2e/run_p2e.py's
  own function (byte-identical copy, executed locally, not modified): 24
  depths `[64, 101, 161, 255, 404, 641, 1016, 1611, 2553, 4048, 4144, 4425,
  4705, 4986, 5266, 5547, 5828, 6108, 6389, 6670, 6950, 7231, 7511, 7792]` —
  confirms max target depth is 7792, matching p2d arm4 / p2e's own
  stratification exactly (this is the set step 1's new needle generator must
  reproduce for direct comparability). Implication for block_size: 7792 +
  prefix_len(128) + needle/query tokens leaves only ~270 tokens of headroom
  inside a flat 8192 block — step 2's verified 8192 GPU envelope (stablegla
  19.4GB/batch=2 feasible) is right at this edge with no slack for the
  needle+question template. Recommend step 1 target a block_size with real
  margin (8448 or 8704) rather than exactly 8192, and re-run step 2's
  benchmark at that revised size before any real training launch.
  Deliberately did NOT touch `probes_gen.py`/`data.py` (the frozen,
  shared battery-generation code used by past sealed campaigns p1b/p1c/p1d) —
  writing the actual long-context needle generator is real step-1 work
  (new absolute-depth needle placement logic, new corpus slice, new salt,
  fresh verification against exactly this program's own history of
  battery-indexing bugs) and stays deferred to a dedicated build pass, same
  reasoning as the standing chunked-kernel-rewrite deferral. This tick's
  addition is pure computation + documentation, no code changed, no risk.

- 2026-08-02 ~06:20Z (operator tick): **Step 2 follow-up DONE — GPU envelope
  re-verified at the REVISED block_size 8704** (the prior note's own open
  item: "re-run step 2's benchmark at that revised size before any real
  training launch"). `~/archlab-s05/bench_longctx_8704.py` (monkeypatches
  bench_longctx.BLOCK=8704, leaves the original 8192 script untouched),
  results in `bench_longctx_result_8704.json`: stablegla @8704 FEASIBLE —
  batch=2, peak 20.55GB, ~7.3s/step on V100 (vs 19.4GB/~6.6s at 8192;
  scaling near-linear, ~11GB headroom left on a 32GB card). Step 3's
  cheapest arm (stablegla, unmodified) is therefore cleared for
  block_size=8704 with real margin past stratum depth 7792 + prefix +
  needle/query template. Transformer at 8704 not benchmarked (still needs
  the fp16/efficient-attention override per the 8192 finding; deferred with
  that arm choice). Step 2 now fully closed at both sizes.

## Status

Suffix `p2f` stays reserved (`~/.archlab-suffix-claims/p2f` lockfile) for
this build. No campaign.json, no launch, no cloud spend. Step 2 of 5 done
and closed at BOTH 8192 and the revised 8704 target. Step 1's target strata
confirmed/documented; the actual battery-generator code is still unwritten
(remaining substantive build work: steps 1, 3, 4, 5).
