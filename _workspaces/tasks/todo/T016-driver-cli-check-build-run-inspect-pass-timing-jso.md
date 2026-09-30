---
id: T016
title: Driver CLI: check/build/run/inspect, pass timing, JSON diagnostics
phase: P2-frontend
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T015]
priority: 26
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/driver, tests/driver]
spec: [0257, tasks/0411, 0146]
---
# T016 — Driver CLI: check/build/run/inspect, pass timing, JSON diagnostics

## Goal
Stable CLI contract for humans, tests and AI agents.

## Scope
- Commands: `check`, `build -o`, `run [--interp]`, `inspect --emit=...`, `version`, `--features` (capability probe for the runner).
- Options: `--target`, `-O0/-O1`, `--json`, `--time-passes`, `--color=never`; exit codes: 0 ok, 1 diagnostics, 2 usage, 3 ICE.
- Pipeline orchestration module that later stages plug into (stubs return 'not yet supported' diagnostics).

## Acceptance
- [ ] tests/driver cases for each command/option and exit code.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T016-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
