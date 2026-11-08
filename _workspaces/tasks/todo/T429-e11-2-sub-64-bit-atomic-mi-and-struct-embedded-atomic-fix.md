---
id: T429
title: E11.2 — Sub-64-bit atomic MI size preservation & struct-embedded Atomic<T> prelude resolution
phase: P11-concurrency-async
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T407, T408]
priority: 129
status: todo
attempts: 0
paths: [compiler/driver/pipeline.ax, compiler/types/typeck.ax, tests/run/atomics]
locks: [tests/selfhost]
spec: [spec/SPEC-31-atomics.md]
covers: [REQ-CONC-134, REQ-ATM-022]
---
# T429 — E11.2 — Sub-64-bit atomic MI size preservation & struct-embedded Atomic<T> prelude resolution

## Goal
Fix sub-64-bit atomic machine instruction operand width clobbering in `compiler/driver/pipeline.ax` and struct-embedded `Atomic<T>` resolution ordering against the appended prelude in `compiler/types/typeck.ax`, ensuring width-exact native x86-64 code generation (1/2/4-byte `XCHG`, `LOCK XADD`, bitwise CAS loops, `LOCK CMPXCHG`) without adjacent field corruption or broken negative signed CAS, and full method / `view<Atomic<T>>` resolution for struct-embedded atomics across `--interp` and native execution.

## Scope
- `compiler/driver/pipeline.ax`:
  - Preserve `(*inst).size` for `X64_MI_XCHG`, `X64_MI_LOCK_XADD`, `X64_MI_ATOMIC_RMW_LOOP`, and `X64_MI_LOCK_CMPXCHG` at lines 1859–1864 (`driver_emit_build_mi_body_obj`) and line 4004 instead of unconditionally overwriting `size = 8u8`.
  - Ensure `x64_encode_mi_inst_obj` emits size-exact 1-byte (`AL`, `lock cmpxchg BYTE PTR`, `xchg BYTE PTR`), 2-byte (`AX`, `lock cmpxchg WORD PTR`), 4-byte (`EAX`, `lock cmpxchg DWORD PTR`), and 8-byte (`RAX`, `lock cmpxchg QWORD PTR`) instructions matching `LirInst.size`.
  - Fix negative signed sub-64-bit CAS (`AtomicI8.new(-1i8).compare_exchange(-1i8, ...)`, `AtomicI16`, `AtomicI32`) so sign-extended comparison registers match narrow memory storage without spurious mismatches or neighboring field clobbers (`AXS-ATM-005`, `AXS-ATM-010`, `AXS-ATM-018`).
- `compiler/types/typeck.ax`:
  - Fix `typeck_pass1a` (lines 11336–11392) ordering so all struct `TypeId`s (including appended prelude `Atomic<T>` and prelude aliases) are registered in `thir` before struct field types are resolved via `hir_type_to_typeid`.
  - Prevent `lookup_path_type_by_name` (lines 3604–3609) and `lookup_path_type` (lines 3369, 3653) from caching `t_error` as the `item_type` of prelude atomic aliases (`AtomicBool`, `AtomicU32`, etc.) when user structs reference them prior to prelude AST processing.
  - Ensure user structs embedding `Atomic<T>` or prelude aliases resolve fields cleanly, allow method dispatch (`s.b0.store(...)`, `s.w4.load(...)`), and preserve parameter capability resolution for `view<AtomicBool>` / `view<AtomicU32>` on functions throughout the compilation unit without bogus `AX_TYPE_UNKNOWN_FIELD`.
- Rebuild Stage-2 `axiomc2.exe` in `build-snap-T429/build` since `pipeline.ax` and `typeck.ax` are part of the self-host compiler bundle.
- Add regression tests in `tests/run/atomics/` covering sub-64-bit atomic operations, adjacent struct/array memory safety, negative signed sub-64-bit CAS, struct-embedded atomics, and `view<Atomic<T>>` method calls.

## Acceptance
- [ ] Sub-64-bit atomic operations on `AtomicBool`, `AtomicU8`/`AtomicI8`, `AtomicU16`/`AtomicI16`, `AtomicU32`/`AtomicI32` emit width-exact machine instructions in native `axiomc2.exe` without adjacent memory clobbering.
- [ ] Negative signed sub-64-bit CAS (`compare_exchange` and `compare_exchange_weak`) succeeds across `--interp` and native `-O0`, `-O1`, `-O2` with `0 WEAK-NATIVE`.
- [ ] Struct-embedded `Atomic<T>` and prelude aliases resolve cleanly in typeck; methods and `view<Atomic<T>>` calls compile and execute correctly across `--interp` and native `-O0`, `-O1`, `-O2` with `0 WEAK-NATIVE`.
- [ ] Stage-2 `axiomc2.exe` is rebuilt in `build-snap-T429/build` from Stage-0 and Stage-1 (`tools/build_axiomc.py --out build-snap-T429/build`) and passes the full test suite.
- [ ] All tests in `tests/run/atomics/` pass with `0 FAIL` and `0 WEAK-NATIVE`.
- [ ] `reqcov.py --strict`, `harness_check.py`, and `archcheck.py` exit 0; report `_workspaces/reports/T429-report.md` written with exact `## Files changed`.

## Out of scope
- Modifying `tests/conformance/p11/e11_2_atomics/` (owned by T409).
- Modifying `bootstrap/axiom0/` (frozen at `axiom0-frozen`).
- Modifying `docs/`.

## Notes
- Phase P11 (`P11-concurrency-async`). All compiler and library changes live in `compiler/` and `std/`.
- `pipeline.ax` and `typeck.ax` are in the self-host bundle. Always build Stage-0, Stage-1, and Stage-2 in `build-snap-T429/build` before verifying native execution.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-08 23:15:00 created by axiom-architect to unblock T409 (fixes sub-64-bit atomic MI width clobber and struct-embedded Atomic<T> prelude ordering)
