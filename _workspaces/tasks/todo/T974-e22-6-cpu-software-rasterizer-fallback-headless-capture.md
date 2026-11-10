---
id: T974
title: E22.6 Deterministic CPU software rasterizer fallback (std.sys.gpu.software) & headless frame capture
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T971, T972]
priority: 244
status: todo
attempts: 0
paths: [std/sys/gpu/software_raster, tests/run/software_raster]
locks: [std/sys/gpu/mod.ax]
spec: [spec/decisions/ADR-0040-unified-memory-architecture-uma.md, spec/SPEC-135-raster-graphics-swapchain-software-rasterizer.md, tasks/0846]
covers: [REQ-GPU-065]
---
# T974 — E22.6 Deterministic CPU software rasterizer fallback (std.sys.gpu.software) & headless frame capture

## Goal
Implement the deterministic CPU Software Rasterizer backend in `std/sys/gpu/software_raster` per BOOTSTRAP-615 (`0846 §78–80`), providing pixel-exact raster graphics rendering and headless framebuffer image capture for CI environments without physical GPU hardware.

## Scope
- Implement the core software rasterization pipeline in `std/sys/gpu/software_raster`:
  - Fixed-point vertex processing and clip-space homogeneous division (`w` clipping).
  - Screen mapping and subpixel bounding-box triangle setup with top-left fill rule.
  - Perspective-correct barycentric coordinate evaluation across 8x8 pixel tiles.
  - Depth buffer comparison (`Less`, `LessEqual`, `Greater`, `Always`) and 24-bit/32-bit depth write.
  - Fragment shader evaluation loop invoking CPU-compiled `@fragment` function pointers.
  - Texture sampling with bilinear filtering, mipmap clamping, and repeat/clamp address modes.
  - Color blending (opaque overwrite, standard alpha blend `src_alpha + (1 - src_alpha)`, additive).
- Note Memory Topology: CPU software rasterizer reports `UnifiedSystemPool` (`has_unified_memory = true`, `host_coherent = true`) by default per ADR-0040 §1, with configurable mock topology for CI verification.
- Implement multi-threaded tile binning: divide framebuffer into independent tiles and dispatch across host worker threads (`std.thread`) with zero cross-tile synchronization during rasterization.
- Implement headless framebuffer readback and screenshot capture (`0846 §80`): save rendered color/depth buffers to uncompressed PNG and raw RGBA/binary formats; provide bit-exact image hashing (SHA-256).
- Add software rendering unit tests in `tests/run/software_raster`.

## Acceptance
- [ ] Tests in `tests/run/software_raster` execute on headless CI without GPU hardware and produce deterministic, pixel-exact framebuffers matching expected SHA-256 hashes.
- [ ] Memory topology defaults to `UnifiedSystemPool` and reports zero staging copies on linear buffer transfers.
- [ ] Depth testing correctly occludes background primitives and alpha blending produces mathematically accurate RGBA values.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T974-report.md` with exact `## Files changed`.

## Out of scope
- Advanced SIMD vectorization of the software rasterizer (leveraged from existing P12 primitives where available).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), part of Epic E22.6.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 Raster graphics expansion)
- 2026-11-10 22:30:00 updated by architect (ADR-0040 revision: software rasterizer UnifiedSystemPool topology specification)
