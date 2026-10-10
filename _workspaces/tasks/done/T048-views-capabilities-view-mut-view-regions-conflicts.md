---
id: T048
title: Views & capabilities: view/mut_view, regions, conflicts, escapes
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T047, T123]
priority: 68
status: done
attempts: 1
paths: [bootstrap/axiom0/src/own/cap, bootstrap/axiom0/src/types, tests/ui/cap, tests/run/cap]
locks: [bootstrap/axiom0/src/diag/codes/CAP.def, bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [spec/SPEC-11-capability.md, 0177, 0021, 0028, tasks/0395]
started: 2026-10-10 19:29:20
unblocks: 1
superseded_by: T124
finished: 2026-10-10 19:33:52
---
# T048 — Views & capabilities: view/mut_view, regions, conflicts, escapes

## Goal
Capability semantics that make views safe without a borrow checker clone.

## Scope
- view<T>/mut_view<T> types, ephemeral views at call sites, explicit `view(x)`/`mut_view(x)`, region relation computation (DISJOINT/SAME/CONTAINS/OVERLAPS/UNKNOWN), conflict detection (mutation while viewed, overlapping mut_views), view escape via return/store.
- **Stored views** in struct fields per SPEC-11 (ADR-0004 §3): owner-outlives check, no self-reference.
- Method receivers are T053 (ADR-0006 §6); slices are T048b.

## Acceptance
- [ ] Every test-matrix row tagged T048 passes (0263 §39 first capability test).
- [ ] Stored-view tests: a cursor struct holding `view<[4]i32>` and an index is used in a loop; moving or dropping the owner while the struct is live is rejected; a self-referential struct is rejected.
- [ ] Run tests carry `// native-after: T051` (removed by T051).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T048-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-10 18:49:15 started (attempt 1) T048-impl
- 2026-10-10 18:58:27 block: missing MIR region representation and capability tracker structures
- 2026-10-10 18:59:24 unblocked (cycle 1) 
- 2026-10-10 19:29:20 started (attempt 1) T048-impl
- 2026-10-10 19:32:23 block: need to implement view tracking in own.c and syntax/typeck
- 2026-10-10 19:33:52 superseded by T124 -> done (no code of its own)
