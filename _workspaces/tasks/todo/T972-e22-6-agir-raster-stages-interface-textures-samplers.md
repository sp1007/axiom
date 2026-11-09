---
id: T972
title: E22.6 AGIR raster stages (@vertex, @fragment), stage interface verification, textures & samplers
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T959, T960, T966, T968, T971]
priority: 242
status: todo
attempts: 0
paths: [compiler/agir/raster, compiler/types/graphics, tests/types/graphics, tests/target/raster_shaders]
locks: [compiler/agir/ir.ax, compiler/types/type.ax]
spec: [spec/SPEC-135-raster-graphics-swapchain-software-rasterizer.md, tasks/0846, 0096, 0139]
covers: [REQ-GPU-065]
---
# T972 — E22.6 AGIR raster stages (@vertex, @fragment), stage interface verification, textures & samplers

## Goal
Implement the graphics shader representations in AGIR (`@vertex`, `@fragment`), compile-time inter-stage interface type checking, and texture/sampler type lowering to SPIR-V, HLSL, and MSL.

## Scope
- Extend AGIR in `compiler/agir/raster` and `compiler/agir/ir.ax` with graphics execution domains:
  - `@vertex` entry-point definition with vertex input location attributes (`@location(n)`) and built-in clip position output.
  - `@fragment` entry-point definition with input varying attributes, built-in pixel coordinate/depth, and color render target outputs (`@location(n)`).
- Implement compile-time interface verification between `@vertex` outputs and `@fragment` inputs:
  - Verify location indices match between producer and consumer structs.
  - Verify data types, vector sizes, and interpolation qualifiers (`flat`, `linear`, `centroid`) are identical across the stage boundary.
- Implement texture and sampler type system in `compiler/types/graphics`:
  - `Texture1D<T>`, `Texture2D<T>`, `Texture3D<T>`, `TextureCube<T>`, `StorageTexture<Format, Access>`, and `Sampler`.
  - Texture sampling intrinsics: `texture.sample(sampler, uv)`, `texture.sample_lod(sampler, uv, lod)`, `texture.load(coord)`, `texture.dimensions()`.
- Lower graphics stages to backend targets:
  - SPIR-V: `OpEntryPoint Vertex`, `OpEntryPoint Fragment`, `OpExecutionMode OriginUpperLeft`, `OpTypeImage`, `OpTypeSampledImage`, `OpImageSampleImplicitLod`.
  - HLSL: `vs_6_0` / `ps_6_0`, `SV_Position`, `SV_Target0..7`, `Texture2D<float4>`, `SamplerState`.
  - MSL: `[[vertex]]`, `[[fragment]]`, `[[position]]`, `[[color(0)]]`, `metal::texture2d<float>`, `metal::sampler`.
- Add type checking and codegen tests in `tests/types/graphics` and `tests/target/raster_shaders`.

## Acceptance
- [ ] Tests in `tests/types/graphics` verify mismatched vertex/fragment interfaces or invalid interpolation modes are rejected at compile time with descriptive error codes.
- [ ] Codegen tests in `tests/target/raster_shaders` verify valid vertex and fragment shader pairs emit correct SPIR-V, HLSL, and MSL bytecodes/sources.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T972-report.md` with exact `## Files changed`.

## Out of scope
- Window surface creation and swapchains (`T973`).
- Host pipeline state creation (`T975`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), part of Epic E22.6.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T972/build` and `python tools/axtest.py --compiler build-snap-T972/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 Graphics expansion)
