---
id: T988
title: E22.9 — Headless FBO & Software-Rasterizer differential graphics conformance suite
phase: P22-gpu-heterogeneous-computing
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T987, T974]
priority: 258
status: todo
attempts: 0
paths: [tests/conformance/p22/e22_9_opengl]
spec: [spec/SPEC-138-opengl-gles-glsl-backend.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-GPU-064, REQ-GPU-065]
---
# T988 — E22.9 — Headless FBO & Software-Rasterizer differential graphics conformance suite

## Goal
Certify E22.9 exit criteria with a headless offscreen Framebuffer Object (FBO) conformance suite comparing rendered pixels differentially against the CPU Software Rasterizer (`E22.6`).

## Scope
- Create automated headless graphics conformance tests in `tests/conformance/p22/e22_9_opengl`:
  * Initialize an offscreen OpenGL context and create RGBA8 FBO render targets (512x512 pixels).
  * Render canonical graphics test scenes: shaded triangle, textured cube, depth buffer sorting, blending, uniform buffer updates, and compute-shader image generation.
  * Read back pixel buffers via `glReadPixels` into CPU host memory.
  * Render identical test scenes using the CPU Software Rasterizer (`std/sys/gpu/software`, `T974`).
  * Perform pixel-by-pixel differential image comparison: assert that rasterized images match within a strict tolerance threshold ($\Delta E \le 2$ or max 1-LSB per channel difference).
- Verify driver fallback and resource cleanup without GPU memory leaks.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p22/e22_9_opengl` pass headlessly on host Windows WGL or Linux EGL.
- [ ] Differential comparison between OpenGL and CPU Software Rasterizer passes with 0 perceptual divergence.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T988-report.md` with exact `## Files changed`.

## Out of scope
- Physical display window creation or UI event loop testing.
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T988/build` and `python tools/axtest.py --compiler build-snap-T988/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:40:00 created by axiom-architect (ADR-0039 P22 OpenGL compatibility expansion)
