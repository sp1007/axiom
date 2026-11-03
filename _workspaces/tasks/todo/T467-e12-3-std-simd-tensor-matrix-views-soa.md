---
id: T467
title: E12.3 — Data-oriented SoA, Matrix & TensorView/TensorMutView library over capabilities
phase: P12-numeric-floating-point-simd
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T466, T461]
priority: 157
status: todo
attempts: 0
paths: [std/simd/tensor.ax, std/simd/matrix.ax, tests/std/tensor_matrix]
locks: [std/simd/mod.ax, tests/selfhost]
spec: [spec/SPEC-42-simd.md, 0095, tasks/0337, tasks/0341, tasks/0344, tasks/0426]
covers: [REQ-SIMD-129, REQ-SIMD-130, REQ-SIMD-131, REQ-SIMD-132, REQ-SIMD-133, REQ-SIMD-134, REQ-SIMD-135, REQ-SIMD-136, REQ-SIMD-137, REQ-SIMD-138, REQ-SIMD-139, REQ-SIMD-140, REQ-SIMD-141, REQ-SIMD-144, REQ-SIMD-145, REQ-SIMD-146, REQ-SIMD-147, REQ-SIMD-148, REQ-SIMD-149, REQ-SIMD-150, REQ-SIMD-151, REQ-SIMD-152, REQ-SIMD-153, REQ-SIMD-154, REQ-SIMD-155, REQ-SIMD-158, REQ-SIMD-159, REQ-SIMD-229, REQ-SIMD-230, REQ-SIMD-231, REQ-SIMD-232, REQ-SIMD-233, REQ-SIMD-234, REQ-SIMD-235, REQ-SIMD-236, REQ-SIMD-237, REQ-SIMD-238, REQ-SIMD-239, REQ-SIMD-240, REQ-SIMD-291, REQ-SIMD-292, REQ-SIMD-293, REQ-SIMD-294, REQ-SIMD-295, REQ-SIMD-296, REQ-SIMD-297, REQ-SIMD-298, REQ-SIMD-299, REQ-SIMD-300, REQ-SIMD-301, REQ-SIMD-302, REQ-SIMD-303, REQ-SIMD-306, REQ-SIMD-307, REQ-SIMD-308, REQ-SIMD-309, REQ-SIMD-310, REQ-SIMD-311, REQ-SIMD-312, REQ-SIMD-313, REQ-SIMD-314, REQ-SIMD-315, REQ-SIMD-316, REQ-SIMD-317, REQ-SIMD-320, REQ-SIMD-321]
---
# T467 — E12.3 — Data-oriented SoA, Matrix & TensorView/TensorMutView library over capabilities

## Goal
Implement zero-overhead library `TensorView<T, R>`, `TensorMutView<T, R>`, fixed `Vec2..4`/`Mat2..4`, and SoA slice helpers in `std/simd/tensor.ax` and `std/simd/matrix.ax` (`ANUM-64..95`, `ASIMD-83..96`).

## Scope
- Create `std/simd/tensor.ax` implementing `TensorView<T, R>` (holding `data: view<[T]>`, `shape: [R]usize`, `strides: [R]isize`) and `TensorMutView<T, R>` (holding `data: mut_view<[T]>`, `shape: [R]usize`, `strides: [R]isize`) with no nested view objects (`ANUM-66..70`), verifying bounds and contiguous vs strided layout on construction, indexing, `subview`, `transpose`, `reshape_contiguous`, and read-only `broadcast` (rejecting overlapping mutable capabilities, `ANUM-71..72`).
- Create `std/simd/matrix.ax` implementing value-semantic `Vec2<T>`, `Vec3<T>`, `Vec4<T>`, `Mat2<T>`, `Mat3<T>`, `Mat4<T>`, and SIMD-accelerated contiguous slice/tensor kernels (`dot`, `axpy`, `gemv`, tiled `matmul`, and lane-strided SoA iteration helpers) in pure Axiom without external BLAS dependencies (`ANUM-75..78`).

## Acceptance
- [ ] `tests/std/tensor_matrix/*.ax` passes under `--interp` (and native once `T472` lands), verifying `TensorView`/`TensorMutView` shape/stride indexing, transpose, subview capability exclusivity, `Mat4` transforms, and tiled `matmul` accuracy.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T467` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T467-report.md` with exact `## Files changed`.

## Out of scope
- GPU device tensor storage and host-device transfers (`Phase 22 E22.2`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T467/build` and `python tools/axtest.py --compiler build-snap-T467/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
