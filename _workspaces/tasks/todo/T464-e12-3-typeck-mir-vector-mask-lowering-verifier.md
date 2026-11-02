---
id: T464
title: E12.3 — TypeKind.Vector/Mask, MIR VectorOp/Splat/Shuffle/Reduce lowering & verifier rules
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T463, T457]
priority: 154
status: todo
attempts: 0
paths: [compiler/types, compiler/hir, compiler/mir, tests/typeck/simd, tests/mir/simd]
locks: [compiler/verify/verifier.ax, compiler/diag/code.ax, tests/selfhost]
spec: [spec/SPEC-42-simd.md, spec/SPEC-04-core-extensibility.md, 0095, tasks/0341, tasks/0344, tasks/0347]
covers: [REQ-SIMD-054, REQ-SIMD-055, REQ-SIMD-056, REQ-SIMD-057, REQ-SIMD-098, REQ-SIMD-099, REQ-SIMD-107, REQ-SIMD-111, REQ-SIMD-112, REQ-SIMD-113, REQ-SIMD-114, REQ-SIMD-115, REQ-SIMD-116, REQ-SIMD-178, REQ-SIMD-179, REQ-SIMD-183, REQ-SIMD-184, REQ-SIMD-248, REQ-SIMD-249, REQ-SIMD-250, REQ-SIMD-251, REQ-SIMD-252, REQ-SIMD-253, REQ-SIMD-254, REQ-SIMD-329]
---
# T464 — E12.3 — TypeKind.Vector/Mask, MIR VectorOp/Splat/Shuffle/Reduce lowering & verifier rules

## Goal
Activate `TypeKind.Vector` and `TypeKind.Mask` (`AXS-EXT-020`), `ConstValue.Vector` (`AXS-EXT-024`), and MIR `VectorOp`/`Splat`/`Extract`/`Insert`/`Shuffle`/`Reduce` rvalues (`AXS-EXT-042`) with full MIR verifier validation.

## Scope
- Enable `TypeKind.Vector { elem, lanes }` and `TypeKind.Mask { lanes }` in `compiler/types/types.ax` and `compiler/types/typeck.ax`, validating that `elem` is a supported scalar integer/float and `lanes` is a power of two in `2..=64` (`AX_SIMD_INVALID_ELEMENT`, `AX_SIMD_INVALID_LANES`).
- Compute size and alignment for `Vector<T, N>` and `Mask<N>` in `compiler/types/layout.ax` and implement `Copy`, `Clone`, `Eq`, and `PartialEq`.
- Lower SIMD operators and `@intrinsic` functions (`simd_add`, `simd_sub`, `simd_mul`, `simd_div`, `simd_rem`, `simd_wrapping_*`, `simd_saturating_*`, `simd_bitand/or/xor/not/shl/shr`, `simd_eq/ne/lt/le/gt/ge`, `simd_splat`, `simd_extract`, `simd_insert`, `simd_shuffle`, `simd_select`, `simd_reduce_*`, `simd_cast`, `simd_bitcast`, `simd_load_masked`, `simd_store_masked`, `simd_gather`, `simd_scatter`) to MIR rvalues in `compiler/mir/builder.ax`.
- Extend `compiler/verify/verifier.ax` to verify lane count and element type consistency on every MIR vector/mask rvalue, static lane index bounds on `Extract`/`Insert`/`Shuffle`, and exact byte-size equality on `simd_bitcast`.

## Acceptance
- [ ] `tests/typeck/simd/*.ax` verifies compile-time diagnostics for invalid vector element types, non-power-of-two lane counts, out-of-range lane/shuffle indices, and mismatched `simd_bitcast` sizes.
- [ ] `tests/mir/simd/*.ax` (`inspect --emit=mir` and `--verify-each`) verifies MIR lowering of `VectorOp`, `Splat`, `Extract`, `Insert`, `Shuffle`, and `Reduce`.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T464` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T464-report.md` with exact `## Files changed`.

## Out of scope
- MIR interpreter evaluation (`T465`), `std.simd` library wrappers (`T466`), and LIR/x86-64 native lowering (`E12.4`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T464/build` and `python tools/axtest.py --compiler build-snap-T464/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
