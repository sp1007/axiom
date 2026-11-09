---
id: T942
title: E21.10 — macOS and iOS kqueue / kevent64 async reactor & EVFILT_TIMER integration
phase: P21-standard-library-completion
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T940, T667]
priority: 254
status: todo
attempts: 0
paths: [std/async/reactor/darwin, tests/run/darwin_reactors]
spec: [spec/SPEC-129-cross-os-async-reactors.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-RT-156, REQ-ASY-158]
---
# T942 — E21.10 — macOS and iOS kqueue / kevent64 async reactor & EVFILT_TIMER integration

## Goal
Implement the macOS and iOS native asynchronous I/O reactor using `kqueue` and `kevent64` system calls, integrating edge-triggered socket polling and kernel timer queues.

## Scope
- Implement `std/async/reactor/darwin`:
  * Initialize kernel event queue with `kqueue()`.
  * Register file descriptors and sockets for read/write interest using `EVFILT_READ` and `EVFILT_WRITE` filters with `EV_ADD | EV_ENABLE | EV_CLEAR` flags.
  * Use `kevent64` for batched event dequeueing with 64-bit user data (`udata`) carrying async task wakers.
  * Implement async sleep and deadline timers using `EVFILT_TIMER` with nanosecond precision (`NOTE_NSECONDS`), eliminating the need for background timer threads.
- Support async socket I/O (`accept`, `connect`, `recv`, `send`) with non-blocking error handling (`EWOULDBLOCK`, `EAGAIN`).

## Acceptance
- [ ] Run tests in `tests/run/darwin_reactors` verify async socket TCP communications and precise timer scheduling under macOS AArch64 / Darwin mock harness.
- [ ] Conformance tests verify graceful cancellation of pending kqueue read/write operations without descriptor leaks.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T942-report.md` with exact `## Files changed`.

## Out of scope
- Mach port IPC integration (reserved for post-v1).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T942/build` and `python tools/axtest.py --compiler build-snap-T942/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:30:00 created by axiom-architect (ADR-0039 P21 async reactors expansion)
