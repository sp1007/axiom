---
id: T033
title: Native catch-up: CFG, calls, Windows ABI completeness
phase: P5-language
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T032]
priority: 53
status: done
attempts: 1
paths: [bootstrap/axiom0/src/lir, bootstrap/axiom0/src/abi, bootstrap/axiom0/src/target/x64, bootstrap/axiom0/src/driver, tests/run/native_abi, tests/run/basic, tests/run/vars, tests/run/cfg, tests/run/fn]
spec: [0181, 0189, 0230, 0232, 0252]
started: 2026-10-08 11:42:46
unblocks: 1
finished: 2026-10-08 14:09:13
---
# T033 — Native catch-up: CFG, calls, Windows ABI completeness

## Goal
All P5 tests so far pass natively.

## Scope
- Branch/loop lowering, calls with >4 args (stack args at [rsp+32..]), shadow space everywhere, alignment, callee-saved preservation, recursion depth test.
- Remove every `// native-after: T033` directive from tests/run/{basic,vars,cfg,fn} (ADR-0005 §1) and make those tests pass natively. New instruction forms go into the encoder only with GNU-as validation tables (T024 method).
- First ABI test `add(20, 22)` (moved here from T029: in the ladder 0263 §51 calls come after VS#1).

## Acceptance
- [ ] Every run test without a later `native-after` passes in both modes (differential green).
- [ ] `grep -rn "native-after: T033" tests` prints nothing; every run test that depended on this task passes in both modes.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T033-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-08 11:26:08 started (attempt 1) T033-impl
- 2026-10-08 11:41:04 block: need paths for bootstrap/axiom0/src/driver to fix native linker issues
- 2026-10-08 11:41:50 unblocked (cycle 1) 
- 2026-10-08 11:42:46 started (attempt 1) T033-impl
- 2026-10-08 14:09:13 accepted by QA -> done
