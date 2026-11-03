---
id: T918
title: E21.5 Hierarchical timer wheels, Deadline, Sleep/Interval & deterministic MockClock
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T916, T917]
priority: 228
status: todo
attempts: 0
paths: [std/time/timer_wheel, std/time/deadline, std/time/mock_clock, tests/run/std_time_timers]
spec: [spec/SPEC-124-time-clocks-timers.md, tasks/0440, tasks/0464]
covers: [REQ-RT-153, REQ-RT-176, REQ-RT-621, REQ-RT-622, REQ-RT-623, REQ-RT-624, REQ-RT-625, REQ-RT-626, REQ-RT-627, REQ-RT-628, REQ-RT-629, REQ-RT-630, REQ-RT-631, REQ-RT-632, REQ-RT-633, REQ-RT-634, REQ-RT-635]
---
# T918 — E21.5 Hierarchical timer wheels, Deadline, Sleep/Interval & deterministic MockClock

## Goal
Implement O(1) hierarchical timer wheels, `Deadline` budgets, periodic `Interval` timers, and deterministic `MockClock` in `std.time` per `spec/SPEC-124-time-clocks-timers.md`.

## Scope
- Implement `std/time/timer_wheel` (4-level hashed hierarchical timer wheel with 64-slot wheels, O(1) timer insertion/cancellation by generational `TimerId`, and zero heap allocation after pre-sizing for real-time profiles; `tasks/0464 §8-16`, `REQ-RT-176`).
- Implement `std/time/deadline` (`Deadline`, `TimeoutError`, `MissedTickBehavior.Burst|Delay|Skip`, and periodic `Interval` ticker).
- Implement `std/time/mock_clock` (`Clock` trait, `SystemClock`, and `MockClock` with `advance(Duration)` and `set_wall_time(SystemTime)` so timeout/retry/rate-limiter logic can be tested deterministically without real wall-clock sleeps; `REQ-RT-153`).
- Add run tests in `tests/run/std_time_timers`.

## Acceptance
- [ ] Run tests in `tests/run/std_time_timers` verify hierarchical timer wheel expiration ordering, O(1) cancellation, `MissedTickBehavior` (`Burst`, `Delay`, `Skip`), and deterministic `MockClock` advancement in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T918-report.md` with exact `## Files changed`.

## Out of scope
- OS kernel driver hard-RTOS scheduling (`P24`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T918/build` and `python tools/axtest.py --compiler build-snap-T918/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
