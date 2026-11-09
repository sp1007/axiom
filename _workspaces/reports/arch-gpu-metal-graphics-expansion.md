# Architecture Report — GPU Graphics, Metal, WebGPU, Tensor MMA & Hot-Reload Expansion

## Tóm tắt
- Thực hiện chỉ thị của chủ sở hữu dự án ("tiến hành đi"), kiến trúc sư đã hoàn thành việc mở rộng kiến trúc Phase P16 và Phase P22 để giải quyết triệt để 6 khoảng trống kiến trúc đối chiếu với các tài liệu chuẩn (normative sources: `docs/base/tasks/0846 - BOOTSTRAP-615.md`, `docs/base/tasks/0626 - BOOTSTRAP-367.md`, `docs/base/specs/0096`, `docs/base/specs/0139`).
- Đã ban hành quyết định kiến trúc chuẩn `spec/decisions/ADR-0038-gpu-graphics-metal-webgpu-tensor-expansion.md`.
- Mở rộng Phase P16: bổ sung Epic `E16.13 iOS AArch64 & iOS Simulator Mach-O target` với 3 task (`T697–T699`) lấp đầy toàn bộ slot còn lại của P16, cập nhật ma trận artifact và nối vào cổng `T316`.
- Mở rộng Phase P22: bổ sung task sinh mã D3D12 HLSL/DXIL `T966` trong `E22.3`, thêm 4 epic mới gồm `E22.5 Apple Metal backend & MSL codegen` (`T967–T970`), `E22.6 Native raster graphics pipeline, surface/swapchain & software rasterizer fallback` (`T971–T975`), `E22.7 WebGPU backend & WGSL codegen` (`T976–T979`), và `E22.8 GPU AI acceleration & runtime shader hot-reload` (`T980–T984`), nối toàn bộ vào cổng `T322`.
- Cập nhật đồng bộ các task hiện có (`T316`, `T322`, `T962`, `T963`, `T965`), cập nhật `spec/ROADMAP.md`, `spec/INDEX.md`, và ánh xạ 25 yêu cầu trong `spec/requirements/CATALOG.md` (toàn bộ `REQ-GPU-*`, `REQ-ECO-5958`, và các yêu cầu iOS).
- Toàn bộ 4 công cụ kiểm định nghiêm ngặt (`lint`, `validate`, `reqcov --strict`, `harness_check`) đều đạt 100% PASS (0 gaps, 0 problems).

---

## Architectural Summary

### 1. D3D12 Shader Codegen Bridge (`AGIR -> HLSL / DXIL`)
- **Gap**: `T960` produced SPIR-V 1.6 (`.spv`), but Windows D3D12 (`ID3D12Device` in `T963`) cannot natively ingest raw SPIR-V.
- **Resolution**: Added `T966` in `E22.3` (`compiler/target/hlsl_dxil` and `compiler/obj/dxil`), lowering AGIR kernels to clean HLSL 6.x compute source, compiling via `dxcompiler.dll` or native DXIL container packaging, and generating root-signature reflection metadata. `T963` now depends on `T966`, enabling native shader execution on Windows D3D12.

### 2. Apple iOS Target (`P16` `E16.13`) + Apple Metal Backend & `AGIR -> MSL` Codegen (`P22` `E22.5`)
- **Gap**: Apple iOS target was missing from P16; no Metal Shading Language (`.metal`) or `Metal.framework` host runtime was planned.
- **Resolution**:
  - In P16: Added Epic `E16.13` (`T697–T699`) specifying `SPEC-150` for `aarch64-apple-ios` and `aarch64-apple-ios-sim`, Mach-O `LC_BUILD_VERSION` platform load commands (platform 2 and 7), Xcode SDK sysroot discovery, ad-hoc code signing, and `UIApplication`/`CAMetalLayer` windowing bootstrap.
  - In P22: Added Epic `E22.5` (`T967–T970`) specifying `SPEC-134` for MSL 3.x source generation (`compiler/target/msl`), argument buffer binding reflection, `std/sys/gpu/metal` host driver via Objective-C runtime (`MTLDevice`, `MTLCommandQueue`, `MTLComputePipelineState`, `MTLRenderPipelineState`, `MTLSharedEvent`), and zero-copy `UnifiedBuffer` fast-path for Apple Silicon.

### 3. Full Raster Graphics Pipeline, Textures/Samplers, Window Surface & Swapchain + Software Rasterizer Fallback (`P22` `E22.6`)
- **Gap**: P22 was compute-only; BOOTSTRAP-615 (`0846 §10–56, §78–90`, `REQ-GPU-065`) mandates full raster graphics, cross-platform surfaces, swapchains, and a deterministic CPU software rasterizer fallback for headless CI.
- **Resolution**: Added Epic `E22.6` (`T971–T975`) specifying `SPEC-135`:
  - AGIR graphics stages (`@vertex`, `@fragment`) with compile-time inter-stage interface type checking.
  - Textures (`Texture1D/2D/3D/Cube`, `StorageTexture`) and samplers.
  - Multi-backend native `Surface` & `Swapchain` lifecycle (Win32 `HWND`, `CAMetalLayer`, Wayland/X11, Android `ANativeWindow`, `HTMLCanvas`).
  - Deterministic CPU Software Rasterizer (`std/sys/gpu/software_raster`) providing subpixel triangle rasterization, depth testing, blending, and headless image capture (SHA-256 verified) without physical GPU hardware.
  - High-level `GraphicsPipeline` and `RenderPass` command recording with MRT support.

### 4. WebGPU Backend & `AGIR -> WGSL` Codegen for `wasm32` (`P22` `E22.7`)
- **Gap**: WebAssembly cannot run desktop Vulkan/D3D12/Metal APIs; running Axiom GPU code on the web requires WebGPU and WGSL.
- **Resolution**: Added Epic `E22.7` (`T976–T979`) specifying `SPEC-136`:
  - `compiler/target/wgsl` translating AGIR to clean WGSL with internal syntax/semantic validation.
  - `std/sys/gpu/webgpu` bridging to browser `navigator.gpu` via WASM imports, with a native WebGPU C ABI fallback for portable execution.
  - Conformance suite for WebAssembly WebGPU execution.

### 5. Subgroup / Warp Collectives, `f16`/`bf16` & Cooperative Matrix / Tensor Core MMA (`P22` `E22.8`)
- **Gap**: AI inference and training workloads require low-level SIMT collectives, half-precision arithmetic, and hardware tensor core acceleration.
- **Resolution**: In Epic `E22.8` (`T980–T982`, `T984`), specified `SPEC-137`:
  - Capability-gated Subgroup collectives (`subgroup.size`, `subgroup.shuffle`, `subgroup.broadcast`, `subgroup.ballot`, `subgroup.reduce_add/min/max`, respecting `REQ-GPU-062`).
  - Half-precision floating-point types `f16` and `bf16` in AGIR.
  - Cooperative Matrix / Tensor MMA (`TileMatrix<T, M, N, K>`, `mma_sync`) lowering across SPIR-V (`OpTypeCooperativeMatrixKHR`), HLSL/DXIL WaveMMA, and Apple MSL (`simdgroup_matrix`).

### 6. Live Shader & Pipeline Hot-Reload (`P22` `E22.8`)
- **Gap**: Game engines and creative tools require instant shader reloading without application restart or frame drops (`0846 §252–254`).
- **Resolution**: In Epic `E22.8`, added task `T983`: `std/gpu/hot_reload` watching shader sources, compiling dynamically, verifying ABI compatibility (descriptor layouts, push constants, render targets), and atomically swapping pipeline state pointers at frame boundaries with safe rollback on error.

---

## Inventory of New Epics and Tasks

| Epic | Task ID | Phase | Title | Owner | Model | Priority |
|---|---|---|---|---|---|---|
| **E16.13** | `T697` | P16 | E16.13 Canonical iOS AArch64 & iOS Simulator Mach-O target specification (SPEC-150) | axiom-architect | opus | 140 |
| **E16.13** | `T698` | P16 | E16.13 aarch64-apple-ios & aarch64-apple-ios-sim TargetDesc, Mach-O LC_BUILD_VERSION & iOS SDK sysroot linker | axiom-backend | sonnet | 141 |
| **E16.13** | `T699` | P16 | E16.13 iOS UIApplication / CAMetalLayer host bootstrap shim, simulator test harness & target conformance suite | axiom-backend | sonnet | 142 |
| **E22.3** | `T966` | P22 | E22.3 AGIR -> HLSL emitter, dxcompiler DXIL bytecode container & root-signature reflection | axiom-backend | sonnet | 236 |
| **E22.5** | `T967` | P22 | E22.5 Canonical Apple Metal backend & MSL codegen specification (SPEC-134) | axiom-architect | opus | 237 |
| **E22.5** | `T968` | P22 | E22.5 AGIR -> MSL (.metal) source emitter, argument buffer reflection & metallib pipeline | axiom-backend | sonnet | 238 |
| **E22.5** | `T969` | P22 | E22.5 Apple Metal host driver (std.sys.gpu.metal), Objective-C bridge & UnifiedBuffer zero-copy path | axiom-backend | sonnet | 239 |
| **E22.5** | `T970` | P22 | E22.5 Metal compute & render pipeline cross-platform (macOS & iOS) conformance suite | axiom-backend | sonnet | 240 |
| **E22.6** | `T971` | P22 | E22.6 Canonical raster graphics pipeline, surface/swapchain & software rasterizer specification (SPEC-135) | axiom-architect | opus | 241 |
| **E22.6** | `T972` | P22 | E22.6 AGIR raster stages (@vertex, @fragment), stage interface verification, textures & samplers | axiom-backend | sonnet | 242 |
| **E22.6** | `T973` | P22 | E22.6 Multi-backend Surface & Swapchain lifecycle (Win32, Wayland, X11, CAMetalLayer, ANativeWindow, HTMLCanvas) | axiom-backend | sonnet | 243 |
| **E22.6** | `T974` | P22 | E22.6 Deterministic CPU software rasterizer fallback (std.sys.gpu.software) & headless frame capture | axiom-backend | sonnet | 244 |
| **E22.6** | `T975` | P22 | E22.6 High-level GraphicsPipeline, RenderPass, MRT, blend/depth-stencil & graphics conformance suite | axiom-backend | sonnet | 245 |
| **E22.7** | `T976` | P22 | E22.7 Canonical WebGPU runtime & WGSL codegen specification (SPEC-136) | axiom-architect | opus | 246 |
| **E22.7** | `T977` | P22 | E22.7 AGIR -> WGSL source emitter, address space mapping & WGSL syntax validator | axiom-backend | sonnet | 247 |
| **E22.7** | `T978` | P22 | E22.7 WebGPU host & wasm32 browser bridge (std.sys.gpu.webgpu, navigator.gpu / WebGPU C ABI) | axiom-backend | sonnet | 248 |
| **E22.7** | `T979` | P22 | E22.7 WebGPU compute & graphics on wasm32 / headless conformance suite | axiom-backend | sonnet | 249 |
| **E22.8** | `T980` | P22 | E22.8 Canonical GPU AI acceleration, tensor matrix-multiplication-accumulate & hot-reload specification (SPEC-137) | axiom-architect | opus | 250 |
| **E22.8** | `T981` | P22 | E22.8 Capability-gated SIMT Subgroup collectives & f16/bf16 device arithmetic in AGIR | axiom-backend | sonnet | 251 |
| **E22.8** | `T982` | P22 | E22.8 Cooperative Matrix / Tensor MMA (TileMatrix, mma_sync) lowering to SPIR-V, DXIL & MSL | axiom-backend | sonnet | 252 |
| **E22.8** | `T983` | P22 | E22.8 Live shader & pipeline hot-reload (std.gpu.hot_reload) with ABI validation & atomic swap | axiom-backend | sonnet | 253 |
| **E22.8** | `T984` | P22 | E22.8 Subgroup collectives, Tensor MMA & hot-reload differential verification suite | axiom-backend | sonnet | 254 |

---

## Verification Results

1. **`taskctl.py lint` (27 files checked)**:
   - All 22 new task files and 5 modified existing task files passed with exit code 0 (`OK`).
2. **`taskctl.py validate`**:
   - Exit code 0: `OK (621 tasks)`.
3. **`reqcov.py --strict`**:
   - Exit code 0: `COVERAGE OK` (32,308 requirements, 0 gaps, 0 problems).
4. **`harness_check.py`**:
   - Exit code 0: `HARNESS OK`.

---

## Files changed
- spec/decisions/ADR-0038-gpu-graphics-metal-webgpu-tensor-expansion.md
- spec/INDEX.md
- spec/ROADMAP.md
- spec/requirements/CATALOG.md
- _workspaces/tasks/todo/T316-phase-p16-gate-targets-platforms.md
- _workspaces/tasks/todo/T322-phase-p22-gate-gpu-heterogeneous-computing.md
- _workspaces/tasks/todo/T697-e16-13-canonical-ios-aarch64-macho-target-spec.md
- _workspaces/tasks/todo/T698-e16-13-aarch64-ios-targetdesc-macho-sysroot-linker.md
- _workspaces/tasks/todo/T699-e16-13-ios-uiapplication-cametallayer-shim-conformance.md
- _workspaces/tasks/todo/T962-e22-4-host-runtime-vulkan-d3d12-compute-device-spec.md
- _workspaces/tasks/todo/T963-e22-4-host-gpu-intrinsics-devicemanager-vulkan-d3d12-drivers.md
- _workspaces/tasks/todo/T965-e22-4-gpu-kernel-execution-vulkan-d3d12-oracle-conformance.md
- _workspaces/tasks/todo/T966-e22-3-agir-hlsl-emitter-dxil-container-root-signature.md
- _workspaces/tasks/todo/T967-e22-5-canonical-apple-metal-msl-backend-spec.md
- _workspaces/tasks/todo/T968-e22-5-agir-msl-emitter-argument-buffer-metallib.md
- _workspaces/tasks/todo/T969-e22-5-apple-metal-host-driver-objc-unifiedbuffer.md
- _workspaces/tasks/todo/T970-e22-5-metal-compute-render-macos-ios-conformance.md
- _workspaces/tasks/todo/T971-e22-6-canonical-raster-graphics-swapchain-software-rasterizer-spec.md
- _workspaces/tasks/todo/T972-e22-6-agir-raster-stages-interface-textures-samplers.md
- _workspaces/tasks/todo/T973-e22-6-multi-backend-surface-swapchain-lifecycle.md
- _workspaces/tasks/todo/T974-e22-6-cpu-software-rasterizer-fallback-headless-capture.md
- _workspaces/tasks/todo/T975-e22-6-graphicspipeline-renderpass-mrt-conformance.md
- _workspaces/tasks/todo/T976-e22-7-canonical-webgpu-wgsl-backend-spec.md
- _workspaces/tasks/todo/T977-e22-7-agir-wgsl-emitter-address-spaces-validator.md
- _workspaces/tasks/todo/T978-e22-7-webgpu-host-wasm32-bridge-navigator-gpu.md
- _workspaces/tasks/todo/T979-e22-7-webgpu-compute-graphics-wasm32-conformance.md
- _workspaces/tasks/todo/T980-e22-8-canonical-gpu-ai-tensor-mma-hot-reload-spec.md
- _workspaces/tasks/todo/T981-e22-8-subgroup-collectives-f16-bf16-agir-arithmetic.md
- _workspaces/tasks/todo/T982-e22-8-cooperative-matrix-tensor-mma-spirv-dxil-msl.md
- _workspaces/tasks/todo/T983-e22-8-live-shader-pipeline-hot-reload-abi-swap.md
- _workspaces/tasks/todo/T984-e22-8-subgroups-tensor-mma-hot-reload-conformance.md
