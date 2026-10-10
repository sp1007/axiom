---
id: T125
title: "Views & capabilities: view/mut_view, regions, conflicts, escapes"
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T124]
priority: 68
status: done
attempts: 1
paths: [bootstrap/axiom0/src/own/cap, bootstrap/axiom0/src/types, bootstrap/axiom0/src/own/own.c, bootstrap/axiom0/src/mir/build/builder.c, bootstrap/axiom0/src/resolve/resolve.c, tests/ui/cap, tests/run/cap]
locks: [bootstrap/axiom0/src/diag/codes/CAP.def, bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [spec/SPEC-11-capability.md, 0177, 0021, 0028, tasks/0395]
started: 2026-10-10 19:53:01
finished: 2026-10-10 22:45:17
---
# T125 — Views & capabilities: view/mut_view, regions, conflicts, escapes

## Goal
Capability semantics that make views safe without a borrow checker clone.

## Scope
- view<T>/mut_view<T> types, ephemeral views at call sites, explicit `view(x)`/`mut_view(x)`, region relation computation (DISJOINT/SAME/CONTAINS/OVERLAPS/UNKNOWN), conflict detection (mutation while viewed, overlapping mut_views), view escape via return/store.
- **Stored views** in struct fields per SPEC-11 (ADR-0004 §3): owner-outlives check, no self-reference.
- Method receivers are T053 (ADR-0006 §6); slices are T048b.

## Acceptance
- [ ] Every test-matrix row tagged T048/T125 passes.
- [ ] Stored-view tests: a cursor struct holding `view<[4]i32>` and an index is used in a loop; moving or dropping the owner while the struct is live is rejected; a self-referential struct is rejected.
- [ ] Run tests carry `// native-after: T051` (removed by T051).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T125-report.md` with exact `## Files changed`.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-10 19:53:01 started (attempt 1) T125-impl
- 2026-10-10 22:45:17 accepted by QA -> done
