---
id: T962
title: E22.4 Canonical heterogeneous host runtime, Vulkan/D3D12 compute dispatch & device discovery specification (SPEC-133)
phase: P22-gpu-heterogeneous-computing
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T222, T311, T312, T316, T958]
priority: 232
status: todo
attempts: 0
paths: [spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md, spec/SPEC-04-core-extensibility.md]
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/SPEC-130-execution-domains-kernel-model.md, spec/SPEC-131-device-memory-cross-device-ownership.md, spec/SPEC-132-gpu-ir-spirv-codegen-backend.md, spec/SPEC-04-core-extensibility.md, 0096, 0139, tasks/0626, tasks/0843, tasks/0845, tasks/0846]
covers: [REQ-ECO-5958, REQ-GPU-007, REQ-GPU-034, REQ-GPU-035, REQ-GPU-036, REQ-GPU-041, REQ-GPU-064, REQ-GPU-065]
---
# T962 — E22.4 Canonical heterogeneous host runtime, Vulkan/D3D12 compute dispatch & device discovery specification (SPEC-133)

## Goal
Consolidate the canonical specification for Axiom's heterogeneous host runtime, hardware/GPU device discovery (`std.device`), Vulkan and Direct3D 12 compute backends, command recording/pipeline runtime (`std.gpu`, `std.gfx`), and deterministic software compute fallback into `spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md` (`AXS-GPURT-*` rule IDs).

## Scope
- Write `spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-GPURT-NNN` rules (`0096 §9-19`, `0139 §XX.29-33, §XX.39-40`, `tasks/0626 §12-15, §27, §39-42`, `tasks/0843 §1-15`, `tasks/0845 §1`, `tasks/0846 §1-18`).
- Specify the hardware and accelerator discovery contract (`std.device`, `REQ-GPU-064`, `tasks/0843 §5-11`, `tasks/0845`): `DeviceManager.enumerate()`, generational `DeviceId { provider, physical_id, generation }`, `DeviceClass` (`Cpu`, `Gpu`, `Npu`, `Accelerator`, `Display`), `DeviceState`, capability-controlled device handles, and pay-for-what-you-use runtime linking (`AGPU-25`), including rich multi-GPU adapter topology and selection:
  - `GpuAdapterInfo`: `device_id: DeviceId`, `name: str`, `vendor: GpuVendor` (`Nvidia | Amd | Intel | Apple | Qualcomm | Arm | Other(u32)`), `pci_vendor_id: u32`, `pci_device_id: u32`, `device_type: GpuDeviceType` (`IntegratedGpu | DiscreteGpu | VirtualGpu | CpuSoftware`), `dedicated_vram_bytes: u64`, `shared_system_bytes: u64`, `compute_units: u32`, `supports_graphics: bool`, `supports_compute: bool`, `supports_present: bool`, `backend: GpuBackendKind`;
  - `PowerPreference = LowPower | HighPerformance | ExplicitAdapter` and `GpuAdapterSelector = DefaultForPower(PowerPreference) | IntegratedOnly | DiscreteOnly | ByVendor(GpuVendor) | ByPciId { vendor_id: u32, device_id: u32 } | ByDeviceId(DeviceId) | ByIndex(usize)` so normal lightweight GUI apps can bind to the onboard `IntegratedGpu` (`PowerPreference.LowPower`) while heavy graphics/compute apps (e.g., 3D texture painter, AI training/inference) bind explicitly to the discrete `Nvidia`/`Amd` GPU (`PowerPreference.HighPerformance`, `ByVendor(GpuVendor.Nvidia)`, or `ByDeviceId(id)`), or use both GPUs concurrently in the same process.
- Specify Unified Memory Architecture discovery and budgeting (ADR-0040): `GpuAdapterInfo.memory_architecture: GpuMemoryArchitecture` (`Discrete | CacheCoherentUma | NonCoherentUma | ReBarHostVisible`), `is_unified_memory: bool`, `unified_pool_bytes: u64`, detection rules per backend (D3D12 `D3D12_FEATURE_ARCHITECTURE1` `UMA` / `CacheCoherentUMA`; Vulkan `DEVICE_LOCAL | HOST_VISIBLE` (+`HOST_COHERENT` / `HOST_CACHED`) memory types and ReBAR heaps; Metal `hasUnifiedMemory`; conservative `Discrete` for WebGPU / OpenGL unless confirmed), the configurable mock architecture of the CPU fallback for headless CI, and `GpuMemoryBudget` (`MTLDevice.recommendedMaxWorkingSetSize`, `IDXGIAdapter3.QueryVideoMemoryInfo`, `VK_EXT_memory_budget`) with `pressure: Normal | Warning | Critical`.
- Specify the GPU command and graphics/compute substrate (`std.gpu`, `std.gfx`, `REQ-GPU-065`, `tasks/0846 §4-18`): `GraphicsContext.open(selector: GpuAdapterSelector)`, `GpuAdapter`, `GpuDevice` with generational device-loss detection/recovery (`GraphicsDeviceState = Created | Ready | Lost | Recovering | Recreated | Destroyed`), `MultiGpuGroup` (`MultiGpuGroup.open(selectors)`, `MultiGpuGroup.all_discrete()`, `MultiGpuGroup.all_by_vendor(GpuVendor.Nvidia)`, `MultiGpuGroup.all_compute_capable()`) for pooling 2..N GPUs into a coordinated multi-GPU compute/AI cluster on a single machine, `ExecutionQueue`, `ComputePipeline`, `PipelineCache`, `CommandEncoder`, `ComputePass`, `RenderGraph` compute/transfer/render DAG submission pinned to an explicit `GpuDevice` or partitioned across a `MultiGpuGroup`, `gpu.dispatch_on(device, kernel, grid, block, args...)`, and parallel multi-GPU `gpu.dispatch_multi_gpu(group, grid_per_gpu, block, per_rank_args) -> Result<MultiGpuEvent, GpuError>` alongside collective AI/compute operations (`all_reduce`, `all_gather`, `reduce_scatter`, `broadcast` for Data-Parallel / Tensor-Parallel / Pipeline-Parallel AI training & inference and large scientific simulations) with cross-device buffer ownership verification (`DeviceBuffer<T>` tied to its owning `DeviceId` so accidental cross-GPU buffer mixing without an explicit peer/staging transfer is rejected).
- Specify the Vulkan Compute (1.2/1.3 timeline semaphores, descriptor sets, `.spv` shader modules) and Windows Direct3D 12 Compute (`ID3D12Device`, compute command queues/lists, root signatures, fences) host backend adapters, plus the explicit deterministic CPU/software compute fallback (`tasks/0626 §27`, `tasks/0846 §2.9-10`, `AGPU-23`) so headless CI machines without a physical GPU or driver still execute the full GPU compute runtime with identical semantics.
- Append the `host.gpu_*` intrinsic signatures to `spec/SPEC-04-core-extensibility.md` §11 (`AXS-EXT-110`) and update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-GPURT-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `spec/SPEC-04-core-extensibility.md` §11 lists the `host.gpu_*` host-interface intrinsics.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T962-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the Vulkan/D3D12 host drivers and high-level `std.gpu`/`std.gfx` runtime (`T963`–`T964`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T962/build` and `python tools/axtest.py --compiler build-snap-T962/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
- 2026-11-10 21:40:00 scope extended by architect (ADR-0040 Unified Memory Architecture)
