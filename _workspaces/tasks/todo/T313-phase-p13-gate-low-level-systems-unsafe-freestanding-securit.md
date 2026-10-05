---
id: T313
title: Phase P13 gate — Low-level systems, unsafe, freestanding, security
phase: P13-low-level-systems-unsafe-frees
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T213]
priority: 313
status: todo
attempts: 0
paths: [tests/conformance/p13, _workspaces/reports/phase-P13-review.md]
spec: [spec/ROADMAP.md]
covers: [REQ-SEC-123]
---
# T313 — Phase P13 gate: Low-level systems, unsafe, freestanding, security

## Goal
Certify that phase P13 meets the exit criteria of every epic in `spec/ROADMAP.md` §3 and that all
requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks.
- `reqcov.py --phase P13-low-level-systems-unsafe-frees`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p13` (index + missing cases added).
- Ask axiom-architect (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion demonstrated with commands and results in the QA report.
- [ ] Full suite green (gate rule: PASS or BLOCKED; only `xfail` entries for spec gaps with an ADR may remain); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T313-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T213, which adds every phase task as a dependency of this gate.

## Log
- 2026-10-06 02:31:20 covers += REQ-SEC-123 (metadata only)
