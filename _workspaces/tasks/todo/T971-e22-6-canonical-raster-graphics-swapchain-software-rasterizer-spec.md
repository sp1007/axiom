---
id: T971
title: E22.6 Canonical raster graphics pipeline, surface/swapchain & software rasterizer specification (SPEC-135)
phase: P22-gpu-heterogeneous-computing
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T222, T311, T312, T316, T958, T962]
priority: 241
status: todo
attempts: 0
paths: [spec/SPEC-135-raster-graphics-swapchain-software-rasterizer.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [tasks/0846, 0096, 0139]
covers: [REQ-GPU-065]
---
# T971 — E22.6 Canonical raster graphics pipeline, surface/swapchain & software rasterizer specification (SPEC-135)

## Goal
Consolidate the canonical specification for Axiom's complete native raster graphics pipeline, shader stages (`@vertex`, `@fragment`), textures, samplers, multi-window surface & swapchain lifecycle, and the deterministic CPU software rasterizer fallback into `spec/SPEC-135-raster-graphics-swapchain-software-rasterizer.md` (`AXS-GFX-*` rule IDs per BOOTSTRAP-615 `docs/base/tasks/0846`).

## Scope
- Write `spec/SPEC-135-raster-graphics-swapchain-software-rasterizer.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-GFX-NNN` rules citing `docs/base/tasks/0846` (§10–56, §78–90, §230–240) and `REQ-GPU-065`.
- Specify graphics shader stages in AGIR (`0846 §46-47`):
  - `@vertex` entry points taking vertex attributes and generating clip-space positions (`[[builtin(Position)]]` / `SV_Position`) and user varyings.
  - `@fragment` entry points taking interpolated varyings and outputting color render targets (`[[location(n)]]`) and optional fragment depth (`[[builtin(FragDepth)]]`).
  - Strict compile-time interface matching between vertex output struct and fragment input struct (matching locations, types, and interpolation modes: `flat`, `linear`, `centroid`).
- Specify textures and samplers (`0846 §30-33, §55-56`):
  - Texture dimensions (`Texture1D`, `Texture2D`, `Texture3D`, `TextureCube`), multi-sampled textures (`Texture2DMS`), array textures, and read-write `StorageTexture`.
  - Texture formats: unorm, snorm, uint, sint, float (e.g. `Rgba8Unorm`, `Rgba8UnormSrgb`, `Bgra8Unorm`, `Rgba16Float`, `R32Float`, `Depth24PlusStencil8`).
  - Samplers: filtering (Nearest, Linear), mipmap modes, address modes (Repeat, MirrorRepeat, ClampToEdge, ClampToBorder), comparison samplers for shadow mapping.
- Specify the `GraphicsPipeline` and `RenderPass` state models (`0846 §36, §44, §231-239`):
  - Vertex buffers, vertex layouts (stride, attributes, step modes per-vertex or per-instance).
  - Primitive topology (PointList, LineList, LineStrip, TriangleList, TriangleStrip).
  - Rasterizer state (cull mode Front/Back/None, front face CCW/CW, depth bias, polygon mode).
  - Depth/stencil state (depth write, depth compare function, stencil test).
  - Color blend states (alpha blend, additive, premultiplied, write masks) and Multiple Render Targets (MRT, up to 8 targets).
- Specify the multi-backend native `Surface` & `Swapchain` lifecycle (`0846 §10-25, §88-90`):
  - Native surface handles: Win32 `HWND`, macOS/iOS `CAMetalLayer`, Linux Wayland `wl_surface` / X11 `Window`, Android `ANativeWindow`, WASM `HTMLCanvas`.
  - Present modes: FIFO (VSync), Mailbox (low-latency triple buffer), Immediate (tearing).
  - Surface resize, DPI scaling, swapchain recreation, and HDR/sRGB color space negotiation.
- Specify the deterministic CPU Software Rasterizer (`0846 §78-79`):
  - Bit-exact software fallback implementing fixed-point triangle setup, barycentric rasterization, subpixel precision, perspective-correct attribute interpolation, depth test, and alpha blend.
  - Headless framebuffer capture producing deterministic PNG/RAW images for automated visual regression CI without requiring a physical GPU.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-135-raster-graphics-swapchain-software-rasterizer.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-GFX-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T971-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of raster stages and pipeline runtime (`T972`–`T975`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), opens Epic E22.6.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T971/build` and `python tools/axtest.py --compiler build-snap-T971/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 Graphics expansion)
