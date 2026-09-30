---
id: T087
title: Stage-2/3 fixed point + reproducible bootstrap
phase: P10-selfhost
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: sonnet
depends: [T086]
priority: 121
status: todo
attempts: 0
paths: [tools/bootstrap.py, tests/selfhost/fixedpoint, spec/BOOTSTRAP.md]
spec: [0167, tasks/0473, 0150]
---
# T087 — Stage-2/3 fixed point + reproducible bootstrap

## Goal
axiomc compiles itself to a fixed point.

## Scope
- axiomc1 (by axiom0) → axiomc2 → axiomc3; axiomc2 and axiomc3 byte-identical; document trust chain and reproduction steps.

## Acceptance
- [ ] Fixed point reached and verified in CI.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T087-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
