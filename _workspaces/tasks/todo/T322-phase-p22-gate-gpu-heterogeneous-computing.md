---
id: T322
title: Phase P22 gate — GPU & heterogeneous computing
phase: P22-gpu-heterogeneous-computing
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T222, T311, T312, T316, T950, T951, T952, T953, T954, T955, T956, T957, T958, T959, T960, T961, T962, T963, T964, T965, T966, T967, T968, T969, T970, T971, T972, T973, T974, T975, T976, T977, T978, T979, T980, T981, T982, T983, T984]
priority: 322
status: todo
attempts: 0
paths: [tests/conformance/p22, _workspaces/reports/phase-P22-review.md]
spec: [spec/ROADMAP.md, spec/SPEC-130-execution-domains-kernel-model.md, spec/SPEC-131-device-memory-cross-device-ownership.md, spec/SPEC-132-gpu-ir-spirv-codegen-backend.md, spec/SPEC-133-host-runtime-vulkan-d3d12-compute.md, spec/SPEC-134-apple-metal-msl-backend.md, spec/SPEC-135-raster-graphics-swapchain-software-rasterizer.md, spec/SPEC-136-webgpu-wgsl-backend.md, spec/SPEC-137-gpu-ai-tensor-mma-hot-reload.md]
covers: [REQ-GPU-064, REQ-GPU-065]
---
# T322 — Phase P22 gate: GPU & heterogeneous computing

## Goal
Certify that phase P22 meets the exit criteria of every epic in `spec/ROADMAP.md` §3 (`E22.1`–`E22.8`: GPU compute, graphics, Metal, WebGPU, AI tensors, and hot-reload run with oracle-checked results) and that all requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks (`E22.1` `T953`, `E22.2` `T957`, `E22.3` `T961`, `E22.4` `T965`, `E22.5` `T970`, `E22.6` `T975`, `E22.7` `T979`, `E22.8` `T984`).
- `reqcov.py --phase P22-gpu-heterogeneous-computing`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p22` (index + missing cases added).
- Ask axiom-architect (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion demonstrated with commands and results in the QA report.
- [ ] Full suite green (gate rule: PASS or BLOCKED; only `xfail` entries for spec gaps with an ADR may remain); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T322-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T222, prerequisite phase gates `T311`, `T312`, `T316`, and all P22 tasks `T950`–`T965`.

## Log
- 2026-10-06 02:23:59 covers += REQ-GPU-064, REQ-GPU-065 (metadata only)
- 2026-11-03 10:55:00 updated by T222: depends on T311, T312, T316, T950–T965
