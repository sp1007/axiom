---
id: T967
title: E22.5 Canonical Apple Metal backend & MSL codegen specification (SPEC-134)
phase: P22-gpu-heterogeneous-computing
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T222, T311, T312, T316, T958, T962]
priority: 237
status: todo
attempts: 0
paths: [spec/SPEC-134-apple-metal-msl-backend.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-130-execution-domains-kernel-model.md, spec/SPEC-131-device-memory-cross-device-ownership.md, spec/SPEC-132-gpu-ir-spirv-codegen-backend.md, 0096, 0139, tasks/0626, tasks/0846]
covers: [REQ-ECO-5958, REQ-GPU-007, REQ-GPU-064]
---
# T967 — E22.5 Canonical Apple Metal backend & MSL codegen specification (SPEC-134)

## Goal
Consolidate the canonical specification for Axiom's Apple Metal Shading Language (`MSL`, `.metal`) compute codegen backend, argument buffer ABI, `std.sys.gpu.metal` host driver, Objective-C runtime bridge, and Apple Silicon unified memory fast-path into `spec/SPEC-134-apple-metal-msl-backend.md` (`AXS-MTL-*` rule IDs).

## Scope
- Write `spec/SPEC-134-apple-metal-msl-backend.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-MTL-NNN` rules (`0096 §3-26`, `0139 §XX.7-44`, `tasks/0626 §20-38`, `0846 §13, §44-48`).
- Specify the Metal Shading Language 3.0+ target representation (`ObjectFormat.MetalLib`, `CallConv.GpuKernel`):
  - Function qualifiers: `kernel` for compute functions, address space qualifiers (`device`, `constant`, `threadgroup`, `thread`).
  - SIMT built-in attributes: `[[thread_position_in_grid]]`, `[[thread_position_in_threadgroup]]`, `[[threadgroup_position_in_grid]]`, `[[threads_per_threadgroup]]`, `[[threads_per_grid]]`.
  - Synchronization: `threadgroup_barrier(mem_flags::mem_device | mem_flags::mem_threadgroup)`.
  - Atomic operations using `metal::atomic<T>` and memory orders.
- Specify the Metal argument buffer and buffer binding ABI:
  - Deterministic binding index mapping: `[[buffer(i)]]`, `[[texture(i)]]`, `[[sampler(i)]]`.
  - Small parameters passed as scalar/struct uniforms in `constant` address space or push-constant equivalents.
  - Emission of reflection tables mapping Axiom `@kernel` arguments to Metal buffer indices and argument encoders.
- Specify the host driver integration (`std/sys/gpu/metal`):
  - Binding to `Metal.framework` via Objective-C runtime (`objc_msgSend`): `MTLCreateSystemDefaultDevice()`, `MTLCopyAllDevices()` for multi-GPU Macs (e.g. Intel Macs with discrete AMD GPUs or external eGPUs), `MTLDevice`, `MTLCommandQueue`, `MTLCommandBuffer`, `MTLComputeCommandEncoder`.
  - Compilation pipeline: source JIT via `newLibraryWithSource:options:error:` or offline `.metallib` binary loading via `newLibraryWithData:error:`.
  - Synchronization using `MTLSharedEvent` (timeline semaphore equivalent) and command buffer completion handlers.
- Specify the Apple Silicon zero-copy unified memory path (`StorageModeShared`):
  - Invariants and capability rules for `MTLResourceStorageModeShared` buffers on unified architecture devices (`device.hasUnifiedMemory == true`), allowing CPU and GPU to share the same physical allocation without staging copies while preserving Axiom capability exclusivity.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-134-apple-metal-msl-backend.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-MTL-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T967-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the MSL emitter (`T968`) and host driver (`T969`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), opens Epic E22.5.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T967/build` and `python tools/axtest.py --compiler build-snap-T967/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 Metal expansion)
