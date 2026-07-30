# ar AUDIT — this campaign cannot support a conclusion about reach

Written 2026-07-30 by the interactive session. Revised 12:20 UTC against the
COMPLETE 6/6-cell results (`decision.json`, BOUNDARY_COMPLETE 12:14:03Z),
superseding the 4-cell version of this note. Cell results are untouched.

## The completed data

Panel: every retrieval distance is exactly 160 (verified empirically below, not
read from the source comment). Predicate `0 <= i-j < W`, so direct reach = W-1.

| cell | W | direct reach | transitions | max recall |
|---|---|---|---|---|
| w156 | 156 | 155 | 1/6 | 1.000 |
| w158 | 158 | 157 | **6/6** | 1.000 |
| w160 | 160 | 159 | 5/6 | 1.000 |
| w161 | 161 | 160 | 2/6 | 1.000 |
| w162 | 162 | 161 | 3/6 | 1.000 |
| w164 | 164 | 163 | **0/6** | 0.126 |

## Why no reach-based account survives this

**W=164 has direct reach 163. It covers the distance-160 target outright, with
three tokens to spare, and it failed 6 seeds out of 6** — max recall 0.126, no
seed even partially acquiring the task. These runs are not broken: identical
token count (30,924,800), the state-tracking task solved at 1.0 in every seed,
and final losses on the same ~0.90–0.99 plateau that marks "learned STATE, never
learned MQAR". They trained correctly and simply never acquired recall.

Meanwhile W=158, with reach 157 — three tokens *short* of the target — solved it
6/6 at loss ~0.0000.

More information available produced total failure; less information available
produced perfect success. **Reach is not the variable governing these outcomes.**
That rules out the pre-registered strict and inclusive conventions, the
depth-relay hypothesis recorded in `INTERIM.md`, and the convolution hypothesis
proposed in the 4-cell version of this note. None of them predict w164.

`INTERIM.md`'s conclusion — "the depth-relay hypothesis is supported" — does not
follow from the completed data and should not be carried into the paper or the
specification.

## What is probably going on: width changes difficulty, not just reach

The program's own central finding is that acquisition is a compute-gated phase
transition whose *probability* depends on task difficulty at fixed budget. A
wider window admits more candidate source positions that the model must learn to
suppress. Transition counts fall roughly as W grows —
158:6/6, 160:5/6, 162:3/6, 161:2/6, 164:0/6 — which is what a difficulty effect
looks like, with n=6 noise on the ordering.

So this design conflates two different quantities:

1. whether the target is *reachable* through the window, and
2. how hard the optimization is at that window width, at a fixed budget.

Transition count answers (1) only if (2) is held constant. It is not.

The 158 onset still has a clean candidate explanation — the candidate's causal
depthwise conv has kernel 4, supplying exactly `k-1 = 3` tokens of pre-attention
reach, so the target first becomes reachable at `W >= 158`, precisely where the
jump occurs (156:1/6 -> 158:6/6). That remains the most parsimonious account of
the *onset*. It explains nothing about the decline, and the decline is what
makes the campaign uninterpretable as a reach test.

Note also the single 1.000 seed at W=156 (reach 155, five tokens short, beyond
even the conv's allowance). One seed in six finding a route that the other five
did not is the signature of a rare mechanism — possibly genuine depth relay —
but n=6 cannot establish it.

## A second, independent design problem

Because *every* distance is identical, a model can satisfy this panel by copying
from a constant offset, without ever matching query content against a stored key.
At W=158 the value is reachable (via convolved position `v+3 = q-157`) but the
**key is not** — the key at `q-161` appears only in convolved positions
`[q-161, q-158]`, all outside a reach of `q-157`. A model transitioning at W=158
therefore cannot be doing content-based retrieval. The panel measures
reachability of a fixed-offset copy, not associative retrieval, which is the
quantity the provisioning law is about.

## Consequences

1. **The provisioning rule is unaffected and stays as recorded**: size W by the
   strict convention and treat any extra reach as margin. That is conservative
   under every hypothesis on the table, including "we don't know".
2. **specification-v3.2's "effective retrieval reach" paragraph** recites the
   relay mechanism. The claims are safe — they instruct conservative sizing — but
   the mechanism sentence is not supported by this campaign and should be
   softened to an observation that effective reach may exceed the nominal window
   for reasons not yet established, rather than attributing it to block relay.
3. **The paper must not cite ar as evidence of excess reach.** preprint §6(5) is
   written to report the boundary failure and decline attribution; it should now
   also decline the *existence* claim on this campaign's evidence.

## The campaign that would settle it (`at`)

Reach and difficulty must be separated:

- **Hold width constant, vary distance.** Fix W and sweep the retrieval distance
  across the boundary (W-4 … W+4). Difficulty is then constant and reach is the
  only variable. This is the correct inversion of ar's design and should have
  been the primary arm.
- **Vary conv kernel** k in {1,2,4,8} at fixed W and distance. Conv hypothesis:
  the onset shifts by exactly `k-1`. Relay hypothesis: no dependence on k.
- **Vary depth** (4/8/12 blocks) at fixed W, k, distance. Relay hypothesis: reach
  grows with depth. Otherwise flat.
- **Jittered-distance control panel** to remove the constant-offset shortcut.
- **n >= 16 per cell**, and report a graded recall statistic alongside transition
  counts — at n=6 a 6/6 vs 2/6 difference is Fisher p~0.06 and carries no
  ordering information.

## Reproduce

```bash
cd ~/archlab-runs/stablegla-boundary-20260730-ar/w158
~/archlab/.venv/bin/python - <<'EOF'
import json, numpy as np, data as D
m=json.load(open('manifest.json')); p=m['panel']
D.configure(**{k:v for k,v in p.items() if k not in ('id','gpu')})
toks,mask=D.gen_mqar(D._rng(1,1),2,D.MQAR_PAIRS,D.MQAR_QUERIES,D.SEQ_LEN)
ans=np.where(mask[0])[0]
print(sorted({(a-1)-(2*j+1) for j,a in enumerate(ans)}))   # query->value distances
EOF
grep -n 'Conv1d' cand_variant.py
python3 -c "import json;d=json.load(open('../decision.json'));print({k:(v['window'],v['transitions']) for k,v in d['arms'].items()})"
```

## Naming

`as` is taken by `stablegla-transformer-lr-audit-20260730-as` (pre-registered,
ledger-timestamped 3891b16/1512e67, cannot be renamed). This campaign is `at`.
