---
id: T959
title: E22.3 AGIR lowering, kernel fusion, transfer optimization & structured CFG reconstruction
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T222, T311, T312, T316, T955, T958]
priority: 229
status: todo
attempts: 0
paths: [compiler/gpu/agir, compiler/gpu/opt, compiler/gpu/structurize, tests/selfhost/gpu_agir]
locks: [compiler/driver/pipeline.ax]
spec: [spec/SPEC-132-gpu-ir-spirv-codegen-backend.md, spec/SPEC-04-core-extensibility.md, 0139, 0162, tasks/0626]
covers: [REQ-GPU-023, REQ-GPU-024, REQ-GPU-032, REQ-GPU-045, REQ-GPU-046, REQ-GPU-047, REQ-GPU-052, REQ-GPU-053, REQ-GPU-054, REQ-GPU-055]
---
# T959 — E22.3 AGIR lowering, kernel fusion, transfer optimization & structured CFG reconstruction

## Goal
Implement `AGIR` lowering from verified kernel MIR/LIR, `GpuKernelABI` descriptor layout, proof-preserving kernel fusion and transfer elimination, and structured control-flow reconstruction in `compiler/gpu/` per `spec/SPEC-132-gpu-ir-spirv-codegen-backend.md`.

## Scope
- Implement `compiler/gpu/agir`: lower verified `BodyKind.Kernel` and `@device` functions into `AGIR`, computing `GpuKernelABI` descriptor bindings (`StorageBuffer`, `UniformConstant`, `Workgroup`, `PushConstant`), explicit parameter layouts, alignment, and workgroup shared-memory footprints (`tasks/0626 §20, §22-23`, `0162 §32-33`).
- Implement `compiler/gpu/opt`: build the heterogeneous `ExecutionGraph` (`tasks/0626 §24-30, §37-38`) and implement proof-preserving producer-consumer elementwise `KernelFusion` (`AGPU-19`, `AGPU-51`), redundant host↔device transfer elimination (`AGPU-28`), constant/shared/register promotion (`0139 §XX.35`), and `GpuCostModel`/occupancy estimation (`AGPU-21`, `AGPU-22`), re-running `AGIR` verification after every pass (`AGPU-29`).
- Implement `compiler/gpu/structurize`: reconstruct structured control-flow regions (`SelectionMerge` for conditionals/switches and `LoopMerge` with header, merge block, and continue target for loops) required by SPIR-V 1.6 while preserving barrier uniformity.
- Register `--emit=agir` in `compiler/driver/pipeline.ax` and add unit/golden tests in `tests/selfhost/gpu_agir`.

## Acceptance
- [ ] Tests in `tests/selfhost/gpu_agir` verify `AGIR` lowering, `GpuKernelABI` descriptor assignment, proof-preserving `KernelFusion` (and rejection of fusion across incompatible barriers or side-effecting atomics), transfer elimination, and `LoopMerge`/`SelectionMerge` CFG structurization.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T959-report.md` with exact `## Files changed`.

## Out of scope
- Binary SPIR-V `.spv` emission and internal SPIR-V bytecode validation (`T960`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T959/build` and `python tools/axtest.py --compiler build-snap-T959/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
