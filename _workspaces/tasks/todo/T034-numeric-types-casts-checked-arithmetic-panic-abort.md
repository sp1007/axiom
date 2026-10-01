---
id: T034
title: Numeric types, casts, checked arithmetic, panic=abort
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T032]
priority: 54
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, tests/run/numeric, tests/ui/numeric]
locks: [bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [tasks/0327, tasks/0334, spec/SPEC-03-core-semantics.md, 0068]
---
# T034 — Numeric types, casts, checked arithmetic, panic=abort

## Goal
All integer widths, bool ops, `char`, `as` casts, overflow/div-zero/shift semantics exactly per SPEC-03. Floating point is not part of axiom0 (owner decision 2026-09-30, ROADMAP R7): f32/f64 are implemented once, in Axiom, in P12 (E12.2).

## Scope
- Cast rules table, checked ops emitting MIR assert/panic terminators, panic intrinsic → abort path with the defined exit code.
- `char` = one Unicode scalar value (0..=0x10FFFF excluding 0xD800..=0xDFFF), 4 bytes: comparison, `c as u32`, `u8 as char` (always valid), `u32 as char` as a **checked cast** that panics on a non-scalar value (ADR-0006 §2; `char.from_u32` returning Option is library code in T069); no arithmetic on char.
- Float literals and `f32`/`f64` still lex and parse, but type checking reports `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` ("floating point arrives in P12") — never a crash, never a silent integer. The TypeKind variants stay reserved per SPEC-04.
- Wrapping and bit intrinsics (ADR-0004 §1), declared with `@intrinsic`: `wrapping_add/sub/mul/neg`, `rotate_left/right`, `leading_zeros`, `trailing_zeros`, `count_ones` for every integer width — MIR operations without an overflow assert, with exact oracle semantics. Hashing (kernel hash, HashMap, mangling) depends on them.

## Acceptance
- [ ] Boundary-value run tests per width (MIN, MAX, overflow edges) in interp; run tests carry `// native-after: T037` (removed by T037).
- [ ] char tests: `'ế' as u32 == 0x1EBF`; with u32 operands, `0x10FFFF as char` succeeds while `0xD800 as char` and `0x110000 as char` abort with the panic exit code; ordering by scalar value.
- [ ] ui test: a program using `1.5` or `f64` gets AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP at the right span.
- [ ] Wrapping/bit intrinsic tests at MIN/MAX of every width; a hand-unrolled FNV-1a over four literal bytes with `wrapping_mul` equals the reference constant.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T034-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Runs in parallel with the native catch-up T033 (different directories; its run tests carry `native-after: T037`). T037 depends on T033.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
