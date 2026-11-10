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
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/SPEC-130-execution-domains-kernel-model.md, spec/SPEC-131-device-memory-cross-device-ownership.md, spec/SPEC-132-gpu-ir-spirv-codegen-backend.md, spec/SPEC-04-core-extensibility.md, spec/requirements/OWNER.md, 0096, 0139, tasks/0626, tasks/0843, tasks/0845, tasks/0846]
covers: [REQ-OWNER-009, REQ-ECO-5958, REQ-GPU-007, REQ-GPU-034, REQ-GPU-035, REQ-GPU-036, REQ-GPU-041, REQ-GPU-064, REQ-GPU-065]
---
# T962 — E22.4 Canonical heterogeneous host runtime, Vulkan/D3D12 compute dispatch & device discovery specification (SPEC-133)

## Goal
Consolidate the canonical specification for Axiom's heterogeneous host runtime, hardware/GPU device discovery (`std.device`), Vulkan and Direct3D 12 compute backends, command recording/pipeline runtime (`std.gpu`, `std.gfx`), and deterministic software compute fallback into `spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md` (`AXS-GPURT-*` rule IDs).

## Scope
- Write `spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-GPURT-NNN` rules (`0096 §9-19`, `0139 §XX.29-33, §XX.39-40`, `tasks/0626 §12-15, §27, §39-42`, `tasks/0843 §1-15`, `tasks/0845 §1`, `tasks/0846 §1-18`).
- Specify the hardware and accelerator discovery contract (`std.device`, `REQ-GPU-064`, `tasks/0843 §5-11`, `tasks/0845`): `DeviceManager.enumerate()`, generational `DeviceId { provider, physical_id, generation }`, `DeviceClass` (`Cpu`, `Gpu`, `Npu`, `Accelerator`, `Display`), `DeviceState`, capability-controlled device handles, and pay-for-what-you-use runtime linking (`AGPU-25`), including rich multi-GPU adapter topology and selection:
  - `GpuAdapterInfo`: `device_id: DeviceId`, `name: str`, `vendor: GpuVendor` (`Nvidia | Amd | Intel | Apple | Qualcomm | Arm | Other(u32)`), `pci_vendor_id: u32`, `pci_device_id: u32`, `device_type: GpuDeviceType` (`IntegratedGpu | DiscreteGpu | VirtualGpu | CpuSoftware`), `dedicated_vram_bytes: u64`, `shared_system_bytes: u64`, `compute_units: u32`, `supports_graphics: bool`, `supports_compute: bool`, `supports_present: bool`, `backend: GpuBackendKind`;
  - `PowerPreference = LowPower | HighPerformance | ExplicitAdapter` and `GpuAdapterSelector = DefaultForPower(PowerPreference) | IntegratedOnly | DiscreteOnly | ByVendor(GpuVendor) | ByPciId { vendor_id: u32, device_id: u32 } | ByDeviceId(DeviceId) | ByIndex(usize)`.
- Specify orthogonal Memory Topology discovery and hardware API precision per ADR-0040 revision and REQ-OWNER-009:
  - Detection tables per backend for `GpuMemoryTopology` (`DiscretePool | UnifiedSystemPool | CoherentMultiPoolNuma`), per-heap `HeapFlags` (`DeviceLocal | HostVisible | HostCoherent | HostCached`), and ReBAR aperture size (> 256 MiB vs legacy 256 MiB BAR).
  - D3D12: initialize `D3D12_FEATURE_DATA_ARCHITECTURE1.NodeIndex = 0` explicitly; custom heap L0 for UMA vs L1 for discrete ReBAR; `OpenExistingHeapFromFileMapping` for Win32 file mappings vs `OpenExistingHeapFromAddress` for `VirtualAlloc`.
  - Vulkan: cache coherence is per-`VkMemoryType` (`VK_MEMORY_PROPERTY_HOST_COHERENT_BIT`); ReBAR detection checking host-visible local heap > 256 MiB; `minImportedHostPointerAlignment` (up to 64 KiB); `VK_ANDROID_external_memory_android_hardware_buffer`; `VK_EXT_external_memory_dma_buf`.
  - DXGI: query `DXGI_MEMORY_SEGMENT_GROUP_LOCAL` only on UMA (`NON_LOCAL` reports 0); register for budget change notification events.
  - Budget & OS pressure: formula `usage_ratio = current_allocated_bytes / recommended_max_working_set_bytes` (<75% Normal, 75-90% Warning, >90% Critical); integration with Windows DXGI, Apple GCD / `os_proc_available_memory`, Linux PSI, Android `onTrimMemory`.
- Specify GPU command/graphics substrate: `GraphicsContext`, `GpuAdapter`, `GpuDevice`, `MultiGpuGroup`, `ExecutionQueue`, `ComputePipeline`, `PipelineCache`, `CommandEncoder`, `ComputePass`, `RenderGraph`, `gpu.dispatch_on`, `gpu.dispatch_multi_gpu`, and collectives with device-affinity ownership verification.
- Specify Vulkan Compute, Direct3D 12 Compute, and deterministic CPU/software compute fallback with configurable mock topologies for CI.
- Append `host.gpu_*` intrinsic signatures to `spec/SPEC-04-core-extensibility.md` §11 and update `spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-GPURT-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] SPEC-133 specifies per-backend detection tables for `GpuMemoryTopology`, per-heap `HeapFlags`, ReBAR > 256 MiB differentiation, D3D12 `NodeIndex = 0` initialization, DXGI `LOCAL` segment rules on UMA, Vulkan per-memory-type coherence, and OS pressure formulas across Windows/Linux/macOS/iOS/Android.
- [ ] `spec/SPEC-04-core-extensibility.md` §11 lists the `host.gpu_*` host-interface intrinsics.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T962-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the Vulkan/D3D12 host drivers and runtime (`T963`, `T964`, `T991`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, P16 gate `T316`, and `T958`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T962/build` and `python tools/axtest.py --compiler build-snap-T962/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
- 2026-11-10 21:40:00 scope extended by architect (ADR-0040 Unified Memory Architecture)
- 2026-11-10 22:30:00 updated by architect (ADR-0040 revision: per-backend topology tables, D3D12 NodeIndex, DXGI LOCAL segment, Vulkan per-memory-type coherence, REQ-OWNER-009)
