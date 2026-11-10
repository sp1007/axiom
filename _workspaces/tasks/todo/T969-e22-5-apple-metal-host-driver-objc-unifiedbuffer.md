---
id: T969
title: E22.5 Apple Metal host driver (std.sys.gpu.metal), Objective-C bridge & UnifiedBuffer zero-copy path
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T668a, T921, T922, T956, T967, T968]
priority: 239
status: todo
attempts: 0
paths: [std/sys/gpu/metal, compiler/interp/host_metal, tests/run/gpu_metal_driver]
locks: [std/sys/gpu/mod.ax]
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/SPEC-134-apple-metal-msl-backend.md, spec/SPEC-131-device-memory-cross-device-ownership.md, spec/requirements/OWNER.md, 0096, 0139, tasks/0626, tasks/0846]
covers: [REQ-OWNER-009, REQ-ECO-5958, REQ-GPU-007, REQ-GPU-035, REQ-GPU-036, REQ-GPU-064]
---
# T969 — E22.5 Apple Metal host driver (std.sys.gpu.metal), Objective-C bridge & UnifiedBuffer zero-copy path

## Goal
Implement the Apple Metal host driver in `std/sys/gpu/metal` and `compiler/interp/host_metal`: driving `Metal.framework` via the Objective-C runtime, managing `MTLDevice`, pipelines, command queues, and shared memory buffers, and implementing the zero-copy `UnifiedBuffer` path for Apple Silicon per ADR-0040.

## Scope
- Implement the lightweight Objective-C runtime bridge in `std/sys/gpu/metal`: `objc_getClass`, `sel_registerName`, `objc_msgSend` bindings for `MTLCreateSystemDefaultDevice`, `MTLCopyAllDevices`, `MTLCommandQueue`, `MTLLibrary`, and `MTLComputePipelineState`.
- Implement device enumeration and initialization: query `MTLDevice` properties (name, registryID, `hasUnifiedMemory`, `maxThreadsPerThreadgroup`, `recommendedMaxWorkingSetSize`), exposing clean `GpuAdapterInfo` with `memory_topology = UnifiedSystemPool` on Apple Silicon.
- Implement buffer management:
  - Allocate `MTLBuffer` with appropriate storage modes (`MTLResourceStorageModeShared` vs `MTLResourceStorageModePrivate`).
  - Provide fast zero-copy `UnifiedBuffer` mapping on Apple Silicon (`hasUnifiedMemory == true`), allowing CPU pointers to be accessed by GPU dispatches without intermediate staging transfers while enforcing Axiom's borrow and capability invariants.
  - Implement host memory import via `newBufferWithBytesNoCopy:length:options:deallocator:` per ADR-0040 §4: strictly enforce that the pointer is aligned to `vm_page_size` (16 KiB on Apple Silicon) AND `length` is an integer multiple of `vm_page_size`; file mappings without page-multiple padding fail cleanly with `GpuError.HostImportMisaligned`.
  - Expose `GpuMemoryBudget` and memory pressure: `recommendedMaxWorkingSetSize` is advisory on macOS; on iOS/iPadOS integrate `os_proc_available_memory()` and listen for `DISPATCH_SOURCE_TYPE_MEMORYPRESSURE` events to signal pressure levels (`Normal`, `Warning`, `Critical`) and prevent Jetsam termination; return `GpuError.OutOfDeviceMemory` under `AllocPolicy.StrictBudget`.
- Implement compute dispatch and synchronization: MSL pipeline state compilation, compute command encoders, and `MTLSharedEvent` synchronization.
- Add host driver enumeration, buffer allocation, and compute dispatch tests in `tests/run/gpu_metal_driver`.

## Acceptance
- [ ] Tests in `tests/run/gpu_metal_driver` verify device discovery, `MTLBuffer` allocation, and kernel dispatch on macOS (and mock/replay validation on non-macOS test environments).
- [ ] Apple Silicon reports `UnifiedSystemPool` (`has_unified_memory = true`, `host_coherent = true`); zero-copy buffer handoff elides copies without staging.
- [ ] `HostImport` via `newBufferWithBytesNoCopy` strictly enforces 16 KiB page alignment and page-multiple length, cleanly returning `GpuError.HostImportMisaligned` on misaligned mappings.
- [ ] Memory pressure integration signals `Normal | Warning | Critical` and respects `AllocPolicy` without Jetsam termination.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T969-report.md` with exact `## Files changed`.

## Out of scope
- `CAMetalLayer` window surface presentation (`E22.6`, `T973`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, P16 gate `T316`, P16 Objective-C `T668a`, P21 virtual memory `T921`/`T922`, and Metal tasks `T956`, `T967`, `T968`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T969/build` and `python tools/axtest.py --compiler build-snap-T969/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 Metal expansion)
- 2026-11-10 21:40:00 scope extended by architect (ADR-0040 Unified Memory Architecture)
- 2026-11-10 22:30:00 updated by architect (ADR-0040 revision: wired T921/T922, 16 KiB page constraints, Jetsam/GCD pressure integration, REQ-OWNER-009)
