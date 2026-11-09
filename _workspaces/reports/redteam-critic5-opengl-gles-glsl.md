# Red-Team Architectural Review: Proposal #12 (`P22` `E22.9` OpenGL 4.x / OpenGL ES 3.1+ Compatibility Backend & `AGIR -> GLSL`)

**Scope**: Adversarial review of owner request *"quên opengl"* against normative `docs/base/tasks/0846 - BOOTSTRAP-615.md §216` (`OpenGL Boundary`).

---

## Verdict: `ACCEPT WITH MANDATORY ARCHITECTURE, THREAD-SAFETY & NDC CLIP-SPACE GUARDRAILS`

Place as **Epic `E22.9` (OpenGL 4.5+ / OpenGL ES 3.1+ Compatibility Backend & GLSL/ESSL Codegen, `SPEC-138`)** in **`P22-gpu-heterogeneous-computing`** using free numeric IDs **`T985`–`T988`**, wired into `T322`.

---

## Critical Traps Caught & Guardrails Enforced

1. **`0846 §216` Explicit Architecture Boundary (Zero Global GL State Leakage)**:
   - `0846 §216` mandates: *"OpenGL may be supported as an optional compatibility backend. It MUST NOT define the architecture. The core design remains modern explicit graphics."*
   - `std/sys/gpu/opengl` implements the internal backend driver trait underneath `std.gpu` / `std.gfx` (`CommandEncoder`, `ComputePipeline`, `GraphicsPipeline`, `DeviceBuffer`). Global mutable OpenGL state (`glBind*`) NEVER leaks into public Axiom APIs.

2. **OpenGL Thread-Affinity Crash Trap (`MakeCurrent` Race Prevention)**:
   - Unlike Vulkan/D3D12/Metal, an `HGLRC`/`EGLContext` can only be current on **one OS thread at a time**; calling GL functions from multi-threaded Axiom worker tasks causes immediate UB/driver crashes in C++.
   - Remedy: `CommandEncoder` records pure Axiom command buffers on any thread (`Send`), and `Queue.submit` replays them deterministically on the context-owning submission thread using Direct State Access (`GL_ARB_direct_state_access` on GL 4.5+) or a shadow state-diff tracker on GL 4.3 / GLES 3.1+.

3. **Coordinate-System & Depth-Range Mismatch Trap (`[-1, 1]` vs `[0, 1]` NDC)**:
   - Vulkan, D3D12, Metal, WebGPU, and Axiom's Software Rasterizer all use **`[0, 1]` clip-space Z depth**. OpenGL defaults to **`[-1, 1]`** and bottom-left framebuffer origin — causing clipped geometry and upside-down render-to-texture if unhandled!
   - Remedy: Use `glClipControl(GL_LOWER_LEFT, GL_ZERO_TO_ONE)` when `GL 4.5` / `GL_EXT_clip_control` is present, AND emit an automatic vertex epilogue `gl_Position.z = gl_Position.z * 2.0 - gl_Position.w` + Y-inversion uniform/epilogue in `compiler/target/glsl` when targeting GLES 3.1/3.2 without `GL_EXT_clip_control`!

4. **Apple macOS/iOS Deprecation Reality**:
   - Apple froze OpenGL at 4.1 (no compute shaders!) and deprecated it in favor of Metal (`E22.5`).
   - Remedy: Scope `std/sys/gpu/opengl` cleanly to **OpenGL 4.3–4.6 Core via WGL (Windows) & EGL/GLX (Linux)** + **OpenGL ES 3.1–3.2 via EGL 1.5 (Android & Embedded Linux ARM/RISC-V SBCs)**, plus capability-queried raster-only fallback when compute shaders are unavailable (`DeviceCapabilities.supports_compute == false`), while Apple targets always prefer Metal (`E22.5`).

5. **Deterministic Headless Testing on Windows Host**:
   - Test `compiler/target/glsl` output deterministically on all hosts via an internal GLSL 450 / ESSL 310 structural & binding validator, plus dynamic `opengl32.dll` + `WGL` offscreen pixelbuffer / FBO execution on Windows (gracefully falling back to `E22.6` Software Rasterizer when running on a GPU-less VM/CI runner where only `GDI Generic` OpenGL 1.1 is present!).
