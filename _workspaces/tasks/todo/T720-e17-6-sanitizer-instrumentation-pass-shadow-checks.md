---
id: T720
title: E17.6 Compiler sanitizer instrumentation pass (address/bounds/provenance, uninit, UB & thread shadow hooks)
phase: P17-debugging-runtime-introspectio
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T217, T316, T719]
priority: 191
status: todo
attempts: 0
paths: [compiler/instrument/sanitize, tests/selfhost/debug/sanitize]
spec: [spec/SPEC-97-sanitizers-runtime-verification.md, 0147, tasks/0599, tasks/0733]
covers: [REQ-DBG-116, REQ-DBG-120]
---
# T720 — E17.6 Compiler sanitizer instrumentation pass (address/bounds/provenance, uninit, UB & thread shadow hooks)

## Goal
Implement the compiler sanitizer instrumentation pass (--sanitize=address|memory|ub|thread|bounds|all) inserting shadow-memory, provenance, initialization, UB, and thread hooks.

## Scope
- Implement `compiler/instrument/sanitize` running after static ownership, capability, and MIR verification (`ADEBUG-82`/`ADEBUG-83`).
- Insert `ASan`/`Bounds` redzone and shadow checks around stack frames, globals, raw-pointer dereferences, and slice/ptr indexing (eliding checks already proven in-bounds by verified `OptIR` certificates per `0599 §12`).
- Insert `MSan` shadow-initialization propagation for `MaybeUninit<T>` and raw memory reads, `UBSan` checks for alignment, null raw pointers, shift counts, unchecked arithmetic, and enum/bool bit patterns, and `TSan` memory-access/atomic/lock hooks, carrying `SourceOrigin` metadata to every check site.
- Add selfhost unit tests in `tests/selfhost/debug/sanitize`.

## Acceptance
- [ ] `axiomc build --sanitize=address|memory|ub|thread|bounds|all` lowers sanitizer checks with accurate `SourceOrigin` IDs while leaving static type/ownership/capability errors unchanged.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T720-report.md` with exact `## Files changed`.

## Out of scope
- Sanitizer runtime library `std.rt.sanitize` (`T721`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
