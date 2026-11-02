---
id: T409
title: E11.2 — Atomic & memory-ordering litmus conformance suite
phase: P11-concurrency-async
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T407, T408]
priority: 130
status: todo
attempts: 0
paths: [tests/conformance/p11/e11_2_atomics]
spec: [spec/SPEC-31-atomics.md, 0033, 0092, 0128, 0208, tasks/0328, tasks/0515]
covers: [REQ-CONC-076, REQ-CONC-077, REQ-CONC-078, REQ-CONC-079, REQ-ATM-028, REQ-ATM-029, REQ-ATM-030]
---
# T409 — E11.2 — Atomic & memory-ordering litmus conformance suite

## Goal
Verify the `E11.2` exit criterion ('litmus tests pass under oracle and native stress') with a comprehensive atomic & memory-ordering conformance suite.

## Scope
- Create `tests/conformance/p11/e11_2_atomics/` covering all `AXS-ATM-*` rules and classic memory-model litmus tests: Message Passing (`MP` with Acquire/Release and fence variants), Store Buffering (`SB` with `SeqCst`), Load Buffering (`LB`), Read-Modify-Write (`RMW` counter and spinlock), CAS retry loops (`compare_exchange` and `compare_exchange_weak`), and raw-pointer `Atomic<*mut T>` tagged/epoch patterns.
- Run every litmus test under both the MIR interpreter oracle (`[interp]`) and native x86-64 (`[native]`, `[native-O1]`) with observable output verification.

## Acceptance
- [ ] All litmus and conformance tests in `tests/conformance/p11/e11_2_atomics/` pass in `[interp]`, `[native]`, and `[native-O1]` under `axiomc2.exe` (`WEAK-NATIVE 0`, `0 FAIL`).
- [ ] Full test suite passes in `build-snap-T409` under `axiomc2.exe`; `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T409-report.md` with exact `## Files changed`.

## Out of scope
- Modifying compiler or std source files.

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T409/build` and `python tools/axtest.py --compiler build-snap-T409/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
