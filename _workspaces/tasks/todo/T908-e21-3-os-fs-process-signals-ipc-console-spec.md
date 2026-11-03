---
id: T908
title: E21.3 Canonical OS filesystem, process, env, signals, IPC & console/ConPTY IO specification (SPEC-122)
phase: P21-standard-library-completion
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T221, T311, T313]
priority: 218
status: todo
attempts: 0
paths: [spec/SPEC-122-os-fs-process-signals-ipc.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [tasks/0335, tasks/0443, tasks/0840]
covers: [REQ-STD-173, REQ-RT-001, REQ-RT-002, REQ-RT-003, REQ-RT-004, REQ-RT-005, REQ-RT-006, REQ-RT-007, REQ-RT-008, REQ-RT-009, REQ-RT-010, REQ-RT-011, REQ-RT-012, REQ-RT-013, REQ-RT-015, REQ-RT-016, REQ-RT-017, REQ-RT-018, REQ-RT-019, REQ-RT-020, REQ-RT-021, REQ-RT-132, REQ-RT-133, REQ-RT-134]
---
# T908 — E21.3 Canonical OS filesystem, process, env, signals, IPC & console/ConPTY IO specification (SPEC-122)

## Goal
Consolidate the canonical specification for Axiom's complete OS abstraction layer—filesystem durability, positional I/O, file locks, process pipelines, environment, signal handling, IPC channels, and Windows `WriteConsoleW`/ConPTY console I/O (`ADR-0034` §8 OI-13)—into `spec/SPEC-122-os-fs-process-signals-ipc.md` (`AXS-OS-*` rule IDs).

## Scope
- Write `spec/SPEC-122-os-fs-process-signals-ipc.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-OS-NNN` rules.
- Specify move-only OS resource ownership (`File`, `ChildProcess`, `PipeReader`, `PipeWriter`, `NamedPipe`, `SharedMem`; `tasks/0335 §3-18`, `tasks/0443 §1-14`, `tasks/0840 §1-12`, `REQ-STD-173`, `REQ-RT-144`, `REQ-RT-158`..`REQ-RT-163`), distinguishing `ProcessId` value identity from `ChildProcess` handle ownership and `Drop` cleanup vs explicit fallible `sync_all`/`close`.
- Specify positional random-access file I/O (`read_at`, `write_at` without mutating file seek cursor; `REQ-RT-159`), advisory/mandatory file locking (`lock_shared`, `lock_exclusive`, `try_lock`), atomic file replacement (`AtomicWriteFile`), symlink/hardlink inspection, and filesystem change notifications.
- Specify child process spawning (`Command` builder, explicit argv array without implicit shell interpolation, environment/cwd isolation, piped stdin/stdout/stderr), signal notification channels (`CtrlC` / `SIGTERM` / `SIGINT` delivered as synchronous/async event streams rather than arbitrary re-entrant callbacks; `REQ-RT-149`), and anonymous/named pipe & shared-memory IPC (`tasks/0443 §15-28`).
- Specify the hosted console vs redirected pipe I/O contract (`ADR-0006`, `ADR-0034` §8 OI-13): `GetConsoleMode` detection on Windows standard handles, UTF-8 → UTF-16 `WriteConsoleW` / `ReadConsoleW` when attached to a console/ConPTY vs raw UTF-8 `WriteFile` when redirected to a pipe/file, and the mandatory `CreatePseudoConsole` (ConPTY) verification contract for `Xin chào thế giới`.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-122-os-fs-process-signals-ipc.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-OS-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T908-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of extended filesystem, process, IPC, and ConPTY console modules (`T909`–`T910`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T908/build` and `python tools/axtest.py --compiler build-snap-T908/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
