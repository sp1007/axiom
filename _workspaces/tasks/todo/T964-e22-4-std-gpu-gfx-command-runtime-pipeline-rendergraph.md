---
id: T964
title: E22.4 High-level std.gpu & std.gfx command runtime: ComputePipeline, CommandEncoder, RenderGraph & async dispatch
phase: P22-gpu-heterogeneous-computing
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T963]
priority: 234
status: todo
attempts: 0
paths: [std/gpu/runtime, std/gpu/pipeline, std/gfx/command, tests/run/gpu_compute_runtime]
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md, 0096, 0139, tasks/0626, tasks/0846]
covers: [REQ-GPU-034, REQ-GPU-041, REQ-GPU-064, REQ-GPU-065]
---
# T964 — E22.4 High-level std.gpu & std.gfx command runtime: ComputePipeline, CommandEncoder, RenderGraph & async dispatch

## Goal
Implement the high-level `std.gpu.runtime`, `std.gpu.pipeline`, and `std.gfx.command` layers (`GraphicsContext`, `ComputePipeline`, `PipelineCache`, `CommandEncoder`, `RenderGraph`, and `gpu.dispatch`) per `spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md` (`REQ-GPU-065`).

## Scope
- Implement `std/gpu/runtime` and `std/gpu/pipeline`: multi-GPU device context creation, typed `ComputePipeline<K>` and `PipelineCache` validated against `GpuKernelABI` reflection metadata, `gpu.dispatch`, explicit-device `gpu.dispatch_on`, parallel multi-GPU `gpu.dispatch_multi_gpu`, collective synchronization, `ExecutionQueue` submission, device-affinity validation, and generational `GraphicsDeviceState` recovery.
- Implement `std/gfx/command`: `GraphicsContext.open(selector: GpuAdapterSelector)`, offscreen/headless `RenderTarget` and `TextureView` descriptors, `CommandEncoder`, `ComputePass`, `TransferPass`, explicit resource barrier transitions, and `RenderGraph` DAG compilation (topological pass scheduling, transient buffer aliasing, per-pass device affinity, and automatic barrier insertion between producer/consumer compute and transfer passes).
- Implement copy elision in `RenderGraph` transfer passes per ADR-0040 §3: on shared-pool devices (`has_unified_memory == true`), linear 1D buffer transfer nodes lower to domain transitions + barriers without staging copies; 2D/3D textures and images always emit hardware tiling/swizzling blits.
- Verify that programs not importing `std.gpu`/`std.gfx` link zero GPU runtime symbols (`AGPU-25`).
- Add end-to-end run tests in `tests/run/gpu_compute_runtime`.

## Acceptance
- [ ] Run tests in `tests/run/gpu_compute_runtime` pass in `--interp` and native modes with `0 WEAK-NATIVE`, verifying typed `gpu.dispatch`, multi-pass `CommandEncoder` and `RenderGraph` execution, `PipelineCache` reuse, `GpuEvent` async/blocking completion, and generational device-loss recovery.
- [ ] `RenderGraph` transfer passes on shared-pool devices elide copies for linear buffers while preserving identical output contents; texture passes emit layout conversion blits.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T964-report.md` with exact `## Files changed`.

## Out of scope
- Full retained-mode GUI widget toolkits or 3D scene/physics engines (post-v1 `P24` / `E24.2`, `E24.4`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, P16 gate `T316`, and `T963`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T964/build` and `python tools/axtest.py --compiler build-snap-T964/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
- 2026-11-10 22:30:00 updated by architect (ADR-0040 revision: RenderGraph linear buffer copy elision vs texture tiling blit)
