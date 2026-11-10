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
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/requirements/OWNER.md, 0096, 0139, tasks/0459, tasks/0468, tasks/0470, tasks/0826, tasks/0846]
covers: [REQ-OWNER-009, REQ-OPT-347, REQ-ECO-5958, REQ-GPU-045, REQ-GPU-061, REQ-GPU-062]
---
# T980 — E22.8 Canonical GPU AI acceleration, tensor matrix-multiplication-accumulate & hot-reload specification (SPEC-137)

## Goal
Consolidate the canonical specification for Axiom's GPU AI acceleration (subgroup/warp SIMT collectives, half-precision `f16`/`bf16`, Cooperative Matrix / Tensor Core MMA) and safe live runtime shader & pipeline hot-reload into `spec/SPEC-137-gpu-ai-tensor-mma-hot-reload.md` (`AXS-MMA-*` and `AXS-HOT-*` rule IDs citing `0096`, `0139`, `tasks/0459`, `tasks/0468`, `tasks/0470`, and BOOTSTRAP-615 `0846 §252–254`).

## Scope
- Write `spec/SPEC-137-gpu-ai-tensor-mma-hot-reload.md` starting with a Vietnamese `## Tóm tắt` section and numbered rule IDs:
- Specify Subgroup / Warp SIMT collectives (`REQ-GPU-045`, `REQ-GPU-062`, `tasks/0470 §211.31-32`): subgroup size discovery, capability-gated collective operations, and subgroup arithmetic reductions.
- Specify half-precision float representations in AGIR: `f16`, `bf16`, and mixed-precision MMA arithmetic.
- Specify Cooperative Matrix / Tensor Core MMA (`REQ-GPU-061`, `tasks/0459 §200`, `tasks/0468 §209`): generic `TileMatrix<T, M, N, K, Use>`, `load`, `store`, `fill`, and `mma_sync` lowering across SPIR-V, HLSL/DXIL, and MSL.
- Wire AI tensor storage domains and weights loading to the ADR-0040 zero-copy contract:
  - Specify that Tensor `.to(device)` / `.to_async(device)` take `self` by value (by-move ownership transfer per REQ-OPT-347 and ADR-0040 §3), enabling zero-copy transfer elision on shared-pool devices while preserving value semantics and REQ-GPU-061 explicit transfer requirements.
  - Specify `Tensor.from_host_import(ImportedDeviceView<T>, shape)` for read-only `mmap`-loaded model weights without allocating device memory.
- Specify Live Shader & Pipeline Hot-Reload (`0846 §252-254`, `std.gpu.hot_reload`): recompilation, strict ABI compatibility validation, atomic frame-boundary pipeline pointer swap, and safe rollback.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-137-gpu-ai-tensor-mma-hot-reload.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-MMA-NNN` and `AXS-HOT-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] SPEC-137 specifies by-value tensor `.to(device)` copy elision and `Tensor.from_host_import` zero-copy weight loading conforming to ADR-0040 and REQ-GPU-061.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T980-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of subgroup/MMA emitters (`T981`, `T982`) and hot-reload runtime (`T983`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), part of Epic E22.8.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 AI acceleration expansion)
- 2026-11-10 22:30:00 updated by architect (ADR-0040 revision: tensor by-value .to(device) copy elision & Tensor.from_host_import, REQ-OWNER-009)
