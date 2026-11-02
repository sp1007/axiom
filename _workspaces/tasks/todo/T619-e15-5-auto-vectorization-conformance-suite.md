---
id: T619
title: E15.5 — Loop & SLP auto-vectorization conformance suite
phase: P15-optimizer-2-0
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T312, T618]
priority: 113
status: todo
attempts: 0
paths: [tests/conformance/p15/e15_5_autovec]
spec: [spec/SPEC-74-auto-vectorization.md, 0095, tasks/0402, tasks/0403, tasks/0406, tasks/0407]
covers: [REQ-OPT-219, REQ-OPT-220, REQ-OPT-221, REQ-OPT-222]
---
# T619 — E15.5 — Loop & SLP auto-vectorization conformance suite

## Goal
Certify E15.5 exit criteria with an end-to-end differential conformance suite covering loop auto-vectorization, `SLP` straight-line vectorization, capability-disjoint dependence proofs, reduction legality, scalar remainder epilogues, and `Source → MIR → OptIR → LIR → Machine` provenance.

## Scope
- Create differential conformance tests in `tests/conformance/p15/e15_5_autovec` verifying:
  - exact scalar/vector numerical and panic equivalence across `i8`..`i64`, `u8`..`u64`, `f32`, and `f64` loops with arbitrary trip counts (`0`, `1`, prime lengths, aligned/unaligned slices);
  - vectorization enabled by disjoint `mut_view<[T]>` + `view<[T]>` parameters vs conservative scalar fallback on raw-pointer `MayAlias`, strict FP reductions, or checked-overflow traps (`REQ-OPT-219`, `REQ-OPT-220`);
  - inspectable `Source → MIR → OptIR → LIR → Machine` vectorization remarks and provenance (`REQ-OPT-221`, `REQ-OPT-222`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p15/e15_5_autovec` pass in `--interp` and native `-O0`/`-O1`/`-O2` modes with `0 WEAK-NATIVE`, and machine dumps confirm vector instruction emission on legal kernels.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T619-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`); depends on P12 gate `T312` (`ROADMAP.md` §3/§4).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T619/build` and `python tools/axtest.py --compiler build-snap-T619/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:42:00 created by T215 (P15 phase planning)
