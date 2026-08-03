# SUCCESSOR-DIRECTIVE — dose lineage handover to hub operator
Written 2026-08-03T15:1xZ by the interactive session (d1 lineage owner).
Per COORDINATION rule 6: the operator now OWNS the Lab 3 dose-* lineage
successor. Charter: ~/archlab3/LAB3-CHARTER.md (P1 section). Do not wait for
further interactive input.

## P0 outcome you are inheriting (decision.json in this dir)
- P0 PASS: controls all pass; 0/6 sustained dead-zone per capability; both
  8%-dose recall runs land ON the analytic ceiling (0.468/0.475 vs 0.4769).
- Capability-dependent thresholds confirmed: state transitions at 0.5% dose,
  recall floors at 2% and transitions by 8% (lr 1e-3).
- PRE-REGISTERED TRIPWIRE FIRED: lr 3e-3 at 2% dose = 1 HIGH + 1 dead-zone
  (vs lr 1e-3 both floor) => dose threshold is LR-modulated. Per P0-PREREG:
  NO P1 promotion without an LR-CROSSED design. This is binding.
- Timing arm UNINFORMATIVE (placed at sub-threshold 2%; all schedules floor).
  Rerun timing at a transitioning dose inside P1.

## P1 requirements (charter + the above)
1. LR-crossed dose grid: dose {0.5,1,2,4,8}% x lr {1e-3,3e-3} x 2 seeds per
   capability (recall + state; 2-hop as workload only if budget allows).
   Seeds 3002+ (ledger this dir + charter range 3000-3999).
2. Fit H1 (fraction x tokens = N*) vs H2 (d* . C^alpha = k): needs >=2
   compute budgets on at least a dose subset — include a half-budget row.
3. SEAL held-out (fraction, capability, lr) cell predictions in the public
   ledger BEFORE those cells train (ap-style; GitHub timestamp).
4. Controls-first barrier, fresh salt, harness archived at launch — clone
   the d1 pattern (harness/ in this dir; queue_runner controls gate).
5. Suffix d2 (already lockfile-claimed). Campaign ~/archlab3-runs/dose-*-d2.

## GPU gating (binding, charter priority rules)
- Wait until chain_qwen_mistral.sh is DONE (no run_audit.py process and
  ~/archlab-audit-sweep/chain_restart_20260803T15.log shows mistral audit OK
  or TERMINAL) before taking GPU 3.
- GPU 2 usable ONLY after the p1e wave-B verdict is scored (your standing
  instruction) — p1e scoring takes priority the moment P1E_COMPLETE_B lands.
- Yield to Lab 1/2 on any contention (pause-checkpoint, never compete).
- The audit1 campaign (Qwen/Mistral arms) is interactive-owned: when its
  chain finishes, fold results into AUDIT-TABLE.md is NOT your job — leave it.

## Working dirs
~/archlab-d1/ and ~/archlab-cs1/ remain build-agent-owned archives — read-
only for you. Create ~/archlab-d2/ fresh as your own.
