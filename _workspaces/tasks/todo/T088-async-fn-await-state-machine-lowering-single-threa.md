---
id: T088
title: E11.4 — MIR state-machine lowering, cancellation drop glue & block_on poll driver
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T211, T417]
priority: 140
status: todo
attempts: 0
paths: [compiler/mir/async_lower.ax, std/future/block_on.ax, tests/run/async, tests/mir/async]
locks: [compiler/mir/mir.ax, compiler/mir/drop.ax, compiler/mir/builder.ax, compiler/verify/verifier.ax, compiler/types/layout.ax, compiler/driver/pipeline.ax, compiler/interp/interp.ax, std/future/mod.ax, tests/selfhost]
spec: [spec/SPEC-33-async.md, 0093, 0127, 0135, 0201, 0202, 0248, tasks/0275, tasks/0297, tasks/0619]
covers: [REQ-ASY-167, REQ-ASY-168]
---
# T088 — E11.4 — MIR state-machine lowering, cancellation drop glue & block_on poll driver

## Goal
Transform `async fn` MIR bodies (`Suspend` terminators) into verified, zero-heap structural state machines implementing `Future<Output = T>` with per-state cancellation `Drop` glue and a minimal executor-free `std.future.block_on` poll driver per `spec/SPEC-33-async.md`.

## Scope
- Implement `compiler/mir/async_lower.ax` (wired into `compiler/driver/pipeline.ax` before MIR verification and optimization): transform each `Coroutine` MIR body into a structural state-machine ADT (`state_tag: u32`, saved parameters, and only the locals live across each `Suspend` point as computed by `T417`).
- Generate the `Future.poll(self: mut_view<Self>, cx: mut_view<Context>) -> Poll<Output>` MIR body dispatching on `state_tag`: state `0` (unpolled entry), states `1..N` (resumption points after each `.await`), `COMPLETED` (`u32::MAX`), and `PANICKED`/`CANCELLED`.
- Generate deterministic per-state `Drop` glue in `compiler/mir/drop.ax` and `compiler/mir/async_lower.ax`: dropping a `Future` while suspended in state `k` drops only the owned fields live in state `k` in reverse declaration order, and dropping a completed `Future` is a no-op (`REQ-ASY-009, 034, 052`).
- Implement `std/future/block_on.ax` (`pub fn block_on<F: Future>(f: F) -> F.Output`) using a stack-local no-op/park `Waker` so `async fn` programs can be polled to completion on the stack without any heap allocation or runtime executor (`REQ-ASY-016, 021, 036`).

## Acceptance
- [ ] `tests/mir/async/*.ax` (`inspect --emit=mir`) verifies state-machine lowering, `SwitchInt` dispatch on `state_tag`, minimal live-across-await field layout, and per-state cancellation drop glue.
- [ ] `tests/run/async/*.ax` (`modes: interp native`, checking `-O0` and `-O1`) verifies `async fn` execution via `block_on`, multi-step `.await` chains, branching/loops across `.await`, `?` early exit in `async fn`, and deterministic `Drop` of owned locals when a suspended `Future` is dropped before completion.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T088` under `axiomc2.exe` (`WEAK-NATIVE 0`); build warning-free; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T088-report.md` with exact `## Files changed`.

## Out of scope
- Multi-task `LocalExecutor` and work-stealing `Executor` (`T421`), `TaskGroup` (`T422`), and Windows IOCP async I/O (`T426`).

## Notes
- Roadmap epic E11.4. Implemented in `compiler/` (Axiom) / `std/` — `axiom0` is frozen after T087 (ROADMAP R3).
- Refined by T211 to focus on the MIR state-machine lowering, cancellation drop glue, and minimal `block_on` driver after `T415`–`T417`, followed by `T418`–`T419` and `E11.5` (`T420`–`T424`).
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-10-06 02:23:54 covers += REQ-ASY-167, REQ-ASY-168 (metadata only)
- 2026-11-03 00:10:00 refined scope, paths, locks, and dependencies in T211 (P11 phase planning)
