---
id: T975
title: E22.6 High-level GraphicsPipeline, RenderPass, MRT, blend/depth-stencil & graphics conformance suite
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T972, T973, T974]
priority: 245
status: todo
attempts: 0
paths: [std/gfx/pipeline, std/gfx/renderpass, tests/conformance/p22/e22_6_raster_graphics]
locks: [std/gfx/mod.ax]
spec: [spec/SPEC-135-raster-graphics-swapchain-software-rasterizer.md, tasks/0846]
covers: [REQ-GPU-065]
---
# T975 — E22.6 High-level GraphicsPipeline, RenderPass, MRT, blend/depth-stencil & graphics conformance suite

## Goal
Implement the high-level `GraphicsPipeline` and `RenderPass` command recording abstractions in `std/gfx/pipeline` and `std/gfx/renderpass`, and certify the complete raster graphics runtime with an end-to-end conformance suite in `tests/conformance/p22/e22_6_raster_graphics`.

## Scope
- Implement `GraphicsPipeline` creation and descriptor validation in `std/gfx/pipeline`:
  - Vertex layout binding: stride, attribute offsets, vertex formats (`Float32x2`, `Float32x3`, `Float32x4`, `Unorm8x4`), step mode (`Vertex` vs `Instance`).
  - Primitive topology: `TriangleList`, `TriangleStrip`, `LineList`, `PointList`.
  - Rasterizer state: `CullMode` (`None`, `Front`, `Back`), `FrontFace` (`Ccw`, `Cw`), polygon depth bias.
  - Depth/stencil state: `DepthCompare` (`Less`, `LessEqual`, `Greater`, `Always`), depth write enable, stencil operations.
  - Multi-target color blend: independent blend state per render target (up to 8 MRT attachments).
- Implement `RenderPass` command encoder in `std/gfx/renderpass`:
  - Begin pass with clear/load/store actions (`ColorAttachment` with clear color, `DepthStencilAttachment`).
  - Command recording: `set_pipeline(pipeline)`, `set_vertex_buffer(slot, buffer)`, `set_index_buffer(buffer, format)`, `set_bind_group(index, group)`, `set_viewport(x, y, w, h)`, `set_scissor_rect(rect)`.
  - Draw commands: `draw(vertex_count, instance_count, first_vertex, first_instance)` and `draw_indexed(index_count, instance_count, first_index, base_vertex, first_instance)`.
  - End pass and transition attachments to present or shader resource states.
- Implement the comprehensive E22.6 graphics conformance suite in `tests/conformance/p22/e22_6_raster_graphics`:
  - Basic triangle drawing with smooth vertex color interpolation.
  - Textured cube rendering with perspective projection, 3D depth buffer testing, and mipmapped texture sampling.
  - Multiple Render Targets (MRT): rendering albedo, normals, and depth to 3 independent textures simultaneously.
  - Multi-backend verification: run conformance tests across available native backends (Vulkan, D3D12, Metal) and compare against the deterministic software rasterizer reference output.

## Acceptance
- [ ] Conformance tests in `tests/conformance/p22/e22_6_raster_graphics` pass with zero image differences between native GPU outputs and the deterministic software rasterizer fallback.
- [ ] MRT rendering writes correctly to multiple attachments in a single pass without corruption.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T975-report.md` with exact `## Files changed`.

## Out of scope
- Ray tracing or mesh shading pipelines (`0846 §145-146`, deferred post-v1).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), closes Epic E22.6.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T975/build` and `python tools/axtest.py --compiler build-snap-T975/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 Graphics expansion)
