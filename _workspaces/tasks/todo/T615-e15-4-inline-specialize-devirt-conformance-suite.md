---
id: T615
title: E15.4 — Inlining, specialization, devirtualization & SROA conformance suite
phase: P15-optimizer-2-0
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T614]
priority: 109
status: todo
attempts: 0
paths: [tests/conformance/p15/e15_4_inline_specialize_devirt]
spec: [spec/SPEC-73-inlining-specialization-devirt.md, 0131, tasks/0401, tasks/0551]
covers: [REQ-OPT-108, REQ-OPT-109, REQ-OPT-110, REQ-OPT-111, REQ-OPT-112, REQ-OPT-113]
---
# T615 — E15.4 — Inlining, specialization, devirtualization & SROA conformance suite

## Goal
Certify E15.4 exit criteria with an end-to-end differential conformance suite covering copy/move propagation, `SROA`, return-slot construction, inlining, call-site specialization, devirtualization, and tail-call optimization.

## Scope
- Create differential conformance tests in `tests/conformance/p15/e15_4_inline_specialize_devirt` verifying:
  - complete abstraction erasure (`SROA` + closure inlining + `RVO`) on nested generic/closure pipelines with exact `Drop` and panic fidelity;
  - `dyn Trait` and function-pointer devirtualization enabling subsequent inlining (`REQ-OPT-112`, `REQ-OPT-113`), while respecting open-world/export/dynamic-load/reflection boundaries (`REQ-OPT-108..111`);
  - `@inline(always)`, `@inline(never)`, and deep tail-recursive calls executing in constant stack space at `-O2`.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p15/e15_4_inline_specialize_devirt` pass in `--interp` and native `-O0`/`-O1`/`-O2` modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T615-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T615/build` and `python tools/axtest.py --compiler build-snap-T615/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:41:00 created by T215 (P15 phase planning)
