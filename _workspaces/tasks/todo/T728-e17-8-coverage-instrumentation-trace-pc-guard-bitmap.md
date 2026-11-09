---
id: T728
title: E17.8 — Edge coverage instrumentation pass (trace-pc-guard) & shared-memory coverage map
phase: P17-debugging-runtime-introspectio
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T727, T720]
priority: 199
status: todo
attempts: 0
paths: [compiler/instrument/coverage, compiler/lir, compiler/target/x64, tests/lir/coverage, tests/run/fuzz_instrumentation]
spec: [spec/SPEC-99-coverage-guided-fuzzing.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-TST-014, REQ-CNF-006]
---
# T728 — E17.8 — Edge coverage instrumentation pass (trace-pc-guard) & shared-memory coverage map

## Goal
Implement the compile-time edge-coverage instrumentation pass (`-fsanitize-coverage=trace-pc-guard`), assigning unique deterministic guard IDs to basic-block edges and emitting inline updates to a 64 KiB shared-memory coverage map.

## Scope
- In `compiler/instrument/coverage` and `compiler/lir`, implement the edge-coverage instrumentation pass inserted after control-flow linearization:
  * Assign a consecutive 32-bit guard ID to every basic-block and conditional branch target.
  * Emit an inline atomic/saturating increment into a 64 KiB shared-memory coverage bitmap (`__ax_fuzz_coverage_map[guard_id % 65536]++`) or a call to `__sanitizer_cov_trace_pc_guard(guard_ptr)`.
- Support Windows named shared memory (`CreateFileMappingW` / `MapViewOfFile`) and Linux POSIX shared memory (`shm_open` / `mmap`) for zero-overhead, crash-immune telemetry passing to the coordinator.
- Ensure that the instrumentation inserts zero heap allocations, preserves all function arguments, and maintains leaf-function red zones on x86-64.

## Acceptance
- [ ] LIR golden tests in `tests/lir/coverage` verify insertion of edge counters on all CFG branch splits.
- [ ] Run tests in `tests/run/fuzz_instrumentation` verify accurate edge counter updates in the 64 KiB coverage bitmap during execution of branching algorithms.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T728-report.md` with exact `## Files changed`.

## Out of scope
- Mutator generation and process coordinator logic (`T729`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T728/build` and `python tools/axtest.py --compiler build-snap-T728/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:15:00 created by axiom-architect (ADR-0039 P17 coverage fuzzing expansion)
