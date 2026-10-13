---
id: T077c
title: Port diagnostics emitter to Axiom (codes, formatters, json)
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T076]
priority: 111
status: done
attempts: 1
paths: [compiler/diag, tests/selfhost/diag]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-DRV-020]
started: 2026-10-14 03:45:15
finished: 2026-10-14 06:54:02
---
# T077c — Port diagnostics emitter to Axiom (codes, formatters, json)

## Goal
Port compiler diagnostic reporting and error emission (`compiler/diag/`) from C to Axiom.

## Scope
- Port diagnostic code taxonomy (ADR-0011), diagnostic sink, text span highlighter, and `--json` diagnostic serializer to Axiom.
- Ensure text and JSON diagnostic formats are identical to `bootstrap/axiom0/src/diag/`.
- Unit tests under `tests/selfhost/diag/`.

## Acceptance
- [ ] Diagnostic emitter implemented in `compiler/diag/` with ≤ 1,500 lines of Axiom.
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Differential test verifies byte-identical `--json` diagnostic output on error fixtures.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T077c-report.md` with exact `## Files changed`.

## Out of scope
- Parsing or type checking error generation logic (handled in respective phases).

## Notes
- Sub-task of T077 split per ADR-0005 §8 and SPEC-20 §4.1.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-14 03:45:15 started (attempt 1) 
- 2026-10-14 06:54:02 accepted by QA -> done
