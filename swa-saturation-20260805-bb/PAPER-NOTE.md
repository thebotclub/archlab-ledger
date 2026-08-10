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

---
## FINAL VERDICT RECORDED 2026-08-09 03:45Z (operator tick) — pooled bb+bc

bc's decision.json landed 2026-08-09T03:29:41Z (verdict
ESCALATION_UNDERPOWERED, control confirmed at 6e16, win10 still
underpowered, win14 10/16 + win28 3/8 transitioned with 0 ceiling-confirmed).
The pooled bb+bc adjudication per this campaign's pre-registered
verdict_definitions and the SWA-SATURATION-DIRECTIVE pooling rule
(win10/win14 from bc@6e16, win20 from bb@3e16, win28 pooled, control pooled
48 runs) is recorded in full in bc's decision.json `pooled_verdict` block.

**VERDICT: FAMILY_SPECIFIC (Branch B).** Control confirmed (21/48
transitions; all transitioned runs recall >= 0.9258, 19/21 >= 0.95; the
3e16 marginals 3017/3021 did not reproduce at 6e16; flagged seed 3041
(0.6328) never crossed the 0.8 transition threshold — retained for manual
review only). Every powered window arm failed ceiling confirmation with
transitions to spare: win14 10 transitioned / 0 confirmed (all >= 0.8932 vs
ceiling 0.282), win20 6/0 (all >= 0.973 vs 0.590), win28 8/0 (all >= 0.9626
vs 0.912). win10 stayed underpowered at both budgets (reported inconclusive
at this compute scale per Branch C's own guidance; it cannot change the
verdict).

The Branch A and Branch C drafts above are now MOOT (kept for the audit
trail — the sealed record must show both branches were written before any
result was seen). The paragraph to insert into the v0.6 preprint's
limitation-5 discussion is Branch B, filled in as follows:

> We further tested whether the recall-ceiling saturation law observed for
> windowed StableGLA (§4.X) transfers to windowed *plain* softmax attention
> (vanilla transformer, sliding-window causal mask, no decay/gating/conv).
> Using the one regime where unwindowed plain attention is known to cross
> the MQAR recall threshold (easy48, budget 3×10¹⁶, escalated to 6×10¹⁶ per
> a pre-registered ladder), we trained windowed variants at four window
> widths spanning the predicted ceiling from near-chance to near-1.0
> (0.150/0.282/0.590/0.912 for W = 10/14/20/28). The unwindowed control
> confirmed (21/48 pooled transitions, every transitioned run at recall ≥
> 0.9258). Runs that acquired the retrieval circuit (in-window accuracy >
> 0.8) nonetheless landed at aggregate recall far ABOVE the geometry-
> predicted ceiling at every powered width: minimum observed 0.973 vs
> ceiling 0.590 at W=20, 0.893 vs 0.282 at W=14, and 0.963 vs 0.912 at
> W=28 (0/24 transitioned runs within ±0.05 of their ceilings across the
> three powered arms; W=10 never acquired the circuit even at 6×10¹⁶ and
> is reported as inconclusive at this compute scale). Mechanistically,
> transitioned plain-attention runs also recalled *out-of-window* queries
> at ~0.97–1.0, so the sliding-window mask does not cap aggregate recall
> the way it caps windowed StableGLA. This indicates the ceiling law does
> not transfer unconditionally to plain attention — limitation 5 stands as
> a decay-attention-family-specific result, and the mechanism by which
> windowed StableGLA reaches its geometric ceiling (its per-step
> softplus-gated decay/read structure) is not merely a byproduct of the
> window mask but plays a load-bearing role.

bb `.handled` (2026-08-06) and bc `.handled` (2026-08-07, arm-reassignment
marker) both predate this verdict; the pooled verdict is the terminal
action of the SWA-SATURATION directive. No successor campaign is implied:
both outcome branches were pre-registered as terminal (publishable either
way), the escalation ladder is exhausted (6e16 rung done), and no further
rung was pre-registered. Ledger sync + Telegram milestone fired this tick.

---

## v0.6 PRECISION NOTE — limitation 5 parenthetical is now STALE (added 2026-08-09, Hani session)

When inserting the Branch B (FAMILY_SPECIFIC) paragraph above, limitation 5 must ALSO
be corrected. Its current text reads:

> All windowed arms in this programme carry the full decay-attention component set;
> windowed vanilla softmax attention is untested here — **at these budgets it does not
> transition at all (§4.10)** — and the only plain sliding-window evidence is the
> deployed-checkpoint series, which certifies the cliff but not saturation.

Two clauses are superseded by bb+bc:

1. "windowed vanilla softmax attention is untested here" — it is now tested. bb (3e16)
   and bc (6e16) are the test, pooled verdict FAMILY_SPECIFIC.
2. "at these budgets it does not transition at all" — FALSE as written on the easy48
   panel. bb/bc observed 24 in-window transitions across the powered window arms
   (win14 10/16, win20 6/8, win28 8/16) at 3e16 and 6e16. The original clause is only
   true of the HARD panels (the §4.10 context); read literally and unqualified it is now
   contradicted by our own data. It must be scoped explicitly to the hard panels, or
   dropped in favour of the bb/bc result.

Replacement should state the positive finding rather than the absence: windowed plain
softmax attention transitions readily on easy48 at these budgets, and when it does it
recalls FAR ABOVE the geometry-predicted ceiling (win14 >=0.8932 vs 0.282344;
win20 >=0.973 vs 0.59023; win28 >=0.9626 vs 0.911559 — 0/24 ceiling confirmations),
i.e. it reaches past its own window where the decay-attention family does not. That is
what makes limitation 5 family-specific rather than a general property of windowing.

Note the interaction with the (5, updated) addendum, which says "the depth-relay reading
is refuted, not confirmed" on the basis of p1d Battery B (recall stops dead one token
past W in every cell). That refutation is about the DECAY-ATTENTION family on natural
text and remains correct as stated — but v0.6 should say so explicitly, because bb/bc
now show plain attention apparently DOES reach past its window. Left unqualified, the
two statements will read as contradictory to a referee. They are not: they are different
architecture families, which is the whole point of the FAMILY_SPECIFIC verdict.

Caveat to carry: win10 stayed underpowered at both budgets (0/8 transitions at 6e16),
so the verdict rests on three window widths, not four. Disclose it.

Nothing in the v0.5.9 preprint sent to La Trobe on 2026-08-05 is CONTRADICTED by bb/bc.
Limitation 5 disclosed plain windowed attention as untested; it is now tested, and the
answer is the one favourable to the paper's scoping. This is a precision upgrade, not
an erratum. No correction to the sent version is required.


---

## v0.6 MOTIVATION PARAGRAPH — ADD AT DRAFTING (added 2026-08-10, Hani session)

See ~/archlab-operator/ARCH-LANDSCAPE-20260810.md section 4A for the full brief. Summary:
the paper is weakest on "why does this matter at scale?". Four 2025-26 frontier designs each
hand-tune an allocation constant this law would compute: Kimi Linear 3:1 KDA/full-attention
(arXiv:2510.26692); NSA compressed/selected/sliding branch budgets + top-n (arXiv:2502.11089,
ACL 2025 best paper); Engram compute-vs-static-memory split (arXiv:2601.07372); Titans/HOPE
window-vs-long-term-memory split. CITE ESPECIALLY Engram own abstract: "by delegating local
dependencies to lookups, it frees up attention capacity for global context, substantially
boosting long-context retrieval" — a frontier lab independently confirming that what attention
must cover is a budget and that shifting the retrieval-distance distribution changes recall.
DO NOT claim Engram shipped in DeepSeek V4 — VERIFIED FALSE (V4 shipped mHC + sparse attention
only, 2026-04-24). NSA sliding-window branch is plain windowed softmax attention, i.e. exactly
what bb/bc measured — connect limitation 5 to it.
