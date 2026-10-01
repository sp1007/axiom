---
id: T061
title: Const items and constant expressions (via the MIR interpreter)
phase: P7-abstraction
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T059]
priority: 81
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/interp, bootstrap/axiom0/src/types/const, bootstrap/axiom0/src/mir, tests/run/comptime, tests/ui/comptime]
locks: [bootstrap/axiom0/src/diag/codes/CONST.def, bootstrap/axiom0/src/diag/codes/TYPE.def, bootstrap/axiom0/src/driver/pipeline.c]
spec: [0102, 0140, tasks/0274, tasks/0509, tasks/0346]
---
# T061 — Const items and constant expressions

## Goal
Compile-time evaluation reusing the oracle (no separate mini-language).

## Scope
- `const` items and constant expressions (array sizes, tables) evaluated by the MIR interpreter, evaluation limits and diagnostics. `comptime fn`, `comptime {}` blocks, const generics and reflection are E14.1/E14.2 (after self-hosting, ROADMAP R7) — but keep the evaluator reusable so they plug in without redesign.
- **Const-evaluator interface** (ADR-0004 §8): `types` declares the interface, the driver wires the interpreter into it; `types` never includes `interp` (archcheck rule of T006).
- **Constant tables** (ADR-0004 §2): a `const` item of aggregate type (arrays of structs with integer, bool, `char`, `Str` fields) that is used as a place is materialised **once** — one interpreter allocation here, `.rdata` natively in T061d — and indexed in place, never copied per use. `static` and `static mut` items stay outside the subset and report AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP (E13.3, ADR-0001).

## Acceptance
- [ ] run + ui tests: scalar constants and constant array lengths in both modes.
- [ ] Table tests (a keyword table of `Str`, a table of structs with `Str` and integer fields, a 256-entry `u8` table indexed in a loop) pass in interp and carry `// native-after: T061d`; a ui test for `static`.
- [ ] Evaluation-limit and cyclic-constant diagnostics have ui tests.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T061-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
