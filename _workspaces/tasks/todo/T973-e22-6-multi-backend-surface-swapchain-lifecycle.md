---
id: T973
title: E22.6 Multi-backend Surface & Swapchain lifecycle (Win32, Wayland, X11, CAMetalLayer, ANativeWindow, HTMLCanvas)
phase: P22-gpu-heterogeneous-computing
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T222, T311, T312, T316, T963, T969, T971]
priority: 243
status: todo
attempts: 0
paths: [std/gfx/surface, std/gfx/swapchain, tests/run/gfx_surface]
locks: [std/gfx/mod.ax]
spec: [spec/SPEC-135-raster-graphics-swapchain-software-rasterizer.md, tasks/0846]
covers: [REQ-GPU-064, REQ-GPU-065]
---
# T973 — E22.6 Multi-backend Surface & Swapchain lifecycle (Win32, Wayland, X11, CAMetalLayer, ANativeWindow, HTMLCanvas)

## Goal
Implement the cross-platform window surface abstraction (`std/gfx/surface`) and native swapchain lifecycle engine (`std/gfx/swapchain`) across Windows, Linux, macOS, iOS, Android, and WebAssembly per BOOTSTRAP-615 (`0846 §10–25, §88–90`).

## Scope
- Implement native window surface handle wrapping in `std/gfx/surface`:
  - Windows: Win32 `HWND` and `HINSTANCE` (`SurfaceHandle.Win32 { hwnd, hinstance }`).
  - Linux: Wayland `wl_display` / `wl_surface`, X11 `Display` / `Window`.
  - Apple: macOS `NSWindow` / `CAMetalLayer`, iOS `UIView` / `CAMetalLayer`.
  - Android: `ANativeWindow` pointer.
  - Web: HTML5 `HTMLCanvasElement` selector / WebGPU canvas context.
  - Headless: Offscreen rendering surface (`SurfaceHandle.Headless { width, height }`).
- Implement the backend swapchain lifecycle engine in `std/gfx/swapchain`:
  - Vulkan: `VkSurfaceKHR`, `vkCreateSwapchainKHR`, `VkSwapchainKHR`, image acquisition with timeline fences, present queue submission (`vkQueuePresentKHR`).
  - Direct3D 12: `IDXGIFactory4.CreateSwapChainForHwnd`, `IDXGISwapChain3`, flip model (`DXGI_SWAP_EFFECT_FLIP_DISCARD`), `Present(1, 0)` vs `Present(0, DXGI_PRESENT_ALLOW_TEARING)`.
  - Metal: `CAMetalLayer`, `nextDrawable`, `MTLRenderPassDescriptor.colorAttachments[0].texture = drawable.texture`, `presentDrawable:`.
- Implement robust surface lifecycle and recreation logic (`0846 §88-90`):
  - Handle window resizing, minimize/restore, and DPI scaling without memory leaks or GPU crashes.
  - Recover gracefully from out-of-date or suboptimal swapchains (`VK_ERROR_OUT_OF_DATE_KHR`, `DXGI_STATUS_OCCLUDED`).
  - Coordinate frames in flight (2 or 3 frames) with present tokens and fence pacing to eliminate CPU/GPU stutter.
- Add surface creation, resize handling, and present loop unit tests in `tests/run/gfx_surface`.

## Acceptance
- [ ] Tests in `tests/run/gfx_surface` verify headless surface creation, frame acquisition, present token retirement, and resize recreation across Vulkan, D3D12, Metal, and software backends.
- [ ] Zero GPU memory leaks across 100 consecutive swapchain resize events.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T973-report.md` with exact `## Files changed`.

## Out of scope
- High-level RenderPass command recording (`T975`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P22 (`P22-gpu-heterogeneous-computing`), part of Epic E22.6.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T973/build` and `python tools/axtest.py --compiler build-snap-T973/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 Graphics expansion)
