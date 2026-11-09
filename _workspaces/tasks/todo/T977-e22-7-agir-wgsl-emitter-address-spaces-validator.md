---
id: T977
title: E22.7 AGIR -> WGSL source emitter, address space mapping & WGSL syntax validator
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T959, T972, T976]
priority: 247
status: todo
attempts: 0
paths: [compiler/target/wgsl, tests/target/wgsl]
locks: [compiler/target/desc.ax]
spec: [spec/SPEC-136-webgpu-wgsl-backend.md, tasks/0846, 0162]
covers: [REQ-GPU-054, REQ-GPU-055, REQ-GPU-065]
---
# T977 — E22.7 AGIR -> WGSL source emitter, address space mapping & WGSL syntax validator

## Goal
Implement the WebGPU Shading Language source emitter and internal WGSL syntax/semantic validator in `compiler/target/wgsl`: translating AGIR compute and raster shaders into valid WGSL source code.

## Scope
- Register the WebGPU target in `compiler/target/wgsl` and `compiler/target/desc.ax` (`SPEC-04 AXS-EXT-052/060/070`, `ObjectFormat.Wgsl`, `CallConv.GpuKernel`).
- Implement the AGIR to WGSL translator:
  - Generate `@compute @workgroup_size(X, Y, Z)`, `@vertex`, and `@fragment` entry-point functions.
  - Map address spaces to WGSL variables: `var<storage, read_write>`, `var<storage, read>`, `var<uniform>`, `var<workgroup>`, `var<private>`.
  - Map SIMT built-ins: `@builtin(global_invocation_id)`, `@builtin(local_invocation_id)`, `@builtin(workgroup_id)`, `@builtin(num_workgroups)`, `@builtin(position)`.
  - Map memory barriers to `workgroupBarrier()` and `storageBarrier()`.
  - Map atomic operations to `atomic<u32>` operations (`atomicAdd`, `atomicSub`, `atomicMin`, `atomicMax`, `atomicExchange`, `atomicCompareExchangeWeak`).
  - Map texture types to WGSL types: `texture_2d<f32>`, `texture_storage_2d<rgba8unorm, write>`, `sampler`, `sampler_comparison`.
- Implement WGSL host-shareable struct layout generator:
  - Enforce WebGPU 16-byte alignment rules for array elements and nested structs within uniform and storage buffers.
  - Generate `@group(0) @binding(n)` annotations corresponding deterministically to AGIR kernel argument indices.
- Implement the internal WGSL syntax validator:
  - Verify generated WGSL is syntactically well-formed, contains no illegal keyword identifiers, and satisfies WebGPU structural rules before output.
- Add WGSL code generation and validation tests in `tests/target/wgsl`.

## Acceptance
- [ ] Tests in `tests/target/wgsl` verify that `@kernel`, `@vertex`, and `@fragment` functions lower to syntactically valid WGSL source code satisfying WebGPU specifications.
- [ ] Address space decorators, binding attributes, and atomic expressions produce valid WGSL constructs and pass the internal validator.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T977-report.md` with exact `## Files changed`.

## Out of scope
- WebGPU host driver execution (`T978`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), part of Epic E22.7.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T977/build` and `python tools/axtest.py --compiler build-snap-T977/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 WebGPU expansion)
