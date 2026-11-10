---
id: T989
title: E22.10 Canonical UMA, Host Import & Memory Topology Specification (SPEC-139)
phase: P22-gpu-heterogeneous-computing
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T222, T311, T312, T316, T920, T954, T962]
priority: 259
status: todo
attempts: 0
paths: [spec/SPEC-139-unified-memory-architecture.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/SPEC-131-device-memory-cross-device-ownership.md, spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md, spec/SPEC-125-virtual-memory-mmap.md, spec/requirements/OWNER.md, 0096, 0139, tasks/0626, tasks/0846]
covers: [REQ-OWNER-009, REQ-OPT-347, REQ-GPU-035, REQ-GPU-036]
---
# T989 — E22.10 Canonical UMA, Host Import & Memory Topology Specification (SPEC-139)

## Goal
Consolidate the canonical specification for Axiom's Unified Memory Architecture (UMA), orthogonal memory topology classification, type-safe host memory import, value-preserving copy elision, and hardware-independent coherency into `spec/SPEC-139-unified-memory-architecture.md` (`AXS-UMA-*` rule IDs) strictly resolving the 39 Red-Team findings from ADR-0040 and satisfying `REQ-OWNER-009`.

## Scope
- Write `spec/SPEC-139-unified-memory-architecture.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-UMA-NNN` rules citing `ADR-0040`, `0139 §XX.6-18, §XX.29-44`, `0096`, `tasks/0626`, `REQ-OWNER-009`, and `REQ-OPT-347`.
- Specify orthogonal memory topology descriptors (`AXS-UMA-001..010`):
  - `GpuMemoryTopology = DiscretePool | UnifiedSystemPool | CoherentMultiPoolNuma`.
  - `HeapFlags = DeviceLocal | HostVisible | HostCoherent | HostCached`.
  - `rebar_aperture_bytes: u64` (> 256 MiB distinguishing Resizable BAR from legacy 256 MiB PCIe BAR aperture).
  - Multi-pool NUMA topology for NVIDIA Grace Hopper / AMD MI300A (coherent HBM3 + LPDDR5X with distinct bandwidth tiers).
- Specify value-preserving copy elision rules (`AXS-UMA-011..020`):
  - `upload`/`download`/`device_copy` preserve value semantics (RAM→RAM `memcpy` without staging on UMA).
  - Copy elision applies strictly to domain handoffs on the same `UnifiedBuffer<T>`, by-value `.into_device(self)`, by-value `.to(device)` (REQ-OPT-347), and `shared_read_views()`.
  - Explicitly exclude 2D/3D tiled/swizzled textures from linear zero-copy claims (layout conversion blit mandatory).
  - Profiling counters: `TransferStats { bytes_copied, bytes_written_over_bus, cache_flushes, cache_invalidates }`.
- Specify type-safe host memory import contracts (`AXS-UMA-021..030`):
  - `HostImport.read<T: PlainData>(src: view<Mmap>) -> Result<ImportedDeviceView<T>, GpuError>`.
  - `HostImport.write<T: PlainData>(src: mut_view<MmapMut>) -> Result<ImportedDeviceMutView<T>, GpuError>`.
  - `HostImport.region<T: PlainData>(src: mut_view<VirtualRegion>, offset: usize, len: usize) -> Result<ImportedDeviceMutView<T>, GpuError>`.
  - External handles: Android `AHardwareBuffer` (`VK_ANDROID_external_memory_android_hardware_buffer`) and Linux `dma-buf` (`VK_EXT_external_memory_dma_buf`).
  - Runtime alignment: `max(page_size(), minImportedHostPointerAlignment)` (64 KiB on Vulkan/Mesa, 16 KiB on Apple Silicon Metal; length must be multiple of 16 KiB on Metal).
  - Rejection of `MmapCow` mutable GPU import; static rejection of `protect`/`decommit`/`munmap` while import view is active; file truncation safety contract.
- Specify hardware API precision rules (`AXS-UMA-031..040`):
  - D3D12: `D3D12_FEATURE_DATA_ARCHITECTURE1.NodeIndex = 0` explicit initialization; custom heap L0 for UMA vs L1 for discrete ReBAR; `OpenExistingHeapFromFileMapping` for Win32 file mappings vs `OpenExistingHeapFromAddress` for `VirtualAlloc`.
  - Vulkan: cache coherence checked per `VkMemoryType` (`VK_MEMORY_PROPERTY_HOST_COHERENT_BIT`); flush/invalidate emitted only when flag is absent.
  - DXGI: query `DXGI_MEMORY_SEGMENT_GROUP_LOCAL` only on UMA (`NON_LOCAL` reports 0).
  - Host access patterns: `HostAccessPattern = WriteOnly | ReadOnly | ReadWrite` (`WriteOnly` -> `WRITE_COMBINE`, `ReadOnly`/`ReadWrite` -> `WRITE_BACK` / `HOST_CACHED` to prevent 90-99% CPU read throughput collapse).
  - Unified budget: `GpuError.OutOfDeviceMemory { requested_bytes, budget }`, `AllocPolicy = Advisory | StrictBudget`, and OS memory pressure formulas (Windows DXGI, Apple GCD / `os_proc_available_memory`, Linux PSI, Android `onTrimMemory`).
- Specify portability contract and headless CI verification (`AXS-UMA-041..050`): program legality is hardware-independent; simulated non-coherent cache poisoning in CPU fallback; software ICD verification (WARP / Lavapipe).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-139-unified-memory-architecture.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-UMA-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] SPEC-139 contains numbered rules resolving 100% of the 39 Red-Team findings from `redteam-uma-semantics.md` and `redteam-uma-hardware.md`.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T989-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of `std.gpu.uma` types (`T990`) and driver backend adapters (`T991`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), first task of Epic E22.10.
- Depends on P11 gate `T311`, P12 gate `T312`, P16 gate `T316`, P21 virtual memory spec `T920`, and P22 specs `T954`, `T962`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T989/build` and `python tools/axtest.py --compiler build-snap-T989/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-10 22:30:00 created by architect (ADR-0040 revision: Epic E22.10 specification for UMA, Host Import & Memory Topology)
