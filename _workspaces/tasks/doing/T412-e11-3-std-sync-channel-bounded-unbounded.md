---
id: T412
title: E11.3 — std.sync.channel: bounded & unbounded ownership-transferring channels
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T411]
priority: 134
status: doing
attempts: 1
paths: [std/sync/channel, tests/std/channel]
locks: [std/sync/mod.ax]
spec: [spec/SPEC-32-threads-sync.md, 0136, 0206, tasks/0278, tasks/0329, tasks/0837]
covers: [REQ-CONC-007, REQ-CONC-011, REQ-CONC-041, REQ-CONC-042, REQ-CONC-043, REQ-CONC-099, REQ-CONC-103, REQ-CONC-104, REQ-CONC-115, REQ-CONC-116, REQ-CONC-143, REQ-CONC-185, REQ-CONC-186]
started: 2026-11-09 13:31:56
agent: T412-impl
---
# T412 — E11.3 — std.sync.channel: bounded & unbounded ownership-transferring channels

## Goal
Implement `std.sync.channel` providing bounded and unbounded typed channels with move-only ownership transfer, backpressure, disconnection detection, and deterministic cleanup of unread messages.

## Scope
- Implement `channel_bounded<T>(capacity: usize) -> (Sender<T>, Receiver<T>)` and `channel_unbounded<T>() -> (UnboundedSender<T>, UnboundedReceiver<T>)` where `T: Send`.
- Support `send` (moves `T` without copying or serialization), `try_send` (`Full(T)` / `Disconnected(T)`), `recv`, `try_recv` (`Empty` / `Disconnected`), and explicit `close()`.
- Support SPSC, MPSC (cloned `Sender<T>`), and MPMC (cloned `Sender<T>` and `Receiver<T>`) patterns with Acquire/Release happens-before synchronization between `send` and `recv`.
- Ensure dropping all `Sender`s wakes blocked `Receiver`s with `Disconnected`, dropping all `Receiver`s returns ownership of rejected value in `SendError(T)`, and dropping the last endpoint deterministically drops all remaining queued `T` values.

## Acceptance
- [ ] `tests/std/channel/*.ax` (`modes: interp native`) verifies bounded backpressure, unbounded growth, SPSC/MPSC/MPMC multi-thread transfers, `!Copy` move-only payload ownership transfer, disconnection wakeups, and deterministic `Drop` of queued items on channel teardown.
- [ ] Full test suite passes in `build-snap-T412` under `axiomc2.exe` (`WEAK-NATIVE 0`); `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T412-report.md` with exact `## Files changed`.

## Out of scope
- Async `.await` channel adapters (implemented in `T421`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T412/build` and `python tools/axtest.py --compiler build-snap-T412/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
- 2026-11-09 11:48:15 started (attempt 1) T412-impl
- 2026-11-09 13:14:43 requeue: user stopped (not charged: attempt refunded)
- 2026-11-09 13:31:56 started (attempt 1) T412-impl
