---
id: T311
title: Phase P11 gate — Concurrency & async
phase: P11-concurrency-async
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: sonnet
depends: [T211, T088, T089, T090]
priority: 311
status: todo
attempts: 0
paths: [tests/conformance/p11, _workspaces/reports/phase-P11-review.md]
spec: [spec/ROADMAP.md]
---
# T311 — Phase P11 gate: Concurrency & async

## Goal
Certify that phase P11 meets the exit criteria of every epic in `spec/ROADMAP.md` §3 and that all
requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks.
- `reqcov.py --phase P11-concurrency-async`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p11` (index + missing cases added).
- Ask axiom-architect (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion demonstrated with commands and results in the QA report.
- [ ] Full suite green; `reqcov.py --strict` exits 0.
- [ ] Report `_workspaces/reports/T311-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T211, which adds every phase task as a dependency of this gate.
