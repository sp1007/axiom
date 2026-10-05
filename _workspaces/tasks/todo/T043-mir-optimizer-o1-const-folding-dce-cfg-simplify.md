---
id: T043
title: MIR optimizer -O1: const folding, DCE, CFG simplify
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T041, T040]
priority: 63
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/opt, tests/opt, tests/diff/opt]
locks: [bootstrap/axiom0/src/driver/pipeline.c]
spec: [0165, 0226, 0074, 0263]
covers: [REQ-ABI-001, REQ-ABI-002, REQ-ABI-003, REQ-ABI-004]
---
# T043 — MIR optimizer -O1: const folding, DCE, CFG simplify

## Goal
First optimization ladder rung, guarded by re-verification and differential tests.

## Scope
- Pass manager skeleton (ordered passes; the verifier runs after each pass in every build used by tools/axtest.py and CI — option `--verify-each`, on by default in tests; verification before LIR is mandatory at every -O level, ABOOT-70), constant folding respecting SPEC-03 (never fold away a trap incorrectly), dead code elimination, CFG simplification; `-O1` flag.

## Acceptance
- [ ] First optimization test (40+2 → const 42); all run tests pass at -O0 and -O1 in both modes.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T043-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Depends on T041 (string-constant operands exist in MIR) and T040; runs in parallel with T042 — string tests keep `native-after: T042` until T042 removes it, and the P5 gate T044 checks the combination.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 02:23:53 covers += REQ-ABI-001, REQ-ABI-002, REQ-ABI-003, REQ-ABI-004 (metadata only)
