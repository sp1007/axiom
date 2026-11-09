---
id: T979
title: E22.7 WebGPU compute & graphics on wasm32 / headless conformance suite
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T975, T978]
priority: 249
status: todo
attempts: 0
paths: [tests/conformance/p22/e22_7_webgpu]
locks: [tests/conformance/p22/mod.ax]
spec: [spec/SPEC-136-webgpu-wgsl-backend.md, tasks/0846]
covers: [REQ-GPU-065]
---
# T979 — E22.7 WebGPU compute & graphics on wasm32 / headless conformance suite

## Goal
Implement the conformance test suite in `tests/conformance/p22/e22_7_webgpu`, certifying WebGPU compute kernels and raster graphics pipelines on `wasm32` (NodeJS/browser) and headless native runtimes.

## Scope
- Implement the test suite in `tests/conformance/p22/e22_7_webgpu`:
  - Compute kernels: 1D vector add, 2D matrix multiplication, workgroup shared memory reduction.
  - Storage buffer read/write and atomic operations under WGSL semantics.
  - Graphics pipeline rendering: drawing indexed color triangles and textured meshes to an offscreen render target or HTMLCanvas.
  - Texture sampling: loading textures and sampling with nearest and linear filtering.
- Implement an automated test runner for WebAssembly WebGPU execution using headless Chrome / NodeJS with WebGPU flags enabled.
- Verify differential equivalence between WebGPU rendered images / computed buffers and the CPU reference software rasterizer.

## Acceptance
- [ ] Conformance tests in `tests/conformance/p22/e22_7_webgpu` pass under headless browser / NodeJS WASM environment.
- [ ] Computed buffers and rendered pixels match the CPU reference implementation bit-for-bit.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T979-report.md` with exact `## Files changed`.

## Out of scope
- Advanced WebGPU features not in core specification (e.g., experimental subgroups).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), closes Epic E22.7.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T979/build` and `python tools/axtest.py --compiler build-snap-T979/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 WebGPU expansion)
