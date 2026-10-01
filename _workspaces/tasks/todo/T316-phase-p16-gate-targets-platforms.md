---
id: T316
title: Phase P16 gate — Targets & platforms
phase: P16-targets-platforms
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T216, T066]
priority: 316
status: todo
attempts: 0
paths: [tests/conformance/p16, _workspaces/reports/phase-P16-review.md]
spec: [spec/ROADMAP.md]
---
# T316 — Phase P16 gate: Targets & platforms

## Goal
Certify that phase P16 meets the exit criteria of every epic in `spec/ROADMAP.md` §3 and that all
requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks.
- `reqcov.py --phase P16-targets-platforms`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p16` (index + missing cases added).
- Ask axiom-architect (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion demonstrated with commands and results in the QA report.
- [ ] Full suite green (gate rule: PASS or BLOCKED; only `xfail` entries for spec gaps with an ADR may remain); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T316-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T216, which adds every phase task as a dependency of this gate.
