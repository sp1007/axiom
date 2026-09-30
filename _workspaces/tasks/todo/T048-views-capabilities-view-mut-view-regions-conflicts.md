---
id: T048
title: Views & capabilities: view/mut_view, regions, conflicts, escapes
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T047]
priority: 68
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/own/cap, bootstrap/axiom0/src/types, tests/ui/cap, tests/run/cap]
spec: [spec/SPEC-11-capability.md, 0177, 0021, 0028, tasks/0395]
---
# T048 — Views & capabilities: view/mut_view, regions, conflicts, escapes

## Goal
Capability semantics that make views safe without a borrow checker clone.

## Scope
- view<T>/mut_view<T> types, ephemeral views at call sites, explicit `view(x)`/`mut_view(x)`, region relation computation (DISJOINT/SAME/CONTAINS/OVERLAPS/UNKNOWN), conflict detection (mutation while viewed, overlapping mut_views), view escape via return/store, method receivers.
- Dynamic-length views (slices) in the spec's form (e.g. `view<[T]>` / `mut_view<[T]>`): array → slice coercion, `len`, bounds-checked indexing, sub-range views `s[a..b]` with checked bounds, disjoint split of a mut_view (`split_at_mut`-style) accepted by the region analysis.

## Acceptance
- [ ] Slice tests: sum over `view<[i32]>` of an array, sub-range views, out-of-range sub-view panics, two overlapping mut sub-views rejected, disjoint split accepted.
- [ ] Test matrix rows for capability pass (0263 §39 first capability test).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T048-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
