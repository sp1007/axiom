---
id: T978
title: E22.7 WebGPU host & wasm32 browser bridge (std.sys.gpu.webgpu, navigator.gpu / WebGPU C ABI)
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T675a, T676, T956, T976, T977]
priority: 248
status: todo
attempts: 0
paths: [std/sys/gpu/webgpu, tests/run/gpu_webgpu]
locks: [std/sys/gpu/mod.ax]
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/SPEC-136-webgpu-wgsl-backend.md, tasks/0846]
covers: [REQ-ECO-5958, REQ-GPU-064]
---
# T978 — E22.7 WebGPU host & wasm32 browser bridge (std.sys.gpu.webgpu, navigator.gpu / WebGPU C ABI)

## Goal
Implement the WebGPU runtime backend in `std/sys/gpu/webgpu`, bridging Axiom GPU compute and rendering dispatches to `navigator.gpu` when compiling to WebAssembly (`wasm32`), and providing native WebGPU C ABI bindings for headless desktop execution.

## Scope
- Implement the WebAssembly WebGPU bridge in `std/sys/gpu/webgpu` for target `wasm32`:
  - Define JS import bindings for WebGPU API objects: `navigator.gpu.requestAdapter`, `adapter.requestDevice`, `device.createShaderModule`, `device.createComputePipeline`, `device.createBuffer`, `queue.writeBuffer`, `queue.submit`, `buffer.mapAsync`.
  - Handle asynchronous promises from JavaScript via event loop poll ticks without blocking the main WASM thread.
- Implement the native WebGPU C ABI fallback in `std/sys/gpu/webgpu` for desktop targets: dynamically load native WebGPU implementation libraries (`wgpu-native` / `Dawn`), implementing standard WebGPU objects.
- Implement memory management and buffer operations:
  - Allocate GPU buffers with usage flags (`Storage`, `Uniform`, `CopySrc`, `CopyDst`).
  - Implement fast-path initial population using `mappedAtCreation = true` per ADR-0040 §1, avoiding separate staging buffer allocation when creating pre-populated buffers.
  - Staging buffer upload and asynchronous readback mapping.
- Add browser/NodeJS and native headless test cases in `tests/run/gpu_webgpu`.

## Acceptance
- [ ] Tests in `tests/run/gpu_webgpu` verify adapter discovery, buffer creation, WGSL shader compilation, and compute dispatch under WASM runtime (NodeJS / headless browser) and native WebGPU.
- [ ] Initial buffer population via `mappedAtCreation = true` verified to bypass intermediate staging copies.
- [ ] Buffer round-trip operations preserve exact data bytes between host and device.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T978-report.md` with exact `## Files changed`.

## Out of scope
- WebGPU canvas surface configuration and HTML event loop integration (`T979`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), part of Epic E22.7.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T978/build` and `python tools/axtest.py --compiler build-snap-T978/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 WebGPU expansion)
- 2026-11-10 22:30:00 updated by architect (ADR-0040 revision: mappedAtCreation initial upload fast-path)
