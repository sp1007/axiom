---
id: T076
title: Self-hosting plan: feature audit, compiler/ layout, differential strategy
phase: P10-selfhost
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T075]
priority: 110
status: todo
attempts: 0
paths: [spec/SPEC-20-selfhost.md, _workspaces/tasks/todo]
spec: [0167, 0150, tasks/0260, tasks/0261, tasks/0371, tasks/0473]
---
# T076 — Self-hosting plan: feature audit, compiler/ layout, differential strategy

## Goal
Plan the port of axiom0 to Axiom (axiomc).

## Scope
- Audit which language/library features the port needs vs implemented; create gap tasks; define compiler/ layout mirroring axiom0 modules; differential plan per module (tokens/AST/HIR/MIR/bytes).

## Acceptance
- [ ] Spec + gap tasks filed with dependencies; board validates.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T076-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- ROADMAP R3: after T087 axiom0 is frozen (bug fixes for bootstrapping only); all P11+ work happens in compiler/ + std/. Design compiler/ so every later epic has a natural home.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
