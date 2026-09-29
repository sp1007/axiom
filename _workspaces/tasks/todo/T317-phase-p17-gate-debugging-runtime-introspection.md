---
id: T317
title: Phase P17 gate — Debugging & runtime introspection
phase: P17-debugging-runtime-introspectio
owner: axiom-qa
reviewer: axiom-architect
depends: [T217, T068]
priority: 317
status: todo
attempts: 0
paths: [tests/conformance/p17, _workspaces/reports/phase-P17-review.md]
spec: [spec/ROADMAP.md]
---
# T317 — Phase P17 gate: Debugging & runtime introspection

## Goal
Certify that phase P17 meets the exit criteria of every epic in `spec/ROADMAP.md` §3 and that all
requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks.
- `reqcov.py --phase P17-debugging-runtime-introspectio`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p17` (index + missing cases added).
- Ask axiom-architect (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion demonstrated with commands and results in the QA report.
- [ ] Full suite green; `reqcov.py --strict` exits 0.
- [ ] Report `_workspaces/reports/T317-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T217, which adds every phase task as a dependency of this gate.
