---
id: T312
title: Phase P12 gate — Numeric, floating point & SIMD
phase: P12-numeric-floating-point-simd
owner: axiom-qa
reviewer: axiom-architect
depends: [T212]
priority: 312
status: todo
attempts: 0
paths: [tests/conformance/p12, _workspaces/reports/phase-P12-review.md]
spec: [spec/ROADMAP.md]
---
# T312 — Phase P12 gate: Numeric, floating point & SIMD

## Goal
Certify that phase P12 meets the exit criteria of every epic in `spec/ROADMAP.md` §3 and that all
requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks.
- `reqcov.py --phase P12-numeric-floating-point-simd`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p12` (index + missing cases added).
- Ask axiom-architect (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion demonstrated with commands and results in the QA report.
- [ ] Full suite green; `reqcov.py --strict` exits 0.
- [ ] Report `_workspaces/reports/T312-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T212, which adds every phase task as a dependency of this gate.
