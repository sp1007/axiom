---
id: T315
title: Phase P15 gate — Optimizer 2.0
phase: P15-optimizer-2-0
owner: axiom-qa
reviewer: axiom-architect
depends: [T215, T063, T064]
priority: 315
status: todo
attempts: 0
paths: [tests/conformance/p15, _workspaces/reports/phase-P15-review.md]
spec: [spec/ROADMAP.md]
---
# T315 — Phase P15 gate: Optimizer 2.0

## Goal
Certify that phase P15 meets the exit criteria of every epic in `spec/ROADMAP.md` §3 and that all
requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks.
- `reqcov.py --phase P15-optimizer-2-0`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p15` (index + missing cases added).
- Ask axiom-architect (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion demonstrated with commands and results in the QA report.
- [ ] Full suite green; `reqcov.py --strict` exits 0.
- [ ] Report `_workspaces/reports/T315-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T215, which adds every phase task as a dependency of this gate.
