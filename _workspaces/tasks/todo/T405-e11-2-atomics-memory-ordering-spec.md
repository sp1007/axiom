---
id: T405
title: E11.2 — Canonical atomics & memory ordering specification (SPEC-31)
phase: P11-concurrency-async
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T400]
priority: 126
status: todo
attempts: 0
paths: [spec/SPEC-31-atomics.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [0092, 0128, 0161, 0162, 0208, tasks/0328, tasks/0515]
covers: [REQ-ATM-001, REQ-CONC-013, REQ-CONC-059, REQ-CONC-060, REQ-CONC-097, REQ-ATM-002, REQ-ATM-014, REQ-ATM-015, REQ-ATM-031, REQ-MIR-144, REQ-CONC-172, REQ-CONC-174, REQ-CONC-178]
---
# T405 — E11.2 — Canonical atomics & memory ordering specification (SPEC-31)

## Goal
Write canonical `spec/SPEC-31-atomics.md` (`AXS-ATM-*` rule IDs) defining `Atomic<T>`, memory orderings, fences, MIR/LIR lowering, x86-64 instruction mapping, and oracle schedule-exploration semantics.

## Scope
- Write `spec/SPEC-31-atomics.md` with a Vietnamese `## Tóm tắt` section and numbered `AXS-ATM-NNN` rules.
- Define `Atomic<T>` as a type-level storage abstraction over target-supported widths (`bool`, `i8..i64`, `u8..u64`, `isize`, `usize`, `*const T`, `*mut T`), distinct from ordinary memory and `Volatile<T>` (`0092`, `0128`).
- Specify `Ordering` (`Relaxed`, `Acquire`, `Release`, `AcqRel`, `SeqCst`), operations (`new`, `load`, `store`, `swap`, `compare_exchange`, `compare_exchange_weak`, `fetch_add`, `fetch_sub`, `fetch_and`, `fetch_or`, `fetch_xor`, `fence`, `compiler_fence`, `is_lock_free`), wrapping two's-complement arithmetic for integer RMW, and compile-time rejection of invalid orderings (such as `Release`/`AcqRel` on CAS failure or `Acquire` on `store`).
- Forbid converting `Atomic<T>` to `mut_view<T>` or bypassing atomic operations through ordinary mutable capabilities.
- Specify the exact MIR `Atomic` statement (`AXS-EXT-043`), LIR `Atomic*`/`Fence` operations (`AXS-EXT-051`), x86-64 lowering rules, and deterministic oracle modification-order / schedule-exploration rules.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-31-atomics.md` exists with a Vietnamese `## Tóm tắt`, `AXS-ATM-NNN` rule IDs, x86-64 lowering table, and litmus test specifications.
- [ ] `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md` are updated.
- [ ] `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T405-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or std implementation (handled by `T406`–`T408`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T405/build` and `python tools/axtest.py --compiler build-snap-T405/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
