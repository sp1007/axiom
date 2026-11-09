---
id: T986
title: E22.9 — compiler/target/glsl GLSL 450 & ESSL 310 emitter with NDC clip normalization
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T985, T959]
priority: 256
status: todo
attempts: 0
paths: [compiler/target/glsl, tests/glsl]
spec: [spec/SPEC-138-opengl-gles-glsl-backend.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-GPU-064, REQ-GPU-065]
---
# T986 — E22.9 — compiler/target/glsl GLSL 450 & ESSL 310 emitter with NDC clip normalization

## Goal
Implement the `compiler/target/glsl` backend lowering AGIR shader stages into valid, compilable GLSL 450 Core (Desktop OpenGL) and ESSL 310 (OpenGL ES / Mobile) source code with automatic NDC clip-space depth and Y-axis normalization.

## Scope
- Implement `compiler/target/glsl`:
  * Lower compute, vertex, and fragment stages from AGIR to text GLSL (`#version 450 core` or `#version 310 es`).
  * Emit uniform block definitions with `layout(std140, binding = N)` and shader storage buffer objects with `layout(std430, binding = M)`.
  * Map 2D/3D/Cube texture samplers (`layout(binding = K) uniform sampler2D u_tex`).
  * Emit inter-stage varyings with explicit location indices (`layout(location = 0) in/out`).
- Implement NDC coordinate system normalization:
  * Normalize depth from OpenGL default `[-1, 1]` to Axiom standard `[0, 1]`: emit automatic vertex shader epilogue `gl_Position.z = gl_Position.z * 2.0 - gl_Position.w` when targeting drivers without `glClipControl`.
  * Support framebuffer Y-axis inversion across render-to-texture passes.
- Support runtime shader compilation and validation via Khronos reference GLSLang validator.

## Acceptance
- [ ] Golden tests in `tests/glsl` verify that emitted GLSL 450 and ESSL 310 shaders pass official Khronos `glslangValidator` without warnings or syntax errors.
- [ ] Mathematical tests verify that vertex Z normalization maps `[0, 1]` depth inputs to expected OpenGL clip coordinates.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T986-report.md` with exact `## Files changed`.

## Out of scope
- Direct legacy OpenGL 2.x/3.x fixed-function pipeline codegen.
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T986/build` and `python tools/axtest.py --compiler build-snap-T986/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:40:00 created by axiom-architect (ADR-0039 P22 OpenGL compatibility expansion)
