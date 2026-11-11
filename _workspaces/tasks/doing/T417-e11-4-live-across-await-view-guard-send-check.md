---
id: T417
title: E11.4 — Live-across-await analysis: view, lock-guard & Future Send checking
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T416, T401, T411]
priority: 139
status: doing
attempts: 1
timeout_min: 360
paths: [tests/ui/async/borrow_across_await, tests/ui/async/lock_guard_await, tests/ui/async/send_bounds]
locks: [compiler/own/cap.ax, compiler/own/move.ax, compiler/own/unsafe.ax, compiler/mir/mir.ax, compiler/mir/builder.ax, compiler/traits/solver.ax, compiler/types/typeck.ax, compiler/verify/verifier.ax, compiler/driver/pipeline.ax, compiler/diag/code.ax, compiler/diag/format.ax, tests/selfhost]
spec: [spec/SPEC-33-async.md, 0093, 0105, 0118, 0127, 0135, 0248, tasks/0275, tasks/0297, tasks/0488, tasks/0619]
covers: [REQ-ASY-003, REQ-ASY-004, REQ-ASY-005, REQ-ASY-006, REQ-ASY-008, REQ-ASY-012, REQ-CONC-017, REQ-ASY-015, REQ-CONC-048, REQ-CONC-093, REQ-ASY-025, REQ-ASY-028, REQ-ASY-029, REQ-ASY-030, REQ-ASY-031, REQ-ASY-042, REQ-ASY-053, REQ-ASY-069, REQ-ASY-071, REQ-ASY-072, REQ-ASY-087, REQ-ASY-090, REQ-ASY-091, REQ-ASY-095, REQ-ASY-097, REQ-ASY-106, REQ-ASY-107, REQ-ASY-128, REQ-ASY-150, REQ-ASY-160]
started: 2026-11-10 22:22:00
agent: T417-impl
---
# T417 — E11.4 — Live-across-await analysis: view, lock-guard & Future Send checking

## Goal
Implement live-across-await dataflow analysis in `axiomc` to compute the exact live state at each `.await` suspension point, reject `view<T>`, `mut_view<T>`, and synchronous lock guards crossing `.await`, and derive `Future: Send` strictly from live-across-await state.

## Scope
- Lower `.await` in `compiler/mir/builder.ax` to a `Suspend` terminator (`AXS-EXT-044`) with an explicit `SuspensionPointId` (`REQ-ASY-160`) and pre-suspension drop elaboration for locals whose lexical scope or liveness ends before `.await` (`REQ-ASY-024, 033`).
- Compute the live-across-await variable set at each `Suspend` terminator by combining liveness, move/initialization state, and drop analysis (`REQ-ASY-025`).
- Reject any `view<T>` or `mut_view<T>` capability that is live across a `Suspend` point (`AX_ASYNC_VIEW_ACROSS_AWAIT`, `REQ-ASY-028..031`), while permitting `view<T>`/`mut_view<T>` created and consumed strictly between suspension points or re-borrowed after `.await`.
- Reject synchronous lock guards (`MutexGuard`, `RwLockReadGuard`, `RwLockWriteGuard`) and `@no_suspend_hold` types live across a `Suspend` point (`AX_ASYNC_GUARD_ACROSS_AWAIT`, `REQ-CONC-010, 017, 048`, `REQ-ASY-053`).
- Determine `Coroutine`/`Future: Send` in `compiler/traits/solver.ax` strictly from parameters and locals in the live-across-await set (so a `!Send` temporary dropped before `.await` does not disqualify the `Future` from being `Send`, `REQ-ASY-042`), and ensure `Future: !Share` (`REQ-ASY-043, 077`).

## Acceptance
- [ ] `tests/ui/async/borrow_across_await/*.ax` verifies rejection of `view<T>` and `mut_view<T>` held across `.await`, and acceptance of views confined to a synchronous segment or re-borrowed after `.await`.
- [ ] `tests/ui/async/lock_guard_await/*.ax` verifies rejection of `MutexGuard` and `RwLock*Guard` held across `.await`, and acceptance when the guard is explicitly dropped before `.await`.
- [ ] `tests/ui/async/send_bounds/*.ax` verifies that a `Future` with a `!Send` local dropped before `.await` satisfies `Send`, whereas a `!Send` local live across `.await` fails `Send` with a diagnostic naming the suspension point and local.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T417` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T417-report.md` with exact `## Files changed`.

## Out of scope
- State-machine transformation into `poll` bodies (`T088`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T417/build` and `python tools/axtest.py --compiler build-snap-T417/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
- 2026-11-10 22:22:00 started (attempt 1) T417-impl
