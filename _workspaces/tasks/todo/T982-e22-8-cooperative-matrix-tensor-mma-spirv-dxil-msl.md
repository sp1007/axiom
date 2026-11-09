---
id: T982
title: E22.8 Cooperative Matrix / Tensor MMA (TileMatrix, mma_sync) lowering to SPIR-V, DXIL & MSL
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T960, T966, T968, T981]
priority: 252
status: todo
attempts: 0
paths: [compiler/target/tensor_mma, tests/target/tensor_mma]
locks: [compiler/agir/ir.ax]
spec: [spec/SPEC-137-gpu-ai-tensor-mma-hot-reload.md, 0096, 0139, tasks/0459, tasks/0468]
covers: [REQ-GPU-061]
---
# T982 — E22.8 Cooperative Matrix / Tensor MMA (TileMatrix, mma_sync) lowering to SPIR-V, DXIL & MSL

## Goal
Implement the Cooperative Matrix / Tensor Core Matrix-Multiply-Accumulate (`MMA`) compiler lowering in `compiler/target/tensor_mma`, translating high-level `TileMatrix<T, M, N, K>` and `mma_sync` operations into hardware-accelerated tensor instructions across Vulkan, Direct3D 12, and Apple Metal.

## Scope
- Implement the `TileMatrix` tile abstraction in AGIR:
  - Standard tile shapes: `16x16x16` (standard FP16 MMA), `8x8x4`, `32x8x16`.
  - Roles: `TileMatrixUse.MatrixA`, `TileMatrixUse.MatrixB`, `TileMatrixUse.Accumulator`.
  - Matrix operations: `TileMatrix.load_from(view, stride)`, `TileMatrix.store_to(mut_view, stride)`, `TileMatrix.fill(scalar)`, and fused multiply-accumulate `mma_sync(a, b, c) -> TileMatrix` (`REQ-GPU-061`).
- Lower to SPIR-V 1.6 (`OpTypeCooperativeMatrixKHR`):
  - Emit capability `OpCapability CooperativeMatrixKHR` and extension `SPV_KHR_cooperative_matrix`.
  - Lower `load_from` to `OpCooperativeMatrixLoadKHR`, `store_to` to `OpCooperativeMatrixStoreKHR`, and `mma_sync` to `OpCooperativeMatrixMulAddKHR`.
- Lower to Direct3D 12 / HLSL 6.x:
  - Lower matrix tiles to HLSL WaveMMA / Matrix intrinsics (`[RootSignature]` requirement checks).
- Lower to Apple Metal / MSL:
  - Lower matrix tiles to `simdgroup_matrix<half, 8, 8>` and `simdgroup_multiply_accumulate`.
- Provide software reference fallback: evaluate `TileMatrix` operations on CPU thread pools using standard loops when running on hardware without hardware MMA support.
- Add code generation and lowering tests in `tests/target/tensor_mma`.

## Acceptance
- [ ] Tests in `tests/target/tensor_mma` verify that `mma_sync` correctly lowers to `OpCooperativeMatrixMulAddKHR` in SPIR-V, WaveMMA in HLSL, and `simdgroup_matrix` in MSL.
- [ ] Emitted tensor operations produce bit-accurate matrix multiplication outputs matching CPU reference oracle calculations.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T982-report.md` with exact `## Files changed`.

## Out of scope
- High-level deep learning framework integration (deferred post-v1).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), part of Epic E22.8.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T982/build` and `python tools/axtest.py --compiler build-snap-T982/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 AI & Hot-Reload expansion)
