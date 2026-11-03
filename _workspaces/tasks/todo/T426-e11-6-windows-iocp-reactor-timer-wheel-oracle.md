---
id: T426
title: E11.6 — Windows IOCP reactor, timer wheel & oracle async I/O backend
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T425, T422, T423]
priority: 149
status: todo
attempts: 0
paths: [std/sys/windows/iocp.ax, std/async/reactor.ax, std/async/timer.ax, tests/std/async/reactor, tests/selfhost]
locks: [std/core/host.ax, std/async/mod.ax, std/async/executor.ax, compiler/interp/oracle.ax, compiler/interp/interp.ax, compiler/types/typeck.ax, compiler/lir/builder.ax, tests/selfhost]
spec: [spec/SPEC-35-async-io.md, 0221, tasks/0335, tasks/0438, tasks/0440, tasks/0464]
covers: [REQ-ASY-153, REQ-ASY-154, REQ-ASY-158, REQ-ASY-159]
---
# T426 — E11.6 — Windows IOCP reactor, timer wheel & oracle async I/O backend

## Goal
Implement the Windows IOCP completion reactor (`std/sys/windows/iocp.ax`, `std/async/reactor.ax`), hierarchical timer wheel (`std/async/timer.ax`), and deterministic oracle async I/O & timer driver.

## Scope
- Add `host.aio_*` intrinsics in `std/core/host.ax`, implement them for Windows x64 in `std/sys/windows/iocp.ax` (`CreateIoCompletionPort`, `GetQueuedCompletionStatusEx`, `PostQueuedCompletionStatus`, `CancelIoEx`, overlapped file/socket initiation), and implement deterministic completion/timer queueing in `compiler/interp/oracle.ax`.
- Implement `Reactor` in `std/async/reactor.ax` integrated with `LocalExecutor` and `Executor`: manages in-flight completion slots, retains owned `IoBuf` buffers until the OS completion packet arrives even if the awaiting `Future` is dropped early (`REQ-ASY-152, 157`), and wakes registered `Waker`s on completion.
- Implement `std/async/timer.ax` (`sleep(duration)`, `sleep_until(deadline)`, `Interval` with explicit missed-tick burst/skip/delay policy) driven directly by the reactor's next-expiration timeout without spawning OS threads per timer (`REQ-ASY-154, 159`).

## Acceptance
- [ ] `tests/std/async/reactor/*.ax` (`modes: interp native`) verifies IOCP completion wakeup, timer wheel ordering across 100+ concurrent timers with zero extra OS threads, `Interval` missed-tick policies, and safe buffer retention when an in-flight operation's `Future` is dropped before completion.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T426` under `axiomc2.exe` (`WEAK-NATIVE 0`); `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T426-report.md` with exact `## Files changed`.

## Out of scope
- High-level `AsyncFile` and `AsyncTcpStream`/`AsyncUdpSocket` APIs (`T427`); Linux `epoll`/`io_uring` native syscalls (Phase 16 `E16.9`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T426/build` and `python tools/axtest.py --compiler build-snap-T426/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
