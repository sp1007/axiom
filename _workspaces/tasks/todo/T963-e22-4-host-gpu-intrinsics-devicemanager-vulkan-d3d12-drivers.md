---
id: T963
title: E22.4 Host GPU intrinsics, DeviceManager enumeration & Vulkan / D3D12 compute backend drivers
phase: P22-gpu-heterogeneous-computing
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T956, T960, T962, T966]
priority: 233
status: todo
attempts: 0
paths: [std/device, std/sys/gpu/vulkan, std/sys/gpu/d3d12, std/sys/gpu/cpu_fallback, compiler/interp/host_gpu, tests/run/gpu_host_driver]
locks: [std/core/host.ax, compiler/interp/interp.ax]
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md, spec/SPEC-04-core-extensibility.md, spec/requirements/OWNER.md, tasks/0626, tasks/0843, tasks/0845, tasks/0846]
covers: [REQ-OWNER-009, REQ-ECO-5958, REQ-GPU-035, REQ-GPU-036, REQ-GPU-064, REQ-GPU-065]
---
# T963 — E22.4 Host GPU intrinsics, DeviceManager enumeration & Vulkan / D3D12 compute backend drivers

## Goal
Implement the `host.gpu_*` intrinsics, `std.device` hardware/GPU discovery (`REQ-GPU-064`), and the Vulkan, Windows Direct3D 12, and deterministic CPU-fallback compute backend drivers per `spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md`.

## Scope
- Declare the `host.gpu_*` intrinsics in `std/core/host.ax` and wire their oracle execution in `compiler/interp/host_gpu` and `compiler/interp/interp.ax` (`SPEC-04 AXS-EXT-110`).
- Implement `std/device` (`REQ-GPU-064`, `tasks/0843`, `tasks/0845`): `DeviceManager.enumerate`, `DeviceManager.enumerate_gpus`, `DeviceManager.select_gpu(selector: GpuAdapterSelector)`, `DeviceManager.find`, generational `DeviceId`, `DeviceClass`, `DeviceState`, `DeviceCapability`, and multi-GPU `GpuAdapterInfo` discovery.
- Implement `std/sys/gpu/vulkan`: dynamic Vulkan compute loader, `VkInstance`/`vkEnumeratePhysicalDevices`, `VkDevice`, compute `VkQueue`, device/staging buffer allocation, `.spv` `VkShaderModule`, `VkComputePipeline`, descriptor-set binding, `vkCmdDispatch`, timeline semaphore / `VkFence` synchronization; detect per-memory-type `HOST_COHERENT`; detect ReBAR > 256 MiB; query `VK_EXT_memory_budget`.
- Implement `std/sys/gpu/d3d12`: dynamic Windows Direct3D 12 compute backend, DXIL bytecode ingestion, `IDXGIFactory6.EnumAdapterByGpuPreference`, `ID3D12Device`, compute `ID3D12CommandQueue`/`GraphicsCommandList`, root signatures, UAV/SRV/CBV heaps, `Dispatch`, and fence event synchronization; initialize `NodeIndex = 0` before calling `CheckFeatureSupport(D3D12_FEATURE_ARCHITECTURE1)`; query DXGI `LOCAL` segment only on UMA (`NON_LOCAL` reports 0); allocate in `D3D12_MEMORY_POOL_L0` for UMA vs `L1` for discrete ReBAR; configure `HostAccessPattern` (`WRITE_COMBINE` for WriteOnly, `WRITE_BACK` for ReadOnly/ReadWrite with map/unmap invalidation); `OpenExistingHeapFromAddress` for `VirtualRegion`.
- Implement `std/sys/gpu/cpu_fallback`: deterministic software compute backend with configurable mock `GpuMemoryTopology` and simulated non-coherent cache poisoning (`MOCK_STALE_CACHE_READ` on un-invalidated reads) for headless testing.
- Add driver enumeration, buffer round-trip, and kernel dispatch tests in `tests/run/gpu_host_driver`.

## Acceptance
- [ ] Run tests in `tests/run/gpu_host_driver` pass in `--interp` and native modes with `0 WEAK-NATIVE`, verifying `DeviceManager` enumeration, generational `DeviceId` validation, buffer upload/download, and compute dispatch across available hardware backends (Vulkan / D3D12) and the deterministic software compute backend.
- [ ] `tests/run/gpu_host_driver` verifies `memory_topology` reporting, zero-copy heap selection, D3D12 `NodeIndex = 0` initialization, DXGI `LOCAL` segment querying on UMA, Vulkan per-memory-type cache maintenance (flushing only non-`HOST_COHERENT` allocations), and `memory_budget()` reporting.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T963-report.md` with exact `## Files changed`.

## Out of scope
- High-level `RenderGraph` runtime (`T964`) and specialized UMA import extensions (`E22.10`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, P16 gate `T316`, `T956`, `T960`, `T962`, `T966`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T963/build` and `python tools/axtest.py --compiler build-snap-T963/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
- 2026-11-10 21:40:00 scope extended by architect (ADR-0040 Unified Memory Architecture)
- 2026-11-10 22:30:00 updated by architect (ADR-0040 revision: D3D12 NodeIndex=0, L0 UMA vs L1 ReBAR, DXGI LOCAL segment, Vulkan per-memory-type coherence, REQ-OWNER-009)
