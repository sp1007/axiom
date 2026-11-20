---
id: T444b
title: Fix — tuple-variant pattern with two bindings reports AX_MOVE_USE_AFTER_MOVE on the second binding
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T445]
priority: 23
status: doing
attempts: 1
timeout_min: 600
paths: [tests/run/pattern_multi_binding, tests/ui/pattern_multi_binding]
locks: [compiler/own/move.ax, compiler/own/init.ax, compiler/mir/builder.ax]
spec: [spec/decisions/ADR-0043-cyclic-type-graphs-and-symbol-id-space.md, spec/SPEC-10-ownership.md]
covers: [REQ-OWN-051, REQ-TST-072]
started: 2026-11-21 01:48:13
agent: T444b-impl
---
# T444b — Fix: two bindings in one tuple-variant pattern

## Goal
Binding several payload fields of one variant by value moves each field once (a partial move of the scrutinee), as
REQ-OWN-051 requires; the second binding is never reported as a use after move (T444 report F1).

## Scope
- Repro (baseline `axiomc2` and `axiomc1`): `enum Choice { Pair(u8, u64), ... }`; `match c { Choice.Pair(a, b) => ... }`
  reports `AX_MOVE_USE_AFTER_MOVE` on `b` with "moved here" on `a`. Expected: each binding moves (or copies) only its
  own field place; the scrutinee is partially moved afterwards.
- Check the same for struct patterns with several bindings, nested tuple-variant patterns and `if let` / `while let`.
- Tests: `tests/run/pattern_multi_binding/*.ax` (interp, native, native-O1, exact `// stdout:`) with Copy and
  non-Copy (owning, with `Drop`) payload fields — each owned field dropped exactly once; `tests/ui/pattern_multi_binding/`
  keeps a real use-after-move (using the scrutinee after a by-value binding of a non-Copy field) an error.

## Acceptance
- [ ] Run tests pass in the three modes (WEAK-NATIVE 0); ui tests report exactly the expected diagnostics.
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline.
- [ ] Report `_workspaces/reports/T444b-report.md` with the root cause and exact `## Files changed`.

## Out of scope
- Payload offsets of mixed-size fields (T444a; use same-size fields in the tests until it is done).
- `bootstrap/axiom0` (frozen), `std/`, `docs/`.

## Notes
- Depends on T445 (moves through `mut_view` fields and receivers) — same files, related move-path logic.
- If the fix lies outside the listed locks, stop and report.
- Canonical syntax (`=`, `.`), see axiom-syntax.

## Log
- 2026-11-17 created by axiom-architect (T444 report F1; ADR-0043 §4)
- 2026-11-21 01:48:13 started (attempt 1) T444b-impl
