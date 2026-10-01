---
id: T052
title: P6 gate: adversarial semantic suite
phase: P6-ownership
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T051]
priority: 72
status: todo
attempts: 0
paths: [tests/conformance/adversarial, tests/conformance/stress]
spec: [0026, 0022, 0019, 0020, 0028, 0017]
---
# T052 — P6 gate: adversarial semantic suite

## Goal
Attack the ownership/capability implementation with the adversarial cases from the specs.

## Scope
- Port 0026 adversarial tests + relevant 0022 stress tests into canonical syntax; report every divergence as finding or spec gap.

## Acceptance
- [ ] The whole suite passes. A divergence that is a spec gap gets an architect ADR and an `xfail: <task-id>` entry; an implementation bug blocks the gate until its fix task is done (0264 §20: PASS or BLOCKED, never "almost done").
- [ ] Gate rule (ADR-0005 §3): PASS or BLOCKED. Every non-passing test is an `xfail: <task-id>` for a spec gap that has an ADR; implementation bugs are fixed (their fix task done) before the gate closes; XPASS counts as a failure.
- [ ] `python tools/gatecheck.py`, `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T052-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
