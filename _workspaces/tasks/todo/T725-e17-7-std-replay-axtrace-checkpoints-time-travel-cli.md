---
id: T725
title: E17.7 std.replay (.axtrace recorder/replayer, state checkpoints & time-travel query engine) & axiom replay CLI
phase: P17-debugging-runtime-introspectio
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T217, T316, T712, T724]
priority: 196
status: todo
attempts: 0
paths: [std/replay, compiler/driver/replay_cmd, tests/run/replay]
spec: [spec/SPEC-98-trace-replay.md, 0147, tasks/1058, tasks/0694]
covers: [REQ-DBG-116, REQ-DBG-121]
---
# T725 — E17.7 std.replay (.axtrace recorder/replayer, state checkpoints & time-travel query engine) & axiom replay CLI

## Goal
Implement the std.replay native record/replay runtime (.axtrace writer/reader, scheduler/clock/RNG/IO replay injectors, checkpoints, and time-travel queries) and the axiomc replay CLI.

## Scope
- Implement `std.replay` (`ReplaySession`, `.axtrace` binary event-log encoder/decoder, deterministic replay hooks for `std.sys` clock/RNG/file/network and `std.sync`/executor scheduling, periodic state checkpoints, and divergence detection).
- Implement `compiler/driver/replay_cmd` (`axiomc replay --record`, `axiomc replay --replay`, `--reverse-step`, `--reverse-continue`, and `--last-writer <addr/var>`) integrated with `compiler/debug/symbolicate`.
- Add end-to-end native record/replay tests in `tests/run/replay`.

## Acceptance
- [ ] Native programs recorded with `axiomc replay --record` replay identically under `axiomc replay --replay` across clock reads, RNG calls, file I/O, and multi-task schedules.
- [ ] `axiomc replay` supports `--reverse-step` and `--last-writer` queries and detects trace divergence with a clear diagnostic.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T725-report.md` with exact `## Files changed`.

## Out of scope
- P17 phase gate review (`T317`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
