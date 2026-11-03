---
id: T910
title: E21.3 Process pipelines, signals, anonymous/named IPC & Windows WriteConsoleW/ConPTY runtime
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T908, T909]
priority: 220
status: todo
attempts: 0
paths: [std/process/spawn, std/os/signal, std/os/ipc, std/os/console, tests/run/std_process_ipc]
spec: [spec/SPEC-122-os-fs-process-signals-ipc.md, tasks/0335, tasks/0443]
covers: [REQ-RT-136, REQ-RT-137, REQ-RT-145, REQ-RT-146, REQ-RT-147, REQ-RT-148, REQ-RT-149, REQ-RT-161, REQ-RT-162, REQ-RT-163]
---
# T910 — E21.3 Process pipelines, signals, anonymous/named IPC & Windows WriteConsoleW/ConPTY runtime

## Goal
Implement child process spawning and pipelines, signal notification channels, anonymous/named pipes, and the Windows `WriteConsoleW` / `CreatePseudoConsole` (ConPTY) console runtime (`ADR-0034` §8 OI-13) per `spec/SPEC-122-os-fs-process-signals-ipc.md`.

## Scope
- Implement `std/process/spawn` (`Command`, `Stdio.Inherit|Piped|Null`, `ChildProcess`, `ProcessId`, `wait`, `try_wait`, `kill`, `wait_with_output`, ensuring explicit argv escaping without shell injection and distinct `ProcessId` vs `ChildProcess` ownership; `REQ-RT-145`..`REQ-RT-148`, `REQ-RT-161`..`REQ-RT-163`).
- Implement `std/os/signal` (`SignalReceiver` for `SIGINT`/`SIGTERM`/`CtrlC`/`CtrlBreak` via `SetConsoleCtrlHandler` on Windows and `signalfd`/self-pipe on Linux, delivering signals as safe channel messages without re-entrant UB; `REQ-RT-149`).
- Implement `std/os/ipc` (anonymous `pipe()`, Windows named pipes / Unix domain IPC streams, and cross-process IPC framing; `tasks/0443 §20-28`).
- Implement `std/os/console` (`ConsoleHandle`, `is_terminal` via `GetConsoleMode`, UTF-8 → UTF-16 `WriteConsoleW`/`ReadConsoleW` console path, and `PseudoConsole` wrapper around `CreatePseudoConsole`/`ResizePseudoConsole`/`ClosePseudoConsole` + `PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE`; `ADR-0034` §8 OI-13).
- Add run tests in `tests/run/std_process_ipc`, including an automated ConPTY test spawning a child Axiom binary attached to `PseudoConsole` that prints `Xin chào thế giới` via the `WriteConsoleW` path and verifies the captured UTF-8/VT output stream.

## Acceptance
- [ ] Run tests in `tests/run/std_process_ipc` verify `Command` child spawning, piped stdin/stdout pipelines, `SignalReceiver` graceful termination, anonymous/named pipe IPC, and the `CreatePseudoConsole` (ConPTY) `WriteConsoleW` path outputting `Xin chào thế giới` (`ADR-0034` §8 OI-13) with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T910-report.md` with exact `## Files changed`.

## Out of scope
- TCP/UDP networking (`E21.4`) and `VirtualAlloc`/`mmap` (`E21.6`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T910/build` and `python tools/axtest.py --compiler build-snap-T910/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
