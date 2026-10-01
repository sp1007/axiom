---
id: T037
title: Native catch-up: numerics, aggregates, arrays, struct ABI
phase: P5-language
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T036, T033]
priority: 57
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/lir, bootstrap/axiom0/src/abi, bootstrap/axiom0/src/target/x64, tests/run/native_aggr, tests/run/numeric, tests/run/struct, tests/run/array]
spec: [0189, 0230, 0250, 0181]
---
# T037 — Native catch-up: numerics, aggregates, arrays, struct ABI

## Goal
All numeric/struct/array tests pass natively.

## Scope
- Sign/zero extension, all widths, overflow checks (jo), div-by-zero checks, memcpy-like lowering, Win64 aggregate passing (by value ≤8 bytes pow2, else by reference to copy) and hidden return pointer, bounds check traps.
- Remove every `// native-after: T037` directive from tests/run/{numeric,struct,array} (ADR-0005 §1) and make those tests pass natively. New instruction forms go into the encoder only with GNU-as validation tables (T024 method).
- Wrapping/bit intrinsics without `jo` (baseline x86-64 only: `bsr`/`bsf` sequences with a zero check and a bit-twiddling popcount — no `lzcnt`/`tzcnt`/`popcnt`, which need CPU feature detection, E12.5); `char` compare and zero-extension; checked `u32 as char`; shifts.
- Stack robustness tests (ADR-0003): a function with a 64 KB local array, and recursion 1000 deep over frames larger than 4 KB, both run natively without a crash.

## Acceptance
- [ ] Differential green for all run tests without a later `native-after`.
- [ ] `grep -rn "native-after: T037" tests` prints nothing; every run test that depended on this task passes in both modes.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T037-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
