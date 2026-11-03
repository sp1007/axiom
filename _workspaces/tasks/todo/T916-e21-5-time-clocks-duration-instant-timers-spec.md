---
id: T916
title: E21.5 Canonical monotonic/wall clocks, Duration/Instant/SystemTime & deadline timer specification (SPEC-124)
phase: P21-standard-library-completion
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T221, T311, T313]
priority: 226
status: todo
attempts: 0
paths: [spec/SPEC-124-time-clocks-timers.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [tasks/0440, tasks/0464]
covers: [REQ-RT-150, REQ-RT-151, REQ-RT-152, REQ-RT-153, REQ-RT-176, REQ-RT-586, REQ-RT-587, REQ-RT-588, REQ-RT-589, REQ-RT-590, REQ-RT-591, REQ-RT-592, REQ-RT-593, REQ-RT-594, REQ-RT-595, REQ-RT-596, REQ-RT-597, REQ-RT-598, REQ-RT-599, REQ-RT-600]
---
# T916 — E21.5 Canonical monotonic/wall clocks, Duration/Instant/SystemTime & deadline timer specification (SPEC-124)

## Goal
Consolidate the canonical specification for Axiom's temporal model—`Duration`, monotonic `Instant`, civil `SystemTime`, checked/saturating time arithmetic, hierarchical timer wheels, and deterministic `MockClock`—into `spec/SPEC-124-time-clocks-timers.md` (`AXS-TIM-*` rule IDs).

## Scope
- Write `spec/SPEC-124-time-clocks-timers.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-TIM-NNN` rules.
- Specify the strict type separation between elapsed span (`Duration`), monotonic point in time (`Instant`, backed by `QueryPerformanceCounter` on Windows and `CLOCK_MONOTONIC` on Linux; never moves backward; `REQ-RT-150`, `REQ-RT-151`), and wall-clock time (`SystemTime`, `UtcDateTime`, subject to NTP/leap adjustments; `tasks/0440 §3-18`).
- Specify checked, saturating, and trapping temporal arithmetic (`Instant + Duration -> Instant`, `Instant - Instant -> Duration`, `checked_duration_since`, `saturating_duration_since`; `REQ-RT-152`) and the memory-model invariant that `sleep`/time passage never substitutes for atomic/mutex synchronization (`REQ-RT-153`).
- Specify deadline scheduling (`Deadline`, hierarchical hashed timer wheels, `Interval` ticks with missed-tick policies `Burst|Delay|Skip`, real-time non-allocating clock profiles, and deterministic `MockClock` for reproducible testing; `tasks/0464 §3-20`, `REQ-RT-176`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-124-time-clocks-timers.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-TIM-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T916-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of clocks, civil calendar formatting, and timer wheels (`T917`–`T918`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T916/build` and `python tools/axtest.py --compiler build-snap-T916/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
