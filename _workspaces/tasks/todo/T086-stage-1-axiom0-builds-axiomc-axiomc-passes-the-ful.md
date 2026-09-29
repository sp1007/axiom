---
id: T086
title: Stage-1: axiom0 builds axiomc; axiomc passes the full suite
phase: P10-selfhost
owner: axiom-qa
reviewer: axiom-qa
depends: [T085]
priority: 120
status: todo
attempts: 0
paths: [tools/bootstrap.py, tests/selfhost/stage1]
spec: [0167, 0150, tasks/0371]
---
# T086 — Stage-1: axiom0 builds axiomc; axiomc passes the full suite

## Goal
The Axiom compiler, written in Axiom, works.

## Scope
- tools/bootstrap.py builds axiomc with axiom0; test runner runs the full suite with `--compiler axiomc`.

## Acceptance
- [ ] Full suite green with axiomc.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T086-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
