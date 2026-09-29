---
id: T020
title: MIR verifier v1 (structural + types)
phase: P3-semantic-core
owner: axiom-semantics
reviewer: axiom-qa
depends: [T019]
priority: 33
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/verify, tests/verify]
spec: [0027, 0029, 0034, 0035, tasks/0365]
---
# T020 — MIR verifier v1 (structural + types)

## Goal
Guard the verified-MIR boundary: nothing malformed reaches the interpreter or backend.

## Scope
- CFG well-formedness, every block terminated, operand types match, locals initialised before use (simple), call signatures, return type; AX_VERIFY_* diagnostics (internal, but reported).
- Driver runs the verifier after MIR build in every mode.

## Acceptance
- [ ] Negative tests using hand-written MIR text (one per rule); all builder outputs verify.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T020-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
