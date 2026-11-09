---
id: T729
title: E17.8 — Multi-process fuzz coordinator/worker runner, @derive(Arbitrary) & axiom test --fuzz CLI
phase: P17-debugging-runtime-introspectio
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T728, T558]
priority: 200
status: todo
attempts: 0
paths: [compiler/driver, std/fuzz, tests/fuzz, tests/run/fuzz_runner]
spec: [spec/SPEC-99-coverage-guided-fuzzing.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-TST-013, REQ-CNF-006]
---
# T729 — E17.8 — Multi-process fuzz coordinator/worker runner, @derive(Arbitrary) & axiom test --fuzz CLI

## Goal
Implement the multi-process crash-isolated fuzzing engine, the `@derive(Arbitrary)` structured input generation macro using Comptime 2.0 reflection, and the `axiom test --fuzz` CLI driver.

## Scope
- Implement the fuzzing coordinator process in `std/fuzz` and `compiler/driver`:
  * Manage corpus queuing, power schedules, and mutation strategies (bit flips, byte swaps, dictionary insertions).
  * Spawn worker processes executing target harnesses with execution timeouts (`--timeout=ms`) and memory caps (`--rss-limit-mb`).
  * Read the 64 KiB shared coverage map between iterations to identify new edge transitions, saving interesting inputs into `fuzz/corpus/<target>/`.
  * Isolate process crashes (segfault, abort, panic, timeout, ASan violation), saving failing inputs into `fuzz/crashes/<crash_id>.bin`.
- Implement `std.fuzz.Arbitrary` trait and `@derive(Arbitrary)`:
  * Read from a structured `Unstructured` byte buffer.
  * Leverage `TypeInfo` reflection to generate valid instances of enums, structs, primitives, and bounded collections.
- Implement the `axiom test --fuzz <target>` command-line interface with live terminal metrics (iterations/sec, unique edges, corpus size).

## Acceptance
- [ ] Run tests in `tests/run/fuzz_runner` verify that the coordinator detects crashing inputs in isolated workers without killing the coordinator process.
- [ ] Conformance tests in `tests/fuzz` verify `@derive(Arbitrary)` generating valid arbitrary instances for complex recursive data types.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T729-report.md` with exact `## Files changed`.

## Out of scope
- Distributed cluster fuzzing (AFL++ / OSS-Fuzz cluster integration is post-v1).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T729/build` and `python tools/axtest.py --compiler build-snap-T729/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:15:00 created by axiom-architect (ADR-0039 P17 coverage fuzzing expansion)
