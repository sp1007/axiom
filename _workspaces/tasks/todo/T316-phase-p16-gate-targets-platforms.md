---
id: T316
title: Phase P16 gate — Targets & platforms
phase: P16-targets-platforms
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T216, T313, T066, T650, T651, T652, T653, T654, T655, T656, T657, T658, T659, T660, T661, T662, T663, T664, T664a, T665, T666, T667, T668, T668a, T669, T670, T671, T672, T673, T674, T675, T675a, T676, T677, T678, T679, T680, T681, T682, T683, T684, T685, T686, T687, T688, T689, T690, T691, T692, T693, T694, T695, T696, T697, T698, T699]
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
