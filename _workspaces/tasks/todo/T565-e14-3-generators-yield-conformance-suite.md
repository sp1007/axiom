---
id: T565
title: E14.3 — Generators, yield state machines & lazy control-flow conformance suite
phase: P14-comptime-2-0-reflection-genera
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T562, T563, T564]
priority: 185
status: todo
attempts: 0
paths: [tests/conformance/p14/e14_3_generators]
spec: [spec/SPEC-62-generators.md, tasks/0512, tasks/0539]
covers: [REQ-CORE-3026, REQ-CORE-3027, REQ-CORE-3028, REQ-CORE-3029, REQ-CORE-3030]
---
# T565 — E14.3 — Generators, yield state machines & lazy control-flow conformance suite

## Goal
Certify E14.3 exit criteria with an end-to-end conformance suite covering `gen fn`, `yield`, ownership and capability verification across suspension points, per-state `Drop` cleanup, and lazy `std.iter` pipelines.

## Scope
- Create positive and negative conformance tests in `tests/conformance/p14/e14_3_generators` covering:
  - lazy generator construction, multi-yield control flow (loops, match, early return), and terminal `None` state;
  - deterministic per-state `Drop` cleanup when a generator is dropped at each suspension point vs after completion;
  - negative UI tests rejecting `yield` outside `gen fn`, self-referential borrows across `yield`, and escaping ephemeral capabilities (`AX_GEN_*`);
  - differential (`--interp` and native, `-O0` and `-O1`) agreement on recursive/nested generator pipelines and comptime generator evaluation.

## Acceptance
- [ ] All positive and negative tests in `tests/conformance/p14/e14_3_generators` pass in both `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T565-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T565/build` and `python tools/axtest.py --compiler build-snap-T565/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:22:30 created by T214 (P14 phase planning)
