# PAPER-NOTE — campaign bb (SWA-SATURATION)

Drafted at seal (2026-08-05), both branches written before any result is
seen, per SWA-SATURATION-DIRECTIVE.md's reporting requirement. At verdict,
whoever closes this campaign (any future session, or the operator itself)
deletes the branch(es) that did not occur and inserts the remaining
paragraph into the v0.6 preprint's limitation-5 discussion. This is
copy-editing at that point, not authorship.

Design recap: 4 window widths (10/14/20/28) on windowed PLAIN softmax
attention (no decay/gating/conv/output-norm — vanilla RoPE attention with a
sliding-window causal mask), easy48 panel, budget 3e16 (the only regime
plain attention is known to cross: ax, transformer 2/6 at this exact
budget/lr/panel). Predicted ceilings from the empirically-sampled
retrieval-distance distribution (0.150/0.282/0.590/0.912 for W=10/14/20/28).
Control: unwindowed plain attention at the same budget. Full gates in
`campaign.json`.

## Branch A — verdict SATURATES_GENERIC

> We further tested whether the recall-ceiling saturation law observed for
> windowed StableGLA (§4.X) also holds for windowed *plain* softmax
> attention — the vanilla transformer with a sliding-window causal mask and
> no decay, gating, or convolution. Using the one regime where unwindowed
> plain attention is known to cross the MQAR recall threshold at all
> (easy48, budget 3×10¹⁶), we trained windowed variants at four window
> widths chosen to span the predicted ceiling f+(1−f)·p_chance from near-
> chance to near-1.0. Among runs that acquired the retrieval circuit (read
> via in-window accuracy, since aggregate recall is itself capped by the
> window for narrow W), observed recall matched the geometry-derived
> ceiling within ±0.05 in [N/4] of 4 window arms (control confirmed at
> [X]/[N] transitions, recall ≥0.95). This closes limitation 5 generically:
> the ceiling law is a property of *windowing itself*, not of the decay-
> attention family — any architecture with a fixed causal window should be
> expected to saturate at the same geometry-derived ceiling once it has
> otherwise acquired the underlying capability.

## Branch B — verdict FAMILY_SPECIFIC

> We further tested whether the recall-ceiling saturation law observed for
> windowed StableGLA (§4.X) transfers to windowed *plain* softmax attention
> (vanilla transformer, sliding-window causal mask, no decay/gating/conv).
> Using the one regime where unwindowed plain attention is known to cross
> the MQAR recall threshold (easy48, budget 3×10¹⁶), we trained windowed
> variants at four window widths spanning the predicted ceiling from near-
> chance to near-1.0. [DESCRIBE OBSERVED DEVIATION: e.g. "runs that acquired
> the retrieval circuit (in-window accuracy > 0.8) nonetheless landed at
> aggregate recall of [Y], systematically [above/below] the geometry-
> predicted ceiling of [Z] for window W=[W]" — fill from decision.json's
> `arms` block for whichever arm(s) failed to confirm]. This indicates the
> ceiling law does not transfer unconditionally to plain attention — limitation
> 5 stands as a decay-attention-family-specific result, and the mechanism by
> which windowed StableGLA reaches its geometric ceiling (its per-step
> softplus-gated decay/read structure) is not merely a byproduct of the
> window mask but plays a load-bearing role.

## Branch C — verdict UNDERPOWERED

> [Not preprint-ready.] At budget 3×10¹⁶, [control and/or arm(s) W=...] did
> not reach the pre-registered minimum of 3 transitioned runs (fewer than
> ~2.7 expected per arm at ax's own 2/6 rate; escalated per campaign.json's
> pre-registered ladder to 6×10¹⁶ on 8 fresh seeds continuing this
> campaign's own seed block). Re-run this note once the escalation rung
> lands and a verdict of SATURATES_GENERIC or FAMILY_SPECIFIC is reached, or
> if escalation also underpowers, report the result as inconclusive at this
> compute scale rather than force a claim.

---
Verdict + fill-in happens when `decision.json` lands (`status: COMPLETE`).
See `campaign.json`'s `verdict_definitions` for the exact adjudication rule
applied by `monitor.py`.

## VERDICT RECORDED 2026-08-06 17:50Z (operator tick)

Sealed decision.json: verdict **CONTROL_ANOMALOUS_INCONCLUSIVE**
(completed 2026-08-06T17:42:27Z). Raw outcome: control (unwindowed plain
attention, 32 runs) 7/32 transitioned (recall>0.8), of which 6/7 at
recall≥0.95 and **seed 3041 at 0.6328** — a partial transition between
threshold and near-ceiling, which bb's pre-registered definitions flag as
anomalous given ax's control behavior at this exact budget/panel. Window
arms @3e16: win10 0/8 and win14 2/8 in-window transitions
(UNDERPOWERED_ESCALATE_6E16 per the sealed ladder); win20 6/8 and win28 5/8
in-window transitioned with **0 ceiling-confirmed** in both
(SATURATION_NOT_CONFIRMED — transitioned runs landed at recall ~0.97-1.0,
far above the W-capped geometric ceilings 0.590/0.912, because their
out-of-window accuracy also rose to ~0.97-1.0; i.e. at 3e16 a transitioned
plain-attention run at W≥20 recalls BEYOND its window, so the window does
not cap aggregate recall the way it caps windowed StableGLA).

Actions taken per the sealed ladder + directive: bb `.handled` created;
escalation rung **swa-saturation-esc-20260806-bc** designed, sealed
(pre-registered, fresh salt, fresh seeds 3042-3073 continuing bb's block,
sha-verified byte-identical harness) and LAUNCHED on all 4 GPUs at
~17:50Z (win10/win14 escalated to 6e16 with 8 fresh seeds each; 16 fresh
control runs at 6e16 across 2 dedicated shards to re-test the anomaly at
2x budget; win28 re-run at 6e16 for a second independent read of the
highest-ceiling arm; win20 not re-run — bb resolved its power). ETA
~26-28h. Branch selection for the v0.6 insert is DEFERRED to bc's verdict:
the transition-count evidence so far leans FAMILY_SPECIFIC-adjacent
(win20/win28 transitioned runs ignore their windows' geometric cap), but
bb's own gates require a confirmed control before adjudicating any window
arm, and the control was anomalous. No branch above is deleted yet; the
final paragraph is written when bc's decision.json lands, per the
directive's "no future session needed" protocol.
