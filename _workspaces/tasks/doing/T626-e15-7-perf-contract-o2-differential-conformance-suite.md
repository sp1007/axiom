---
id: T626
title: E15.7 — Performance contract, -O2 differential equivalence & CI regression budget conformance suite
phase: P15-optimizer-2-0
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T612, T615, T619, T623, T625, T629]
priority: 120
status: doing
attempts: 1
paths: [tests/conformance/p15/e15_7_perf_contract]
spec: [spec/SPEC-76-performance-contract.md, 0074, tasks/0408, tasks/0595, tasks/0706]
covers: [REQ-OPT-251, REQ-OPT-252, REQ-OPT-253, REQ-OPT-254, REQ-OPT-255, REQ-OPT-256]
started: 2026-11-08 16:29:16
agent: T626-impl
---
# T626 — E15.7 — Performance contract, -O2 differential equivalence & CI regression budget conformance suite

## Goal
Certify E15.7 and the phase P15 exit criterion (`differential green at -O2; benchmark targets met and tracked in CI`) with an end-to-end conformance and regression-gate verification suite in `tests/conformance/p15/e15_7_perf_contract`.

## Scope
- Create conformance tests in `tests/conformance/p15/e15_7_perf_contract` verifying:
  - differential equivalence across `--interp`, `-O0`, `-O1`, `-O2`, and `-Oz` on combined multi-pass stress programs (`OptIR` + alias/escape + BCE/LICM + inlining/SROA/devirt + auto-vectorization + LTO/GC + linear-scan regalloc, `REQ-OPT-251..256`);
  - `tools/perf.py` benchmark execution meeting the `SPEC-76` compile-time, runtime throughput, startup latency, and binary size budgets;
  - deterministic, reproducible output across repeated `-O2` builds and inspectable optimization provenance.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p15/e15_7_perf_contract` pass in `--interp` and native `-O0`/`-O1`/`-O2`/`-Oz` modes with `0 WEAK-NATIVE`, and `python tools/perf.py --check-budgets` exits 0.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T626-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated phases; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T626/build` and `python tools/axtest.py --compiler build-snap-T626/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:44:00 created by T215 (P15 phase planning)
- 2026-11-08 16:29:16 started (attempt 1) T626-impl
