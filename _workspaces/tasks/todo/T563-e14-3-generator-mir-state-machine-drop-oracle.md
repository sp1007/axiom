---
id: T563
title: E14.3 — Generator MIR state-machine lowering, per-state Drop cleanup & oracle (--interp) execution
phase: P14-comptime-2-0-reflection-genera
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T562]
priority: 183
status: todo
attempts: 0
paths: [compiler/mir/gen_lower.ax, compiler/verify, compiler/interp, tests/mir/generators, tests/run/generators]
spec: [spec/SPEC-62-generators.md, tasks/0512, tasks/0539]
covers: [REQ-CORE-3008, REQ-CORE-3009, REQ-CORE-3010, REQ-CORE-3011, REQ-CORE-3012, REQ-CORE-3013, REQ-CORE-3014, REQ-CORE-3015, REQ-CORE-3016, REQ-CORE-3017, REQ-CORE-3018]
---
# T563 — E14.3 — Generator MIR state-machine lowering, per-state Drop cleanup & oracle (--interp) execution

## Goal
Implement `compiler/mir/gen_lower.ax` to lower `gen fn` MIR bodies (`MirTerminator.Yield`) into zero-heap stack-allocatable state-machine structs implementing `Iterator<Item = T>` with per-state `Drop` glue, MIR verification (`compiler/verify`), and oracle (`--interp`) execution.

## Scope
- Lower each generator body in `compiler/mir/gen_lower.ax` into a state-machine ADT (`state_tag: u32`, parameters, and only locals live across `YieldPointId`s) and generate its `next(self: mut_view<Self>) -> Option<T>` MIR body using a `SwitchInt` dispatch table (`0` = unstarted, `1..K` = suspended at yield `k`, `u32.MAX` = completed/poisoned; `AGEN-21..44`, `AMIR-38..48`).
- Generate per-state `Drop` glue so dropping an in-progress generator at state `k` drops only the owned locals live in state `k` in reverse declaration order, and dropping an unstarted or completed generator drops only remaining live captures without double-drop (`AGEN-45..49`).
- Extend `compiler/verify` and `compiler/interp` to validate generator state transitions and execute generator state machines in `--interp` and native codegen.

## Acceptance
- [ ] MIR golden tests in `tests/mir/generators` verify state-machine struct synthesis, `SwitchInt` dispatch, minimal captured locals, and per-state `Drop` cleanup blocks.
- [ ] Differential (`--interp` and native) tests in `tests/run/generators` verify lazy start, multi-`yield` loops, early break/drop of a suspended generator with `Drop`-tracking locals, and terminal `None` after completion.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`) with `0 WEAK-NATIVE`.
- [ ] Report `_workspaces/reports/T563-report.md` with exact `## Files changed`.

## Out of scope
- Standard library `std.iter` generator combinators (`T564`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T563/build` and `python tools/axtest.py --compiler build-snap-T563/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:22:30 created by T214 (P14 phase planning)
