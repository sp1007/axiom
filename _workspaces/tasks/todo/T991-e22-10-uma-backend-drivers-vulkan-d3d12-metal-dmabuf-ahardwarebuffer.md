---
id: T991
title: E22.10 UMA backend drivers: Vulkan, D3D12, Metal, AHardwareBuffer, dma-buf & OS memory pressure
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T963, T969, T990]
priority: 261
status: todo
attempts: 0
paths: [std/sys/gpu/vulkan/uma.ax, std/sys/gpu/d3d12/uma.ax, std/sys/gpu/metal/uma.ax, std/sys/gpu/linux/dmabuf.ax, std/sys/gpu/android/ahardwarebuffer.ax, tests/run/gpu_uma_driver]
locks: [std/sys/gpu/mod.ax]
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/SPEC-139-unified-memory-architecture.md, spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md, spec/SPEC-134-apple-metal-msl-backend.md, spec/requirements/OWNER.md]
covers: [REQ-OWNER-009, REQ-GPU-035, REQ-GPU-036]
---
# T991 — E22.10 UMA backend drivers: Vulkan, D3D12, Metal, AHardwareBuffer, dma-buf & OS memory pressure

## Goal
Implement the low-level OS and driver backend integration for Unified Memory Architecture across Direct3D 12, Vulkan, Apple Metal, Android `AHardwareBuffer`, Linux `dma-buf`, and OS memory pressure monitoring per `spec/SPEC-139-unified-memory-architecture.md`.

## Scope
- Implement Direct3D 12 UMA & ReBAR driver extensions (`std/sys/gpu/d3d12/uma.ax`):
  - Query `CheckFeatureSupport(D3D12_FEATURE_ARCHITECTURE1)` with `NodeIndex = 0` initialized.
  - Create heaps: `D3D12_HEAP_TYPE_CUSTOM` + `D3D12_MEMORY_POOL_L0` on UMA; on ReBAR discrete adapters allocate in `D3D12_MEMORY_POOL_L1` with `CPU_PAGE_PROPERTY_WRITE_COMBINE` (`D3D12_HEAP_TYPE_GPU_UPLOAD`).
  - Host import: `ID3D12Device3::OpenExistingHeapFromAddress` for `VirtualRegion` (`VirtualAlloc`); `ID3D12Device3::OpenExistingHeapFromFileMapping` for Win32 file mappings; return `GpuError.HostImportUnsupported` when file mapping handle is unavailable.
  - DXGI memory budget: query `DXGI_MEMORY_SEGMENT_GROUP_LOCAL` on UMA; register for budget change events.
- Implement Vulkan UMA driver extensions (`std/sys/gpu/vulkan/uma.ax`):
  - Check `VK_MEMORY_PROPERTY_HOST_COHERENT_BIT` per memory type; emit `vkFlushMappedMemoryRanges` / `vkInvalidateMappedMemoryRanges` only on non-coherent types.
  - Host import: `VK_EXT_external_memory_host` querying `minImportedHostPointerAlignment` (up to 64 KiB).
  - External handles: `VK_ANDROID_external_memory_android_hardware_buffer` (`std/sys/gpu/android/ahardwarebuffer.ax`) on Android, and `VK_EXT_external_memory_dma_buf` (`std/sys/gpu/linux/dmabuf.ax`) on Linux.
  - Budget query: `VK_EXT_memory_budget`.
- Implement Apple Metal UMA driver extensions (`std/sys/gpu/metal/uma.ax`):
  - `newBufferWithBytesNoCopy:length:options:deallocator:` strictly enforcing `vm_page_size` (16 KiB) alignment and page-multiple length.
  - Integrate Grand Central Dispatch `DISPATCH_SOURCE_TYPE_MEMORYPRESSURE` and iOS/iPadOS `os_proc_available_memory()`.
- Implement OS memory pressure listeners on Linux (PSI `/proc/pressure/memory`) and Android (`ComponentCallbacks2.onTrimMemory`).
- Add driver tests in `tests/run/gpu_uma_driver`.

## Acceptance
- [ ] Run tests in `tests/run/gpu_uma_driver` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] D3D12 driver initializes `NodeIndex = 0`, places UMA allocations in L0, places ReBAR allocations in L1, and uses `OpenExistingHeapFromFileMapping` for file mappings.
- [ ] Vulkan driver enforces `minImportedHostPointerAlignment` (up to 64 KiB) and emits flush/invalidate only on non-`HOST_COHERENT` memory types.
- [ ] Metal driver enforces 16 KiB page alignment and page-multiple length.
- [ ] External memory import passes on Android (`AHardwareBuffer`) and Linux (`dma-buf`).
- [ ] OS memory pressure notifications map correctly to `Normal | Warning | Critical`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T991-report.md` with exact `## Files changed`.

## Out of scope
- End-to-end conformance test matrix across 4 topologies (`T992`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), part of Epic E22.10.
- Depends on P11 gate `T311`, P12 gate `T312`, P16 gate `T316`, `T963`, `T969`, and `T990`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T991/build` and `python tools/axtest.py --compiler build-snap-T991/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-10 22:30:00 created by architect (ADR-0040 revision: Epic E22.10 low-level driver implementations across D3D12, Vulkan, Metal, Android, Linux)
