---
id: T407
title: E11.2 — LIR atomic operations & x86-64 instruction selection/encoding
phase: P11-concurrency-async
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T406]
priority: 128
status: doing
attempts: 1
paths: [compiler/lir, compiler/target/x64, tests/lir/atomics, tests/encode/atomics, tests/run/concurrency/atomics_native]
locks: [compiler/backend/session.ax, tests/selfhost]
spec: [spec/SPEC-31-atomics.md, 0092, 0162, 0208, tasks/0328, tasks/0515]
covers: [REQ-CONC-075, REQ-CONC-134, REQ-CONC-135, REQ-CONC-179]
started: 2026-11-08 01:21:57
agent: T407-impl
---
# T407 — E11.2 — LIR atomic operations & x86-64 instruction selection/encoding

## Goal
Lower MIR `Atomic` statements to LIR atomic operations (`AXS-EXT-051`) and emit verified x86-64 machine instructions (`LOCK XADD`, `LOCK CMPXCHG`, `XCHG`, `MFENCE`, `PAUSE`, and TSO-ordered `MOV`) in `axiomc`.

## Scope
- Implement LIR `AtomicLoad`, `AtomicStore`, `AtomicRmw`, `AtomicCmpXchg`, and `Fence` in `compiler/lir/lir.ax` and `compiler/lir/builder.ax`, preserving ordering, bit width (8/16/32/64), and alignment (`0162 §12, §43`).
- Lower LIR atomic ops in `compiler/target/x64/isel.ax` and `compiler/target/x64/encode.ax`: `MOV` for `Relaxed`/`Acquire` loads and `Relaxed`/`Release` stores, `XCHG` (or `MOV` + `MFENCE`) for `SeqCst` stores, `LOCK XADD` for `fetch_add`/`fetch_sub`, `LOCK AND`/`OR`/`XOR` (or CAS loop when old value is used) for bitwise RMW, `LOCK CMPXCHG` for strong/weak CAS, `MFENCE` for `SeqCst` hardware fence, compiler scheduling barrier for `Acquire`/`Release`/`AcqRel` fences, and `PAUSE` (`F3 90`) for `spin_loop_hint`.
- Add GNU-as / machine-code encoding vectors in `tests/encode/atomics/` for all 8/16/32/64-bit `LOCK`-prefixed instructions and `MFENCE`/`PAUSE`.

## Acceptance
- [ ] `tests/lir/atomics/*.ax` verifies LIR emission for all atomic operations and orderings.
- [ ] `tests/encode/atomics/*.ax` verifies byte-exact encoding of `LOCK XADD`, `LOCK CMPXCHG`, `XCHG`, `LOCK ADD/SUB/AND/OR/XOR`, `MFENCE`, and `PAUSE`.
- [ ] `tests/run/concurrency/atomics_native/*.ax` executes native x86-64 tests for all `Atomic<T>` widths (`bool`, `u8`, `u16`, `u32`, `u64`, `i64`, `usize`, `*mut T`), wrapping arithmetic (`fetch_add`/`fetch_sub` at overflow boundaries), and `compare_exchange`.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T407` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T407-report.md` with exact `## Files changed`.

## Out of scope
- AArch64/RISC-V atomic codegen (Phase 16 `E16.3`/`E16.7`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T407/build` and `python tools/axtest.py --compiler build-snap-T407/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
- 2026-11-08 01:21:57 started (attempt 1) T407-impl
