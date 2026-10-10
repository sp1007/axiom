---
id: T048b
title: Slices: dynamic-length views
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T125]
priority: 68
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/own/cap, bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, tests/run/slice, tests/ui/slice]
locks: [bootstrap/axiom0/src/diag/codes/CAP.def, bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [spec/SPEC-11-capability.md, 0177, 0021, 0028, tasks/0395, tasks/0326, 0087]
covers: []
started: 2026-10-10 22:45:58
unblocks: 1
---
# T048b — Slices: dynamic-length views

## Goal
Dynamic-length views over arrays — the type every buffer, string and collection API of the self-host std is built on (split from T048, ADR-0005 §8).

## Scope
- Slice views in the spec's form (`view<[T]>` / `mut_view<[T]>`): array → slice coercion, built-in `len`, bounds-checked indexing.
- `Str` folded into the view rules: a `Str` is a read-only view of UTF-8 bytes (0263 §39).
- Stored slice views (struct field holding `view<[T]>`) follow the T048 rule.

## Acceptance
- [ ] Slice tests: sum over `view<[i32]>` of an array.
- [ ] A slice-iterator struct `{ s: view<[u8]>, i: usize }` used in a `while` loop; rejected when the array is moved while the struct is live.
- [ ] Every test-matrix row tagged T048b passes. Run tests carry `// native-after: T051` (removed by T051).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T048b-report.md` with exact `## Files changed`.

## Out of scope
- Slice patterns; owned unsized values; `for` over slices (T072).
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-10 22:45:58 started (attempt 1) T048b-impl
- 2026-10-10 22:58:16 block: Sub-range views (s[a..b]) require introducing a new MIR projection kind and symbolic reasoning for disjoint ranges, which is too extensive for a single step.
- 2026-10-10 23:01:37 unblocked (cycle 1) 
