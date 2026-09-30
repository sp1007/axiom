---
id: T034
title: Numeric types, casts, checked arithmetic, panic=abort
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T033]
priority: 54
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, tests/run/numeric, tests/ui/numeric]
spec: [tasks/0327, tasks/0334, spec/SPEC-03-core-semantics.md, 0068]
---
# T034 — Numeric types, casts, checked arithmetic, panic=abort

## Goal
All integer widths, bool ops, `char`, `as` casts, overflow/div-zero/shift semantics exactly per SPEC-03. Floating point is not part of axiom0 (owner decision 2026-09-30, ROADMAP R7): f32/f64 are implemented once, in Axiom, in P12 (E12.2).

## Scope
- Cast rules table, checked ops emitting MIR assert/panic terminators, panic intrinsic → abort path with the defined exit code.
- `char` = one Unicode scalar value (0..=0x10FFFF excluding 0xD800..=0xDFFF), 4 bytes: comparison, `c as u32`, `u8 as char` (always valid), checked `char.from_u32(n) -> Option<char>` (or the spec's equivalent); no arithmetic on char.
- Float literals and `f32`/`f64` still lex and parse, but type checking reports `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` ("floating point arrives in P12") — never a crash, never a silent integer. The TypeKind variants stay reserved per SPEC-04.

## Acceptance
- [ ] Boundary-value run tests per width (MIN, MAX, overflow edges) in interp.
- [ ] char tests: `'ế' as u32 == 0x1EBF`; `char.from_u32` accepts 0x10FFFF, rejects 0xD800 and 0x110000; ordering by scalar value.
- [ ] ui test: a program using `1.5` or `f64` gets AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP at the right span.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T034-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
