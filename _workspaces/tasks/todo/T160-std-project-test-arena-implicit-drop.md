---
id: T160
title: Project-mode std test - the real std.core.arena Arena is dropped implicitly (replaces the copied-Arena evidence of T141)
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T146]
priority: 115
status: todo
attempts: 0
paths: [tests/std/project]
spec: [spec/SPEC-12-drop.md, spec/decisions/ADR-0006-bootstrap-forms-manifest-std-root.md]
covers: [REQ-LAY-047, REQ-DRP-051]
---
# T160 — Project-mode std test for `Arena` implicit drop

## Goal
T141's acceptance ("a value of `std.core.arena`'s `Arena`, or a type owning one, is dropped
implicitly") is only met loosely: `tests/run/drop/arena_implicit_drop.ax` tests a local copy of
`Arena`, because single-file programs load only `std.core.host` and the prelude
(`driver/pipeline.c` `stage_source`), and `tests/std/arena/*` inline copies for the same reason.
Prove it with the real module through project mode (`axiom.toml` + std root, ADR-0006), which
`tests/modules/std_root.test` already exercises.

## Scope
- A project test under `tests/std/project/arena_drop/` (`axiom.toml`, `src/main.ax`) that imports
  `std.core.arena.arena.Arena` (exact path per the std tree), allocates from it in a function and in a
  struct that owns an `Arena`, and observes the implicit drop (for example a counter of live chunks
  exposed by the module, or a destructor of an owning wrapper printing after the arena's own
  bookkeeping — whatever the real API allows without changing `std/`).
- A `.test` manifest running it with `{compiler}` in interp and native (`run` and `build` + execute),
  with a hand-derived expected stdout and exit code.
- Keep `tests/run/drop/arena_implicit_drop.ax` (it remains valid scalar-field-drop evidence); the
  report states that T141's arena criterion is now met by this test.

## Acceptance
- [ ] `python tools/axtest.py --compiler build/axiom0.exe --filter std/project` passes in
      `build-snap-T160`; a spot mutation of the expected stdout fails in both legs (native evidence,
      axiom-qa Gate 4a).
- [ ] No file under `std/` or `bootstrap/` changes; if the real API cannot show the drop, report it in
      `## Follow-ups` instead of adding API.
- [ ] Full suite passes; report `_workspaces/reports/T160-report.md` with exact `## Files changed`.

## Out of scope
- Making single-file tests import std (driver change; not needed for self-host).

## Notes
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
