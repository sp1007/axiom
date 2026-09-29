---
id: T022
title: VS0 gate: subset conformance on the oracle
phase: P3-semantic-core
owner: axiom-qa
reviewer: axiom-qa
depends: [T021, T016]
priority: 35
status: todo
attempts: 0
paths: [tests/conformance/vs0, tools/ci.sh]
spec: [0263, 0114, 0017]
---
# T022 — VS0 gate: subset conformance on the oracle

## Goal
Prove the whole front half works end-to-end before any native code exists.

## Scope
- Port the 0263 first-test set and applicable 0114 E2E cases into tests/conformance/vs0 (canonical syntax).
- Seam review: parser↔HIR↔THIR↔MIR exhaustiveness (every node kind lowered or diagnosed).

## Acceptance
- [ ] All VS0 tests pass in interp mode; seam review written in the QA report with any gaps filed as follow-ups.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T022-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
