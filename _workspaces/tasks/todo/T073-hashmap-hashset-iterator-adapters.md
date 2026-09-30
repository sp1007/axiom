---
id: T073
title: HashMap/HashSet + iterator adapters
phase: P9-stdlib
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T071, T072, T059]
priority: 104
status: todo
attempts: 0
paths: [std/collections, std/core/iter/adapters, tests/std/collections, std/text/chars]
spec: [0045, 0210, tasks/0333]
---
# T073 — HashMap/HashSet + iterator adapters

## Goal
Collections the compiler rewrite will need.

## Scope
- HashMap/HashSet with deterministic hashing, map/filter/enumerate/zip/collect adapters, Vec iteration.

- `Str.chars()` and `Str.char_indices()` iterators on top of T071's `decode_char_at` (in `std/text/chars`).

## Acceptance
- [ ] `"Xin chào thế giới".chars().count() == 17`; `char_indices` yields byte offsets on char boundaries.
- [ ] run tests.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T073-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
