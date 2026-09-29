---
id: T091
title: E23.2 v1.0 conformance audit & release certification
phase: P23-v1-0-conformance-freeze-release
owner: axiom-architect
reviewer: axiom-qa
depends: [T223]
priority: 140
status: todo
attempts: 0
paths: [spec/RELEASE-v1.md, spec/decisions]
spec: [0150, 0151, tasks/0602, 0121]
---
# T091 — v1.0 conformance audit & release certification

## Goal
Audit spec vs implementation and certify Axiom v1.0 bootstrap.

## Scope
- Contradiction audit update, list of unimplemented spec areas with follow-up tasks, release notes.

## Acceptance
- [ ] Release document; follow-up tasks filed.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T091-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Roadmap epic E23.2. Implemented in `compiler/` (Axiom) / `std/` — axiom0 is frozen after T087 (ROADMAP R3).
- The P11/P23 planning task may split this task further; keep its id for the first slice.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
