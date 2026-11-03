---
id: T466
title: E12.3 — std.simd portable Vector<T, N>, Mask<N>, lane ops, reductions & masked memory API
phase: P12-numeric-floating-point-simd
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T465, T460]
priority: 156
status: todo
attempts: 0
paths: [std/simd, tests/std/simd, tests/selfhost]
locks: [std/core/prelude.ax, tests/selfhost]
spec: [spec/SPEC-42-simd.md, 0095, tasks/0337, tasks/0341, tasks/0344, tasks/0347, tasks/0427]
covers: [REQ-SIMD-041, REQ-SIMD-052, REQ-SIMD-053, REQ-SIMD-126, REQ-SIMD-127, REQ-SIMD-128, REQ-SIMD-190, REQ-SIMD-191, REQ-SIMD-192, REQ-SIMD-193, REQ-SIMD-212, REQ-SIMD-225, REQ-SIMD-226, REQ-SIMD-227, REQ-SIMD-228, REQ-SIMD-286, REQ-SIMD-287, REQ-SIMD-288, REQ-SIMD-289, REQ-SIMD-290, REQ-SIMD-328]
---
# T466 — E12.3 — std.simd portable Vector<T, N>, Mask<N>, lane ops, reductions & masked memory API

## Goal
Implement the portable `std.simd` module (`std/simd/mod.ax`) exposing `Vector<T, N>`, `Mask<N>`, standard fixed-width aliases, operators, lane manipulations, reductions, and capability-safe slice/masked/gather/scatter memory operations.

## Scope
- Create `std/simd/mod.ax` with `Vector<T, N>`, `Mask<N>`, and canonical type aliases (`i8x16`, `u8x16`, `i16x8`, `u16x8`, `i32x4`, `u32x4`, `i64x2`, `u64x2`, `f32x4`, `f64x2`, `i32x8`, `u32x8`, `f32x8`, `f64x4`, `mask8x16`, `mask16x8`, `mask32x4`, `mask64x2`, `mask32x8`, `mask64x4`).
- Implement arithmetic and bitwise operator traits (`+`, `-`, `*`, `/`, `%`, unary `-`, `&`, `|`, `^`, `~`, `<<`, `>>`), `splat`, `from_array`, `to_array`, `extract`, `insert`, `shuffle`, `interleave_lo`, `interleave_hi`, `wrapping_add/sub/mul`, `saturating_add/sub`, `abs`, `min`, `max`, `clamp`, `sqrt`, `fma`, `floor`, `ceil`, `round`, `trunc`, `cast`, and `bitcast`.
- Implement lane comparisons (`simd_eq`, `simd_ne`, `simd_lt`, `simd_le`, `simd_gt`, `simd_ge`), `Mask<N>` methods (`all`, `any`, `none`, `bitmask`, `select`, `to_array`), horizontal reductions (`reduce_add`, `reduce_add_ordered`, `reduce_mul`, `reduce_min`, `reduce_max`, `reduce_and`, `reduce_or`, `reduce_xor`), and safe `view<[T]>`/`mut_view<[T]>` memory operations (`from_slice`, `copy_to_slice`, `load_unaligned`, `store_unaligned`, `load_masked`, `store_masked`, `gather`, `scatter`).

## Acceptance
- [ ] `tests/std/simd/*.ax` passes under `--interp` (with `native-after: T472` where native vector codegen arrives in `E12.4`) covering all `std.simd` types, lane operations, masks, reductions, and slice/masked/gather/scatter APIs.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T466` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T466-report.md` with exact `## Files changed`.

## Out of scope
- Data-oriented `TensorView` and `MatrixView` abstractions (`T467`) and native SSE2/AVX2 instruction selection (`T472`–`T473`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T466/build` and `python tools/axtest.py --compiler build-snap-T466/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
