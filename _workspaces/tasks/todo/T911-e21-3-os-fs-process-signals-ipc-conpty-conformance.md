---
id: T911
title: E21.3 OS filesystem, process, signals, IPC & ConPTY WriteConsoleW conformance suite
phase: P21-standard-library-completion
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T910]
priority: 221
status: todo
attempts: 0
paths: [tests/conformance/p21/e21_3_os_fs_process_ipc]
spec: [spec/SPEC-122-os-fs-process-signals-ipc.md, tasks/0335, tasks/0443, tasks/0840]
covers: [REQ-STD-173, REQ-RT-132, REQ-RT-133, REQ-RT-134, REQ-RT-136, REQ-RT-137, REQ-RT-144, REQ-RT-145, REQ-RT-146, REQ-RT-147, REQ-RT-148, REQ-RT-149, REQ-RT-158, REQ-RT-159, REQ-RT-160, REQ-RT-161, REQ-RT-162, REQ-RT-163]
---
# T911 — E21.3 OS filesystem, process, signals, IPC & ConPTY WriteConsoleW conformance suite

## Goal
Certify E21.3 exit criteria and `ADR-0034` §8 OI-13 with an end-to-end OS conformance suite covering filesystem durability, positional I/O, process pipelines, signals, IPC, and Windows ConPTY `WriteConsoleW` output of `Xin chào thế giới`.

## Scope
- Create conformance tests in `tests/conformance/p21/e21_3_os_fs_process_ipc` verifying move-only `File` and `ChildProcess` handle lifecycle (`Drop` closes descriptors deterministically; `REQ-RT-158`, `REQ-RT-161`..`REQ-RT-163`), `read_at`/`write_at` positional concurrency (`REQ-RT-159`), and `AtomicWriteFile` durability (`REQ-RT-160`, `REQ-STD-173`).
- Verify multi-stage child process pipelines, environment variable isolation (`REQ-RT-148`), signal notification delivery (`REQ-RT-149`), and bidirectional IPC over anonymous/named pipes.
- Verify `ADR-0034` §8 (audit 2026-10-19 OI-13): run an automated Windows `CreatePseudoConsole` (ConPTY) test confirming `is_terminal() == true`, exercising the `WriteConsoleW` UTF-16 console path (distinct from the redirected pipe `WriteFile` path), and asserting the exact rendered `Xin chào thế giới` output.
- Verify differential agreement between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p21/e21_3_os_fs_process_ipc` (including the automated ConPTY `WriteConsoleW` check for `Xin chào thế giới`) pass with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T911-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T911/build` and `python tools/axtest.py --compiler build-snap-T911/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
