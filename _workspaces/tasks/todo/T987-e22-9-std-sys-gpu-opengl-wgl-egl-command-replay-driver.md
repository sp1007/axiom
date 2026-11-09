---
id: T987
title: E22.9 — std/sys/gpu/opengl thread-safe WGL/EGL/GLX command replay driver & state tracker
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T986, T963]
priority: 257
status: todo
attempts: 0
paths: [std/sys/gpu/opengl, tests/run/opengl_driver]
locks: [std/sys/gpu/mod.ax]
spec: [spec/SPEC-138-opengl-gles-glsl-backend.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-GPU-064, REQ-GPU-065]
---
# T987 — E22.9 — std/sys/gpu/opengl thread-safe WGL/EGL/GLX command replay driver & state tracker

## Goal
Implement the thread-safe `std/sys/gpu/opengl` compatibility driver wrapping WGL (Windows), EGL (Linux/Android), and GLX (X11), with command replay offloading, Direct State Access, and shadow state differential tracking.

## Scope
- Implement `std/sys/gpu/opengl`:
  * Context creation: WGL Core Profile 4.5+ on Windows, EGL 1.5 on Linux/Android.
  * Dynamically load OpenGL function pointers (`wglGetProcAddress`, `eglGetProcAddress`).
  * Implement `Queue.submit`: dequeue recorded commands recorded by `CommandEncoder` on arbitrary worker threads and replay them sequentially on the dedicated OpenGL context thread.
- Implement state tracking mechanisms:
  * Fast-path: On OpenGL 4.5+ drivers, use Direct State Access (`glCreateBuffers`, `glNamedBufferStorage`, `glBindTextureUnit`, `glCreateFramebuffers`) to manipulate GPU objects without altering global binding state.
  * Compatibility fallback: On OpenGL 4.3 / GLES 3.1, implement shadow state tracking to minimize redundant `glBind*` calls and restore prior context state before foreign calls.
- Implement swapchain presentation via `SwapBuffers` / `eglSwapBuffers`.

## Acceptance
- [ ] Run tests in `tests/run/opengl_driver` verify context creation, shader compilation, buffer upload, and offscreen rendering under Windows WGL and Linux EGL.
- [ ] Multi-thread test verifies recording commands across 4 worker threads and executing them safely via `Queue.submit` without thread-affinity panic.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T987-report.md` with exact `## Files changed`.

## Out of scope
- Apple macOS OpenGL (Apple deprecated OpenGL in macOS 10.14; Metal `E22.5` is the normative backend).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), depends on P11 gate `T311`, P12 gate `T312`, and P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T987/build` and `python tools/axtest.py --compiler build-snap-T987/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:40:00 created by axiom-architect (ADR-0039 P22 OpenGL compatibility expansion)
