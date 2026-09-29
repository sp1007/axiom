---
id: T033
title: Native catch-up: CFG, calls, Windows ABI completeness
phase: P5-language
owner: axiom-backend
reviewer: axiom-qa
depends: [T032]
priority: 53
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/lir, bootstrap/axiom0/src/abi, bootstrap/axiom0/src/target/x64, tests/run/native_abi]
spec: [0181, 0189, 0230, 0232, 0252]
---
# T033 — Native catch-up: CFG, calls, Windows ABI completeness

## Goal
All P5 tests so far pass natively.

## Scope
- Branch/loop lowering, calls with >4 args (stack args at [rsp+32..]), shadow space everywhere, alignment, callee-saved preservation, recursion depth test.

## Acceptance
- [ ] Every run test passes in both modes (differential green).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T033-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
