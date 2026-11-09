---
id: T985
title: E22.9 — Canonical specification for OpenGL 4.5+ / GLES 3.1+ compatibility backend (SPEC-138)
phase: P22-gpu-heterogeneous-computing
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T222, T311, T312, T316]
priority: 255
status: todo
attempts: 0
paths: [spec/SPEC-138-opengl-gles-glsl-backend.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-138-opengl-gles-glsl-backend.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-GPU-064, REQ-GPU-065]
---
# T985 — E22.9 — Canonical specification for OpenGL 4.5+ / GLES 3.1+ compatibility backend (SPEC-138)

## Goal
Consolidate the canonical specification for the OpenGL 4.5+ Core / OpenGL ES 3.1+ compatibility backend and `AGIR -> GLSL 450 / ESSL 310` emission into `spec/SPEC-138-opengl-gles-glsl-backend.md` (`AXS-GLSL-*` rule IDs) strictly conforming to `0846 §216`.

## Scope
- Write `spec/SPEC-138-opengl-gles-glsl-backend.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-GLSL-NNN` rules.
- Specify the architectural boundary per `0846 §216`: OpenGL is strictly an optional implementation backend for `std.gpu` / `std.gfx`; zero legacy global mutable state (`glBind*`) is exposed to Axiom developer APIs.
- Specify thread-affinity decoupling: `CommandEncoder` records execution streams safely across worker threads (`Send`), while `Queue.submit` replays recorded commands deterministically on the context-owning OS thread.
- Specify GLSL 450 Core and ESSL 310 source emission from AGIR: uniform buffers, storage buffers, textures, samplers, stage interfaces, and coordinate system normalization (mapping NDC depth from `[-1, 1]` to Axiom standard `[0, 1]` via `glClipControl` or vertex shader epilogues, plus framebuffer Y-axis inversion).
- Specify state tracking: Direct State Access (`GL_ARB_direct_state_access`) on OpenGL 4.5+, with shadow state-diff tracker on OpenGL 4.3 / GLES 3.1+.
- Specify headless offscreen FBO rasterization and differential image comparison against the CPU Software Rasterizer (`E22.6`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-138-opengl-gles-glsl-backend.md` exists with Vietnamese `## Tóm tắt`, numbered `AXS-GLSL-NNN` rules, and coordinate normalization diagrams.
- [ ] `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T985-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of GLSL emitter and OpenGL driver (`T986`–`T988`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T985/build` and `python tools/axtest.py --compiler build-snap-T985/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:40:00 created by axiom-architect (ADR-0039 P22 OpenGL compatibility expansion)
