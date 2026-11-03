---
id: T721
title: E17.6 Sanitizer runtime library (std.rt.sanitize): redzone quarantine, shadow state, TSan vector clocks & reports
phase: P17-debugging-runtime-introspectio
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T217, T316, T712, T720]
priority: 192
status: todo
attempts: 0
paths: [std/rt/sanitize, tests/run/sanitize]
spec: [spec/SPEC-97-sanitizers-runtime-verification.md, 0147, tasks/0599, tasks/0694, tasks/0733]
covers: [REQ-DBG-116, REQ-DBG-120]
---
# T721 — E17.6 Sanitizer runtime library (std.rt.sanitize): redzone quarantine, shadow state, TSan vector clocks & reports

## Goal
Implement std.rt.sanitize providing shadow memory, redzone-quarantine heap hooks, MSan initialization tracking, UBSan handlers, TSan vector clocks/lock-order detection, and symbolicated violation reports.

## Scope
- Implement `std.rt.sanitize` Address/Provenance sanitizer runtime: shadow-memory mapping, heap redzone poisoning, quarantine ring buffer recording allocation and deallocation `Backtrace`s, and pointer-provenance generation checks.
- Implement `std.rt.sanitize` Memory (`MaybeUninit` shadow bitmaps), UB (alignment, null, shift, overflow, invalid enum tag), and Thread (vector-clock shadow cells for concurrent accesses + lock-acquisition DAG cycle detector) runtime handlers.
- Format deterministic, symbolicated sanitizer error reports (`ERROR: AxiomSanitizer: <kind> at <file>:<line>:<col>`) with access, allocation, and deallocation stack traces and exit code `102`.
- Add end-to-end sanitizer tests in `tests/run/sanitize`.

## Acceptance
- [ ] Programs built with `--sanitize=all` detect memory, bounds, uninitialized read, UB, and concurrency violations and print symbolicated stack traces in `tests/run/sanitize`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T721-report.md` with exact `## Files changed`.

## Out of scope
- Deterministic execution recording and replay (`E17.7`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
