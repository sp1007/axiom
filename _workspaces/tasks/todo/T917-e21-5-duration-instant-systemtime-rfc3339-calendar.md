---
id: T917
title: E21.5 Duration, Instant, SystemTime, checked/saturating temporal math & RFC 3339/ISO 8601 civil time
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T916]
priority: 227
status: todo
attempts: 0
paths: [std/time/instant, std/time/system_time, std/time/calendar, tests/run/std_time_clocks]
spec: [spec/SPEC-124-time-clocks-timers.md, tasks/0440, tasks/0464]
covers: [REQ-RT-150, REQ-RT-151, REQ-RT-152, REQ-RT-153, REQ-RT-601, REQ-RT-602, REQ-RT-603, REQ-RT-604, REQ-RT-605, REQ-RT-606, REQ-RT-607, REQ-RT-608, REQ-RT-609, REQ-RT-610, REQ-RT-611, REQ-RT-612, REQ-RT-613, REQ-RT-614, REQ-RT-615, REQ-RT-616, REQ-RT-617, REQ-RT-618, REQ-RT-619, REQ-RT-620]
---
# T917 — E21.5 Duration, Instant, SystemTime, checked/saturating temporal math & RFC 3339/ISO 8601 civil time

## Goal
Implement complete `Duration`, `Instant`, `SystemTime`, checked/saturating temporal arithmetic, and RFC 3339 / ISO 8601 UTC civil calendar formatting and parsing in `std.time` per `spec/SPEC-124-time-clocks-timers.md`.

## Scope
- Implement `std/time/instant` (`Duration` nanosecond-precision 96/128-bit representation, `from_secs`, `from_millis`, `from_micros`, `from_nanos`, `checked_add`, `checked_sub`, `checked_mul`, `saturating_add`, `saturating_sub`, and monotonic `Instant.now()`, `elapsed()`, `checked_duration_since()`, `saturating_duration_since()`; `REQ-RT-150`..`REQ-RT-152`).
- Implement `std/time/system_time` (`SystemTime.now()` via `GetSystemTimePreciseAsFileTime` on Windows and `clock_gettime(CLOCK_REALTIME)` on Linux, `UNIX_EPOCH`, `duration_since_epoch`, and explicit handling of backward wall-clock steps).
- Implement `std/time/calendar` (`UtcDateTime`, `FixedOffset`, proleptic Gregorian leap-year/day-of-year calculations, and RFC 3339 / ISO 8601 timestamp formatting and parsing).
- Add run tests in `tests/run/std_time_clocks`.

## Acceptance
- [ ] Run tests in `tests/run/std_time_clocks` verify `Duration` overflow/saturation boundaries, monotonic `Instant` ordering, `SystemTime` epoch conversions, and RFC 3339 leap-year/timezone round-trips in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T917-report.md` with exact `## Files changed`.

## Out of scope
- Timer wheels, `Deadline`, and `MockClock` (`T918`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T917/build` and `python tools/axtest.py --compiler build-snap-T917/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
