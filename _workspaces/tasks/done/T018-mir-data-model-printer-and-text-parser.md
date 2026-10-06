---
id: T018
title: MIR data model, printer and text parser
phase: P3-semantic-core
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T017, T003a, T045]
priority: 31
status: done
attempts: 1
paths: [bootstrap/axiom0/src/mir, tests/mir, bootstrap/axiom0/src/driver/emit_mir.c]
spec: [0161, 0227, 0228, 0247, 0024, tasks/0393, 0054, 0056, spec/SPEC-04-core-extensibility.md]
started: 2026-10-06 09:26:39
finished: 2026-10-06 10:05:25
---
# T018 — MIR data model, printer and text parser

## Goal
Define the full MIR (designed for ownership from day one) with a round-trippable text form for tests.

## Scope
- Bodies, locals with types, basic blocks, statements (assign, storage live/dead), rvalues (use/copy/move operands, binary/unary ops, aggregate, cast, view/view_mut, len), places with projections (field, index, deref, downcast), terminators (goto, switch, call, return, drop, assert/panic, unreachable).
- Printer (`--emit=mir`) and parser (read MIR text) so verifier/interpreter tests can be hand-written.
- Places, operands and terminators carry what SPEC-10/11/12 (T045) list as required of MIR — projections for partial moves, drop flags, view/region annotations, storage markers — even though T019 emits only a few of them (0263 §42, ABOOT-43..45).
- The MIR text parser is C-only test infrastructure (ADR-0004 §9): outside the self-host subset, never ported to axiomc.

## Acceptance
- [ ] Round-trip tests: print(parse(text)) == text for a corpus of MIR files.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T018-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Depends on T045 (ADR-0005 §5): the ownership/capability/drop rules exist before the MIR that must express them.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 09:26:39 started (attempt 1) T018-impl
- 2026-10-06 10:05:25 accepted by QA -> done
