# T408 Report: E11.2 — Oracle Atomic Memory Model & Deterministic Schedule Explorer

STATUS: COMPLETE

## Summary

Implemented the `SPEC-31` §6 reference interpreter (`axiom0 run` / `axiomc run`) atomic memory model, vector-clock synchronization, ordinary/mixed data-race detector, deterministic schedule explorer, and deterministic `compare_exchange_weak` spurious-failure simulator across `compiler/interp/`, regenerated selfhost interpreter bundles, and added the `tests/run/concurrency/atomics_oracle/` verification suite.

### Key Changes
1. **Oracle Atomic Memory Model & Vector-Clock State (`compiler/interp/value.ax`, `compiler/interp/oracle.ax`)**:
   - Added `InterpVecClock`, `InterpAtomicWrite`, `InterpAtomicLoc`, `InterpOrdAccess`, and `InterpOracleState` on `InterpCtx`.
   - Maintained per-location modification order $H(X) = [W_0, W_1, \dots, W_k]$ (`AXS-ATM-050`) with coherence checks (read-read, write-read, write-write, read-write).
   - Implemented vector-clock acquire/release synchronization (`AXS-ATM-051`), release sequences across same-thread writes and arbitrary-thread RMW/CAS chains, standalone `fence` (`Acquire`, `Release`, `AcqRel`, `SeqCst`) and `compiler_fence` synchronization, and `SeqCst` total order ticks.
   - Implemented deterministic `compare_exchange_weak` spurious failure simulation (`AXS-ATM-054`) and wrapping two's-complement arithmetic (`fetch_add`, `fetch_sub`, `fetch_and`, `fetch_or`, `fetch_xor`, `swap`) across all legal atomic widths (`bool`, `u8..u64`, `i8..i64`, `usize`, `isize`, `*mut T`).
2. **Data-Race & Mixed-Access UB Detection (`compiler/interp/oracle.ax`, `compiler/interp/interp.ax`)**:
   - Tracked per-location ordinary read/write epochs and active atomic locations (`AXS-ATM-052`).
   - Reported `AX_UNSAFE_INTERP_UB` (exit code `125`) on unsynchronized ordinary read/write or write/write races across threads, mixed atomic and non-atomic memory access races, and misaligned/null/dangling atomic pointer dereferences (`AXS-ATM-025`).
3. **MIR Atomic Execution & Deterministic Schedule Explorer (`compiler/interp/frame.ax`, `compiler/interp/interp.ax`)**:
   - Implemented `exec_atomic_stmt` for `MIR_STMT_ATOMIC` (`MIR_ATOMIC_LOAD`, `MIR_ATOMIC_STORE`, `MIR_ATOMIC_SWAP..MIR_ATOMIC_XOR`, `MIR_ATOMIC_CMPXCHG`, `MIR_ATOMIC_CMPXCHG_WEAK`, `MIR_ATOMIC_FENCE`, `MIR_ATOMIC_COMPILER_FENCE`, `MIR_ATOMIC_SPIN_HINT`), including proper `CasResult<T>` field offset calculation via `type_field_offset`.
   - Added deterministic seeded PRNG (`xorshift64*`) schedule exploration (`AXS-ATM-053`) across concurrent thread closures when `spin_loop_hint()` or multi-invocation thread patterns execute.
4. **Self-Host Bundles & Verification Suite (`tests/selfhost/`, `tests/run/concurrency/atomics_oracle/`)**:
   - Regenerated `tests/selfhost/interp/*` and `tests/selfhost/interp_opt/*`.
   - Added 5 oracle concurrency & atomics tests in `tests/run/concurrency/atomics_oracle/` covering all atomic widths/ops, wrapping overflow, `compare_exchange_weak` retry loops, `Atomic<*mut T>`, message passing (`Release`/`Acquire` and fences), store buffering (`SeqCst` and fences), RMW release sequences, CAS spinlocks, unsynchronized ordinary data-race UB, mixed atomic/ordinary access UB, and misaligned atomic pointer UB.

## Verification

- Synchronized snapshot `build-snap-T408` via `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T408`.
- Built Stage 1 (`axiomc1.exe`) and Stage 2 (`build-snap-T408/build/axiomc2.exe`) via `python build-snap-T408/tools/build_axiomc.py --out build-snap-T408/build`.
- Executed verification suite with `-j 1`:
  ```
  python tools/axtest.py --compiler build-snap-T408/build/axiomc2.exe --root build-snap-T408 --build-dir build-snap-T408/build -j 1 --exclude-requires axiom0-internal run/concurrency/atomics_oracle run/concurrency/atomics_native mir/atomics selfhost/interp/bundles_current.test selfhost/interp_opt/bundles_current.test
  ```
  Result: `WEAK-NATIVE 0`, `TOTAL 19 PASS 19 FAIL 0 SKIP 0 XFAIL 0`.

## Files changed

- compiler/interp/frame.ax
- compiler/interp/interp.ax
- compiler/interp/oracle.ax
- compiler/interp/value.ax
- tests/run/concurrency/atomics_oracle/atomics_oracle_litmus.ax
- tests/run/concurrency/atomics_oracle/atomics_oracle_ops.ax
- tests/run/concurrency/atomics_oracle/race_mixed_atomic_ordinary.ax
- tests/run/concurrency/atomics_oracle/race_ordinary_unsync.ax
- tests/run/concurrency/atomics_oracle/ub_atomic_misaligned.ax
- tests/selfhost/interp/qa_interp_exec_a.ax
- tests/selfhost/interp/qa_interp_exec_b.ax
- tests/selfhost/interp/qa_interp_unit.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_unit.ax
