---
id: T445
title: Fix — move out of a mut_view field then re-assign drops the moved value (FU-4); method call on a mut_view parameter treated as a move (FU-6)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T452]
priority: 22
status: todo
attempts: 0
timeout_min: 900
paths: [compiler/own/move.ax, compiler/own/init.ax, compiler/mir/drop.ax, tests/run/own_mut_view_fields, tests/ui/own_mut_view_receiver]
locks: [compiler/own/cap.ax, compiler/types/typeck.ax, compiler/mir/builder.ax, tests/selfhost]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/SPEC-10-ownership.md, spec/SPEC-11-capability.md, spec/SPEC-12-drop.md]
covers: [REQ-TST-072, REQ-TST-032, REQ-TST-034]
---
# T445 — Fix: moves and drops through `mut_view` fields and receivers

## Goal
Partial moves out of a field reached through a `mut_view` and re-initialisation of that field follow SPEC-10/12
(no drop of an already moved-out value), and calling a method on a `mut_view` parameter does not consume the
parameter (T421 FU-4, FU-6; ADR-0042 §2).

## Scope
- FU-4 repro (T421 report): `match self.guard { Option.Some(g) => { ... self.guard = Option.Some(g2) } }` where
  `self: mut_view<S>` runs `Drop` on the old, already moved-out `g` (a mutex guard was released early). Expected per
  SPEC-12: the assignment drops the old value only if it is initialised; after a move out it is not; or the move out
  of a `mut_view` place is rejected if SPEC-10 forbids it — read SPEC-10/12 and implement exactly one, citing the rule.
- FU-6 repro: `cx.waker()` on `cx: mut_view<Context>` makes a later use of `cx` report `AX_MOVE_USE_AFTER_MOVE`;
  a view/mut_view parameter is reborrowed for a `self: view<...>`/`mut_view<...>` receiver, never moved.
- Run tests `tests/run/own_mut_view_fields/*.ax` (drop order printed, interp/native/native-O1, exact `// stdout:`),
  UI tests `tests/ui/own_mut_view_receiver/*.ax` (positive compile, and the negative counterpart still diagnosed).
- Regenerate the selfhost bundles that embed edited modules with their generators.

## Acceptance
- [ ] FU-4 program prints the drop sequence required by SPEC-12 (or the spec'd diagnostic) in all modes.
- [ ] FU-6 program compiles; a real use-after-move of a by-value parameter is still `AX_MOVE_USE_AFTER_MOVE`.
- [ ] `tests/run/own*`, `tests/ui/own*`, `tests/run/drop*`, `tests/std/async` pass.
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline; WEAK-NATIVE 0 for new tests.
- [ ] Report `_workspaces/reports/T445-report.md` with exact `## Files changed`.

## Out of scope
- `std/` workarounds (T421a/T422c), `bootstrap/axiom0`, `docs/`.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §2; T421 FU-4, FU-6)
