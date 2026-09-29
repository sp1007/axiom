---
id: T045
title: Canonical ownership / capability / drop specification
phase: P6-ownership
owner: axiom-architect
reviewer: axiom-qa
depends: [T003]
priority: 65
status: todo
attempts: 0
paths: [spec/SPEC-10-ownership.md, spec/SPEC-11-capability.md, spec/SPEC-12-drop.md]
spec: [0004, 0005, 0160, 0176, 0177, 0178, 0019, 0020, 0021, 0028, 0030, 0086, 0118, tasks/0394, tasks/0395, tasks/0674]
---
# T045 — Canonical ownership / capability / drop specification

## Goal
One precise, testable statement of Axiom's ownership model (ownership ≠ borrow checker), capabilities (view/mut_view, regions) and deterministic destruction.

## Scope
- Rules with IDs AXS-OWN/CAP/DROP-NNN: move/copy classification, place model, partial moves, init states, ephemeral vs stored views, region relations, conflicts, escape rules, drop order, drop flags, cleanup on every edge, panic interaction; a test matrix (rule → positive/negative example programs in canonical syntax).

## Acceptance
- [ ] Three specs with test matrix; ADRs for contradictions among the sources.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T045-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
