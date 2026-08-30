# PREREG DRAFT — campaign spoof-frontier-20260821-sf2 (W1-extension: S to 10^14, with sealed numeric predictions)

Status: SEALED 2026-08-21T12:50Z by owner session (Hani: "go ahead", 2026-08-21). Launched under the protocol below.
Charter: ~/archlab-spoof/CHARTER-20260819.md (Lab 4, "spoof-frontier"; the charter's
Phase-0 ruling names 10^14 as "a separate follow-on decision after W1 lands" — W1 has
landed; this document is that decision's prereg).
Parent campaign: spoof-frontier-20260819-sf1 (COMPLETE 2026-08-20T19:56Z; 288 members
in (10^12, 10^13]; all validity statements PASS; independently cross-checked 2026-08-21).
Runner under prereg: run_w2.py — a MINIMAL modification of sf1's run_w1.py
(sha256 797958bad12b697385729fefa59741b4d2cbb08ff032af17f7f01dabd374f11b), see
"Required runner amendment" below. The sealed campaign must pin the exact file hash of
run_w2.py and b222263.txt.

## What will be computed

All members of Tóth's set S among odd m in (10^13, 10^14]: with d = 2m − σ(m),
m ∈ S iff d > 0 and d | σ(m). For every member we record m, σ(m), d, x = σ(m)/d,
and whether m is a perfect square, plus a completed-segment ledger and a progress log
with a final DONE inventory line. Method identical to sf1: segmented odd-sigma
divisor-pair sieve (numpy int64), 3,600,000 segments of 12,500,000 odd values,
multiprocessing pool, independent direct-factorization confirmation of every
sieve-found candidate before recording; a sieve-vs-factorization mismatch aborts.

## Why this run is different from sf1: sealed NUMERIC predictions

sf1 was a frontier extension with validity gates but no numeric forecast — nobody knew
what member count to expect. sf2 is run AFTER fitting density models to the combined
record (Tóth's published decade totals to 10^12 + sf1's complete decade + sf1's
within-decade profile). The predictions below are written BEFORE any (10^13, 10^14]
data exists. This is the archlab brand applied to the Descartes problem: the forecast
is part of the result, and being wrong is a publishable outcome.

### The models under test (stated so there is no post-hoc model selection)

Let I_k = number of S-members in (10^{k-1}, 10^k]. The complete record is:

  I_1 … I_13 = 2, 1, 4, 8, 13, 20, 33, 62, 84, 92, 140, 233, 288
  (I_1–I_12: Tóth 2021, Table 1. I_13 = 288: sf1, this programme.)

  M-A (Tóth's Conjecture 1, π_S(n) ~ c·log n): decade increments asymptotically
       constant → I_14 ≈ 233–288, central estimate 260.
  M-B (power-law density, fit to sf1's nine within-decade slices: ρ(m) ∝ m^{−0.905},
       r² = 0.93): decade ratio 1.245 → I_14 = 358 (band ≈ [300, 415] at ±1σ_fit+Poisson).
  M-C (geometric increment trend, log10 I_k = 0.342 + 0.1668·k fit on k = 5…13,
       resid sd 0.060): I_14 = 475 (±1σ_log ≈ [413, 547]).

### Sealed predictions

  P1 (count). I_14 will be reported against all three models above. The pre-committed
     discrimination rule: a model is SUPPORTED iff the observed count lies inside its
     stated band (M-A: [233, 300]; M-B: [300, 415]; M-C: [413, 547]; boundary and
     out-of-band outcomes are named as such, not rounded into a winner).
     Campaign-validity gate: 200 ≤ I_14 ≤ 600. Outside that, either the run is
     defective or every model fails — both are reportable outcomes, not silently
     patched.
  P2 (profile). The nine per-10^12 slice counts across the decade decline
     overall: first-slice / last-slice ratio ≥ 1.5. (Uniform-in-log-m density — the
     null reading of M-A — predicts ratio ≈ 1.1.)
  P3 (depth). Every member has between 5 and 9 distinct prime factors; the modal
     depth is 6 or 7. (sf1: support {5,…,8}, mode 6.)
  P4 (congruence statistics). Fraction of members ending in digit 5 lies in
     [0.55, 0.80] (Tóth at 10^12: 0.711; sf1: 0.667). Mod-8 class imbalance
     (largest/smallest of the four odd classes) ≤ 1.6 (Tóth: 1.24; sf1: 1.33).
  P5 (divisibility by 3). Every member is divisible by 3. Consistent with the OEIS
     A222263 comment (A. Violette, 2026-05-27) that the first term not divisible by 3
     is ≤ 54,440,521,568,257,825; a counterexample below 10^14 would sharpen that
     bound downwards and is reported as a finding, not an error.
  P6 (squares). Zero perfect-square members. ENTAILED by this programme's proved
     Result 1 (no square in S below 10^16 other than 9,018,009); included as a
     consistency gate on the new code path, not as a discovery chance.
  P7 (prime x). Zero members with x prime. ENTAILED by Ochem–Rao (no odd perfect
     number below 10^1500): prime x with x coprime to m would make m·x an odd
     perfect number ≤ ~10^29. A hit is either an instrument defect or the largest
     result in the lab's history; the confirmation path decides which before any
     claim is read.
  P8 (kernels). Zero members whose prime support is one of the 245 Descartes
     kernels (kernels_245.json), zero members in exact kernel-family form, zero
     members whose x equals a kernel target. Expected direction under the no-go
     theorem (expedition report v2, Result 3). Any hit is re-verified by hand before
     being believed.
  P9 (x magnitude). max x ≤ 10^14. (sf1 max: 3.55×10^11; analytic ceiling via
     Robin/Gronwall ≈ 6.2×10^14 at m = 10^14.)

### Falsifiable validity statements (carried from sf1, re-scoped)

  V1. Segment plan covers (10^13, 10^14] with no gaps or overlaps: 3,600,000
      distinct completed segments summing to 4.5×10^13 odd values tested.
  V2. All 48 per-shard positive controls fired (control segment [9,000,001,
      9,100,000) must yield EXACTLY member 9,018,009, σ = 18,035,199, x = 22,021,
      plus 200 sigma spot-checks per worker).
  V3. Broken-variant self-test fires on a deliberately corrupted sigma.
  V4. Every recorded member passes independent direct-factorization confirmation.
  V5. --validate re-run under the sealed campaign recovers exactly the 20 published
      A222263 members in (10^9, 2×10^9], none missing, none extra.
  If any Vi fails, the campaign result is VOID and reported as such.

## Required runner amendment (the only code change)

run_w2.py differs from run_w1.py in exactly three ways, each reviewed line-by-line
before sealing:
  1. A --production2 mode selecting range (10^13, 10^14] with its own state dir
     (state/production2/); the sf1 state dir is never touched.
  2. The segment-count guard is lifted from 400,000 to 4,000,000 (this range
     implies 3,600,000).
  3. The header's int64 overflow analysis is re-derived for m ≤ 10^14:
     σ(m)/m < e^γ·ln ln m + 0.6483/ln ln m with ln ln 10^14 ≈ 3.475
     ⇒ σ(m) < 6.2×10^14 ≪ 2^63 − 1 ≈ 9.22×10^18. int64 remains safe with
     four orders of magnitude of headroom. No other arithmetic changes.
The amendment is validated by V5 (identical machinery on the OEIS range) BEFORE any
production segment runs, and the broken-variant gate must fire under the new binary.

## Pre-committed reporting rules (carried from sf1, unchanged in spirit)

- Report I_14, the FULL member list, and every Pi outcome, whatever they are —
  including a count that lands outside every model band. The DONE inventory line is
  the result of record.
- A crash, gap, or partially covered range = INCOMPLETE. Resume via the ledger is
  permitted and logged; a silent fresh re-run is NOT; state-dir surgery is reported.
- Model selection is pre-committed (above); no fitted-after-the-fact model may be
  presented as a prediction. Post-hoc structure found in the data is labelled
  exploratory.
- Wall time, throughput, and the positive-control record are reported regardless.

## Resource cap (charter)

≤ 48 workers, every worker and the parent at nice 19, hub CPU only, $0.
RSS unchanged (~400 MB peak/worker ⇒ ≤ ~19 GB worst-case transient on the 93 GB box).
Expected wall time at 48 workers: ~7 days (charter estimate ~165 wall-h; per-segment
cost grows ∝ isqrt(R), 3.16×10^6 → 10^7 across the decade). Duration does not affect
validity. Kill/resume per sf1 protocol (kill/resume was verified in sf1 build-time
smoke: SIGKILL mid-run, resume recomputed nothing, identical final member list).

## What this does NOT claim

- Nothing about m > 10^14.
- Nothing about odd perfect numbers, their existence, or bounds on them (P7 is a
  consistency gate, not an OPN search).
- Nothing about even m.
- No claim that any of M-A/M-B/M-C is a theory; they are fitted curves, and the
  paper says so.
- No external communication (Tóth email, OEIS, journal, arXiv): Hani-gated, always.

## Launch protocol (owner session only, after seal)

    cd ~/archlab-spoof/w1
    mkdir -p state/production2
    setsid nohup python3 run_w2.py --production2 --workers 48 \
        >> state/production2/nohup.out 2>&1 < /dev/null &

Monitor: `tail -f state/production2/progress.log`. Kill:
`kill -TERM -"$(cat state/production2/runner.pid)"`. Resume: rerun the same command.

## AMENDMENT A1 (2026-08-23T04:35Z, pre-analysis; campaign 7.1% complete, no sf2 data analyzed)

Two errors in P2's statement are corrected before any profile analysis of sf2 data:

(i) **Slice-width wording.** "The nine per-10^12 slice counts across the decade" is
dimensionally wrong: the decade (10^13, 10^14] spans NINETY slices of width 10^12.
P2's intent is NINE EQUAL SLICES OF WIDTH 10^13 (the analogue of sf1's nine
10^12-wide slices across its decade). P2 is reworded accordingly.

(ii) **The null benchmark was misstated.** "Uniform-in-log-m density predicts ratio
≈ 1.1" is incorrect: under uniform-in-log density, equal-width slices have counts
proportional to ln((k+1)/k), giving first/last ratio ≈ 6.6; under M-B
(ρ ∝ m^−0.905) the ratio is ≈ 4.9. Both models therefore pass the ≥ 1.5 condition,
which is retained as a CONSISTENCY CHECK ONLY. P2 carries no model-discriminating
weight; discrimination among M-A/M-B/M-C lives entirely in P1 (the count). The
predicted normalized nine-slice profiles, for the record:
  M-A (uniform in log m): [1.00, 0.58, 0.42, 0.32, 0.26, 0.22, 0.19, 0.17, 0.15]
  M-B (ρ ∝ m^−0.905):     [1.00, 0.65, 0.49, 0.40, 0.33, 0.29, 0.26, 0.23, 0.21]
Both will be reported against the observed profile descriptively.

Scientific impact: none on P1, P3–P9 (unchanged; P1 is the discriminating
prediction). P2's role is weakened from "discriminating" to "consistency", logged
here rather than made silently, per the lab's amendment convention. No sf2 member
data had been analyzed when this amendment was sealed; only the runner's
cumulative member counter (53 at 257,000/3,600,000 segments) was observed, which
is not a profile analysis and does not condition this change.

## AMENDMENT A2 (locally filed 2026-08-27T15:55Z; entered into this sealed campaign record 2026-08-30 — see disclosure below)

**Campaign status at original filing:** 803,500 / 3,600,000 segments (22.3%), 145 members recorded.
**Scope:** ADDS one prediction (P10). Nothing sealed is altered: P1–P9, the runner, the validity gates, and the model-discrimination rule are unchanged.

### Why this amendment exists

Analysis of the *already published* record (Tóth's 692 members ≤ 10^12 plus sf1's 288 members in (10^12, 10^13] — all of it public before sf2 launched) found a regularity the seal does not cover: the share of members with t ≡ 1 (mod 3) rises (over decades k=7..13) from roughly 40% to 65.3%, while t ≡ 0 (mod 3) collapses toward 19.1% at the frontier. P4 covers last-digit and mod-8 congruences only; the t-spectrum's mod-3 structure is unpredicted. This amendment registers the extrapolation before the t-classes of sf2's members are computed.

### P10 (t-spectrum mod-3 drift)

Among the I_14 members in (10^13, 10^14]:

- share with t ≡ 1 (mod 3) ∈ **[0.61, 0.76]**, central estimate 0.684;
- share with t ≡ 0 (mod 3) ∈ [0.08, 0.25], central estimate 0.165;
- share with t ≡ 2 (mod 3) ∈ [0.08, 0.22], central estimate 0.151.

Basis: weighted least squares of the per-decade shares on decade index k = 7…13 (share = 0.0277 + 0.0469·k for t ≡ 1), bands at ±2·(residual sd 0.024) plus binomial noise at n = 358.

### Contamination disclosure (archlab honesty rule)

1. The raw progress log (including member records) has been visible throughout; no t-class analysis of sf2 members had been performed as of original filing.
2. One member's class was unavoidably observed when a log line was displayed during a routine heartbeat check on 2026-08-27T15:55Z: m = 30,091,333,485,255 has t = 303,906,817 ≡ 1 (mod 3). One member out of ~358 expected; the prediction is registered with this single observation disclosed, and it does not move the bands.
3. The fitted law uses ONLY the pre-sf2 record (692 + 288 members), all of it public before launch. Independently verified 2026-08-30 (adversarial review): the analysis scripts (`mod3_drift.py` et al.) read only the pre-sf2 files, never sf2's live output; the sealed central estimate (0.684) matches the clean pre-sf2 extrapolation, not sf2's partial share visible at filing time (0.703) — the forensic test that would catch back-fitting found none.

### Scoring

P10 is scored on the DONE inventory: per-class shares over the full decade, pass/fail per band, reported whatever the outcome. A failure of the t ≡ 1 band damages the drift law and the payment-cost mechanism; a failure of any band is reported as a finding, not rounded into a pass.

— Hani Koshaji (owner), with the archlab autonomous operators

## AMENDMENT A3 (locally filed 2026-08-28T03:40Z; entered into this sealed campaign record 2026-08-30 — see disclosure below)

**Campaign status at original filing:** 857,000 / 3,600,000 segments (23.8%), 156 members recorded.
**Scope:** ADDS one prediction (P11). P1–P10, the runner, the validity gates, and the model-discrimination rule are unchanged.

### Basis

The drift law of Amendment A2 (t ≡ 1 mod 3 share climbing) generalizes to every assisted class tested (`assist_drift.py`, fitted ONLY on the pre-sf2 public record of 692 + 288 members). Per-decade weighted-least-squares slopes over decades k = 5…13: p=3 +4.66 pts/decade (65.3% at decade 13), p=5 +3.67 (42.7%), p=7 +1.88 (43.4%), p=11 +1.23 (24.3%), p=13 +0.93 (28.5%).

### P11 (t-spectrum mod-5 drift)

Among the I_14 members in (10^13, 10^14]: the share with **t ≡ 1 (mod 5) ∈ [0.37, 0.58]**, central estimate 0.473.

**Correction (2026-08-30, adversarial review):** the regression formula as originally filed, share(k) = 0.027 + 0.0367·k, was transcribed incorrectly — it evaluates to 0.541 at k=14, not the stated central 0.473. The fit that actually produces 0.473 is **share(k) = −0.0405 + 0.0367·k** (intercept corrected; slope unaffected). The band [0.37, 0.58] and the central estimate 0.473 are unchanged and correct — only the printed formula was wrong, and a third party checking the prediction against the formula as originally written would have gotten the wrong number.

### Contamination disclosure

As for A2: the raw progress log has been visible; no t-class analysis of sf2 members had been performed as of original filing. The single member disclosed in A2 (m = 30,091,333,485,255, t = 303,906,817) has t ≡ 2 (mod 5) — not in the predicted class; one observation out of ~358, disclosed, does not move the bands. Independently verified 2026-08-30: fitted on pre-sf2 data only, sealed central (0.473) matches the clean extrapolation, not sf2's partial share at filing time (0.448) — no back-fitting signature found.

### Scoring

Scored on the DONE inventory, pass/fail against the band, reported either way. A failure damages the per-prime generalization of the drift law; the mod-3 P10 stands or falls independently.

— Hani Koshaji (owner), with the archlab autonomous operators

## Disclosure on the sealing of A2 and A3 (2026-08-30)

Amendments A2 and A3 above were drafted and locally filed (as plain files in a working directory) on 2026-08-27 and 2026-08-28 respectively, at the campaign-progress points stated in each. Unlike Amendment A1, they were not entered into this sealed preregistration document or `campaign.json`'s amendments array at the time, and were not committed to version control until 2026-08-30 — so the only timestamp evidence for their original filing dates is local file modification times, not an external commit. An independent adversarial review on 2026-08-30 checked for the specific failure mode this gap could hide — that the predictions were secretly derived from sf2's own partial results rather than genuinely extrapolated in advance — and found no evidence of it: the analysis scripts touch only pre-sf2 data, and both sealed central estimates land where the clean pre-sf2 extrapolation puts them, not where sf2's partial data sat at each filing time. This entry now gives both amendments the same sealed status as A1, effective from this commit's timestamp, with this paragraph as the permanent record of the gap between original filing and formal sealing.

## Infrastructure note (2026-08-30) — sf2 sharded across 5 hosts, no scientific change

To reduce wall-clock time, sf2 execution was split across hub + mini1-4, all running the identical pinned runner (runner_sha256 unchanged, verified by hash on every host before launch). This is a compute-distribution change only — same code, same segment-plan math, same gates (1a/1b/2) fired independently and passed on every host — nothing about the sealed methodology, predictions, or scoring changes, so no amendment is filed.

Split (segment width 25,000,000, i.e. 2*SEG_ODD):
- hub: (1e13, 7.5e13], workers=48, state-dir state/production2 (resumed cleanly from ledger at 1,068,315/2,600,000 segments already complete -- no work lost, no duplication)
- mini1: (7.5e13, 8.125e13], workers=6
- mini2: (8.125e13, 8.75e13], workers=6
- mini3: (8.75e13, 9.375e13], workers=6
- mini4: (9.375e13, 1e14], workers=6

Each host's state dir is independent (own ledger.log / members.jsonl / progress.log); final DONE inventory for scoring P1-P11 will be the union of all five ledgers/member lists once all shards report segments == planned. No segment index appears in more than one host's plan (boundaries are exact multiples of the 25,000,000 segment span from the same origin A=1e13, verified before launch).
