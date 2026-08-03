# Released-Checkpoint Window Audit — checkpoint-audit-20260803-audit1

NON-CLAIM survey (no sealed gates). Instrument: p2c behavioural window/boundary probe
(value-anchored distances, strict digit-boundary scoring, matched-regime controls, BOS,
structural mask check via the installed transformers mask builders). Survey precision:
16 reps/stratum over 14 strata (vs 48/24 in p2c) — adequate for cliff/no-cliff verdicts,
not fine rate estimates. All runs fp16, eager attention, one V100 (sm_70, no bf16),
CUDA_VISIBLE_DEVICES=3. Filler corpus and probe design identical to p2c.

Strata (nominal boundary 4096, max context 8192):
64, 116, 209, 378, 684, 1238, 2238, 4048 | 4144, 4288 | 4480, 5584, 6688, 7792

| # | Model | Declared window (config) | Structural finding (mask builder) | Behavioural finding (strict recall) | Verdict |
|---|-------|--------------------------|-----------------------------------|-------------------------------------|---------|
| R1 | microsoft/Phi-3-mini-4k-instruct (prior row, p2c, 48 reps) | sliding_window=2047 | sliding mask: max attendable distance 2046 | 1.00 inside; collapses to 0.00–0.08 for every stratum past 2047; chance 0.000 | Hard cliff exactly at the declared window. Window is real and enforced. |
| R2 | mistralai/Mistral-7B-Instruct-v0.1 (prior row, p2c, 48 reps) | sliding_window=4096 | sliding mask: max attendable distance 4095 | 1.00 through 4048; 0.00–0.08 from 4144 out to 7792; chance 0.003 | Hard cliff exactly at the declared window. Window is real and enforced. |
| A1 | gemma-2-2b-it (via ungated mirror unsloth/gemma-2-2b-it; google/ repo gated, no HF token on host) | sliding_window=4096, HYBRID: layer_types = 13 sliding_attention + 13 full_attention | causal mask: full 4224 visible; sliding mask: 4096 window (applies only to the 13 sliding layers) | 1.00 at every stratum 64→6688, including the 4144/4288 boundary bracket; 0.50 at 7792 (real retrieval failures, generic continuations, not digit noise); chance 0.000 over 56 controls | NO cliff at 4096 — pre-registered p2a expectation CONFIRMED. Global layers carry retrieval past the window. Surprise: 50% degradation at d=7792, approaching the 8192 training context, i.e. the failure edge is the training context, not the window. |
| A2 | Qwen/Qwen2.5-7B-Instruct | sliding_window=131072 BUT use_sliding_window=false (max_window_layers=28, max_position_embeddings=32768) | PENDING — run in flight | PENDING — expectation (pre-registered): window disabled in config → flat recall through 8192, no cliff at 4096 | PENDING |
| A3 | mistralai/Mistral-7B-Instruct-v0.3 | sliding_window=null (config fetched pre-run; rope_theta=1e6, max_position_embeddings=32768) — v0.2's no-window choice KEPT | PENDING — run in flight | PENDING — expectation (pre-registered): no window declared → flat recall through 8192; contrast with v0.1's hard 4096 cliff (R2) | PENDING (config half of the question already answered: yes, they kept the no-window choice) |
| A4 | HuggingFaceTB/SmolLM2-1.7B (chosen over Phi-3-medium-4k: 14B fp16 ~28GB is borderline on one 32GB V100 and a ~28GB download; SmolLM2 gives a clean full-attention baseline row cheaply) | none (llama-style full attention) | causal mask only: full 4224 visible, no sliding builder applicable | 1.00 at 12/14 strata, 0.94 at d=209 and d=684 (isolated single-probe misses, not distance-correlated); 1.00 at all four boundary and all four far strata incl. 7792; chance 0.000 over 56 controls | NO cliff anywhere — expectation confirmed. Full-attention baseline behaves as declared. Note: unlike gemma-2 (A1), holds 16/16 at d=7792. |

## Notes

- Precision: at 16 reps, a stratum at true p=0.5 has 95% CI roughly ±0.24. Cliff/no-cliff
  contrasts here are 1.00-vs-0.0x and are unambiguous at this budget.
- Controls: matched-regime no-needle controls at every stratum, all four runs so far at
  0.000–0.003 strict chance — strict scoring is not creditable by accident.
- gemma-2 d=7792 failures are qualitatively distinct from windowed-model post-cliff
  failures: windowed models emit degenerate digit runs; gemma-2 emits fluent generic
  continuations ("a combination of letters", "a key to the future of"), consistent with
  attention dilution near the training-context edge rather than a mask cutoff.
- Runtimes (probe run only, excludes download): gemma-2-2b-it 187 s; SmolLM2-1.7B 257 s.
- Per-model raw results (all probes + control generations retained):
  audit_gemma2_2b_it.json, audit_smollm2_1_7b.json, audit_qwen2_5_7b_instruct.json (pending),
  audit_mistral_v03.json (pending) in ~/archlab2-runs/checkpoint-audit-20260803-audit1/.
- A2/A3 are executing via the detached chain ~/archlab-audit-sweep/chain_qwen_mistral.sh
  (log: ~/archlab-audit-sweep/chain.log; marker on success:
  ~/archlab2-runs/checkpoint-audit-20260803-audit1/.chain_done). Fill the PENDING cells
  from the two result jsons when the marker appears.
