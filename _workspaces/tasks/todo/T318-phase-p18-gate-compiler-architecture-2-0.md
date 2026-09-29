---
id: T318
title: Phase P18 gate — Compiler architecture 2.0
phase: P18-compiler-architecture-2-0
owner: axiom-qa
reviewer: axiom-architect
depends: [T218, T067]
priority: 318
status: todo
attempts: 0
paths: [tests/conformance/p18, _workspaces/reports/phase-P18-review.md]
spec: [spec/ROADMAP.md]
---
# T318 — Phase P18 gate: Compiler architecture 2.0

## Goal
Certify that phase P18 meets the exit criteria of every epic in `spec/ROADMAP.md` §3 and that all
requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks.
- `reqcov.py --phase P18-compiler-architecture-2-0`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p18` (index + missing cases added).
- Ask axiom-architect (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion demonstrated with commands and results in the QA report.
- [ ] Full suite green; `reqcov.py --strict` exits 0.
- [ ] Report `_workspaces/reports/T318-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T218, which adds every phase task as a dependency of this gate.
