---
id: T819
title: E19.5 Documentation generator, doc-tests, pass replay/bisection & integrated test framework conformance suite
phase: P19-developer-tooling
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T219, T752, T755, T756, T759, T817, T818]
priority: 209
status: doing
attempts: 1
paths: [tests/conformance/p19/e19_5_docgen_test_ux]
spec: [spec/SPEC-104-docgen-test-framework-ux.md, 0120, 0121, 0147, 0161, 0163, tasks/0361, tasks/0418, tasks/0423, tasks/0662]
covers: [REQ-TOOL-002, REQ-TOOL-003, REQ-TOOL-005, REQ-TOOL-006, REQ-TOOL-007, REQ-TOOL-008, REQ-TOOL-009, REQ-TOOL-010, REQ-TOOL-011, REQ-TOOL-179, REQ-TOOL-187, REQ-TOOL-298, REQ-TST-112]
started: 2026-11-08 19:04:33
agent: T819-impl
---
# T819 — E19.5 Documentation generator, doc-tests, pass replay/bisection & integrated test framework conformance suite

## Goal
Certify E19.5 exit criteria with an end-to-end conformance suite covering `axiomc doc`, executable doc-tests, `axiomc test` differential MIR oracle validation, optimization pass replay/bisection, and integrated debug/trace/verification diagnostics.

## Scope
- Create conformance tests in `tests/conformance/p19/e19_5_docgen_test_ux` verifying:
  - `axiomc doc` HTML/JSON generation and `axiomc doc --test` doc-test verification across multi-module packages (`REQ-TOOL-298`);
  - `axiomc test` native + `--interp` differential execution (`REQ-TOOL-009`), optimization pass replay and pass bisection (`REQ-TOOL-179`), and integrated verification/debugging/profiling diagnostics (`REQ-TST-112`);
  - semantic invariance across build features (`REQ-TOOL-002`), zero production runtime overhead for oracle/trace/tooling metadata (`REQ-TOOL-003`, `REQ-TOOL-008`, `REQ-TOOL-187`), and debug metadata invariants (`REQ-TOOL-005`..`REQ-TOOL-007`, `REQ-TOOL-010`, `REQ-TOOL-011`);
  - differential equivalence between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p19/e19_5_docgen_test_ux` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T819-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T819/build` and `python tools/axtest.py --compiler build-snap-T819/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
- 2026-11-08 19:04:33 started (attempt 1) T819-impl
