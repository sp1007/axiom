---
id: T314
title: Phase P14 gate — Comptime 2.0, reflection, generators
phase: P14-comptime-2-0-reflection-genera
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T214, T058]
priority: 314
status: todo
attempts: 0
paths: [tests/conformance/p14, _workspaces/reports/phase-P14-review.md]
spec: [spec/ROADMAP.md]
---
# T314 — Phase P14 gate: Comptime 2.0, reflection, generators

## Goal
Certify that phase P14 meets the exit criteria of every epic in `spec/ROADMAP.md` §3 and that all
requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks.
- `reqcov.py --phase P14-comptime-2-0-reflection-genera`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p14` (index + missing cases added).
- Ask axiom-architect (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion demonstrated with commands and results in the QA report.
- [ ] Full suite green (gate rule: PASS or BLOCKED; only `xfail` entries for spec gaps with an ADR may remain); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T314-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T214, which adds every phase task as a dependency of this gate.
