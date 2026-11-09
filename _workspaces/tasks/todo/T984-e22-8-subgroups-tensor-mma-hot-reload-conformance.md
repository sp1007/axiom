---
id: T984
title: E22.8 Subgroup collectives, Tensor MMA & hot-reload differential verification suite
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T981, T982, T983]
priority: 254
status: todo
attempts: 0
paths: [tests/conformance/p22/e22_8_ai_hot_reload]
locks: [tests/conformance/p22/mod.ax]
spec: [spec/SPEC-137-gpu-ai-tensor-mma-hot-reload.md, 0096, 0139, tasks/0470, tasks/0846]
covers: [REQ-GPU-045, REQ-GPU-062]
---
# T984 — E22.8 Subgroup collectives, Tensor MMA & hot-reload differential verification suite

## Goal
Implement the end-to-end conformance and differential verification suite in `tests/conformance/p22/e22_8_ai_hot_reload`, certifying capability-gated Subgroup collectives, `f16`/`bf16` precision, Tensor Core MMA execution, and safe shader hot-reload across GPU backends and reference CPU oracles.

## Scope
- Implement the conformance suite in `tests/conformance/p22/e22_8_ai_hot_reload`:
  - Subgroup collectives: shuffle, broadcast, ballot, prefix sum scan, and parallel reduction across active warp lanes.
  - Half-precision math: `f16` and `bf16` dot product, vector normalization, and activation functions (ReLU, GELU, Sigmoid).
  - Tensor Core MMA: GEMM (General Matrix Multiply `C = A * B + C`) evaluated using `TileMatrix` instructions against reference FP64 CPU matrices.
  - Live shader hot-reload: programmatically update a compute kernel and a fragment shader during a continuous 100-frame rendering loop, verifying atomic replacement without frame drops, memory leaks, or NaN results.
- Implement fault injection:
  - Inject malformed shaders (syntax error, type mismatch, illegal address space access) into the hot-reload watcher, asserting that the system safely rolls back and reports the expected error diagnostics while continuing rendering.
- Verify differential equivalence across SPIR-V/Vulkan, D3D12, Metal, and the CPU software oracle.

## Acceptance
- [ ] All tests in `tests/conformance/p22/e22_8_ai_hot_reload` pass across available backends.
- [ ] Tensor MMA operations match reference CPU GEMM results within FP16 tolerance thresholds.
- [ ] Pipeline hot-reload successfully updates live shaders across 10 consecutive swaps without crash or memory corruption.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T984-report.md` with exact `## Files changed`.

## Out of scope
- Distributed multi-node model parallelism (deferred post-v1).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), closes Epic E22.8 and completes P22 implementation tasks before gate T322.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T984/build` and `python tools/axtest.py --compiler build-snap-T984/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 AI & Hot-Reload expansion)
