# ADR-0038 — GPU Graphics, Metal, WebGPU, Tensor MMA & Hot-Reload Expansion

Status: accepted (2026-11-09, architect; owner-delegated decision)

## Tóm tắt
- Khảo sát các tài liệu chuẩn (normative) gồm BOOTSTRAP-615 (`docs/base/tasks/0846`), BOOTSTRAP-367 (`docs/base/tasks/0626`), `docs/base/specs/0096`, và Part XX (`docs/base/specs/0139`) cho thấy 6 khoảng trống kiến trúc lớn trong kế hoạch GPU hiện tại: (1) thiếu cầu nối sinh mã D3D12 (HLSL/DXIL) khiến Windows D3D12 không chạy được bytecode SPIR-V trực tiếp; (2) thiếu target Apple iOS và backend Apple Metal (`AGIR -> MSL`); (3) thiếu pipeline đồ họa raster đầy đủ (`@vertex`, `@fragment`, textures/samplers, surface/swapchain đa nền tảng) và bộ rasterizer CPU tất định để chạy CI headless; (4) thiếu backend WebGPU (`AGIR -> WGSL`) cho `wasm32`; (5) thiếu subgroup collectives, kiểu `f16`/`bf16`, và Tensor Core MMA (`TileMatrix`, `mma_sync`) phục vụ AI; (6) thiếu cơ chế nạp nóng shader và pipeline (`std/gpu/hot_reload`) an toàn tại biên khung hình.
- Theo chỉ thị của chủ sở hữu dự án ("tiến hành đi"), kiến trúc sư quyết định mở rộng toàn diện Phase P16 và Phase P22:
  1. Thêm Epic E16.13 trong P16 với 3 task (`T697–T699`) cho target Apple iOS AArch64 và iOS Simulator Mach-O (`SPEC-150`).
  2. Bổ sung task `T966` trong E22.3 thực hiện hạ cấp `AGIR -> HLSL` và đóng gói DXIL (`dxcompiler.dll`) với root-signature reflection, đồng thời cập nhật `T963` phụ thuộc `T966`.
  3. Thêm Epic E22.5 trong P22 với 4 task (`T967–T970`) cho backend Apple Metal (`AGIR -> MSL`, `SPEC-134`) và driver host `std/sys/gpu/metal` (macOS/iOS, unified memory zero-copy).
  4. Thêm Epic E22.6 trong P22 với 5 task (`T971–T975`) cho pipeline đồ họa raster, surface/swapchain đa nền tảng và bộ rasterizer CPU phần mềm tất định (`SPEC-135`).
  5. Thêm Epic E22.7 trong P22 với 4 task (`T976–T979`) cho backend WebGPU (`AGIR -> WGSL`, `SPEC-136`) và cầu nối host/WASM (`std/sys/gpu/webgpu`).
  6. Thêm Epic E22.8 trong P22 với 5 task (`T980–T984`) cho tăng tốc AI (subgroup collectives, `f16`/`bf16`, Tensor Core MMA `TileMatrix`) và live shader/pipeline hot-reload an toàn (`SPEC-137`).
- Tổng cộng: 3 task mới trong P16 (`T697–T699`), 19 task mới trong P22 (`T966–T984`), cập nhật 7 task hiện có (`T958`, `T962`, `T963`, `T964`, `T965`, `T316`, `T322`), ánh xạ toàn bộ `REQ-GPU-*` và `REQ-ECO-5958`, bảo đảm 0 lỗ hổng (0 gaps).

## Context
Axiom aims to deliver a modern systems programming language with first-class heterogeneous computing and zero hidden runtime overhead. The existing P22 roadmap (expanded by T222) established foundational concepts: execution domains (E22.1), device memory capabilities (E22.2), SPIR-V compute emission (E22.3), and Vulkan/D3D12 compute dispatch (E22.4).

However, an exhaustive audit against the normative documents `docs/base/tasks/0846 - BOOTSTRAP-615.md` (Native Graphics, Windowing, Display Composition, Rendering Pipeline & GPU Command Runtime 5.0, `REQ-GPU-065`), `docs/base/tasks/0626 - BOOTSTRAP-367.md`, `docs/base/specs/0096`, and `docs/base/specs/0139` revealed six critical architectural gaps:
1. **D3D12 Shader Codegen Gap**: `T960` produces SPIR-V 1.6 (`.spv`), but Windows Direct3D 12 (`ID3D12Device` in `T963`) cannot natively ingest raw SPIR-V. Without a native HLSL/DXIL emission bridge (`dxcompiler.dll` or direct DXIL container generation), D3D12 compute on Windows is stalled or reliant on runtime translation.
2. **Apple Ecosystem & Metal Gap**: While macOS AArch64 Mach-O exists in P16 (E16.4), Apple iOS (`aarch64-apple-ios` and `aarch64-apple-ios-sim`) was missing from P16. Furthermore, modern macOS and iOS devices use Apple Metal exclusively. No MSL (`.metal`) codegen or native `Metal.framework` host driver (`MTLDevice`, `CAMetalLayer`, unified memory zero-copy) was planned in P22.
3. **Graphics Pipeline & Deterministic Software Fallback Gap**: BOOTSTRAP-615 (§10–56, §78–90, `REQ-GPU-065`) mandates a full raster graphics runtime beyond compute kernels: `@vertex` and `@fragment` stages in AGIR, type-checked stage interfaces, textures (`Texture1D/2D/3D/Cube`, `StorageTexture`), samplers, `GraphicsPipeline`, `RenderPass`, multi-backend native `Surface` and `Swapchain` lifecycle (Win32 `HWND`, macOS/iOS `CAMetalLayer`, Linux Wayland/X11, Android `ANativeWindow`, HTMLCanvas). Crucially, 0846 §78–79 mandates a deterministic CPU Software Rasterizer so headless CI environments can verify rendered framebuffers pixel-for-pixel without requiring a physical GPU.
4. **WebGPU & WGSL Gap for WebAssembly**: `wasm32` is a Tier-2 target in P16 (E16.6). However, browser WebAssembly cannot run Vulkan, D3D12, or Metal directly. Running Axiom GPU compute and graphics on the web requires an `AGIR -> WGSL` source emitter, WGSL validator, and a `std/sys/gpu/webgpu` host/WASM bridge (`navigator.gpu` / WebGPU C ABI).
5. **GPU AI Acceleration Gap (Subgroups, Half-Precision & Tensor Core MMA)**: Modern AI inference and training workloads depend on low-level SIMT collectives and matrix hardware: subgroup/warp shuffles/ballots/reductions (`REQ-GPU-062`), half-precision `f16` and `bf16` data storage and arithmetic, and Cooperative Matrix / Tensor Core MMA (`TileMatrix<T, M, N, K>`, `mma_sync`) lowering to SPIR-V `OpTypeCooperativeMatrixKHR`, HLSL/DXIL WaveMMA, and Apple MSL `simdgroup_matrix`.
6. **Live Shader & Pipeline Hot-Reload Gap**: BOOTSTRAP-615 §252–254 and E20.7 specify live runtime shader and pipeline replacement for high-productivity game engines and interactive visual tools. Axiom requires a safe `std/gpu/hot_reload` subsystem that compiles replacement shaders, verifies descriptor/push-constant/render-target ABI compatibility against the active pipeline, swaps `GraphicsPipeline` / `ComputePipeline` objects atomically at frame boundaries, and rolls back cleanly without crashing on compilation or validation errors.

The project owner explicitly instructed: `"tiến hành đi"` to address all 6 gaps in Axiom v1.

## Options
1. **Option 1: Minimal compute-only SPIR-V backend (Status Quo)**.
   - Restrict P22 to SPIR-V compute kernels and defer all graphics, Metal, WebGPU, AI tensors, and hot-reload to post-v1 (P24).
   - *Rejected*: Violates normative source BOOTSTRAP-615 (`REQ-GPU-065`), leaves Windows D3D12 incapable of running shaders natively, ignores the Apple iOS/macOS ecosystem, and forces AI workloads onto slower scalar/emulated paths.

2. **Option 2: Rely on external third-party translation libraries (e.g., SPIRV-Cross, wgpu-native at C ABI level)**.
   - Emit only SPIR-V and bundle C libraries at runtime to transpile SPIR-V into HLSL, MSL, and WGSL.
   - *Rejected*: Violates core Axiom invariants `INV-BOOT-001` (zero third-party compiler dependencies, standalone compiler) and `INV-ARCH-002` (deterministic compilation). External transpilers introduce unstable intermediate dialects, obscure diagnostic source locations, and impede proof-preserving optimizations.

3. **Option 3: First-class multi-backend AGIR codegen (SPIR-V, HLSL/DXIL, MSL, WGSL) + unified std.gpu / std.gfx runtime with deterministic CPU fallback (Chosen)**.
   - Implement native backend emitters directly in the self-hosted Axiom compiler pipeline from `AGIR`:
     - `AGIR -> SPIR-V` (Vulkan)
     - `AGIR -> HLSL` + DXIL container (`dxcompiler.dll` or direct DXIL container) (Windows D3D12)
     - `AGIR -> MSL` (Apple Metal macOS/iOS)
     - `AGIR -> WGSL` (WebGPU wasm32)
   - Expand `std.gpu` and `std.gfx` to support both compute and graphics pipelines, window surfaces, swapchains, unified memory on Apple Silicon, subgroup collectives, half-precision floats, Cooperative Matrix MMA, live hot-reload, and a deterministic CPU software rasterizer fallback for headless testing.

## Decision
1. **D3D12 Shader Codegen Bridge (`AGIR -> HLSL / DXIL`)**:
   - In `E22.3`, create task `T966`: `compiler/target/hlsl_dxil` lowers AGIR kernels to clean HLSL 6.x source, compiles via `dxcompiler.dll` (or native DXIL container emitter), and generates root-signature reflection metadata.
   - `T963` (`std/sys/gpu/d3d12`) is updated to depend on `T966`, loading native DXIL bytecodes into `ID3D12Device.CreateComputePipelineState`.

2. **Apple iOS Target (`P16` `E16.13`) and Apple Metal Backend (`P22` `E22.5`)**:
   - In Phase P16, add Epic **`E16.13 iOS AArch64 & iOS Simulator Mach-O target`** spanning tasks `T697–T699`:
     - `T697`: Canonical specification `spec/SPEC-150-ios-aarch64-macho.md` (`AXS-IOS-*` rules).
     - `T698`: `aarch64-apple-ios` and `aarch64-apple-ios-sim` `TargetDesc`, Mach-O `LC_BUILD_VERSION` load commands, iOS SDK sysroot resolution, and linker integration.
     - `T699`: iOS `UIApplication` and `CAMetalLayer` host shim, simulator test harness, and target conformance suite. Wire `T697–T699` into P16 gate `T316`.
   - In Phase P22, add Epic **`E22.5 Apple Metal backend & MSL codegen`** spanning tasks `T967–T970`:
     - `T967`: Canonical specification `spec/SPEC-134-apple-metal-msl-backend.md` (`AXS-MTL-*` rules).
     - `T968`: `compiler/target/msl` emitting MSL 3.x source, argument buffer reflection metadata, and `metallib` compilation.
     - `T969`: `std/sys/gpu/metal` host driver for macOS (`NSWindow`/`CAMetalLayer`) and iOS (`UIView`/`CAMetalLayer`) via Objective-C runtime, supporting `MTLDevice`, `MTLCommandQueue`, `MTLComputePipelineState`, `MTLRenderPipelineState`, and zero-copy `UnifiedBuffer` on Apple Silicon.
     - `T970`: Metal compute and render cross-platform conformance suite.

3. **Raster Graphics Pipeline, Surface & Swapchain, Deterministic Software Rasterizer (`P22` `E22.6`)**:
   - Add Epic **`E22.6 Native raster graphics pipeline, surface/swapchain & software rasterizer fallback`** spanning tasks `T971–T975`:
     - `T971`: Canonical specification `spec/SPEC-135-raster-graphics-swapchain-software-rasterizer.md` (`AXS-GFX-*` rules).
     - `T972`: AGIR graphics stages (`@vertex`, `@fragment`), stage interface verification (matching locations, types, interpolation qualifiers), `Texture1D/2D/3D/Cube`, `StorageTexture`, and `Sampler`.
     - `T973`: Multi-backend native `Surface` and `Swapchain` lifecycle (`Win32` `HWND`, `CAMetalLayer`, Wayland/X11, Android `ANativeWindow`, `HTMLCanvas`), present modes (FIFO, Mailbox, Immediate), resize recreation, and HDR/sRGB color spaces.
     - `T974`: Deterministic CPU software rasterizer fallback (`std/sys/gpu/software_raster`, 0846 §78–79) providing exact subpixel rasterization, barycentric interpolation, depth testing, and headless framebuffer capture for bit-exact CI testing.
     - `T975`: High-level `GraphicsPipeline`, `RenderPass`, MRT, blend/depth-stencil states, and graphics conformance test suite.

4. **WebGPU Backend & WGSL Codegen for wasm32 (`P22` `E22.7`)**:
   - Add Epic **`E22.7 WebGPU backend & WGSL codegen`** spanning tasks `T976–T979`:
     - `T976`: Canonical specification `spec/SPEC-136-webgpu-wgsl-backend.md` (`AXS-WGPU-*` rules).
     - `T977`: `compiler/target/wgsl` source emitter, address space mapping (`storage`, `uniform`, `workgroup`, `private`), and WGSL syntax validator.
     - `T978`: `std/sys/gpu/webgpu` host and `wasm32` browser bridge (`navigator.gpu` via JS runtime bridge / native WebGPU C ABI).
     - `T979`: WebGPU compute and graphics on `wasm32` / headless conformance suite.

5. **GPU AI Acceleration: Subgroup Collectives, Half-Precision & Tensor MMA (`P22` `E22.8`)**:
   - In Epic **`E22.8 GPU AI acceleration & runtime shader hot-reload`**, assign tasks `T980–T982`, `T984`:
     - `T980`: Canonical specification `spec/SPEC-137-gpu-ai-tensor-mma-hot-reload.md` (`AXS-MMA-*` and `AXS-HOT-*` rules).
     - `T981`: Capability-gated SIMT Subgroup collectives (`subgroup_size`, `subgroup_shuffle`, `subgroup_broadcast`, `subgroup_ballot`, `subgroup_reduce_add/min/max`, respecting `REQ-GPU-062`), and half-precision `f16` / `bf16` storage and compute in AGIR.
     - `T982`: Cooperative Matrix / Tensor Core MMA (`TileMatrix<T, M, N, K>`, `mma_sync`) lowering to SPIR-V `OpTypeCooperativeMatrixKHR`, HLSL/DXIL WaveMMA, and Apple MSL `simdgroup_matrix`.
     - `T984`: Differential verification suite testing Subgroup collectives and Tensor MMA against reference CPU implementations.

6. **Live Shader & Pipeline Hot-Reload (`P22` `E22.8`)**:
   - In Epic `E22.8`, assign task `T983`: `std/gpu/hot_reload` implementing live shader re-compilation, interface reflection validation (verifying bindings, push constants, and render targets match the existing pipeline layout), and atomic pipeline pointer swapping at frame boundaries, with graceful rollback on error.

7. **Roadmap & Gate Alignment**:
   - Wire `T697–T699` into `T316` `depends:`.
   - Wire `T966–T984` into `T322` `depends:`.
   - Update `T963` to depend on `T966`.
   - Update `T965` to depend on `T966`.
   - Update `ROADMAP.md` §2 (P16 and P22 epics and artifact matrix) and §4 (P16 and P22 task ranges).
   - Update `spec/INDEX.md` and `spec/requirements/CATALOG.md`, resolving all gaps.

## Consequences
- **Positive**:
  - Axiom achieves a world-class, fully native cross-platform GPU stack covering Graphics, Compute, and AI acceleration across Windows (Direct3D 12), Linux/Android (Vulkan), macOS/iOS (Apple Metal), and Web (WebGPU).
  - Headless CI pipelines can test 100% of GPU compute and raster graphics features without GPU hardware via the deterministic CPU software rasterizer.
  - Zero third-party runtime or compiler dependencies are added.
- **Spec & Task Management**:
  - Adds 22 well-scoped tasks across P16 (`T697–T699`) and P22 (`T966–T984`).
  - Strict requirement coverage maintained (`reqcov.py --strict` 0 gaps, 0 problems).

## Sources
- `docs/base/tasks/0846 - BOOTSTRAP-615.md` (Native Graphics, Windowing, Display Composition, Rendering Pipeline & GPU Command Runtime 5.0, `REQ-GPU-065`)
- `docs/base/tasks/0626 - BOOTSTRAP-367.md` (Axiom GPU Kernel, Device Memory & Heterogeneous Compilation Engine)
- `docs/base/specs/0096 - Axiom — Heterogeneous Computing, GPU & Accelerator v0.1.md`
- `docs/base/specs/0139 - Part XX — GPU · Accelerator · Device Memory · Kernel.md`
- `docs/base/specs/0120 - Memory, Ownership, Lifetime & Concurrency.md`
- `docs/base/specs/0162 - Low-Level IR & Target Generation.md`
- `tasks/0459`, `tasks/0468`, `tasks/0470`, `0826 §601.112`
