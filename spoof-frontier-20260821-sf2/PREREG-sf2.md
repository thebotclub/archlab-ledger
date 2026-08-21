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
