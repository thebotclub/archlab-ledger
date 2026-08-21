#!/usr/bin/env python3
# =============================================================================
# W1-extension production runner — campaign spoof-frontier-20260821-sf2
# (Lab 4 charter; amended from sf1's runner run_w1.py,
# sha256 797958bad12b697385729fefa59741b4d2cbb08ff032af17f7f01dabd374f11b)
#
# Computes ALL members of Toth's set S among odd m in a half-open-below range
# (A, B]:  with d = 2m - sigma(m), m is a member iff d > 0 and d | sigma(m).
# Records m, sigma(m), d, x = sigma(m)/d, and whether m is a perfect square.
# Production target (sf2): (10^13, 10^14].  OEIS cross-reference: A222263.
#
# AMENDMENT vs run_w1.py (exactly three substantive changes, per PREREG-sf2):
#   1. New --production2 mode: range (1e13, 1e14], state dir state/production2/.
#      sf1's state/production/ is never touched.
#   2. Segment-count guard lifted 400,000 -> 4,000,000 (this range needs
#      3,600,000 segments).
#   3. int64 overflow analysis re-derived below for m <= 1e14.
#   Header/docstring comments updated to match; no arithmetic changed.
#
# LAUNCH PATTERN (owner session, only after the campaign dir is sealed):
#   cd ~/archlab-spoof/w1
#   mkdir -p state/production2
#   setsid nohup python3 run_w2.py --production2 --workers 48 \
#       >> state/production2/nohup.out 2>&1 < /dev/null &
#   # setsid detaches from the SSH session's process group + controlling TTY,
#   # so logout/HUP cannot kill the run; nohup belt-and-suspenders on top.
#   # Monitor:  tail -f state/production/progress.log
#   # Kill:     kill -TERM -"$(cat state/production/runner.pid)"   (negative
#   #           PID = whole process group: parent + all pool workers)
#   # Resume:   rerun the exact same command. The completed-segment ledger
#   #           (ledger.log) is re-read on start; finished segments are never
#   #           recomputed; previously found members are re-loaded and deduped.
#
# GATES (all structural, all must fire before/around production work):
#   1. Parent startup: full control-segment verification — every sigma in
#      [9,000,001, 9,100,000) computed by the sieve is compared against
#      independent direct factorization; then a BROKEN-VARIANT self-test
#      deliberately corrupts one sigma value and requires the same checker to
#      report a discrepancy (a gate must be shown able to fire).
#   2. Per-shard positive control: every worker process, in its initializer
#      (i.e. before it can receive any production segment), recomputes the
#      control segment with the production code path and requires the member
#      set to be EXACTLY {9,018,009} with sigma = 18,035,199 and x = 22,021,
#      plus 200 random sigma spot-checks against direct factorization. The
#      parent refuses to dispatch production segments until every worker has
#      logged CONTROL PASS; any CONTROL FAIL aborts the run.
#   3. Cross-validation per found member: the sieve only FINDS candidates;
#      every candidate is re-verified in the parent by an independent code
#      path (direct trial-division factorization) before being written to
#      members.jsonl. A sieve-vs-factorization mismatch hard-aborts the run
#      (that is a correctness discrepancy, never silently dropped).
#
# SEGMENT / RSS SIZING (charter: hub is a shared 93 GiB production box):
#   SEG_ODD = 12,500,000 odd values per segment (numeric span 25,000,000).
#   Per worker, peak live arrays during the sieve inner loop (all int64):
#     sig            12.5e6 * 8 B = 100 MB   (persistent for the segment)
#     ms (indices)   <= 12.5e6 * 8 B = 100 MB  (largest at d = 1)
#     qs (pair sums) <= 12.5e6 * 8 B = 100 MB
#     + one transient allocation (np.arange result / floordiv result) 100 MB
#   => peak ~= 400 MB/worker.  Membership extraction afterwards is chunked
#   (1e6-element chunks, ~8 MB temporaries) so the sieve phase governs.
#   48 workers * 0.4 GB ~= 19.2 GB worst-case transient (workers do not all
#   sit at their d=1 peak simultaneously, so typical is lower), against
#   ~80 GB available on the 93 GB box => comfortable margin for the fleet.
#
# int64 OVERFLOW ANALYSIS (re-derived for sf2, m <= 1e14):
#   Largest value ever held in an int64 cell here is sigma(m) for m <= 1e14.
#   Robin/Gronwall bound: sigma(m)/m < e^gamma * ln ln m + 0.6483/ln ln m.
#   For m <= 1e14: ln ln m = ln(32.24) ~= 3.475, so sigma(m)/m < 1.781*3.475
#   + 0.187 < 6.38  =>  sigma(m) < 6.4e14.  int64 max is 9.22e18 — four
#   orders of magnitude of headroom. The accumulation is a sum of positive
#   d+q contributions whose partial sums increase monotonically to the final
#   sigma(m), so no intermediate value ever exceeds sigma(m) itself.
#   Other quantities: m < 1e14, 2m < 2e14, d = 2m - sigma in (-6.4e14, 2e14),
#   ms/qs entries < 1e14 — all safely inside int64.
#
# DEVIATION FROM phase0_bench.py (declared): same divisor-pair enumeration to
# isqrt(R-1) over odd d only, but restructured for memory + speed:
#   (a) multiples start at q0 = max(oddceil(L/d), d) so q >= d structurally,
#       removing the reference's three np.where masks (both/eq/keep);
#   (b) the single q == d case (m = d^2) is corrected by subtracting d from
#       the first contribution (sqrt divisor counted once);
#   (c) np.add.at is replaced by plain fancy sig[idx] += vals — exact here
#       because for a FIXED d the multiples d*q are distinct, so the index
#       array never contains duplicates within one call.
#   The restructure is verified by gates 1-3 above and by --validate, which
#   must recover the 20 published A222263 members in (1e9, 2e9] exactly.
# =============================================================================

import argparse
import fcntl
import json
import math
import multiprocessing as mp
import os
import random
import sys
import time

import numpy as np

SEG_ODD = 12_500_000            # odd values per segment
SEG_SPAN = 2 * SEG_ODD          # numeric span per segment

CONTROL_L, CONTROL_R = 9_000_001, 9_100_000
CONTROL_M = 9_018_009           # = 3003^2 = 3^2 7^2 11^2 13^2, the known S-member
CONTROL_SIGMA = 18_035_199      # 13 * 57 * 133 * 183
CONTROL_X = 22_021              # sigma / (2m - sigma) = 18035199 / 819
CONTROL_SPOTCHECKS = 200

B_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "b222263.txt")


# ---------------------------------------------------------------- sieve path
def sigma_segment_odd(L, R):
    """sigma(m) for odd m in [L, R): returns int64 array sig, sig[i] = sigma(L+2i).

    Divisor-pair enumeration: for every odd d <= isqrt(R-1) and every odd
    q >= d with L <= d*q < R, add d+q (or d alone when q == d) to sig[d*q].
    Every divisor pair (d, q) of every odd m in [L, R) with d <= q has
    d <= isqrt(m) <= isqrt(R-1), so each pair is counted exactly once.
    """
    assert L % 2 == 1 and R > L
    n = (R - L + 1) // 2
    sig = np.zeros(n, dtype=np.int64)
    r = math.isqrt(R - 1)
    for d in range(1, r + 1, 2):
        q0 = (L + d - 1) // d           # ceil(L/d)
        if q0 % 2 == 0:
            q0 += 1                     # q must be odd (m odd)
        if q0 < d:
            q0 = d                      # enforce q >= d (d odd => q0 stays odd)
        start = d * q0
        if start >= R:
            continue
        ms = np.arange(start, R, 2 * d, dtype=np.int64)
        qs = ms // d
        qs += d                         # contribution d + q per pair
        ms -= L
        ms >>= 1                        # ms is now the index array (m-L)/2
        if q0 == d:
            qs[0] -= d                  # m = d^2: sqrt divisor counted once
        sig[ms] += qs                   # indices unique for fixed d => exact
    return sig


def scan_segment(L, R):
    """Return (members, n_odd) for odd m in [L, R).

    members: list of (m, sigma, d, x) for every S-member found by the sieve.
    Membership extraction is chunked to keep temporaries ~8 MB.
    """
    sig = sigma_segment_odd(L, R)
    n = len(sig)
    members = []
    CH = 1_000_000
    for off in range(0, n, CH):
        s_c = sig[off:off + CH]                       # view
        k = len(s_c)
        m_c = (L + 2 * off) + 2 * np.arange(k, dtype=np.int64)
        d_c = 2 * m_c - s_c
        ii = np.nonzero(d_c > 0)[0]
        hits = ii[s_c[ii] % d_c[ii] == 0]
        for i in hits:
            m = int(m_c[i]); s = int(s_c[i]); d = int(d_c[i])
            members.append((m, s, d, s // d))
    return members, n


# ------------------------------------------------- independent (checker) path
def sigma_direct(m):
    """sigma(m) for odd m by direct trial-division factorization.

    Independent of the sieve: no shared state, no numpy. For m <= 1e14 trial
    division runs to isqrt(m) <= 1e7 (odd steps only) — fine for the rare
    per-member confirmations and the control-segment verification.
    """
    if m == 1:
        return 1
    s, t, p = 1, m, 3
    while p * p <= t:
        if t % p == 0:
            pk, tot = 1, 1
            while t % p == 0:
                t //= p
                pk *= p
                tot += pk
            s *= tot
        p += 2
    if t > 1:
        s *= t + 1
    return s


def confirm_member(m, s, d, x):
    """Independent confirmation of a sieve-found member. True iff everything
    the sieve claims is reproduced by direct factorization."""
    s2 = sigma_direct(m)
    if s2 != s:
        return False
    d2 = 2 * m - s2
    return d2 == d and d2 > 0 and s2 % d2 == 0 and s2 // d2 == x


def verify_sigma_block(sig, L):
    """Compare a sigma array against direct factorization for EVERY value.
    Returns list of discrepant m (empty = pass). This is 'the checker' that
    the broken-variant self-test must be able to make fire."""
    bad = []
    for i in range(len(sig)):
        m = L + 2 * i
        if int(sig[i]) != sigma_direct(m):
            bad.append(m)
    return bad


# ------------------------------------------------------------- worker side
_G = {"control_ok": False}


def _append_line(path, line):
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, line.encode())    # single write of one short line: atomic
        os.fsync(fd)
    finally:
        os.close(fd)


def worker_control_check():
    """Per-shard positive control, production code path. Returns (ok, detail)."""
    members, n = scan_segment(CONTROL_L, CONTROL_R)
    if [(m, s, x) for (m, s, d, x) in members] != [(CONTROL_M, CONTROL_SIGMA, CONTROL_X)]:
        return False, "control-segment member set %r != [(%d,%d,%d)]" % (
            members, CONTROL_M, CONTROL_SIGMA, CONTROL_X)
    sig = sigma_segment_odd(CONTROL_L, CONTROL_R)
    rng = random.Random(1)
    for _ in range(CONTROL_SPOTCHECKS):
        m = rng.randrange(CONTROL_L, CONTROL_R) | 1
        if int(sig[(m - CONTROL_L) // 2]) != sigma_direct(m):
            return False, "sigma spot-check mismatch at m=%d" % m
    return True, "member=%d sigma=%d x=%d spotchecks=%d" % (
        CONTROL_M, CONTROL_SIGMA, CONTROL_X, CONTROL_SPOTCHECKS)


def worker_init(control_log):
    try:
        os.nice(19)                     # charter resource cap
    except OSError:
        pass
    ok, detail = worker_control_check()
    _G["control_ok"] = ok
    _append_line(control_log, "CONTROL %s pid=%d %s\n"
                 % ("PASS" if ok else "FAIL", os.getpid(), detail))


def worker_scan(task):
    seg_idx, L, R = task
    if not _G.get("control_ok"):
        return ("CONTROL_FAIL", seg_idx, os.getpid(), None, None, None)
    members, n = scan_segment(L, R)
    return ("OK", seg_idx, L, R, n, members)


# ------------------------------------------------------------- parent side
def log(msg, progress_path=None):
    line = "%s %s" % (time.strftime("%Y-%m-%dT%H:%M:%S%z"), msg)
    print(line, flush=True)
    if progress_path:
        _append_line(progress_path, line + "\n")


def startup_self_tests(progress_path, control_log):
    """Gate 1: full control-segment verification + broken-variant self-test."""
    t0 = time.time()
    sig = sigma_segment_odd(CONTROL_L, CONTROL_R)
    bad = verify_sigma_block(sig, CONTROL_L)
    if bad:
        log("FATAL startup: sieve vs direct factorization discrepancies at %r" % bad[:10],
            progress_path)
        sys.exit(2)
    log("startup gate 1a PASS: full control segment [%d,%d) sigma-verified "
        "against direct factorization (%d values, %.1fs)"
        % (CONTROL_L, CONTROL_R, len(sig), time.time() - t0), progress_path)

    # BROKEN-VARIANT: corrupt one sigma value; the checker MUST report it.
    sig_broken = sig.copy()
    i = (CONTROL_M - CONTROL_L) // 2
    sig_broken[i] += 2
    bad = verify_sigma_block(sig_broken, CONTROL_L)
    if bad != [CONTROL_M]:
        log("FATAL startup: broken-variant self-test DID NOT fire correctly "
            "(checker reported %r, expected [%d]) — gate cannot be trusted"
            % (bad[:10], CONTROL_M), progress_path)
        sys.exit(2)
    log("startup gate 1b PASS: broken-variant self-test fired "
        "(corrupted sigma(%d) detected by checker)" % CONTROL_M, progress_path)
    _append_line(control_log,
                 "SELFTEST PASS full-segment-verify + broken-variant-fired m=%d\n"
                 % CONTROL_M)


def wait_for_shard_controls(control_log, nworkers, progress_path, timeout=600):
    """Gate 2: refuse production until every worker logged CONTROL PASS."""
    t0 = time.time()
    while True:
        lines = []
        if os.path.exists(control_log):
            with open(control_log) as f:
                lines = [l for l in f if l.startswith("CONTROL ")]
        fails = [l for l in lines if l.startswith("CONTROL FAIL")]
        if fails:
            log("FATAL: shard positive control FAILED — refusing production:\n"
                + "".join(fails), progress_path)
            return False
        if len(lines) >= nworkers:
            log("gate 2 PASS: %d/%d shard positive controls fired (control log %s)"
                % (len(lines), nworkers, os.path.basename(control_log)), progress_path)
            return True
        if time.time() - t0 > timeout:
            log("FATAL: timed out waiting for shard controls (%d/%d after %ds)"
                % (len(lines), nworkers, timeout), progress_path)
            return False
        time.sleep(0.5)


def load_ledger(ledger_path):
    """Return completed: dict seg_idx -> (L, R, n_odd)."""
    completed = {}
    if os.path.exists(ledger_path):
        with open(ledger_path) as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 5 and parts[0] == "SEG":
                    completed[int(parts[1])] = (int(parts[2]), int(parts[3]), int(parts[4]))
    return completed


def load_members(members_path):
    """Return dict m -> record, deduped (a crash between the members write and
    the ledger write makes the segment recompute, which may re-append)."""
    out = {}
    if os.path.exists(members_path):
        with open(members_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    out[rec["m"]] = rec
    return out


def run(A, B, workers, state_dir, heartbeat_every, mode):
    os.makedirs(state_dir, exist_ok=True)
    # single-runner guard
    lock_fd = os.open(os.path.join(state_dir, ".lock"), os.O_WRONLY | os.O_CREAT, 0o644)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("FATAL: another runner already holds %s/.lock" % state_dir)
        sys.exit(2)
    with open(os.path.join(state_dir, "runner.pid"), "w") as f:
        f.write(str(os.getpgid(0)) + "\n")

    progress = os.path.join(state_dir, "progress.log")
    ledger = os.path.join(state_dir, "ledger.log")
    members_path = os.path.join(state_dir, "members.jsonl")
    control_log = os.path.join(state_dir, "control-%d.log" % int(time.time()))

    try:
        os.nice(19)
    except OSError:
        pass

    t_start = time.time()
    log("RUN start mode=%s range=(%d, %d] workers=%d seg_odd=%d pid=%d pgid=%d"
        % (mode, A, B, workers, SEG_ODD, os.getpid(), os.getpgid(0)), progress)

    # segment plan over odd m in (A, B]  ==  odd grid [lo, hi_ex)
    lo = A + 1 if (A + 1) % 2 == 1 else A + 2
    hi_ex = B + 1
    if (hi_ex - lo) // SEG_SPAN + 1 > 4_000_000:
        log("FATAL: range implies >4M segments — refusing (guard against "
            "mistyped bounds; production2 (1e13,1e14] needs 3.6M)", progress)
        sys.exit(2)
    seg_list = []
    L = lo
    idx = 0
    while L < hi_ex:
        R = min(L + SEG_SPAN, hi_ex)
        seg_list.append((idx, L, R))
        L = R if R % 2 == 1 else R      # SEG_SPAN even => L stays odd
        idx += 1
    total_segs = len(seg_list)

    completed_full = load_ledger(ledger)
    plan = {i: (L, R) for (i, L, R) in seg_list}
    for i, (Lc, Rc, _) in completed_full.items():
        if plan.get(i) != (Lc, Rc):
            log("FATAL: ledger segment %d = (%d, %d) does not match this "
                "range plan %r — state dir belongs to a different range; "
                "refusing to resume" % (i, Lc, Rc, plan.get(i)), progress)
            sys.exit(2)
    completed = {i: n for i, (_, _, n) in completed_full.items()}
    members = load_members(members_path)
    todo = [t for t in seg_list if t[0] not in completed]
    log("plan: %d segments total, %d already complete (resume), %d to do; "
        "%d members already recorded"
        % (total_segs, len(completed), len(todo), len(members)), progress)

    startup_self_tests(progress, control_log)

    control_record = "gate1a=full-segment-verify PASS; gate1b=broken-variant FIRED"
    if todo:
        pool = mp.Pool(workers, initializer=worker_init, initargs=(control_log,))
        try:
            if not wait_for_shard_controls(control_log, workers, progress):
                pool.terminate()
                sys.exit(2)
            control_record += "; gate2=%d/%d shard controls PASS" % (workers, workers)
            done_this_run = 0
            t_loop = time.time()
            for res in pool.imap_unordered(worker_scan, todo, chunksize=1):
                if res[0] == "CONTROL_FAIL":
                    log("FATAL: worker pid=%d reported failed control mid-run "
                        "(seg %d) — aborting" % (res[2], res[1]), progress)
                    pool.terminate()
                    sys.exit(2)
                _, seg_idx, L, R, n, segmembers = res
                # Gate 3: independent confirmation BEFORE anything is recorded
                for (m, s, d, x) in segmembers:
                    if not confirm_member(m, s, d, x):
                        log("FATAL: SIEVE-VS-FACTORIZATION MISMATCH at m=%d "
                            "(sieve: sigma=%d d=%d x=%d, direct: sigma=%d) — aborting"
                            % (m, s, d, x, sigma_direct(m)), progress)
                        pool.terminate()
                        sys.exit(2)
                    if m not in members:
                        rec = {"m": m, "sigma": s, "d": d, "x": x,
                               "square": math.isqrt(m) ** 2 == m,
                               "seg": seg_idx, "confirmed": "direct-factorization"}
                        members[m] = rec
                        _append_line(members_path, json.dumps(rec) + "\n")
                        log("MEMBER m=%d sigma=%d d=%d x=%d square=%s (seg %d, confirmed)"
                            % (m, s, d, x, rec["square"], seg_idx), progress)
                # ledger append strictly AFTER member persistence
                _append_line(ledger, "SEG %d %d %d %d %d\n" % (seg_idx, L, R, n, len(segmembers)))
                completed[seg_idx] = n
                done_this_run += 1
                if done_this_run % heartbeat_every == 0 or len(completed) == total_segs:
                    rate = done_this_run / (time.time() - t_loop)
                    remaining = total_segs - len(completed)
                    eta_h = remaining / rate / 3600 if rate > 0 else float("inf")
                    log("HEARTBEAT segments %d/%d (this run: %d, %.2f seg/s) "
                        "ETA %.2f h, members so far: %d"
                        % (len(completed), total_segs, done_this_run, rate,
                           eta_h, len(members)), progress)
            pool.close()
            pool.join()
        except KeyboardInterrupt:
            pool.terminate()
            raise
    else:
        log("nothing to do: all segments already complete", progress)
        control_record += "; gate2=skipped (no segments to run)"

    if len(completed) != total_segs:
        log("INCOMPLETE: %d/%d segments — do not report results"
            % (len(completed), total_segs), progress)
        sys.exit(2)

    total_odd = sum(completed.values())
    final = sorted(members)
    wall = time.time() - t_start
    log("DONE range=(%d, %d] total_odd_tested=%d segments=%d members=%d "
        "wall_this_invocation=%.1fs positive_controls=[%s] member_list=%s"
        % (A, B, total_odd, total_segs, len(final), wall, control_record,
           ",".join(str(m) for m in final)), progress)
    return final, members


def oeis_crosscheck(A, B, found, progress):
    """Compare found members against the published A222263 b-file within (A, B]."""
    if not os.path.exists(B_FILE):
        log("VALIDATION FATAL: %s missing — download "
            "https://oeis.org/A222263/b222263.txt first" % B_FILE, progress)
        sys.exit(2)
    expected = []
    with open(B_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            a = int(line.split()[1])
            if A < a <= B:
                expected.append(a)
    expected.sort()
    missing = sorted(set(expected) - set(found))
    extra = sorted(set(found) - set(expected))
    log("OEIS cross-check (A222263 b-file) on (%d, %d]: expected %d, found %d, "
        "missing %r, extra %r"
        % (A, B, len(expected), len(found), missing, extra), progress)
    if missing or extra:
        log("VALIDATION FAIL", progress)
        sys.exit(1)
    log("VALIDATION PASS: published members recovered exactly", progress)


def main():
    ap = argparse.ArgumentParser(description="W1: all of Toth's S for odd m in (A, B]")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--production", action="store_true",
                   help="range (1e12, 1e13], default 48 workers (sf1, COMPLETE)")
    g.add_argument("--production2", action="store_true",
                   help="range (1e13, 1e14], default 48 workers (sf2)")
    g.add_argument("--validate", action="store_true",
                   help="range (1e9, 2e9] + OEIS A222263 b-file cross-check")
    g.add_argument("--range", nargs=2, type=int, metavar=("A", "B"),
                   help="custom range (A, B] (smoke tests)")
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--state-dir", default=None)
    ap.add_argument("--heartbeat-every", type=int, default=250)
    args = ap.parse_args()

    base = os.path.dirname(os.path.abspath(__file__))
    if args.production:
        A, B = 10 ** 12, 10 ** 13
        workers = args.workers or 48
        state = args.state_dir or os.path.join(base, "state", "production")
        mode = "production"
    elif args.production2:
        A, B = 10 ** 13, 10 ** 14
        workers = args.workers or 48
        state = args.state_dir or os.path.join(base, "state", "production2")
        mode = "production2"
    elif args.validate:
        A, B = 10 ** 9, 2 * 10 ** 9
        workers = args.workers or 8
        state = args.state_dir or os.path.join(base, "state", "validate")
        mode = "validate"
    else:
        A, B = args.range
        workers = args.workers or 4
        state = args.state_dir or os.path.join(base, "state", "range_%d_%d" % (A, B))
        mode = "range"
    if workers > 48:
        print("FATAL: charter caps workers at 48")
        sys.exit(2)

    found, _ = run(A, B, workers, state, args.heartbeat_every, mode)
    if args.validate:
        oeis_crosscheck(A, B, found, os.path.join(state, "progress.log"))


if __name__ == "__main__":
    main()
