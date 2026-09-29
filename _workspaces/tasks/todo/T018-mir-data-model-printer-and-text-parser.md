---
id: T018
title: MIR data model, printer and text parser
phase: P3-semantic-core
owner: axiom-semantics
reviewer: axiom-qa
depends: [T017, T003a]
priority: 31
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/mir, tests/mir]
spec: [0161, 0227, 0228, 0247, 0024, tasks/0393, 0054, 0056, spec/SPEC-04-core-extensibility.md]
---
# T018 — MIR data model, printer and text parser

## Goal
Define the full MIR (designed for ownership from day one) with a round-trippable text form for tests.

## Scope
- Bodies, locals with types, basic blocks, statements (assign, storage live/dead), rvalues (use/copy/move operands, binary/unary ops, aggregate, cast, view/view_mut, len), places with projections (field, index, deref, downcast), terminators (goto, switch, call, return, drop, assert/panic, unreachable).
- Printer (`--emit=mir`) and parser (read MIR text) so verifier/interpreter tests can be hand-written.

## Acceptance
- [ ] Round-trip tests: print(parse(text)) == text for a corpus of MIR files.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T018-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
