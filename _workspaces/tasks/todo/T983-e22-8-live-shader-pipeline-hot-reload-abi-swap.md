---
id: T983
title: E22.8 Live shader & pipeline hot-reload (std.gpu.hot_reload) with ABI validation & atomic swap
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T870, T964, T975, T980]
priority: 253
status: todo
attempts: 0
paths: [std/gpu/hot_reload, tests/run/gpu_hot_reload]
locks: [std/gpu/pipeline.ax]
spec: [spec/SPEC-137-gpu-ai-tensor-mma-hot-reload.md, tasks/0846]
covers: [REQ-GPU-065]
---
# T983 — E22.8 Live shader & pipeline hot-reload (std.gpu.hot_reload) with ABI validation & atomic swap

## Goal
Implement the safe live shader and pipeline hot-reload runtime in `std/gpu/hot_reload` per BOOTSTRAP-615 (`0846 §252–254`), compiling modified shader sources on the fly, verifying interface compatibility against active pipelines, and performing atomic pipeline swaps at frame boundaries.

## Scope
- Implement the shader hot-reload engine in `std/gpu/hot_reload`:
  - Watch shader source file paths on disk using filesystem notification events or polling.
  - Invoke the Axiom compiler pipeline dynamically to parse, type check, and compile modified shader modules into target bytecode (SPIR-V, DXIL, MSL, WGSL).
- Implement strict ABI compatibility verification before pipeline replacement (`0846 §254`):
  - Descriptor layout matching: ensure new shader requires no additional descriptor sets or incompatible resource types at existing binding slots.
  - Push-constant layout matching: ensure offsets and byte sizes of uniform constants remain compatible with caller dispatch code.
  - Render pass matching: ensure `@fragment` output targets match existing framebuffer attachment count and pixel formats.
- Implement atomic pipeline replacement at frame boundaries:
  - Create the new `ComputePipeline` / `GraphicsPipeline` state object.
  - Atomically update the active pipeline handle (`AtomicPtr`) at the frame boundary before new command buffer recording begins.
  - Defer destruction of the old pipeline until all currently in-flight frames retire on the GPU timeline (`DeferredReleasePool`).
- Implement safe rollback:
  - If shader recompilation encounters a syntax error, type error, or ABI violation, abort the reload, log a detailed diagnostic, and continue rendering with the existing pipeline without crashing the running application.
- Add live reload simulation unit tests in `tests/run/gpu_hot_reload`.

## Acceptance
- [ ] Tests in `tests/run/gpu_hot_reload` verify that valid shader code updates are applied atomically between rendered frames without memory leaks, resource invalidation, or visual glitches.
- [ ] Malformed shader edits or ABI-incompatible binding modifications trigger clean rollback, leaving the active pipeline intact and reporting diagnostic warnings.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T983-report.md` with exact `## Files changed`.

## Out of scope
- State serialization of arbitrary application memory across process restarts (handled by E20.7 component hot reload).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), part of Epic E22.8.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T983/build` and `python tools/axtest.py --compiler build-snap-T983/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 AI & Hot-Reload expansion)
