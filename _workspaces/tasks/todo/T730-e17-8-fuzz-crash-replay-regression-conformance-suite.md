---
id: T730
title: E17.8 — Crash minimization, < 1.0s regression replay & fuzzing conformance suite
phase: P17-debugging-runtime-introspectio
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T729]
priority: 201
status: todo
attempts: 0
paths: [tests/conformance/p17/e17_8_fuzzing, tests/fuzz/reproduce]
spec: [spec/SPEC-99-coverage-guided-fuzzing.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-TST-013, REQ-CNF-006]
---
# T730 — E17.8 — Crash minimization, < 1.0s regression replay & fuzzing conformance suite

## Goal
Implement crash artifact minimization, fast `< 1.0s` regression replay integration in `axiom test`, and certify E17.8 exit criteria with an end-to-end fuzzing conformance suite.

## Scope
- Implement deterministic crash input minimization (`axiom test --fuzz --minimize <crash_file>`): iteratively prune bytes while preserving the same crash signature/stack trace.
- Implement automatic unit regression replay: when `axiom test` runs, all artifacts located in `tests/fuzz/reproduce/` or `fuzz/crashes/` are executed as standalone deterministic unit tests completing in `< 1.0s`.
- Create end-to-end conformance suite in `tests/conformance/p17/e17_8_fuzzing`:
  * Fuzzing an intentionally flawed parser harness to discover the crashing boundary condition in under 30 seconds.
  * Verifying coverage feedback guidance by proving corpus expansion over time.
  * Verifying structure-aware mutation via `@derive(Arbitrary)`.

## Acceptance
- [ ] Conformance tests in `tests/conformance/p17/e17_8_fuzzing` discover the injected fault and produce minimized crash test cases.
- [ ] Regression replay tests in `tests/fuzz/reproduce` execute deterministically in `< 1.0s` under `axiom test`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T730-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T730/build` and `python tools/axtest.py --compiler build-snap-T730/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:15:00 created by axiom-architect (ADR-0039 P17 coverage fuzzing expansion)
