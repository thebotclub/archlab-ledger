# p2a — CORRECTION, 2026-08-01

An independent adversarial review found faults in p2a's harness and in its
decision record. I verified each claim below directly before accepting it. Three
of p2a's conclusions are withdrawn. The campaign's central dissociation survives.

`decision.json` is NOT rewritten — it stands as issued, and this document
supersedes the parts named here. That is this programme's convention and it
exists so that what was claimed, and when, stays legible.

---

## C1. G1 was never executed. My explanation of its failure was wrong.

`decision.json` says the structural mask check was *"unavailable in this
transformers version"*. That is false. `create_causal_mask` imports fine in
transformers 5.14.1. The harness called it with `input_embeds=` when the
parameter is `inputs_embeds`, and additionally passed a `cache_position` kwarg
that does not exist in the signature. Both raise `TypeError`, which
`except Exception` swallowed — and the fallback then **overwrote the exception
detail**, destroying the evidence before it reached disk.

So I diagnosed an environment fault from evidence my own harness had erased.

There was a second, independent defect that would have produced a false negative
even with the kwargs fixed: windowed models do not use `create_causal_mask` at
all. `MistralModel.forward` and `Phi3Model.forward` dispatch on
`self.config.sliding_window is None` and use **`create_sliding_window_causal_mask`**
when a window is set. G1 was reading the full-causal mask.

**Verified myself, 2026-08-01**, by inspecting `inspect.signature` and running the
correct builder with `_attn_implementation="eager"`.

## C2. The window is EXCLUSIVE (d ≤ W−1). G4 is withdrawn.

Run correctly, the mask says:

| model | config sliding_window | tokens visible | max attendable distance |
|---|---|---|---|
| Phi-3-mini-4k | 2047 | 2047 | **2046 = W−1** |
| Mistral-v0.1 | 4096 | 4096 | **4095 = W−1** |
| Mistral-v0.2 | None | full | no window |
| gemma-2-2b-it | 4096 (local layers) | 4096 | **4095 = W−1** |

`decision.json` G4 states retrieval is *"intact AT the declared window and a few
tokens beyond it"* and *"consistent with p1d's inclusive-mask finding (d ≤ W)"*.
**Both halves are withdrawn.** The mask is exclusive, and p2a did not replicate
p1d — see C3 for why it looked as though it had.

## C3. Distance was anchored to the needle START, not the VALUE token.

`build_prompt` computed `distance = query_position − needle_start`. The
retrievable token is the value, which sits 8–10 tokens further in:

| model | needle length | first value-token index |
|---|---|---|
| Phi-3 | 13 | 9 |
| Mistral | 12 | 8 |

Every p2a distance is therefore **inflated by 8–10 tokens**. Correcting it,
phi3's "perfect at d=2051" is really ~2041 — comfortably inside the 2046 limit —
and its "collapse by d=2063" is really ~2053, outside it. Mistral's "perfect at
d=4100" is really ~4092, inside 4095.

**Every number is consistent with a hard boundary at exactly W−1.** The
"inclusive mask plus a few tokens of soft margin" was an off-by-N in my own
measurement, and the follow-up campaign `decision.json` chartered to explain it
would have been investigating a bug.

The offset is also probe-dependent (`hexagon` is two tokens in Mistral, one in
gemma), so probes at the same nominal distance sat at slightly different true
distances — while the boundary grid was spaced at W±1 and W±4, i.e. **finer than
the instrument's own precision**.

## C4. p1d is NOT affected. I checked.

`gen_p1d_battery.py:83` — *"Place a needle so its VALUE token sits exactly
`distance` before ans_pos"* — and line 124 computes `before_n = ans_pos −
distance − v_idx`, subtracting the value-token index explicitly, with an
assertion on line 145. p1d anchored correctly.

So p1d's inclusive-boundary result stands on its own instrument, and the preprint
(§4.7a, v0.4.3) is unaffected. p2a had not been folded into the paper yet.

That leaves a real and interesting difference rather than a contradiction:
**p1d's own windowed implementation is inclusive; HuggingFace's is exclusive.**
Commercially that is the more useful finding — the convention is
implementation-specific and must be read off the mask, not assumed.

## C5. The within-family control moves more than the window.

`decision.json` claims *"tokenizer, data, scale, depth and recipe are held fixed;
the window is the only thing that moves."* The on-disk configs disagree:
v0.1 has `rope_theta = 10000.0`, v0.2 has `rope_theta = 1000000.0`, and Mistral's
own model card lists a 32k context (vs 8k), the new rope base, and the removal of
sliding-window attention as three separate changes.

This bites mechanically: v0.1 was trained behind a 4096 window on 8k sequences,
so relative offsets beyond 4095 were never seen in training. Removing the mask at
inference exposes untrained RoPE positions. "v0.1 fails past 4096, v0.2 does not"
is therefore **jointly explained** by the mask and by rope/long-context training,
and both predict the same sharp step at 4096.

The claim that the cliff is *caused by the window* is consequently
**descriptively supported but causally unestablished**. The counterfactual that
would settle it — widen v0.1's own window and see whether recall returns — was
never run, and it is exactly the operation "provisioning" means.

## C6. G2's failure is weaker than reported, and scoring-rule dependent.

Pooled beyond W+16 against the measured chance of 0/96:

| arm | residual | Fisher p |
|---|---|---|
| phi3 | 6/96 = 0.0625 | 0.029 |
| mistral_v01 | 2/96 = 0.021 | **0.497 — not significant** |

One of Mistral's two hits is `value=13, generation='13131'` at d=4352, in a
stratum full of degenerate digit runs (`'10000'` ×7, `'12345'`, `'77777'`).
`value in gen[:12]` scores that correct. Under strict scoring Mistral's residual
falls to 1/96 and **Mistral v0.1 would have PASSED G2.**

The headline `GATE_NOT_MET` is therefore scoring-rule dependent for one of the
two positive arms, and the residual I chartered a campaign to explain is, for
Mistral, one or two probes consistent with chance.

## C7. Chance was measured in the wrong regime and its evidence discarded.

All 96 control probes ran at distance 512 (~641-token prompts) and were then
applied to 4000–6300 token prompts, where these models behave completely
differently. `score_probe` also discarded the control generations, so
`p_chance = 0.0000` is **unauditable from the artifacts**. 0/96 has a Wilson upper
bound of 0.038, so "chance is zero" is really "chance ≤ 3.8%".

## C8. Arm 4's negative result has a hole exactly where it matters.

gemma-2 drops **0.917 at d=4352 → 0.250 at d=6144**, and there are no strata
between. G5 required a drop *"within a 64-token span"*, and above 4352 no two
strata are within 1792 tokens — so **G5 was unfalsifiable in the region where the
collapse happens.** `decision.json` says *"0.250 only at d=6144"*; "only" is
unearned. The defensible statement is that gemma-2 has no cliff at its
*declared* window but has an unlocated collapse in (4352, 6144].

---

## What survives

The core dissociation is not a statistical artifact and I could not break it.
v0.1, v0.2 and gemma-2 were run on **probe-for-probe identical** key/value/
distance sequences. At d=4112 the same 24 prompts gave v0.1 **0/24** and v0.2
**24/24**, Fisher p = 6.2×10⁻¹⁴. Distance arithmetic in token-id space is exact
for all 1872 probes (the anchor is wrong; the arithmetic is not), no probe was
truncated or silently dropped, and strict re-scoring leaves in-window recall
untouched.

**A recall cliff appears in pure sliding-window models and not in the controls.**
Its location is W−1, not W. Its cause is not yet established. Its far-field
residual is, for Mistral, indistinguishable from chance.

## What happens now

Campaign **p2c** carries the corrected instrument: distance anchored to the value
token, strict scoring recorded alongside loose, chance measured in the matched
regime with generations retained, BOS prepended, probe overlap reduced, and a
fifth arm that reloads Mistral-v0.1 with `sliding_window=None` — the
counterfactual C5 says the provisioning claim actually depends on.

Campaign p2b was pre-registered and launched before this review landed. It
inherited every one of these faults. It was **halted eight minutes in and no p2b
data was analysed**; it is recorded VOID.
