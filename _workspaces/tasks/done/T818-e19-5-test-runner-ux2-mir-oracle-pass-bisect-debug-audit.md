---
id: T818
title: E19.5 Test runner UX 2.0 (axiomc test), MIR differential harness, optimization pass replay/bisection & debug/trace audit
phase: P19-developer-tooling
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T219, T752, T755, T756, T759, T816]
priority: 208
status: done
attempts: 1
paths: [compiler/test_runner, compiler/opt/bisect, compiler/driver/test_cmd, tests/run/test_ux]
spec: [spec/SPEC-104-docgen-test-framework-ux.md, 0120, 0121, 0147, 0161, 0163, tasks/0361, tasks/0418, tasks/0423, tasks/0662]
covers: [REQ-TOOL-002, REQ-TOOL-003, REQ-TOOL-005, REQ-TOOL-006, REQ-TOOL-007, REQ-TOOL-008, REQ-TOOL-009, REQ-TOOL-010, REQ-TOOL-011, REQ-TOOL-179, REQ-TST-112]
started: 2026-11-08 17:46:44
finished: 2026-11-08 18:18:33
---
# T818 — E19.5 Test runner UX 2.0 (axiomc test), MIR differential harness, optimization pass replay/bisection & debug/trace audit

## Goal
Implement `axiomc test` UX 2.0, integrated MIR interpreter differential validation, optimization pass replay & binary-search bisection (`--opt-replay`, `--opt-bisect`), and native debug/trace invariant auditing per `spec/SPEC-104-docgen-test-framework-ux.md`.

## Scope
- Implement `axiomc test` in `compiler/test_runner` and `compiler/driver/test_cmd` supporting `test "..." { ... }` discovery, parallel test execution, filter predicates, MIR interpreter (`--interp`) vs native differential execution (`REQ-TOOL-009`), and verification that build/test/oracle/trace machinery never changes core language semantics or incurs runtime cost in production builds (`REQ-TOOL-002`, `REQ-TOOL-003`, `REQ-TOOL-008`).
- Implement optimization pass replay (`--opt-replay=<manifest>`) and automated pass bisection (`--opt-bisect`, `--opt-bisect-limit=<N>`) in `compiler/opt/bisect` that evaluates intermediate IR against the MIR oracle to isolate individual passes and functions responsible for miscompilations (`tasks/0418 §70`, `tasks/0423 §78-80`, `REQ-TOOL-179`).
- Integrate native verification, debugging, and profiling diagnostics into `axiomc test` (`REQ-TST-112`), auditing target-independent semantic debug metadata (`REQ-TOOL-007`), `-O0` `.debug_line` source line mapping (`REQ-TOOL-010`) vs tiered rich DWARF sections (`REQ-TOOL-011`), logical inlined function frames (`REQ-TOOL-006`), and `OptimizedOut` variable honesty without artificial physical state (`REQ-TOOL-005`).

## Acceptance
- [ ] Run tests in `tests/run/test_ux` verify `axiomc test` discovery/filtering, MIR interpreter differential checks (`REQ-TOOL-009`), `--opt-replay` and `--opt-bisect` isolation of a seeded pass divergence (`REQ-TOOL-179`), zero runtime trace/oracle overhead when disabled (`REQ-TOOL-003`, `REQ-TOOL-008`), and debug metadata invariant checks (`REQ-TOOL-005`..`REQ-TOOL-007`, `REQ-TOOL-010`, `REQ-TOOL-011`, `REQ-TST-112`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T818-report.md` with exact `## Files changed`.

## Out of scope
- Package manager and external build graph (`P20`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T818/build` and `python tools/axtest.py --compiler build-snap-T818/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
- 2026-11-08 17:46:44 started (attempt 1) T818-impl
- 2026-11-08 18:18:33 accepted by QA -> done
