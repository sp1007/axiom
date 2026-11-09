---
id: T966
title: E22.3 AGIR -> HLSL emitter, dxcompiler DXIL bytecode container & root-signature reflection
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T959]
priority: 236
status: todo
attempts: 0
paths: [compiler/target/hlsl_dxil, compiler/obj/dxil, tests/target/hlsl_dxil, tests/mc/dxil]
locks: [compiler/target/desc.ax, compiler/obj/obj.ax]
spec: [spec/SPEC-132-gpu-ir-spirv-codegen-backend.md, 0096, 0139, 0162, tasks/0626, tasks/0846]
covers: [REQ-GPU-007, REQ-GPU-023, REQ-GPU-054, REQ-GPU-055, REQ-GPU-064]
---
# T966 — E22.3 AGIR -> HLSL emitter, dxcompiler DXIL bytecode container & root-signature reflection

## Goal
Implement the Direct3D 12 shader generation backend in `compiler/target/hlsl_dxil` and `compiler/obj/dxil`: translating `AGIR` into HLSL 6.x compute source, invoking `dxcompiler.dll` (DirectXShaderCompiler) or packaging pre-validated DXIL bitcode containers, and emitting deterministic root-signature reflection metadata for `std.sys.gpu.d3d12`.

## Scope
- Register the Direct3D 12 / DXIL target in `compiler/target/hlsl_dxil` and `compiler/target/desc.ax` (`SPEC-04 AXS-EXT-052/060/070`, `ObjectFormat.Dxil`, `CallConv.GpuKernel`).
- Implement the AGIR to HLSL 6.0+ translator in `compiler/target/hlsl_dxil`:
  - Map AGIR address spaces to HLSL registers: `StorageBuffer` to `RWByteAddressBuffer` or `RWStructuredBuffer<T>` (`u#`), `UniformConstant` to `ConstantBuffer<T>` (`b#`), `Workgroup` to `groupshared` memory declarations (`REQ-GPU-054`).
  - Map SIMT built-ins: `SV_DispatchThreadID`, `SV_GroupThreadID`, `SV_GroupID`, `SV_GroupIndex` to HLSL compute entry-point semantics.
  - Map barriers and atomics: `GroupMemoryBarrierWithGroupSync()`, `DeviceMemoryBarrierWithGroupSync()`, and `Interlocked*` intrinsics (`REQ-GPU-023`).
  - Map structured control flow from AGIR CFG into valid HLSL statements (`[loop]`, `[branch]`).
- Implement DXIL container compilation and packaging in `compiler/obj/dxil`:
  - Dynamically bind to `dxcompiler.dll` (with fallback to pre-compiled bytecode or internal DXIL container builder) to compile HLSL source to DXIL shader model 6.0 (`cs_6_0`).
  - Emit deterministic root signature definition (`[RootSignature("...")]` or versioned binary root signature `ID3DBlob` containing descriptor tables and root constants).
  - Extract reflection metadata: threadgroup dimensions (`[numthreads(X, Y, Z)]`), resource binding register ranges (`t#`, `u#`, `b#`, `s#`), and push-constant offsets.
- Add HLSL code generation and DXIL bytecode tests in `tests/target/hlsl_dxil` and `tests/mc/dxil`.

## Acceptance
- [ ] Tests in `tests/target/hlsl_dxil` and `tests/mc/dxil` verify that `@kernel` functions lower to clean, valid HLSL 6.x and produce valid DXIL binary containers with matching root signatures and reflection metadata.
- [ ] Buffer read/write, barrier, and atomic operations produce correct HLSL register bindings (`u#`, `b#`) and intrinsic invocations.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T966-report.md` with exact `## Files changed`.

## Out of scope
- Host D3D12 command list execution and device initialization (`T963`).
- Raster graphics shaders (`@vertex`, `@fragment` in `E22.6`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), part of E22.3 GPU codegen backend.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T966/build` and `python tools/axtest.py --compiler build-snap-T966/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 GPU expansion)
