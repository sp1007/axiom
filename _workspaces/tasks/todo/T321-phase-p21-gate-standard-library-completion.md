---
id: T321
title: Phase P21 gate — Standard library completion
phase: P21-standard-library-completion
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: sonnet
depends: [T221]
priority: 321
status: todo
attempts: 0
paths: [tests/conformance/p21, _workspaces/reports/phase-P21-review.md]
spec: [spec/ROADMAP.md]
---
# T321 — Phase P21 gate: Standard library completion

## Goal
Certify that phase P21 meets the exit criteria of every epic in `spec/ROADMAP.md` §3 and that all
requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks.
- `reqcov.py --phase P21-standard-library-completion`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p21` (index + missing cases added).
- Ask axiom-architect (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion demonstrated with commands and results in the QA report.
- [ ] Full suite green; `reqcov.py --strict` exits 0.
- [ ] Report `_workspaces/reports/T321-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T221, which adds every phase task as a dependency of this gate.
