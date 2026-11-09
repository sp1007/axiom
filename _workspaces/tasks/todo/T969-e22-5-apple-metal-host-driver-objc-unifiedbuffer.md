---
id: T969
title: E22.5 Apple Metal host driver (std.sys.gpu.metal), Objective-C bridge & UnifiedBuffer zero-copy path
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T668a, T956, T967, T968]
priority: 239
status: todo
attempts: 0
paths: [std/sys/gpu/metal, compiler/interp/host_metal, tests/run/gpu_metal_driver]
locks: [std/sys/gpu/mod.ax]
spec: [spec/SPEC-134-apple-metal-msl-backend.md, 0096, 0139, tasks/0626, tasks/0846]
covers: [REQ-ECO-5958, REQ-GPU-007, REQ-GPU-035, REQ-GPU-036, REQ-GPU-064]
---
# T969 — E22.5 Apple Metal host driver (std.sys.gpu.metal), Objective-C bridge & UnifiedBuffer zero-copy path

## Goal
Implement the Apple Metal host driver in `std/sys/gpu/metal` and `compiler/interp/host_metal`: driving `Metal.framework` via the Objective-C runtime, managing `MTLDevice`, pipelines, command queues, and shared memory buffers, and implementing the zero-copy `UnifiedBuffer` path for Apple Silicon.

## Scope
- Implement the lightweight Objective-C runtime bridge in `std/sys/gpu/metal`: `objc_getClass`, `sel_registerName`, `objc_msgSend` bindings for `MTLCreateSystemDefaultDevice`, `MTLCopyAllDevices`, `MTLCommandQueue`, `MTLLibrary`, and `MTLComputePipelineState`.
- Implement device enumeration and initialization: query `MTLDevice` properties (name, registryID, `hasUnifiedMemory`, `maxThreadsPerThreadgroup`, `recommendedMaxWorkingSetSize`), exposing clean `GpuAdapterInfo` to `DeviceManager`.
- Implement buffer management:
  - Allocate `MTLBuffer` with appropriate storage modes (`MTLResourceStorageModeShared` vs `MTLResourceStorageModePrivate`).
  - Provide fast zero-copy `UnifiedBuffer` mapping on Apple Silicon (`hasUnifiedMemory == true`), allowing CPU pointers to be accessed by GPU dispatches without intermediate staging transfers while enforcing Axiom's borrow and capability invariants.
- Implement compute dispatch and synchronization:
  - Compile pipeline state objects from MSL source via `newLibraryWithSource:options:error:` or load precompiled `.metallib`.
  - Record compute command encoders: `setComputePipelineState:`, `setBuffer:offset:atIndex:`, `setBytes:length:atIndex:`, `dispatchThreadgroups:threadsPerThreadgroup:`.
  - Synchronize execution via `MTLSharedEvent` (timeline semaphore equivalent) and command buffer completion handlers.
- Add host driver enumeration, buffer allocation, and compute dispatch tests in `tests/run/gpu_metal_driver`.

## Acceptance
- [ ] Tests in `tests/run/gpu_metal_driver` verify device discovery, `MTLBuffer` allocation, and kernel dispatch on macOS (and mock/replay validation on non-macOS test environments).
- [ ] Apple Silicon unified memory mode correctly detects zero-copy capability and avoids redundant staging copies.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T969-report.md` with exact `## Files changed`.

## Out of scope
- `CAMetalLayer` window surface presentation (`E22.6`, `T973`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), part of Epic E22.5.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T969/build` and `python tools/axtest.py --compiler build-snap-T969/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 Metal expansion)
