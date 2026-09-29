---
id: T029
title: VS1 gate: differential interp vs native, determinism
phase: P4-native
owner: axiom-qa
reviewer: axiom-architect
depends: [T028, T022]
priority: 46
status: todo
attempts: 0
paths: [tests/diff, tests/conformance/vs1, tools/ci.sh]
spec: [0263, 0152, 0145]
---
# T029 — VS1 gate: differential interp vs native, determinism

## Goal
Establish the three-level oracle (MIR interp / native / agreement) as a permanent CI guard.

## Scope
- Differential suite: every run test executed in both modes and compared; determinism check (build twice, compare bytes) in CI; first ABI test (add(20,22)).

## Acceptance
- [ ] CI runs differential + determinism; QA report documents seams MIR↔LIR↔MC↔COFF↔PE reviewed.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T029-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
