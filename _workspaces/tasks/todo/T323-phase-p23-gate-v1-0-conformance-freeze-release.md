---
id: T323
title: Phase P23 gate — v1.0 conformance, freeze & release
phase: P23-v1-0-conformance-freeze-releas
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T223, T311, T312, T313, T314, T315, T316, T317, T318, T319, T320, T321, T322, T091, T1000, T1001, T1002, T1003, T1004, T1005, T1006, T1007, T1008, T1009, T1010]
priority: 323
status: todo
attempts: 0
paths: [tests/conformance/p23, _workspaces/reports/phase-P23-review.md]
spec: [spec/ROADMAP.md, spec/SPEC-140-conformance-suite-compiler-qualification.md, spec/SPEC-141-global-contradiction-audit-spec-freeze.md, spec/SPEC-142-release-engineering-distribution-versioning.md, spec/RELEASE-v1.md]
covers: [REQ-CNF-001, REQ-CORE-3136]
---
# T323 — Phase P23 gate: v1.0 conformance, freeze & release

## Goal
Certify that phase P23 meets the exit criteria of every epic in `spec/ROADMAP.md` §3 (`E23.1`–`E23.3`: Axiom v1.0 tagged; `reqcov.py --strict` shows every `v1-core` and `v1-full` requirement implemented) and that all requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks (`E23.1` `T1003`, `E23.2` `T1006`, `E23.3` `T1010`).
- `reqcov.py --phase P23-v1-0-conformance-freeze-releas`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p23` (index + missing cases added).
- Ask axiom-architect (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion demonstrated with commands and results in the QA report.
- [ ] Full suite green (gate rule: PASS or BLOCKED; only `xfail` entries for spec gaps with an ADR may remain); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T323-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T223, prerequisite phase gates `T311`–`T322`, and all P23 tasks (`T091`, `T1000`–`T1010`).

## Log
- 2026-11-03 11:15:00 updated by T223: depends on T311–T322, T091, T1000–T1010; covers REQ-CNF-001, REQ-CORE-3136
