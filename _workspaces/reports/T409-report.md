# T409 Report — E11.2: Atomic & Memory-Ordering Litmus Conformance Suite

## Summary

Delivered the complete `E11.2` atomic and memory-ordering litmus conformance suite in `tests/conformance/p11/e11_2_atomics/` per `spec/SPEC-31-atomics.md`, verifying all `AXS-ATM-*` rules (`AXS-ATM-001`..`066`), invariants (`INV-ATM-001`..`005`, `INV-CONC-005`..`007`, `INV-ORACLE-001`..`002`), and `T409` requirements (`REQ-CONC-076`..`079`, `REQ-ATM-028`..`030`, plus upstream `T405`–`T408` contracts) across the MIR interpreter oracle (`[interp]`), baseline native x86-64 (`[native]`), and `-O1` optimized native x86-64 (`[native-O1]`):

1. **Traceability Documentation (`README.md`)**:
   - Comprehensive inventory and requirement matrix covering all 15 files in `tests/conformance/p11/e11_2_atomics/` mapped to `SPEC-31` rules (`AXS-ATM-001`..`066`), invariants, and `E11.2` requirements (`REQ-CONC-076`..`079`, `REQ-ATM-028`..`030`).
2. **Normative Litmus Conformance Tests (`modes: interp native`, running `[interp]`, `[native]`, `[native-O1]`)**:
   - `litmus_mp_acquire_release_and_fences.ax`: `LITMUS-MP` (`AXS-ATM-061`) and `LITMUS-MP-FENCE` (`AXS-ATM-062`) covering `Release`/`Acquire` message passing, Fence-to-Fence (`fence(Release)` + `Relaxed` store / `Relaxed` load + `fence(Acquire)`), Fence-to-Atomic, Atomic-to-Fence, `compiler_fence`, and Release-Sequence RMW (`fetch_add(Relaxed)`) chains.
   - `litmus_sb_seq_cst.ax`: `LITMUS-SB` (`AXS-ATM-063(1)`) covering 32-bit and 64-bit `SeqCst` Store Buffering, `Relaxed` stores/loads separated by `fence(Ordering.SeqCst)`, and Dekker mutual exclusion proving the weak outcome `(r0 == 0 && r1 == 0)` never occurs (`r0 + r1 >= 1`).
   - `litmus_lb_and_coherence.ax`: `LITMUS-LB` (`AXS-ATM-064`) covering Load Buffering (`Acquire`/`Release` and `Relaxed`) no-out-of-thin-air (`OOTA`) guarantees and all four per-location modification-order coherence axioms (`CoRR`, `CoWR`, `CoWW`, `CoRW`) across deterministic oracle schedule seeds `1..24`.
   - `litmus_rmw_counter_wrapping_and_spinlock.ax`: `LITMUS-RMW` (`AXS-ATM-065`) covering lossless concurrent `fetch_add` counters with unique old-value bitmask verification, wrapping two's-complement overflow/underflow across `u8`, `u16`, `u32`, `u64`, `usize`, `i8`, `i16`, `i32`, `i64`, `isize`, bitwise RMW (`fetch_and`, `fetch_or`, `fetch_xor`, `swap`) on `bool` and integers, `is_lock_free<T>()`, and Spinlock mutual exclusion (`compare_exchange_weak` + `spin_loop_hint` + `store(Release)`).
   - `litmus_cas_retry_and_aba.ax`: `LITMUS-CAS-ABA` (`AXS-ATM-066`) covering strong `compare_exchange` non-spurious first-attempt success (`REQ-ATM-018`), `compare_exchange_weak` retry loops converging under oracle deterministic spurious failures (`AXS-ATM-054`, `REQ-ATM-019`), unmitigated raw-value ABA behavior (`REQ-CONC-076`, `REQ-ATM-030`), and packed `(tag: u32, index: u32)` ABA prevention in `Atomic<u64>` (`REQ-CONC-079`).
   - `litmus_atomic_ptr_tagged_epoch.ax`: Raw-pointer `Atomic<*mut T>` (`AXS-ATM-008`, `REQ-CONC-076`..`079`, `REQ-ATM-028`..`030`) verifying address-only atomicity without implicit pointee lifetime/ownership or automatic reclamation, encapsulated lock-free `NodeArena` Treiber stack with generation tags and explicit retirement epochs, and concurrent `Release`/`Acquire` pointer publication.
3. **QA Conformance Boundary Suites (Addressing Finding 3 of Round 0, verified under T429 fixes)**:
   - `qa_signed_cas_const_ptr_and_sb_relaxed.ax`: Conformance verification of width-exact sub-64-bit atomics in contiguous arrays (`[8]AtomicBool`, `[8]AtomicU8`, `[4]AtomicU16`, `[2]AtomicU32`) proving no neighboring byte corruption under `SeqCst XCHG`, `LOCK XADD`, bitwise RMW loop, and `LOCK CMPXCHG` (`AXS-ATM-005`); signed negative CAS and bitwise RMW across `i8`, `i16`, `i32`, `i64`, `isize` (`AXS-ATM-010`, `AXS-ATM-018`); `Atomic<*const T>` address-only atomicity (`AXS-ATM-008`); `LITMUS-SB` under `Ordering.Relaxed` (`AXS-ATM-063(2)`); and uniquely owned `Atomic<T>` move into `into_inner()` (`AXS-ATM-012(2)`).
   - `qa_struct_embedded_atomics_and_view_methods.ax`: Conformance verification of embedding `Atomic<T>` and prelude aliases (`AtomicBool`, `AtomicU8`, `AtomicU16`, `AtomicU32`, `Atomic<u64>`, `Atomic<*mut u64>`) as fields inside a user `struct` alongside non-atomic guard fields (`AXS-ATM-010`, `AXS-ATM-012`), direct atomic method dispatch on struct fields, passing struct fields as `view<AtomicBool>` / `view<AtomicU32>` to helper functions in the same translation unit, and ensuring non-atomic neighboring fields remain uncorrupted (`INV-ATM-002`, `INV-CONC-006`).
4. **Oracle UB & Compile-Time Negative Conformance Tests**:
   - `oracle_race_mp_relaxed_ub.ax` (`modes: interp`, `exit: 125`): Deterministic oracle detection (`AX_UNSAFE_INTERP_UB`) of unsynchronized ordinary payload access when Message Passing uses `Ordering.Relaxed` without fences.
   - `oracle_race_mixed_atomic_ordinary_ub.ax` (`modes: interp`, `exit: 125`): Deterministic oracle detection (`AX_UNSAFE_INTERP_UB`) of concurrent mixed atomic (`AtomicU64.store`) and ordinary (`*raw = ...`) writes to the same location.
   - `oracle_ub_misaligned_atomic_ptr.ax` (`modes: interp`, `exit: 125`): Deterministic oracle detection (`AX_UNSAFE_INTERP_UB`) of unaligned `*mut Atomic<u64>` load access.
   - `ui_atomic_type_align_ordering_and_mut_view.ax` (`test: ui`): Compile-time rejection of invalid atomic payload types (`AX_CONC_INVALID_ATOMIC_TYPE`), arithmetic RMW on `AtomicBool` and `Atomic<*mut T>`, packed/under-aligned atomics (`AX_CONC_INVALID_ATOMIC_ALIGNMENT`), inner `mut_view` or `.v` field projection (`AX_CONC_ATOMIC_MUT_VIEW`), and illegal/non-constant memory orderings (`AX_CONC_INVALID_ATOMIC_ORDERING`).
   - `mir_atomic_opt_and_lowering.ax` (`.test`): Verifies `MIR_STMT_ATOMIC` lowering and `-O1` optimizer preservation across all 13 atomic statement kinds.

## Verification

- `cd build-snap-T409; python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal conformance/p11/e11_2_atomics`:
  `WEAK-NATIVE 0`, `TOTAL 29 PASS 29 FAIL 0 SKIP 0 XFAIL 0`.
- Related concurrency, atomics, and T134 canary suites:
  `cd build-snap-T409; python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax encode/atomics lir/atomics mir/atomics run/atomics run/concurrency ui/concurrency/atomics`:
  `WEAK-NATIVE 0`, `TOTAL 66 PASS 66 FAIL 0 SKIP 0 XFAIL 0`.
- Step 4a Native-evidence liveness check:
  Mutated `stdout:` expectation of `litmus_mp_acquire_release_and_fences.ax` in snapshot, observed native failure (`FAIL [native]: stdout differs at byte 11`), and restored via `taskctl.py snapshot T409`.
- `python build-snap-T409/tools/archcheck.py --root build-snap-T409`:
  `archcheck: 208 files scanned, 0 violations` (exit 0).
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`:
  `requirements: 32308`, `gaps: 0`, `COVERAGE OK` (exit 0).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`:
  `HARNESS OK` (exit 0).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T409`:
  `0 REFUSED` (exit 0).

## Files changed

- tests/conformance/p11/e11_2_atomics/README.md
- tests/conformance/p11/e11_2_atomics/litmus_atomic_ptr_tagged_epoch.ax
- tests/conformance/p11/e11_2_atomics/litmus_cas_retry_and_aba.ax
- tests/conformance/p11/e11_2_atomics/litmus_lb_and_coherence.ax
- tests/conformance/p11/e11_2_atomics/litmus_mp_acquire_release_and_fences.ax
- tests/conformance/p11/e11_2_atomics/litmus_rmw_counter_wrapping_and_spinlock.ax
- tests/conformance/p11/e11_2_atomics/litmus_sb_seq_cst.ax
- tests/conformance/p11/e11_2_atomics/mir_atomic_opt_and_lowering.ax
- tests/conformance/p11/e11_2_atomics/mir_atomic_opt_and_lowering.test
- tests/conformance/p11/e11_2_atomics/oracle_race_mixed_atomic_ordinary_ub.ax
- tests/conformance/p11/e11_2_atomics/oracle_race_mp_relaxed_ub.ax
- tests/conformance/p11/e11_2_atomics/oracle_ub_misaligned_atomic_ptr.ax
- tests/conformance/p11/e11_2_atomics/qa_signed_cas_const_ptr_and_sb_relaxed.ax
- tests/conformance/p11/e11_2_atomics/qa_struct_embedded_atomics_and_view_methods.ax
- tests/conformance/p11/e11_2_atomics/ui_atomic_type_align_ordering_and_mut_view.ax

## Spec deviations

none

## Follow-ups

none

STATUS: COMPLETE round=0
