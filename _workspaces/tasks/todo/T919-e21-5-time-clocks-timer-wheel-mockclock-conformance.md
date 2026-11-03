---
id: T919
title: E21.5 Monotonic/wall clocks, temporal arithmetic, timer wheels & MockClock conformance suite
phase: P21-standard-library-completion
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T918]
priority: 229
status: todo
attempts: 0
paths: [tests/conformance/p21/e21_5_time_clocks]
spec: [spec/SPEC-124-time-clocks-timers.md, tasks/0440, tasks/0464]
covers: [REQ-RT-150, REQ-RT-151, REQ-RT-152, REQ-RT-153, REQ-RT-176, REQ-RT-636, REQ-RT-637, REQ-RT-638, REQ-RT-639, REQ-RT-640, REQ-RT-641, REQ-RT-642, REQ-RT-643, REQ-RT-644, REQ-RT-645, REQ-RT-646, REQ-RT-647]
---
# T919 — E21.5 Monotonic/wall clocks, temporal arithmetic, timer wheels & MockClock conformance suite

## Goal
Certify E21.5 exit criteria with an end-to-end temporal conformance suite covering `Duration`, `Instant` vs `SystemTime`, checked/saturating arithmetic, RFC 3339 calendar rules, hierarchical timer wheels, and `MockClock`.

## Scope
- Create conformance tests in `tests/conformance/p21/e21_5_time_clocks` verifying `Duration` vs `Instant` vs `SystemTime` separation (`REQ-RT-150`), monotonic non-decreasing guarantee (`REQ-RT-151`), and checked/saturating overflow contracts (`REQ-RT-152`).
- Verify pre-allocated zero-allocation timer wheel operation under real-time constraints (`REQ-RT-176`), `MockClock` simulated wall-clock backward jumps (NTP step resilience), and RFC 3339 edge dates.
- Verify differential agreement between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p21/e21_5_time_clocks` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T919-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T919/build` and `python tools/axtest.py --compiler build-snap-T919/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
