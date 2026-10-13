---
id: T077b
title: Port source DB to Axiom (source manager, span decoding, line/col lookup)
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T076]
priority: 111
status: done
attempts: 1
paths: [compiler/source, tests/selfhost/source]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-DRV-021]
started: 2026-10-14 03:45:14
finished: 2026-10-14 04:53:13
---
# T077b — Port source DB to Axiom (source manager, span decoding, line/col lookup)

## Goal
Port source text management and span tracking (`compiler/source/`) from C to Axiom.

## Scope
- Port source span representation, file loader, line table indexing, and source database to Axiom.
- Ensure byte offset to line/column translation is identical to `bootstrap/axiom0/src/source/`.
- Unit tests under `tests/selfhost/source/`.

## Acceptance
- [ ] Source manager implemented in `compiler/source/` with ≤ 1,500 lines of Axiom.
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Differential test verifies span line/column lookup matches `axiom0`.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T077b-report.md` with exact `## Files changed`.

## Out of scope
- Diagnostics formatting (handled in T077c).

## Notes
- Sub-task of T077 split per ADR-0005 §8 and SPEC-20 §4.1.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-14 03:45:14 started (attempt 1) 
- 2026-10-14 04:53:13 accepted by QA -> done
