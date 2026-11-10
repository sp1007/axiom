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
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md, spec/SPEC-04-core-extensibility.md, tasks/0626, tasks/0843, tasks/0845, tasks/0846]
covers: [REQ-ECO-5958, REQ-GPU-035, REQ-GPU-036, REQ-GPU-064, REQ-GPU-065]
---
# T963 — E22.4 Host GPU intrinsics, DeviceManager enumeration & Vulkan / D3D12 compute backend drivers

## Goal
Implement the `host.gpu_*` intrinsics, `std.device` hardware/GPU discovery (`REQ-GPU-064`), and the Vulkan, Windows Direct3D 12, and deterministic CPU-fallback compute backend drivers per `spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md`.

## Scope
- Declare the `host.gpu_*` intrinsics in `std/core/host.ax` and wire their oracle execution in `compiler/interp/host_gpu` and `compiler/interp/interp.ax` (`SPEC-04 AXS-EXT-110`).
- Implement `std/device` (`REQ-GPU-064`, `tasks/0843`, `tasks/0845`): `DeviceManager.enumerate`, `DeviceManager.enumerate_gpus`, `DeviceManager.select_gpu(selector: GpuAdapterSelector)`, `DeviceManager.find`, generational `DeviceId`, `DeviceClass`, `DeviceState`, `DeviceCapability`, and multi-GPU `GpuAdapterInfo` discovery (`GpuDeviceType`: `IntegratedGpu` onboard vs `DiscreteGpu` dedicated vs `VirtualGpu` vs `CpuSoftware`; `GpuVendor`: `Nvidia`, `Amd`, `Intel`, `Apple`, `Qualcomm`; PCI `vendor_id`/`device_id`, dedicated VRAM vs shared system memory, queue family capabilities, and `PowerPreference` `LowPower` onboard vs `HighPerformance` discrete selection).
- Implement `std/sys/gpu/vulkan`: dynamic Vulkan compute loader (`vulkan-1.dll` on Windows, `libvulkan.so.1` on Linux), `VkInstance`/`vkEnumeratePhysicalDevices` multi-GPU enumeration (`VkPhysicalDeviceProperties` `VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU` vs `VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU`, `vendorID` `0x10DE` NVIDIA / `0x1002` AMD / `0x8086` Intel, `VkPhysicalDeviceMemoryProperties`), explicit physical device selection by `DeviceId` / `GpuAdapterSelector`, `VkDevice` initialization, compute `VkQueue`, device/staging buffer allocation, `.spv` `VkShaderModule` and `VkComputePipeline` creation, descriptor-set binding, `vkCmdDispatch`, and timeline semaphore / `VkFence` synchronization.
- Implement `std/sys/gpu/d3d12`: dynamic Windows Direct3D 12 compute backend (`d3d12.dll` / `dxgi.dll`), ingesting DXIL bytecode emitted by `T966` (`compiler/target/hlsl_dxil`), `IDXGIFactory6.EnumAdapterByGpuPreference` (`DXGI_GPU_PREFERENCE_MINIMUM_POWER` for onboard iGPU vs `DXGI_GPU_PREFERENCE_HIGH_PERFORMANCE` for discrete NVIDIA/AMD dGPU) and `EnumAdapters1` (`DXGI_ADAPTER_DESC1` `VendorId`, `DeviceId`, `DedicatedVideoMemory`), explicit adapter selection by `DeviceId` / `GpuAdapterSelector`, `ID3D12Device`, compute `ID3D12CommandQueue` / `ID3D12GraphicsCommandList`, root signature and compute PSO binding, UAV/SRV/CBV heaps, `Dispatch`, and `ID3D12Fence` event synchronization.
- Implement `std/sys/gpu/cpu_fallback`: deterministic software compute backend executing `.spv`/`AGIR` kernels on host worker pools when explicit fallback policy is selected or when running in headless CI without physical GPU hardware (`tasks/0626 §27`, `tasks/0846 §2.9-10`, `AGPU-23`).
- Implement UMA detection and zero-copy allocation (ADR-0040): D3D12 `CheckFeatureSupport(D3D12_FEATURE_ARCHITECTURE1)` with `D3D12_HEAP_TYPE_CUSTOM` + `D3D12_MEMORY_POOL_L0` (`WRITE_BACK` when cache-coherent, `WRITE_COMBINE` otherwise, no intermediate `UPLOAD` heap) and `ID3D12Device3.OpenExistingHeapFromAddress` host import; Vulkan `DEVICE_LOCAL | HOST_VISIBLE` persistent mapping with `vkFlushMappedMemoryRanges` / `vkInvalidateMappedMemoryRanges` only for non-`HOST_COHERENT` types, ReBAR detection, `VK_EXT_external_memory_host` import, and `VK_EXT_memory_budget`; `IDXGIAdapter3.QueryVideoMemoryInfo` budgets; CPU fallback exposing a configurable mock `GpuMemoryArchitecture`.
- Add driver enumeration, buffer round-trip, and low-level kernel dispatch tests in `tests/run/gpu_host_driver`.

## Acceptance
- [ ] Run tests in `tests/run/gpu_host_driver` pass in `--interp` and native modes with `0 WEAK-NATIVE`, verifying `DeviceManager` enumeration, generational `DeviceId` validation, buffer upload/download, and compute dispatch across available hardware backends (Vulkan / D3D12) and the deterministic software compute backend.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T963-report.md` with exact `## Files changed`.

## Out of scope
- High-level `ComputePipeline`, `CommandEncoder`, and `RenderGraph` runtime API (`T964`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T963/build` and `python tools/axtest.py --compiler build-snap-T963/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:55:00 created by T222 (P22 phase planning)
- 2026-11-10 21:40:00 scope extended by architect (ADR-0040 Unified Memory Architecture)
