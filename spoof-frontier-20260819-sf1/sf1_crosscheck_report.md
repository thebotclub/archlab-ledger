# sf1 completion cross-check — spoof-frontier-20260819-sf1

**Campaign:** `spoof-frontier-20260819-sf1` on hub — exhaustive scan of Tóth's set S
(odd m with d = 2m − σ(m) > 0 and d | σ(m)) over (10¹², 10¹³], 360,000 segments, 48 niced workers.
**Completed:** 2026-08-20T19:56:13Z (heartbeat `DONE`, 360000/360000 segments; positive controls
gate1a full-segment-verify PASS, gate1b broken-variant FIRED, gate2 48/48 shard controls PASS).
**Cross-check run:** 2026-08-21, by `sf1_kernel_crosscheck.py` against the live hub ledger
(`sf1_crosscheck_hub-live.json`); members archived at `sf1_members_final.jsonl`.

## Totals

- **288 members** of S in (10¹², 10¹³] — versus ~129 at the quarter mark, i.e. member density held
  roughly constant across the range (no thinning or clustering surprise).
- Every member's σ(m), d and x = σ(m)/d **independently re-verified by direct factorization: all OK.**

## Verdicts

| Check | Result | Interpretation |
|---|---|---|
| Square members below 10¹⁶ | **0** | Confirms the proved Result 1: 9,018,009 remains the only square in S below 10¹⁶. |
| Kernel-support members | **0** (0 in the 245 Descartes-kernel list) | Expected direction under the no-go theorem; no spoof kernel support appears in this decade. |
| Exact kernel-family form ∏ pᵢ²ᵃⁱ | **0** | No member matches a Descartes family shape. |
| x equal to a kernel target | **0** | No x-target coincidences. |

## Depth histogram (distinct prime factors)

| depth | 5 | 6 | 7 | 8 |
|---|---|---|---|---|
| count | 6 | 145 | 113 | 24 |

## Notable members

- Largest x: **m = 7,454,198,513,685**, x = 354,961,833,984 (depth 7;
  3 · 5 · 7 · 11 · 647 · 1051 · 9491 — a squarefree member with an outsized σ/d quotient).
- x spans 120 … 3.55×10¹¹, median ≈ 8.17×10⁶.
- Six depth-5 (shallowest) members: 1,028,065,780,125; 1,352,376,925,263; 3,418,767,129,195;
  5,437,915,576,875; 6,855,733,096,875; 9,581,140,954,125.
- 24 members at depth 8 (e.g. 1,156,842,099,567) — the deepest the survey produced.

## One-line summary

The full (10¹², 10¹³] sweep found 288 members of Tóth's S with **zero squares, zero Descartes
kernel supports, zero kernel-family forms and zero x-target coincidences** — every surprise check
negative, so both standing results (the 9,018,009 square uniqueness below 10¹⁶ and the kernel
no-go direction) survive contact with a further 9×10¹² of range.
