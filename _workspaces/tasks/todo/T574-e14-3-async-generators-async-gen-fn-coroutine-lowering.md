---
id: T574
title: E14.3 — Async generators (async gen fn), AsyncIterator trait & unified coroutine lowering
phase: P14-comptime-2-0-reflection-genera
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T562, T563, T417]
priority: 196
status: todo
attempts: 0
paths: [compiler/mir, compiler/own, compiler/lir, std/iter, tests/ui/async_gen, tests/run/async_gen]
spec: [spec/SPEC-62-generators.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-ASY-036, REQ-CORE-2999]
---
# T574 — E14.3 — Async generators (async gen fn), AsyncIterator trait & unified coroutine lowering

## Goal
Implement async generators (`async gen fn`) lowering to the `AsyncIterator` trait, unified coroutine MIR state machine lowering, suspension-boundary capability checks, composite cancellation `Drop` glue, and canonical consumption via `while let Option.Some(item) = stream.next().await`.

## Scope
- Parse and lower `async gen fn name(...) -> YieldType` producing an anonymous state-machine struct implementing the standard `AsyncIterator<Item = YieldType>` trait (`fn next(mut self) -> impl Future<Output = Option<YieldType>>`).
- Extend capability and ownership borrow-checking in `compiler/own` and `compiler/mir`: strictly reject holding temporary `view<T>` or `mut_view<T>` places live across any `.await` or `yield` suspension point (`AX_CAP_CROSS_SUSPENSION_VIEW`).
- Unify coroutine state-machine lowering in `compiler/mir` for combined async + generator frames: pack live variables into frame structs, generate discriminator-based re-entry dispatch, and emit per-state cancellation `Drop` glue to guarantee clean resource unwinding if the stream is dropped mid-iteration.
- Ensure canonical syntax in tests and stdlib: consume streams using `while let Option.Some(x) = stream.next().await { ... }` (never `for await`).

## Acceptance
- [ ] Negative UI tests in `tests/ui/async_gen` reject borrowing views across `yield` and `.await` points with `AX_CAP_CROSS_SUSPENSION_VIEW`.
- [ ] Run tests in `tests/run/async_gen` verify async generator execution, cancellation drop behavior, and `while let` consumption across `--interp` and native execution (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T574-report.md` with exact `## Files changed`.

## Out of scope
- Non-standard syntax (`for await`, `yield from`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T574/build` and `python tools/axtest.py --compiler build-snap-T574/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:05:00 created by axiom-architect (ADR-0039 P14 async generators expansion)
