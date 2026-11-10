---
id: T976
title: E22.7 Canonical WebGPU runtime & WGSL codegen specification (SPEC-136)
phase: P22-gpu-heterogeneous-computing
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T222, T311, T312, T316, T958, T962, T971]
priority: 246
status: todo
attempts: 0
paths: [spec/SPEC-136-webgpu-wgsl-backend.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, tasks/0846, 0096, 0139, 0162]
covers: [REQ-ECO-5958, REQ-GPU-007]
---
# T976 — E22.7 Canonical WebGPU runtime & WGSL codegen specification (SPEC-136)

## Goal
Consolidate the canonical specification for Axiom's WebGPU Shading Language (`WGSL`) codegen backend, `std.sys.gpu.webgpu` host/browser runtime, and WebAssembly (`wasm32`) GPU bridge into `spec/SPEC-136-webgpu-wgsl-backend.md` (`AXS-WGPU-*` rule IDs per BOOTSTRAP-615 `docs/base/tasks/0846 §13, §47, §217`).

## Scope
- Write `spec/SPEC-136-webgpu-wgsl-backend.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-WGPU-NNN` rules citing `0846 §13, §47, §217` and `REQ-ECO-5958`.
- Specify the WGSL target representation in the compiler (`TargetDesc.Wgpu`, `ObjectFormat.Wgsl`, `CallConv.GpuKernel`):
  - Function entry-point decorators: `@compute`, `@vertex`, `@fragment`.
  - Built-in variable attributes: `@builtin(global_invocation_id)`, `@builtin(local_invocation_id)`, `@builtin(workgroup_id)`, `@builtin(num_workgroups)`, `@builtin(position)`.
  - Address space and access mode mapping (`REQ-GPU-054`): `var<storage, read_write>`, `var<storage, read>`, `var<uniform>`, `var<workgroup>`, and `var<private>`.
  - Workgroup size decorator: `@workgroup_size(x, y, z)`.
  - Barriers and atomics: `workgroupBarrier()`, `storageBarrier()`, and `atomic<u32>` / `atomicAdd` / `atomicExchange`.
- Specify WGSL resource binding ABI: deterministic binding decorators `@group(0) @binding(i)`, storage/uniform buffers, textures, samplers, and struct layout alignment.
- Specify WebGPU memory topology constraints per ADR-0040 §1: WebGPU backend always reports `DiscretePool` and `supports_host_import = false` due to W3C sandbox; specify fast-path `GPUBufferDescriptor.mappedAtCreation = true` to elide staging buffer copies on initial data upload.
- Specify WebGPU runtime substrate (`std/sys/gpu/webgpu`): WASM `navigator.gpu` bridge and native WebGPU C ABI fallback.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-136-webgpu-wgsl-backend.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-WGPU-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] SPEC-136 specifies WebGPU `DiscretePool` reporting, `supports_host_import = false`, and `mappedAtCreation = true` zero-copy initialization fast-path.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T976-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the WGSL emitter (`T977`) and WebGPU host bridge (`T978`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), part of Epic E22.7.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 WebGPU expansion)
- 2026-11-10 22:30:00 updated by architect (ADR-0040 revision: WebGPU DiscretePool and mappedAtCreation specification)
