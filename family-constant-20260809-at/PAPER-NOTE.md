# PAPER-NOTE — campaign at (family-constant-20260809-at)

Pre-written interpretation branches for every outcome, sealed with the
campaign BEFORE training (per FAMILY CONSTANT directive item 7). At verdict,
exactly one branch is copy-edited into the paper; the rest are deleted. No
gate amendment after data; no efficacy stopping.

## Framing (common to all branches)

Campaigns bb/bc established that windowed PLAIN softmax attention does not
saturate the recall ceiling `f + (1-f)·p_chance` that windowed decay
attention (StableGLA/GLA) saturates (aj/ak, p1d). Read one way that is a
limitation — the reach law is FAMILY_SPECIFIC. Campaign `at` tests the
stronger reframing: the law is GENERAL, with a per-architecture-family
effective-reach constant α where `W_eff = α·W`. Decay attention is the
α = 1 anchor (p1d Battery B, natural text: intact at d = W, chance at
d = W+1). Plain windowed attention is the α > 1 candidate (bb/bc: 24
in-window transitions, 0 ceiling confirmations, transitioned runs recalling
0.89–1.0 against geometric ceilings of 0.28/0.59/0.91 — plain attention
reaches past its window). The design is INVERTED (window W fixed, retrieval
distance d swept by the sealed eval) so reach is separated from the
optimization-difficulty confound that campaign `ar` introduced by varying W.
α is read only from transitioned runs (per-run in-window accuracy > 0.8),
never from non-transitioned runs — a family that does not transition yields
no α, not α = 0.

## Branch 1 — FAMILY_CONSTANT_CONFIRMED (G0+G1+G2 PASS)

The recall-reach law is a general provisioning law with a measurable
per-family constant. On the same synthetic instrument, windowed decay
attention reproduced its α = 1 anchor (collapse at the window edge,
d_collapse = W), while windowed plain softmax attention collapsed at
d_collapse ≈ [measured] = α·W with α ≈ [measured] ∈ [1.5, 3.0], cleanly
above the decay-attention anchor. The same window width therefore provisions
different effective reaches depending on the mixer family: a plain-attention
window of W reaches roughly α times as far as a decay-attention window of
W. The law is not decay-attention-specific; it is a general law with one
material constant per architecture family. [If G3 PASS: The plain-attention
α grew with depth (α_L4 ≤ α_L8 ≤ α_L12), the multi-layer-relay /
induction-head signature — consistent with the mechanism Zhixuan Lin
proposed for the base-configuration failure (too few layers to form
induction heads; transformer-circuits.pub, In-context Learning and
Induction Heads).] This converts the bb/bc limitation into a contribution.

## Branch 2 — ALPHA_NOT_STABLE

Plain windowed attention does not have a well-defined reach constant. Its
per-distance accuracy decayed gradually (no distance satisfied the clean
collapse definition), or the per-seed collapse distance scattered beyond
the resolution band — so α is not a stable, measurable property of the
plain-attention family even though it is for decay attention (α = 1 anchor
reproduced). The reach law's coverage term is then well-defined for the
decay family only, and the bb/bc ceiling overshoot reflects a gradual,
seed-variable falloff rather than a sharp extended reach. The law remains
FAMILY_SPECIFIC, now for a sharper reason: the constant itself is
family-dependent in EXISTENCE, not merely in value.

## Branch 3 — PLAIN_REACH_IS_WINDOW

Contrary to the bb/bc reading, windowed plain attention collapses at its
window edge (α_plain ≈ 1), same as decay attention. The bb/bc ceiling
overshoot was an optimization/aggregation artifact of the ceiling-law
framing, not genuine extended reach: when distance is swept directly at
fixed W, plain attention's reach is its window. The two families share
α = 1 on this instrument; the family distinction bb/bc suggested does not
survive the inverted, confound-free design.

## Branch 4 — UNDERPOWERED / INSTRUMENT_SUSPECT

[If G0 fails:] The unwindowed control did not solve the panel at this
budget (recall ≤ 0.8 in too many runs), so the instrument cannot read
reach for any family — no claim is made. [If a candidate arm stays <
min_transitions after escalation:] That arm did not transition even at the
escalated budget, so it yields no α (not α = 0); the campaign reports the
families that did transition and marks the rest underpowered.

## Depth-sweep note (any branch)

The depth sweep (L ∈ {4, 8, 12} on the plain arm) is a direct, pre-registered
test of the mechanism the Forgetting Transformer author volunteered by email
(2026-08-06): that the base-configuration failure came from too few layers to
learn key-shifting and form induction heads. If α_plain tracks depth, that is
evidence for the multi-layer-relay / induction-head account and the induction
-head literature is cited; if α_plain is flat in depth, α is a fixed property
of the attention block, not an emergent multi-layer circuit.
