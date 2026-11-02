---
id: T612
title: E15.3 — Loop optimizations, SCEV & bounds-check elimination conformance suite
phase: P15-optimizer-2-0
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T611]
priority: 105
status: todo
attempts: 0
paths: [tests/conformance/p15/e15_3_loops_bce]
spec: [spec/SPEC-72-loops-scev-bce.md, tasks/0402, tasks/0416, tasks/0426, tasks/0549]
covers: [REQ-OPT-176, REQ-OPT-177, REQ-OPT-178, REQ-OPT-179, REQ-OPT-180, REQ-OPT-181, REQ-OPT-182, REQ-OPT-183, REQ-OPT-184, REQ-OPT-185, REQ-OPT-186, REQ-OPT-187, REQ-OPT-188, REQ-OPT-192, REQ-OPT-193, REQ-OPT-194, REQ-OPT-195, REQ-OPT-196]
---
# T612 — E15.3 — Loop optimizations, SCEV & bounds-check elimination conformance suite

## Goal
Certify E15.3 exit criteria with an end-to-end differential conformance suite covering `SCEV`, `BCE`, `LICM`, loop unrolling/peeling/unswitching, iterator fusion, and loop safety boundaries.

## Scope
- Create differential conformance tests in `tests/conformance/p15/e15_3_loops_bce` verifying:
  - bounds-check elimination on proven in-bounds loops vs mandatory panic preservation on out-of-bounds or wrapping induction edges (`REQ-OPT-176..181`);
  - `LICM` hoisting of invariant loads/computations and refusal to hoist across `MayAlias` writes, atomics, `volatile`, or trapping zero-trip loops (`REQ-OPT-192..196`);
  - deterministic loop analysis, provenance preservation, and zero-overhead iterator pipeline fusion (`REQ-OPT-182..188`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p15/e15_3_loops_bce` pass in `--interp` and native `-O0`/`-O1`/`-O2` modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T612-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T612/build` and `python tools/axtest.py --compiler build-snap-T612/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:40:00 created by T215 (P15 phase planning)
