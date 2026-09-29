---
id: T003
title: Stage-0 bootstrap subset, milestone manifests, core execution semantics
phase: P0-foundation
owner: axiom-architect
reviewer: axiom-qa
depends: [T001]
priority: 3
status: todo
attempts: 0
paths: [spec/SPEC-00-bootstrap.md, spec/SPEC-03-core-semantics.md]
spec: [0263, tasks/0262, tasks/0494, tasks/0260, 0152, 0032, 0041, 0068, tasks/0327, 0010]
---
# T003 — Stage-0 bootstrap subset, milestone manifests, core execution semantics

## Goal
Define exactly which language subset each milestone supports and freeze the core execution semantics the interpreter and backend must agree on.

## Scope
- SPEC-00-bootstrap.md: milestone ladder mapped to board phases (P2..P10) with features allowed/forbidden per milestone; first programs (exit 42, negative type test, MIR test, ABI test, struct test) from 0263 §32-37 in canonical syntax.
- SPEC-03-core-semantics.md: `main` signatures and exit-code mapping; integer types and literal defaulting; overflow behaviour (decide: trap/panic in all builds vs wrapping ops — cite docs); division by zero and INT_MIN/-1; shifts out of range; evaluation order (left-to-right, args, assignment); short-circuit; panic = abort in bootstrap and its exit code; bool representation; unit/never.

## Acceptance
- [ ] Both files exist with rule IDs; every semantic decision cites sources or an ADR.
- [ ] Each milestone lists its must-pass test programs.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T003-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
