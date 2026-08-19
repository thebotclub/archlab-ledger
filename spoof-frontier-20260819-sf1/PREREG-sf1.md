# PREREG DRAFT — campaign spoof-frontier-20260819-sf1 (W1)

Status: SEALED 2026-08-19T05:36:55Z by the owner session, before any production computation.
Pinned hashes: run_w1.py sha256 797958bad12b697385729fefa59741b4d2cbb08ff032af17f7f01dabd374f11b ; b222263.txt sha256 d879e792b76405609c61ffd2801259a8747328cc1f741859006fc7a20f57348e ; charter sha256 b2e90f400f8e47de2b41432e12cbe11e96f898ea5a3a2842b3850e7c4fec492f.
Owner-side verification before seal: independent --validate execution (VALIDATION PASS, 20/20,
missing [], extra []), guard refusal test, and hash agreement with the builder's report.
Charter: ~/archlab-spoof/CHARTER-20260819.md (Lab 4, "spoof-frontier").
Runner under prereg: ~/archlab-spoof/w1/run_w1.py (SEG_ODD = 12,500,000; the
sealed campaign must pin the exact file hash of run_w1.py and b222263.txt).

## What will be computed

All members of Tóth's set S among odd m in (10^12, 10^13]: with
d = 2m − σ(m), m ∈ S iff d > 0 and d | σ(m). For every member we record
m, σ(m), d, x = σ(m)/d, and whether m is a perfect square
(state/production/members.jsonl), plus a completed-segment ledger and a
progress log with a final DONE inventory line.

Method: segmented odd-sigma divisor-pair sieve (numpy int64), 360,000
segments of 12,500,000 odd values, multiprocessing pool. Every sieve-found
candidate is re-verified by an independent direct-factorization code path
before it is recorded; a sieve-vs-factorization mismatch aborts the run.

## Honest framing

This extends Tóth's published computation of S (complete to 10^12; OEIS
A222263, 692 terms, largest 993,727,314,855) by one order of magnitude —
for the FULL set, not only the square subclass. It is a computational
extension of a published search frontier, nothing more.

## Falsifiable statements (the run is VALID only if all hold)

1. Every S-member in (10^12, 10^13] will be found; the segment plan covers
   the range with no gaps or overlaps (ledger must show 360,000 distinct
   completed segments summing to 4.5 × 10^12 odd values tested).
2. All 48 per-shard positive controls fired: each worker process, before any
   production segment, recomputed the control segment [9,000,001, 9,100,000)
   with the production code path and found EXACTLY the known member
   9,018,009 with σ = 18,035,199 and x = 22,021, plus 200 sigma spot-checks
   against direct factorization.
3. The startup broken-variant self-test reported a discrepancy when one
   sigma value was deliberately corrupted (the gate is shown able to fire),
   and the uncorrupted full control segment verified exactly.
4. Every claimed member passes independent direct-factorization
   confirmation (σ, d, divisibility, and x all reproduced).
5. The OEIS-range validation (below) recovers the published members exactly
   — no member missing, no extra member.

If any statement fails, the campaign result is VOID and reported as such.

## Validation coverage (already executed as build-time smoke; will be
re-run under the sealed campaign before launch)

`run_w1.py --validate` covers (10^9, 2×10^9] — 5×10^8 odd values — through
the identical production machinery (same sieve, same gates, same
confirmation path), then cross-checks against the published A222263 b-file:
exactly 20 published members lie in that range and all 20 must be
recovered with nothing extra. Build-time smoke result 2026-08-19:
VALIDATION PASS (20/20, missing [], extra []). The b-file itself was
independently sanity-checked: all 692 terms odd, strictly increasing, and
329 terms re-verified against the S-condition by direct factorization.

## Pre-committed reporting rules

- Report the member count and the FULL member list, whatever they are —
  including zero new members, and including any result that contradicts
  expectation. The DONE inventory line is the result of record.
- A crash, gap, or partially covered range = INCOMPLETE. Resume via the
  ledger is permitted and logged (it recomputes nothing); a silent fresh
  re-run in place of a damaged state dir is NOT. State-dir surgery of any
  kind must be reported in the campaign record.
- Members are recorded only after independent confirmation; a
  sieve-vs-factorization mismatch is reported as a defect, never dropped.
- Wall time, throughput, and the positive-control record are reported in
  the final inventory regardless of outcome.

## Resource cap (charter)

≤ 48 workers, every worker and the parent at nice 19, hub CPU only, $0.
RSS: ~400 MB peak per worker (sizing math in run_w1.py header) ⇒ ≤ ~19 GB
worst-case transient on the 93 GB box. The runner refuses > 48 workers and
refuses ranges implying > 400k segments.

## Runtime expectation (estimate, not a validity condition)

Measured at the low edge (offset 10^12): ~7.0 s/segment/worker
(≈ 1.8×10^6 odd-m/s/core, consistent with Phase 0's 1.75×10^6). Per-segment
cost rises across the decade because the divisor loop runs to isqrt(R)
(1.0×10^6 at 10^12 → 3.16×10^6 at 10^13). Expected wall time at 48 workers:
~17–30 h. The heartbeat (every 250 segments) reports empirical ETA; the
Phase-0 ruling's 16.5 h figure did not model the isqrt growth and the true
figure may exceed it. Duration does not affect validity.

## What this does NOT claim

- Nothing about m > 10^13 (10^14 is a separate follow-on decision).
- Nothing about odd perfect numbers, their existence, or bounds on them.
- Nothing about even m (S is scanned over odd m only, matching A222263).
- No structural/theoretical claims (those are W3/W4).
- No claim of novelty beyond the frontier extension itself; W6 (OEIS
  b-file contribution) and any external communication remain Hani-gated.

## Launch protocol (owner session only, after seal)

    cd ~/archlab-spoof/w1
    mkdir -p state/production
    setsid nohup python3 run_w1.py --production --workers 48 \
        >> state/production/nohup.out 2>&1 < /dev/null &

Monitor: `tail -f state/production/progress.log`. Kill:
`kill -TERM -"$(cat state/production/runner.pid)"`. Resume: rerun the same
command; the ledger prevents recomputation (kill/resume verified in
build-time smoke: SIGKILL at 16/40 segments, resume skipped all 16,
final member list identical to an uninterrupted run, zero duplicate
ledger or member lines).
