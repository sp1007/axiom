---
id: T980
title: E22.8 Canonical GPU AI acceleration, tensor matrix-multiplication-accumulate & hot-reload specification (SPEC-137)
phase: P22-gpu-heterogeneous-computing
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T222, T311, T312, T316, T958, T962, T971]
priority: 250
status: todo
attempts: 0
paths: [spec/SPEC-137-gpu-ai-tensor-mma-hot-reload.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [0096, 0139, tasks/0459, tasks/0468, tasks/0470, tasks/0826, tasks/0846]
covers: [REQ-ECO-5958, REQ-GPU-045, REQ-GPU-061, REQ-GPU-062]
---
# T980 — E22.8 Canonical GPU AI acceleration, tensor matrix-multiplication-accumulate & hot-reload specification (SPEC-137)

## Goal
Consolidate the canonical specification for Axiom's GPU AI acceleration (subgroup/warp SIMT collectives, half-precision `f16`/`bf16`, Cooperative Matrix / Tensor Core MMA) and safe live runtime shader & pipeline hot-reload into `spec/SPEC-137-gpu-ai-tensor-mma-hot-reload.md` (`AXS-MMA-*` and `AXS-HOT-*` rule IDs citing `0096`, `0139`, `tasks/0459`, `tasks/0468`, `tasks/0470`, and BOOTSTRAP-615 `0846 §252–254`).

## Scope
- Write `spec/SPEC-137-gpu-ai-tensor-mma-hot-reload.md` starting with a Vietnamese `## Tóm tắt` section and numbered rule IDs:
- Specify Subgroup / Warp SIMT collectives (`REQ-GPU-045`, `REQ-GPU-062`, `tasks/0470 §211.31-32`):
  - Subgroup size discovery: `subgroup.size()`, `subgroup.invocation_id()`.
  - Capability-gated collective operations: `subgroup.broadcast(val, id)`, `subgroup.shuffle(val, delta)`, `subgroup.shuffle_xor(val, mask)`, `subgroup.ballot(predicate)`, `subgroup.all(predicate)`, `subgroup.any(predicate)`.
  - Subgroup arithmetic reductions: `subgroup.reduce_add(val)`, `subgroup.reduce_min(val)`, `subgroup.reduce_max(val)`, `subgroup.inclusive_scan_add(val)`, `subgroup.exclusive_scan_add(val)`.
  - Invariants: subgroup execution is strictly distinct from CPU threading; non-portable warp assumptions are rejected at compile time unless explicitly capability-checked.
- Specify half-precision float representations in AGIR:
  - Storage and compute types: IEEE 754 16-bit binary floating point `f16`, and Brain Floating Point `bf16`.
  - Mixed-precision arithmetic operations (`f16` input, `f32` accumulator).
- Specify Cooperative Matrix / Tensor Core MMA (`REQ-GPU-061`, `tasks/0459 §200`, `tasks/0468 §209`):
  - Generic matrix tile primitive: `TileMatrix<T, M, N, K, Use>` where `Use` is `MatrixA | MatrixB | Accumulator`.
  - Matrix operations: `TileMatrix.load(view, stride)`, `TileMatrix.store(mut_view, stride)`, `TileMatrix.fill(scalar)`, and fused multiply-accumulate `mma_sync(matrix_a, matrix_b, accumulator) -> TileMatrix`.
  - Lowering across backends:
    - Vulkan / SPIR-V: `OpTypeCooperativeMatrixKHR`, `OpCooperativeMatrixLoadKHR`, `OpCooperativeMatrixStoreKHR`, `OpCooperativeMatrixMulAddKHR`.
    - Direct3D 12 / HLSL: WaveMMA intrinsics.
    - Metal / MSL: `simdgroup_matrix<T, M, N>` load/store/multiply.
- Specify Live Shader & Pipeline Hot-Reload (`0846 §252-254`, `std.gpu.hot_reload`):
  - Recompilation of changed shader source files on disk.
  - Strict ABI compatibility validation: verify that replacement shaders match the live pipeline's descriptor set layout, register bindings, push-constant ranges, and render-target format count.
  - Atomic pipeline pointer swap: swap `ComputePipeline` / `GraphicsPipeline` handles cleanly at frame boundary boundaries without draining or stalling existing in-flight GPU resource buffers.
  - Safe rollback: if compilation or ABI validation fails, retain the existing valid pipeline, emit a non-fatal diagnostic event, and prevent app termination.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-137-gpu-ai-tensor-mma-hot-reload.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-MMA-NNN` and `AXS-HOT-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T980-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of subgroup intrinsics, tensor MMA passes, and hot-reload runtime (`T981`–`T984`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), opens Epic E22.8.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T980/build` and `python tools/axtest.py --compiler build-snap-T980/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 AI & Hot-Reload expansion)
