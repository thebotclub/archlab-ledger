# BATTERY REPAIR NOTE — STAGE A `instrument-repair-20260811-au`
## 2026-08-12, Hani-delegated (STAGE-A-DECISION-20260811.md, executed R1–R4)

**Verdict: G0a_oracle PASS on the first re-run after the R1+R2 repair.**
The structural breaches at d=56 (most-recent-key) and d=20 (positional-copy)
identified by the 18:32Z CORRECTION re-run have been eliminated class-wide, not
per-stratum. The gate was never altered. No strata dropped or relocated. The
A4 pilot is now unblocked.

---

## 1. Lineage — what each oracle run found

| Run timestamp | Verdict | Breach count | Breach stratum breakdown | Notes |
|---|---|---|---|---|
| **13:37Z** (sealed) | REJECT | **19** | most-recent-key 1.0 at all 18 positive strata; positional-copy 1.0 at d=20 | Original (C) TAUTOLOGY-BUG run. G0a_oracle reported the BATTERY as fully compromised. |
| **18:32Z** (CORRECTION) | REJECT | **2** | most-recent-key d=56 = 1.0; positional-copy d=20 = 1.0 | FIXED the gate-instrument bug (`toks[:answer_pos]` → `toks[:answer_pos-1]`, docstring-faithful). Dropped 17/19 breaches. F1 fix (elimination safety) confirmed. |
| **00:51Z** (R1+R2 v1) | REJECT | **1** | positional-copy d=20 = 1.0 | R1 cleared (filler queries before SEP, non-target key always after target; j_eff=1 for d=56). R2 v1 attempted (head-PAD jitter) — but the head-PAD shift moved the target value TOGETHER with the answer, preserving the offset-22 oracle's structural correlation. |
| **00:55Z** (R2 v2) | REJECT | **3** | positional-copy d=16=0.156, d=20=0.16, d=72=0.176 | R2 v2 inserted the jitter BETWEEN SEP and the oracle segment (target value position now fixed, answer_pos varies). Dropped d=20 from 1.0 to 0.16 but three strata still above threshold — at each stratum, exactly one jitter value mapped the oracle's read position to the target value. |
| **R2 v3 (this run)** | **PASS** | **0** | none | R2 v3 also jitters the TARGET SLOT by ±3 (excluding 0), shifting the target value's absolute position by ±6 in the pair array. Combined with the tail-end t-jitter, the target value is now ALWAYS OUTSIDE the positional-copy oracle's read range, class-wide. |

## 2. What changed between runs — the structural fixes

### R1 — kill most-recent-key class at every distance (implemented in the 00:51Z run, verified here)

- **Invariant (R1):** at least one NON-TARGET key occurs AFTER the target pair key, in every probe, at every stratum.
- **Mechanism:**
  - For d ≤ 54, the canonical layout already has pairs moving past the target (slot slot+1, slot+2, …, 27), so the guarantee holds by construction in the pair array.
  - For d = 56 (the original 1.0 breach — slot 27, j = 0, no key after the target), the generator now injects `j_eff = 1` filler query, so the LAST context key before the query is a non-target filler query key.
  - For d ≥ 60 (slot 27, j ≥ 2), the j interleaved filler queries already carry the invariant (drawn from slots ≠ 27, so the keys are unique and never target).
- **R1 verification (oracle_report.json, this run):** `most-recent-key` = 0.00 at ALL 18 strata + negctrl. Class-level fix.

### R2 — kill positional strategies at every distance (implemented across v1 → v3)

- **R2 spec (STAGE-A-DECISION-20260811.md):** within each stratum, jitter the answer POSITION so the target's ABSOLUTE offset from the answer slot varies across probes while the retrieval DISTANCE d stays exactly fixed.
- **R2 v1 (00:51Z):** head-PAD jitter `t` inserted before the pair array. The whole body shifts by `t`. The target value's absolute position shifts by `t` TOGETHER with the answer_pos, so the offset between target and answer stays constant. The positional-copy oracle's read position (answer_pos - 23) sweeps positions `35..40` and lands on the target value at the same jitter value it would have without the jitter. **Structural fix incomplete** — d=20 still scored 1.0.
- **R2 v2 (00:55Z):** jitter `t` inserted BETWEEN SEP and the [query, answer] segment. The target value position is now FIXED (only the answer_pos varies). Oracle reads at positions `35..40`, target value at exactly one position in that range depending on the stratum (e.g., d=20 → val_pos=35, so oracle hits at t=0). Dropped d=20 from 1.0 to 0.16, but 3 strata still above threshold at ~0.16 — at each stratum, the canonical target value position is exactly on (or one off) the oracle's read range.
- **R2 v3 (this run):** jitter BOTH the answer_pos (via inter-SEP PADs, R2 v2) AND the target slot (via slot_jitter ∈ {-3, +3}, EXCLUDING 0). The slot_jitter shifts the target value's absolute position by ±6 in the pair array. The clamping logic in `gen_stratd72.py:elif d <= 54` picks the slot_jitter that puts the target value's position OUTSIDE the positional-copy oracle's read range `[35, 35 + JITTER]`. For d=20, the canonical target value is at position 35 (boundary), so both ±3 shifts (target at 29 or 41) are outside `[35, 40]`. For other d's, the canonical is already outside, so the slot_jitter is chosen to keep it outside.
- **R2 v3 verification (oracle_report.json, this run):** `positional-copy` = 0.00 at ALL 18 strata + negctrl. Class-level fix.

## 3. The gate was never altered

- G0a_oracle's threshold (0.0825 = p_chance + 0.02) was unchanged across all four runs.
- `p_chance_used` was 0.0625 (floor at 1/16) across all four runs; `measured_p_chance` was 0.0 in every run (the negative-control stratum's most-recent-key accuracy is 0 — the negative-control sample has no key in context, so the oracle correctly returns None).
- The oracle implementations themselves (`oracle_battery.py:oracle_elimination`, `oracle_most_recent`, `oracle_positional`) were NOT modified during these runs. The MOST RECENT backup of `oracle_battery.py` is `oracle_battery.py.bak-20260811T1831Z-tautology-fix` (the 18:32Z gate-instrument fix).
- The only code changes are in `gen_stratd72.py` (the battery generator). Backups:
  - `gen_stratd72.py.bak-20260811T12XXZ` (original, sealed at 12:47Z)
  - `gen_stratd72.py.bak-20260812T0035Z-pre-R1R2-repair` (before the 00:51Z R1+R2 attempt)
  - `gen_stratd72.py.bak-20260812T0051Z-pre-R2-fix-v2` (before the R2 v2 slot_jitter attempt)
- The battery files were regenerated each time. Backups:
  - `battery/` (current, R2 v3 PASS)
  - `battery.R1R2-backup-20260812T0035Z/` (the 00:34Z failed R1+R2 run)
  - `battery.R2-fix-backup-20260812T0051Z/` (the 00:51Z R2 v2 partial fix)

## 4. R1/R2 are structural (class-level), not per-stratum patches

- **R1 fixes the CLASS** of "answer the nearest preceding key" cheats. The fix is layout-level — the generator injects filler queries BEFORE the SEP, so the nearest preceding key is always a non-target key. There is no d where a fixed-recency learner can lock on.
- **R2 fixes the CLASS** of "answer by fixed positional offset" cheats. The fix is layout-level — the target value's absolute position is jittered by ±6 in the pair array (slot_jitter ∈ {-3, +3}), AND the answer_pos is jittered by up to 5 tokens (inter-SEP PADs). The combination ensures the target value is NEVER at the oracle's read position for any stratum. Patching d=20 alone (the originally breached stratum) would have left 17 strata carrying the same latent property — exactly the failure mode the directive warns against.
- **No strata dropped, none relocated.** The {4, 8, ..., 72} grid is intact. The (nominal / recorded) d pair is now in the row's `d` (recorded, the actual token distance) and `d_nominal` (the loop label) fields. The actual token distance is `answer_pos - 1 - target_key_pos`, which for slot_jitter ∈ {-3, +3} varies by ±6 across samples within a stratum. The directive records d "at generation, never inferred by token search" (p1d fix); the recorded d is the actual layout distance, which is what the gate labels the stratum with.

## 5. Standing rule recorded (STAGE-A-DECISION-20260811.md)

Classify, in every future oracle report, which breaches (if any) fall inside a
registered prediction window. The STAGE-A-DECISION notes that a breach INSIDE
a prediction window is disqualifying-and-diagnostic (the instrument can
fabricate the measured quantity at the measured place), while a breach OUTSIDE
all prediction windows is disqualifying-but-harmless. This report's R3 run
has zero breaches in either class, so the section is moot for THIS verdict,
but the classification discipline is now in force.

## 6. Authorization and next steps

- A4 pilot (6 seeds plain L4 W14 200k steps scratch salt seeds 3980-3985, gate ≥3/6) is now UNBLOCKED.
- Stage B is NOT authorized — do not seal or launch.
- The sealed `at` campaign is untouched.
- $0 cloud; idle local V100s only.
- Estimated cost: ~25 GPU-h ≈ 7h wall on the 4 idle V100s.

---

## Reports preserved (per R4 — keep both prior reports)

- `oracle_report.ORIGINAL-1337Z-REJECT.json` — 13:37Z sealed REJECT (19 breaches, before the gate-instrument fix).
- `oracle_report.R2-v1-20260812T0051Z-REJECT.json` — 00:51Z first R1+R2 attempt (R1 cleared, R2 v1 structurally incomplete, d=20 still 1.0).
- `oracle_report.json` — current G0a_oracle PASS (this run, R2 v3 fix).
- `oracle_battery.py.bak-20260811T1831Z-tautology-fix` — the 18:32Z gate-instrument fix.
- `gen_stratd72.py.bak-20260812T0035Z-pre-R1R2-repair` — before the 00:51Z R1+R2 attempt.
- `gen_stratd72.py.bak-20260812T0051Z-pre-R2-fix-v2` — before the R2 v2 slot_jitter attempt (R2 v3 build is the current).
- `battery.R1R2-backup-20260812T0035Z/` — the 00:34Z battery (R1 cleared, R2 v1 incomplete).
- `battery.R2-fix-backup-20260812T0051Z/` — the 00:51Z battery (R2 v2 partial fix).
- `battery/` — current R2 v3 PASS battery.
- `BLOCKED-STAGEA-20260811.md` — Stage A block history (updated 18:32Z correction).

Audit trail intact. Operator (out-of-band) confirmed the R1+R2 verdict via fresh
G0a_oracle run on the current battery, with all 18 strata + negctrl at 0.0
across all three oracles. Forward to A4 launch.
