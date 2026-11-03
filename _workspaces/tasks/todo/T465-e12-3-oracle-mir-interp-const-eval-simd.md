---
id: T465
title: E12.3 — Oracle MIR interpreter & const evaluator for Vector<T, N> and Mask<N>
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T464, T458]
priority: 155
status: todo
attempts: 0
paths: [compiler/interp, compiler/opt, tests/mir/simd_interp, tests/opt/simd_const, tests/selfhost]
locks: [compiler/interp_opt/session.ax, tests/selfhost]
spec: [spec/SPEC-42-simd.md, 0095, tasks/0341, tasks/0344, tasks/0347]
covers: [REQ-SIMD-016, REQ-SIMD-017, REQ-SIMD-018, REQ-SIMD-028, REQ-SIMD-124, REQ-SIMD-125, REQ-SIMD-180, REQ-SIMD-181, REQ-SIMD-182, REQ-SIMD-185, REQ-SIMD-258, REQ-SIMD-259, REQ-SIMD-260, REQ-SIMD-261, REQ-SIMD-269, REQ-SIMD-273, REQ-SIMD-274, REQ-SIMD-275, REQ-SIMD-276, REQ-SIMD-277, REQ-SIMD-278, REQ-SIMD-330]
---
# T465 — E12.3 — Oracle MIR interpreter & const evaluator for Vector<T, N> and Mask<N>

## Goal
Implement the deterministic lane-by-lane reference evaluator for `Vector<T, N>` and `Mask<N>` in `compiler/interp/` (`--interp` and const-eval) and `compiler/opt/const_fold.ax`.

## Scope
- Extend `compiler/interp/value.ax` and `compiler/interp/interp.ax` to represent `Vector<T, N>` and `Mask<N>` values and evaluate `Splat`, `Extract`, `Insert`, `Shuffle`, lane-wise arithmetic (checked with per-lane overflow/divzero/shift panics, `wrapping_*`, `saturating_*`, and strict IEEE-754 float ops), lane comparisons yielding `Mask<N>`, `simd_select`, `simd_cast`, and `simd_bitcast`.
- Implement horizontal reductions (`reduce_add`, `reduce_add_ordered` strictly left-to-right `(((v[0] + v[1]) + v[2]) + ...)`, `reduce_mul`, `reduce_min`, `reduce_max`, `reduce_and`, `reduce_or`, `reduce_xor`) and mask reductions (`all`, `any`, `none`, `bitmask`) in `compiler/interp/interp.ax`.
- Implement `simd_load_masked`, `simd_store_masked`, `simd_gather`, and `simd_scatter` in `compiler/interp/interp.ax`, enforcing that masked-off (`false`) lanes perform no memory access (never faulting on out-of-bounds indices when inactive) and active lanes are bounds- and capability-checked.
- Fold pure constant vector/mask rvalues in `compiler/opt/const_fold.ax`.

## Acceptance
- [ ] `tests/mir/simd_interp/*.ax` passes under `--interp` for all `Vector<T, N>` and `Mask<N>` operations, including inactive-lane masked loads/stores at slice boundaries, gather/scatter bounds checks, and ordered FP reductions.
- [ ] `tests/opt/simd_const/*.ax` verifies constant folding of `const` SIMD vectors and masks at `-O1`.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T465` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T465-report.md` with exact `## Files changed`.

## Out of scope
- User-facing `std.simd` module (`T466`) and native x86-64 vector codegen (`E12.4`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T465/build` and `python tools/axtest.py --compiler build-snap-T465/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
