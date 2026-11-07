# T608 — E15.2 — Alias analysis, escape analysis & allocation promotion conformance suite

## Summary

Implemented the end-to-end differential conformance suite for Epic E15.2 (`SPEC-71`: Capability-Driven Alias Analysis, Escape Analysis & Allocation Promotion) under `tests/conformance/p15/e15_2_alias_escape/`.

The suite certifies all six requirements covered by `T608` (`REQ-OPT-307`, `REQ-OPT-308`, `REQ-OPT-309`, `REQ-OPT-310`, `REQ-OPT-385`, `REQ-OPT-386`) across the MIR interpreter (`--interp`) and standalone native AOT compilation (`-O0`, `-O1`, and `-O2 --verify-each`) with `0 WEAK-NATIVE`:

1. **Differential Conformance Programs (`// test: diff`, `--verify-each`) & `-O2 --verify-each` Native Run Companions (`// test: run`)**:
   - `alias_cap_forwarding_rle_dse.ax` + `o2_alias_cap_forwarding_rle_dse.ax`: Exercises capability-driven `NoAlias` (`mut_view<T>` vs `mut_view<T>`, `view<T>` vs `mut_view<T>`), store-to-load forwarding, redundant load elimination (`RLE`), dead store elimination (`DSE`), disjoint struct field projections vs dynamic array index clobbers, sequential reborrow chains, loop-backedge clobber barriers, and raw-pointer `MayAlias` barriers.
   - `escape_box_buffer_slot_promotion.ax` + `o2_escape_box_buffer_slot_promotion.ax`: Exercises `NoEscape` `Box<T>` scalar and aggregate `SROA` elimination (preserving `p as usize != 0` non-null invariants), `ArgumentEscape` stack promotion across mutually recursive SCCs (`scc_even_accumulate` / `scc_odd_accumulate`), bounded inline buffer (`heap_alloc(64, 8)` + `heap_free`) and `Vec<i64>` promotion, and disjoint-lifetime stack slot reuse (`slot_alpha`, `slot_beta`, `slot_gamma`).
   - `closure_signature_capture_promotion.ax` + `o2_closure_signature_capture_promotion.ax`: Exercises explicit closure parameter and return type signatures (`|x: i64, slope: i64| -> i64`, `|v: i64| -> i64`, `|| -> i64`), all four capture modes (`CAP_COPY`, `CAP_VIEW`, `CAP_MUT_VIEW`, `CAP_MOVE`), generic `Fn` / `FnMut` dispatch, sequential mutable capture lifetimes, and `NoEscape` closure environment promotion.
   - `nrvo_return_slot_and_drop_parity.ax` + `o2_nrvo_return_slot_and_drop_parity.ax`: Exercises single-local aggregate struct `NRVO` (`build_nrvo_frame`), multi-branch array `NRVO` (`build_branching_nrvo_digest`), conflicting two-local `NRVO` rejection (`build_conflicting_two_locals`), and deterministic reverse-declaration (`LIFO`) `Drop` ordering across nested scopes and `BoxGuard` payload drops (`drop_lifo_trace=1234`).
   - `stable_address_and_escape_barriers.ax` + `o2_stable_address_and_escape_barriers.ax`: Exercises pointer identity comparison between distinct `Box<i64>` allocations (`(b1.ptr as usize) == (b2.ptr as usize)`), stable-address observation via `address_of` / `address_of_mut` and pointer-to-integer distance/alignment checks, `GlobalEscape` via `mut_view<PtrSink>`, loop-carried heap allocations across loop backedges, oversized (`5120 B > 4096 B`) frame-budget heap retention, and `ptr_copy` overlapping/non-overlapping memory barriers.

2. **Compile-Time Closure Capability UI Diagnostics (`// test: ui`, `REQ-OPT-386`)**:
   - `closure_cap_conflict_mut_ui.ax`: Verifies that capturing a local by mutable borrow (`CAP_MUT_VIEW`) inside a closure while an outer `view` borrow is still active emits `AX_CAP_CONFLICT_MUT`.
   - `closure_cap_move_conflict_ui.ax`: Verifies that reading a non-`Copy` owner after a closure captures it by `CAP_MOVE` emits `AX_MOVE_USE_AFTER_MOVE`.

3. **6-Module Standalone AOT Conformance Probe & Oracle (`e15_2_conformance.test`, `e15_2_conformance_oracle.py`, `e15_2_conformance_probe.ax.in`)**:
   - Bundles `CORE_MODULES` together with `compiler.own.cap`, `compiler.opt.alias`, `compiler.opt.memopt`, and `compiler.opt.escape` into a standalone AOT binary compiled and executed under `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each`.
   - Verifies 41 MIR blobs (`0..32` from `ESCAPE_PROBE_BLOBS`, `33..37` from `ALIAS_PROBE_BLOBS`, and `38..40` from `CAP_PROBE_BLOBS`) covering:
     - Stage 1 (`PROBE_E15_2_ALIAS_AND_MEMOPT=OK`): `AliasResult` (`NoAlias`, `MayAlias`, `MustAlias`, `PartialAlias`), `RegionRelation`, `AliasReason`, `MemDependence`, store-to-load forwarding, `RLE`, `DSE`, `memcpy` -> `memmove` overlap rewrite, volatile/atomic/zeroize/black_box/fixed-MMIO/zero-copy pin barriers, loop-backedge clobber safety, and deterministic `alias_print` / `memopt_print`.
     - Stage 2 (`PROBE_E15_2_CLOSURE_SIGNATURE_AND_CAP=OK`): `TY_CLOSURE` type interning (`intern_type`, `type_get`, `capture_at`) with explicit `param_types`, `ret_type`, and `captures` (`CAP_COPY`, `CAP_VIEW`, `CAP_MUT_VIEW`, `CAP_MOVE`) (`REQ-OPT-385`), plus `mir_cap_tracker_check_conflict` and `own_cap_check` (`AX_CAP_CONFLICT_MUT`, `AX_CAP_CONFLICT_READ`, and conflict-free sequential borrows) (`REQ-OPT-386`).
     - Stage 3 (`PROBE_E15_2_ESCAPE_LATTICE_SCC_AND_BARRIERS=OK`): `EscapeClass` 4-point lattice (`NoEscape < ArgumentEscape < ReturnEscape < GlobalEscape`), `ESC_*` bitset join/inclusion laws, all 10 escape & stable-address barriers, and Tarjan SCC fixed-point interprocedural summary propagation across mutually recursive functions.
     - Stage 4 (`PROBE_E15_2_PROMOTIONS_NRVO_AND_ROLLBACK=OK`): All 6 promotion transforms (`Box<T>` SROA, `Box<T>` stack promotion, closure environment scalarization + direct call rewrite, bounded inline buffer promotion, `NRVO`, and disjoint stack slot reuse), QA soundness regressions (nested `Box<Box<T>>` deref escape, `PtrToPtr` cast escape, multi-alloc non-coalescing, caller `sret` destination synthesis, `Drop` order preservation, and conflicting-return `NRVO` rejection), atomic `PassManager` rollback on postcondition fault, and byte-identical `escape_print` / `escape_promote_print` output.

## Requirement Coverage Matrix

| Requirement | Specification Anchor (`SPEC-71`) | Conformance Tests & Probe Stages |
|---|---|---|
| `REQ-OPT-307` | Heap-to-stack / SROA promotion preserves drop order, panic behavior, and pointer identity / non-null invariants | `escape_box_buffer_slot_promotion.ax`, `nrvo_return_slot_and_drop_parity.ax`, `stable_address_and_escape_barriers.ax`, `e15_2_conformance_probe.ax.in` (Blobs `0, 1, 11, 13, 14..32`) |
| `REQ-OPT-308` | Stable-address observation (`address_of`, `address_of_mut`, `PtrToInt`, FFI, pinned/MMIO/volatile/atomic) blocks invalid relocation | `alias_cap_forwarding_rle_dse.ax`, `stable_address_and_escape_barriers.ax`, `e15_2_conformance_probe.ax.in` (Blobs `1, 19, 23, 26, 27, 33, 35`) |
| `REQ-OPT-309` | Closure environment stack/register promotion and direct call devirtualization for non-escaping closures | `closure_signature_capture_promotion.ax`, `e15_2_conformance_probe.ax.in` (Blobs `12, 24`) |
| `REQ-OPT-310` | Caller-allocated return slot (`NRVO` / `sret`) elides redundant aggregate copies without altering observable state or aliasing | `nrvo_return_slot_and_drop_parity.ax`, `e15_2_conformance_probe.ax.in` (Blobs `13, 21, 22, 25, 31, 32`) |
| `REQ-OPT-385` | Closure semantic representation in `THIR`/`MIR` preserves explicit parameter types, return type, and capture list | `closure_signature_capture_promotion.ax`, `e15_2_conformance_probe.ax.in` (`verify_e15_2_closure_signature_and_cap`) |
| `REQ-OPT-386` | Closure captures obey Axiom capability rules (`view`, `mut_view`, `move`, `Copy`) in `compiler/own` | `closure_cap_conflict_mut_ui.ax`, `closure_cap_move_conflict_ui.ax`, `closure_signature_capture_promotion.ax`, `e15_2_conformance_probe.ax.in` (Blobs `38, 39, 40`) |

## Verification & Live Native Mutation Evidence

1. **Snapshot Stage-2 Build**:
   - Built `axiom0.exe` (Release) and Stage-2 `axiomc2.exe` in `build-snap-T608/build`:
     `BUILD-AXIOMC OK: D:\projects\compiler\new lang\build-snap-T608\build\axiomc2.exe size=6334464 sha256=15086a66d9926d321e4ff36edef002a33e91445f9bbf591b4ffd94ea1bdfabfb`
2. **E15.2 Conformance Suite Execution**:
   - Command:
     `python build-snap-T608/tools/axtest.py --root build-snap-T608 --compiler build-snap-T608/build/axiomc2.exe --build-dir build-snap-T608/build --exclude-requires axiom0-internal -j 1 --verbose conformance/p15/e15_2_alias_escape`
   - Result: `TOTAL 18 PASS 18 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`).
3. **Live Native Mutation Verification**:
   - Mutated expected stdout (`checksum=2318` -> `checksum=9999`) in `build-snap-T608/tests/conformance/p15/e15_2_alias_escape/o2_alias_cap_forwarding_rle_dse.ax` and ran `axtest.py`: confirmed `[native]` failed with `stdout differs at byte 147`.
   - Mutated live read-only input (`let ro: i64 = 40;` -> `let ro: i64 = 41;`) in `build-snap-T608/tests/conformance/p15/e15_2_alias_escape/alias_cap_forwarding_rle_dse.ax` and ran `o2_alias_cap_forwarding_rle_dse.ax`: confirmed `[native]` failed with `exit code 1, expected 0`.
   - Mutated overwritten dead-store initializer (`let mut a: i64 = 1;` -> `let mut a: i64 = 10;`): confirmed `[native]` still passed (`245`), demonstrating dead-store invariance when `*a` is overwritten before any read.
   - Restored snapshot via `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T608` and re-verified `TOTAL 2 PASS 2 FAIL 0`.
4. **Architecture & Line-Ending Hygiene**:
   - `python build-snap-T608/tools/archcheck.py --root build-snap-T608`: `193 files scanned, 0 violations`.
   - All 15 files under `tests/conformance/p15/e15_2_alias_escape/` and this report use LF-only (`\n`) line endings (`0` `\r` bytes).

## Files changed

- tests/conformance/p15/e15_2_alias_escape/alias_cap_forwarding_rle_dse.ax
- tests/conformance/p15/e15_2_alias_escape/closure_cap_conflict_mut_ui.ax
- tests/conformance/p15/e15_2_alias_escape/closure_cap_move_conflict_ui.ax
- tests/conformance/p15/e15_2_alias_escape/closure_signature_capture_promotion.ax
- tests/conformance/p15/e15_2_alias_escape/e15_2_conformance.test
- tests/conformance/p15/e15_2_alias_escape/e15_2_conformance_oracle.py
- tests/conformance/p15/e15_2_alias_escape/e15_2_conformance_probe.ax.in
- tests/conformance/p15/e15_2_alias_escape/escape_box_buffer_slot_promotion.ax
- tests/conformance/p15/e15_2_alias_escape/nrvo_return_slot_and_drop_parity.ax
- tests/conformance/p15/e15_2_alias_escape/o2_alias_cap_forwarding_rle_dse.ax
- tests/conformance/p15/e15_2_alias_escape/o2_closure_signature_capture_promotion.ax
- tests/conformance/p15/e15_2_alias_escape/o2_escape_box_buffer_slot_promotion.ax
- tests/conformance/p15/e15_2_alias_escape/o2_nrvo_return_slot_and_drop_parity.ax
- tests/conformance/p15/e15_2_alias_escape/o2_stable_address_and_escape_barriers.ax
- tests/conformance/p15/e15_2_alias_escape/stable_address_and_escape_barriers.ax

STATUS: COMPLETE round=0
