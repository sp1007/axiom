---
id: T040
title: Native catch-up: enums, match, Option/Result
phase: P5-language
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T039, T037]
priority: 60
status: done
attempts: 1
paths: [bootstrap/axiom0/src/lir, bootstrap/axiom0/src/target/x64, tests/run/native_enum, tests/run/enum, tests/run/pattern, tests/run/result]
spec: [tasks/0268, 0183]
covers: [REQ-ASY-001, REQ-ASY-002]
started: 2026-10-10 10:19:29
finished: 2026-10-10 10:27:37
---
# T040 — Native catch-up: enums, match, Option/Result

## Goal
Enum/match programs pass natively.

## Scope
- Switch lowering (compare chains; jump tables optional), tag/payload access, enum ABI.
- Remove every `// native-after: T040` directive from tests/run/{enum,pattern,result} (ADR-0005 §1) and make those tests pass natively. New instruction forms go into the encoder only with GNU-as validation tables (T024 method).
- Decision trees for literal, range and or-patterns; `enum as uN`.

## Acceptance
- [ ] Differential green, incl. the lexer-style char-range `match` of T038b natively.
- [ ] `grep -rn "native-after: T040" tests` prints nothing; every run test that depended on this task passes in both modes.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T040-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 02:23:54 covers += REQ-ASY-001, REQ-ASY-002 (metadata only)
- 2026-10-10 10:19:29 started (attempt 1) 
- 2026-10-10 10:27:37 accepted by QA -> done
