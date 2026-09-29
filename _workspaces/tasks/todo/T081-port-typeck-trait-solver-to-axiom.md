---
id: T081
title: Port typeck + trait solver to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
depends: [T080]
priority: 115
status: todo
attempts: 0
paths: [compiler/typeck_traits, tests/selfhost/typeck_traits]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
---
# T081 — Port typeck + trait solver to Axiom

## Goal
Port typeck + trait solver to Axiom, keeping behaviour identical to the C implementation.

## Scope
- Idiomatic canonical Axiom port of the corresponding axiom0 modules; same data model and diagnostics codes.
- Differential test harness comparing outputs with axiom0 over the whole tests/ corpus.

## Acceptance
- [ ] Differential equality over the corpus (documented counts); module tests pass in interp and native.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T081-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
