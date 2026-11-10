---
id: T322
title: Phase P22 gate — GPU & heterogeneous computing
phase: P22-gpu-heterogeneous-computing
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T222, T311, T312, T316, T950, T951, T952, T953, T954, T955, T956, T957, T958, T959, T960, T961, T962, T963, T964, T965, T966, T967, T968, T969, T970, T971, T972, T973, T974, T975, T976, T977, T978, T979, T980, T981, T982, T983, T984, T985, T986, T987, T988, T989, T990, T991, T992]
priority: 322
status: todo
attempts: 0
paths: [tests/conformance/p22, _workspaces/reports/phase-P22-review.md]
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/ROADMAP.md, spec/SPEC-130-execution-domains-kernel-model.md, spec/SPEC-131-device-memory-cross-device-ownership.md, spec/SPEC-132-gpu-ir-spirv-codegen-backend.md, spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md, spec/SPEC-134-apple-metal-msl-backend.md, spec/SPEC-135-raster-graphics-swapchain-software-rasterizer.md, spec/SPEC-136-webgpu-wgsl-backend.md, spec/SPEC-137-gpu-ai-tensor-mma-hot-reload.md, spec/SPEC-138-opengl-gles-glsl-backend.md, spec/SPEC-139-unified-memory-architecture.md, spec/requirements/OWNER.md]
covers: [REQ-OWNER-009, REQ-OPT-347, REQ-GPU-064, REQ-GPU-065]
---
# T322 — Phase P22 gate: GPU & heterogeneous computing

## Goal
Certify that phase P22 meets the exit criteria of every epic in `spec/ROADMAP.md` §3 (`E22.1`–`E22.10`: GPU compute, graphics, Metal, WebGPU, AI tensors, hot-reload, OpenGL compatibility, and Unified Memory Architecture run with oracle-checked results) and that all requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks (`E22.1` `T953`, `E22.2` `T957`, `E22.3` `T961`, `E22.4` `T965`, `E22.5` `T970`, `E22.6` `T975`, `E22.7` `T979`, `E22.8` `T984`, `E22.9` `T988`, `E22.10` `T992`).
- `reqcov.py --phase P22-gpu-heterogeneous-computing`: every requirement implemented or explicitly re-mapped (with note), including `REQ-OWNER-009`.
- Collect epic conformance results into `tests/conformance/p22` (index + missing cases added).
- Verify ADR-0040 UMA exit criteria:
  - Orthogonal memory topology detection (`DiscretePool`, `UnifiedSystemPool`, `CoherentMultiPoolNuma`).
  - Zero-copy linear buffer transfer elision while preserving value-copy semantics (`TransferStats.bytes_copied == 0` on by-move transitions; `upload`/`download` reporting full bytes).
  - Type-safe host memory import (`HostImport.read`/`write`/`region`) with runtime alignment verification (64 KiB, 16 KiB) and rejection of `MmapCow`.
  - Hardware API precision (D3D12 `NodeIndex = 0`, custom heap L0 vs L1 ReBAR, Vulkan per-memory-type coherence, DXGI LOCAL segment group).
  - Headless 4-topology test matrix passing with simulated cache poisoning and software ICDs (WARP / Lavapipe).
- Ask axiom-architect (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion (`E22.1`–`E22.10`) demonstrated with commands and results in the QA report.
- [ ] ADR-0040 UMA exit criteria verified across all supported backends and mock architectures (`T992`).
- [ ] Full suite green (gate rule: PASS or BLOCKED; only `xfail` entries for spec gaps with an ADR may remain); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T322-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T222, prerequisite phase gates `T311`, `T312`, `T316`, prerequisite virtual memory tasks in E21.6 (`T921`, `T922`), and all P22 tasks `T950`–`T992`.

## Log
- 2026-10-06 02:23:59 covers += REQ-GPU-064, REQ-GPU-065 (metadata only)
- 2026-11-03 10:55:00 updated by T222: depends on T311, T312, T316, T950–T965
- 2026-11-09 21:45:00 updated by architect: wired E22.5–E22.8 tasks T966–T984
- 2026-11-09 23:40:00 updated by architect: wired E22.9 tasks T985–T988
- 2026-11-10 22:30:00 updated by architect (ADR-0040 revision: wired E22.10 tasks T989–T992, added UMA exit criteria, REQ-OWNER-009)
