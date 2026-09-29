---
id: T052
title: P6 gate: adversarial semantic suite
phase: P6-ownership
owner: axiom-qa
reviewer: axiom-qa
depends: [T051]
priority: 72
status: todo
attempts: 0
paths: [tests/conformance/adversarial, tests/conformance/stress]
spec: [0026, 0022, 0019, 0020, 0028, 0017]
---
# T052 — P6 gate: adversarial semantic suite

## Goal
Attack the ownership/capability implementation with the adversarial cases from the specs.

## Scope
- Port 0026 adversarial tests + relevant 0022 stress tests into canonical syntax; report every divergence as finding or spec gap.

## Acceptance
- [ ] Suite passes or every failure has a filed follow-up task.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T052-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
