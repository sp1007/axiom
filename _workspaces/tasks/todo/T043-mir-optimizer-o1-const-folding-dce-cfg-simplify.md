---
id: T043
title: MIR optimizer -O1: const folding, DCE, CFG simplify
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
depends: [T040]
priority: 63
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/opt, tests/opt, tests/diff/opt]
spec: [0165, 0226, 0074, 0263]
---
# T043 — MIR optimizer -O1: const folding, DCE, CFG simplify

## Goal
First optimization ladder rung, guarded by re-verification and differential tests.

## Scope
- Pass manager skeleton (ordered passes, verify after each in debug), constant folding respecting SPEC-03 (never fold away a trap incorrectly), dead code elimination, CFG simplification; `-O1` flag.

## Acceptance
- [ ] First optimization test (40+2 → const 42); all run tests pass at -O0 and -O1 in both modes.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T043-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
