---
id: T062
title: P7 gate: abstraction conformance + generated-program fuzzing
phase: P7-abstraction
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T061, T060, T061a, T061b, T061c, T061d]
priority: 84
status: todo
attempts: 0
paths: [tests/conformance/p7, tools/progfuzz.py]
spec: [0017, 0026, 0114]
---
# T062 — P7 gate: abstraction conformance + generated-program fuzzing

## Goal
Validate generics/traits/closures/modules together (dyn is E14.4).

## Scope
- Conformance cases; typed-program generator that produces valid programs and checks interp==native at -O0/-O1.

## Acceptance
- [ ] Suite passes; the campaign `python tools/progfuzz.py --seed 1 --iterations 20000` (interp == native at -O0 and -O1) ends with 0 findings — every finding on the way is fixed (fix task done) or minimised into a passing regression test before the gate closes.
- [ ] Gate rule (ADR-0005 §3): PASS or BLOCKED. Every non-passing test is an `xfail: <task-id>` for a spec gap that has an ADR; implementation bugs are fixed (their fix task done) before the gate closes; XPASS counts as a failure.
- [ ] `python tools/gatecheck.py`, `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T062-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
