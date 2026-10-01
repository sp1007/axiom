---
id: T051
title: Native catch-up: views, drops, drop flags
phase: P6-ownership
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T050]
priority: 71
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/lir, bootstrap/axiom0/src/target/x64, tests/run/native_own, tests/run/own, tests/run/init, tests/run/cap, tests/run/slice, tests/run/drop]
spec: [0152, 0162]
---
# T051 — Native catch-up: views, drops, drop flags

## Goal
Ownership programs run natively with correct drop behaviour.

## Scope
- Views lowered to pointers / (ptr,len) — slices included (fat pointer passed by the Windows x64 ABI rules for 16-byte aggregates); drop calls; drop flag storage; ownership erasure after verification.
- Remove every `// native-after: T051` directive from tests/run/{own,init,cap,slice,drop} (ADR-0005 §1) and make those tests pass natively. New instruction forms go into the encoder only with GNU-as validation tables (T024 method).

## Acceptance
- [ ] Differential green for all P6 run tests (stored views and slice structs included).
- [ ] `grep -rn "native-after: T051" tests` prints nothing; every run test that depended on this task passes in both modes.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T051-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
