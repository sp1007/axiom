# Architecture Synthesis Report — ADR-0040 UMA & P22 Task Board Revision

- **Date**: 2026-11-10
- **Author**: `axiom-architect`
- **Scope**: Comprehensive revision of `ADR-0040`, `spec/ROADMAP.md`, `spec/INDEX.md`, `spec/diagnostics.md`, `spec/requirements/OWNER.md`, `spec/requirements/CATALOG.md`, Phase P22 tasks (`T954`–`T957`, `T962`–`T965`, `T969`–`T970`, `T974`, `T976`, `T978`, `T980`, `T985`, `T987`, `T322`), and establishment of Epic `E22.10` (`T989`–`T992`).
- **Goal**: Resolve 100% of the 39 Red-Team findings (22 Semantics findings in `redteam-uma-semantics.md` + 17 Hardware findings in `redteam-uma-hardware.md`), strictly preserve the Axiom single ownership and capability model, ensure hardware-independent program legality, achieve hardware API precision, and restore board hygiene with 0 gaps in `reqcov.py --strict`.

---

## 1. Executive Summary

Commit `57b7c8e6` introduced an initial draft of `ADR-0040` responding to the project owner's instruction regarding unified memory across operating systems and machine architectures. While conceptually aligned with the owner's goal, the draft suffered from two independent sets of critical defects identified by parallel Red-Team audits:
1. **Language semantics & ownership model fit (`redteam-uma-semantics.md`)**: conflation of value semantics and zero-copy transfer elision, illegal machine-dependent compile-time typing, introduction of a redundant 3-state typestate machine violating `REQ-CONC-096`, async deadlock/leak risks in event-held borrows, cross-phase dependency gaps on P21 virtual memory primitives (`T921`/`T922`), dependency inversions between `T956`/`T957` and `T962`/`T963`, missing owner requirement registration in `OWNER.md`, and task oversizing.
2. **Hardware, OS, and driver API correctness (`redteam-uma-hardware.md`)**: D3D12 uninitialized `NodeIndex` returning `E_INVALIDARG`, conflation of D3D12 `MEMORY_POOL_L0` with discrete ReBAR (which requires `L1`), D3D12 host-import incompatibility with file mappings (`MapViewOfFile` vs `OpenExistingHeapFromFileMapping`), Vulkan per-memory-type cache coherence misclassified as adapter-level, Vulkan ReBAR detection conflating standard 256 MiB BAR apertures with full ReBAR, incorrect UMA classification of NVIDIA Grace Hopper NUMA architectures, rejection of 4 KiB host imports due to Vulkan 64 KiB alignment constraints and Metal 16 KiB page-multiple length constraints, iOS Jetsam process termination under advisory Metal working set queries, lack of Android `AHardwareBuffer` / Linux `dma-buf` paths, physical impossibility of 0-copy for tiled textures, and CPU read collapse (90–99% throughput drop) on Write-Combined memory.

This synthesis delivers a gold-standard architecture that resolves all 39 findings without compromise.

---

## 2. Complete Red-Team Findings Resolution Matrix

### Part A: Semantics, Ownership, Capability & Board Consistency (22 Findings)

| ID | Severity | Red-Team Finding | Architectural Resolution in ADR-0040 Revision & Tasks | Impacted Files & Tasks |
|---|---|---|---|---|
| **B1** | **BLOCKER** | Copy elision of `upload`/`download` contradicts value semantics; "identical observable results" is false as written | `upload`, `download`, and `device_copy` strictly preserve value copy semantics on every machine (RAM→RAM `memcpy` without staging on UMA). Copy elision applies strictly to domain transitions on the same object (`UnifiedBuffer<T>`), by-move `.into_device(self)`, by-value `.to(device)` (`REQ-OPT-347`), and `shared_read_views()`. `TransferStats.bytes_copied` reports `len * size_of::<T>()` for upload/download and `0` for by-move handoffs. | ADR-0040 §3; `T954`, `T956`, `T990`, `T992` |
| **B2** | **BLOCKER** | CPU↔GPU race rule framed as UMA-specific, but compile-time legality cannot depend on runtime adapter | Program legality is completely hardware-independent. The rule applies identically across all memory topologies (`DiscretePool`, `UnifiedSystemPool`, `CoherentMultiPoolNuma`, `ReBarHostVisible`) on all host-accessible memory. Topology affects performance, never legality. | ADR-0040 §5, §8; `T954`, `T955`, `T957`, `T989` |
| **B3** | **BLOCKER** | `HostExclusive ↔ DeviceExclusive ↔ SharedRead` is a second ownership/typestate model, violating REQ-CONC-096 | Abolished second domain typestate machine. Mapped domain states to Axiom's existing ownership model: `HostExclusive` = `OWNED` / `mut_view`; `DeviceExclusive` = ownership moved into `InFlight<B>`; `SharedRead` = concurrent host `view<T>` and `DeviceView<T>` under `AXS-CAP-003`. Violations report canonical `AX_CAP_*` / `AX_OWN_*` diagnostics. | ADR-0040 §2; `T954`, `T955`, `T989` |
| **M4** | **MAJOR** | Event-held capabilities collide with async rules, `Drop`, and failure path of `.wait()` | Replaced event-held views with by-value ownership transfer token `InFlight<B>`. `InFlight<B>.wait(self) -> (B, Result<Unit, GpuError>)` returns the buffer on both success and error (`DeviceLost`). `Drop` blocks deterministically. `InFlight<B>` contains no views and is legal across `.await` (`AXS-ASY-034`). | ADR-0040 §2; `T954`, `T955`, `T956`, `T989` |
| **B5** | **BLOCKER** | Hidden cross-phase dependency: `T956`/`T955`/`T969` need P21 `T921`/`T922` but had no dependency edge | Established explicit dependency edges to `T921` (`VirtualRegion`) and `T922` (`Mmap`). Updated `ROADMAP.md` P22 row to `needs P11, P12, P16, E21.6`. Wire `T921`/`T922` into `T955`, `T969`, `T990`. | `spec/ROADMAP.md`; `T955`, `T969`, `T990`, `T322` |
| **B6** | **BLOCKER** | Dependency inversion: `T956`/`T957` consumed `GpuMemoryArchitecture`, mocks and budgets specified in `T962`/`T963` | `SPEC-131` (`T954`) defines core semantic types (`GpuMemoryTopology`, `InFlight<B>`, `TransferStats`). `T956` uses `MemoryTopologyProvider` abstraction trait and in-library mocks. Driver implementations and OS integration live in `T963`, `T969`, and Epic `E22.10` (`T989`–`T992`). | `T954`, `T956`, `T962`, `T963`, `T989` |
| **M7** | **MAJOR** | `UnifiedBuffer.from_mmap` under-typed: read-only capability vs GPU writes, owning vs borrowing type | Replaced with type-safe `HostImport` API: `HostImport.read<T: PlainData>` (`view<Mmap>`), `HostImport.write<T: PlainData>` (`mut_view<MmapMut>`), `HostImport.region<T: PlainData>` (`mut_view<VirtualRegion>`). Returns non-owning stored views `ImportedDeviceView<T>` / `MutView<T>` borrowing mapping. Enforces alignment and `PlainData` marker. | ADR-0040 §4; `T954`, `T989`, `T990` |
| **M8** | **MAJOR** | Host-import hazards not specified: truncation, `MmapCow`, `protect`/`decommit`, alignment, D3D12 file mappings | Forbid `MmapCow` mutable GPU imports. `protect`/`decommit`/`munmap` on `VirtualRegion` statically rejected while import view lives (`AX_CAP_OUTLIVES_OWNER`). Alignment set to `max(page_size(), minImportedHostPointerAlignment)`. D3D12 uses `OpenExistingHeapFromFileMapping` for Win32 file mappings vs `OpenExistingHeapFromAddress` for `VirtualAlloc`. | ADR-0040 §4; `T954`, `T955`, `T989`, `T991` |
| **M9** | **MAJOR** | Hardware-dependent API outcomes need explicit portability contract | Added §8 "Portability Contract": program legality is universal; `shared_read_views()` exists everywhere (using pinned host memory on discrete); `TransferStats` is profiling metadata, not semantic output; oracle `--interp` and CPU fallback use fixed default `UnifiedSystemPool`. | ADR-0040 §8; `T954`, `T989`, `T992` |
| **M10** | **MAJOR** | `OutOfUnifiedMemoryBudget` hard limit is UMA-only, nondeterministic, and defeats motivating example | Replaced with unified error `GpuError.OutOfDeviceMemory { requested_bytes, budget }` on all architectures. Added `AllocPolicy = Advisory | StrictBudget`. Imported host pages count toward `resident_shared_bytes`, not `current_allocated_bytes`. | ADR-0040 §7; `T954`, `T956`, `T962`, `T989` |
| **M11** | **MAJOR** | Diagnostic naming/registration: hardware word in name, overlap with CAP codes, missing registry lock | Canonical capability codes `AX_CAP_CONFLICT_MUT`, `AX_CAP_CONFLICT_READ`, `AX_CAP_OUTLIVES_OWNER` with note `gpu_in_flight` are primary. Dedicated code `AX_GPU_HOST_DEVICE_ACCESS_CONFLICT` registered in `spec/diagnostics.md` §3 and §11 under `GPU` area by `T954`, with `compiler/diag/code.ax` locked by `T955`. | ADR-0040 §5; `spec/diagnostics.md`; `T954`, `T955` |
| **M12** | **MAJOR** | Scope added without acceptance criteria in `T954`, `T957`, `T962`, `T963`, `T969` | Added explicit, verifiable acceptance criteria checkboxes across all modified and newly created tasks. | `T954`, `T957`, `T962`, `T963`, `T969`, `T970`, `T974`, `T976`, `T978`, `T980`, `T985`, `T987`, `T322`, `T989`–`T992` |
| **M13** | **MAJOR** | Task sizing: `T956` and `T963` oversized; "no new tasks" was an artificial constraint | Created dedicated Epic **`E22.10 Unified Memory Architecture (UMA), Zero-Copy Host Import & Coherency Verification`** with 4 right-sized tasks (`T989`–`T992`), offloading specialized UMA driver/import code from `T956`/`T963`. | `spec/ROADMAP.md`; `T956`, `T963`, `T989`–`T992`, `T322` |
| **M14** | **MAJOR** | Traceability: owner request not recorded in `OWNER.md`, no `REQ-*` covers UMA, relevant specs not cited | Recorded `REQ-OWNER-009` in `spec/requirements/OWNER.md` and `spec/requirements/CATALOG.md`. Mapped `REQ-OWNER-009` and `REQ-OPT-347` into `covers:` across tasks. Cited `REQ-SIMD-147`, `REQ-CONC-096`, `REQ-COL-074`. | `spec/requirements/OWNER.md`, `CATALOG.md`; ADR-0040; tasks |
| **M15** | **MAJOR** | `GpuMemoryArchitecture` conflated orthogonal axes and duplicated truth | Replaced with orthogonal `GpuMemoryTopology` (`DiscretePool | UnifiedSystemPool | CoherentMultiPoolNuma`), per-heap `HeapFlags`, and `rebar_aperture_bytes: u64`. `is_unified_memory()` is a derived helper method. | ADR-0040 §1; `T954`, `T962`, `T989` |
| **M16** | **MAJOR** | Mixed iGPU (UMA) + dGPU in one process was unspecified | Specified multi-adapter topology: `UnifiedBuffer` is host-owned and bound per-device via `bind_to(device) -> DeviceView<T>`; dGPU access to host-shared memory is classified as pinned-host access (`REQ-GPU-063`); budgets reported per device. | ADR-0040 §1; `T954`, `T962`, `T989` |
| **m17** | **MINOR** | Tensors (`ATENSOR`) and AI/MMA tasks not wired to zero-copy contract | `T980` (`SPEC-137`) updated: tensor `.to(device)` takes `self` by value (by-move zero-copy elision per `REQ-OPT-347`); `Tensor.from_host_import` provides read-only zero-copy weight loading without allocation; `REQ-GPU-061` preserved. | `T980` |
| **m18** | **MINOR** | WebGPU, OpenGL, software rasterizer and CPU fallback defaults inconsistent or missing | WebGPU defaults to `DiscretePool`, `supports_host_import = false`, fast-path `mappedAtCreation = true`. OpenGL defaults to `DiscretePool`, persistent mapping with client barriers. CPU fallback / software rasterizer default to `UnifiedSystemPool`. | ADR-0040 §1; `T962`, `T974`, `T976`, `T978`, `T985`, `T987` |
| **m19** | **MINOR** | Cache maintenance only on `NonCoherentUma` untestable without trace hook; ReBAR copy accounting undefined | Added `bytes_written_over_bus`, `cache_flushes`, and `cache_invalidates` to `TransferStats`. ReBAR host writes count as bus writes, not `bytes_copied`. Assertions testable via mock driver trace. | ADR-0040 §3; `T956`, `T957`, `T990`, `T992` |
| **m20** | **MINOR** | Downstream runtime/conformance tasks not updated (`T964`, `T965`, `T970`, `T322`) | `T964` lowers linear buffer transfer nodes to domain transitions + barriers; `T965`, `T970` include UMA conformance; `T322` wires `T989`–`T992` and adds UMA exit criteria. | `T964`, `T965`, `T970`, `T322` |
| **m21** | **MINOR** | `WRITE_COMBINE` for non-coherent UMA collapses CPU read throughput | Added `HostAccessPattern = WriteOnly | ReadOnly | ReadWrite`. `WriteOnly` -> `WRITE_COMBINE`; `ReadOnly`/`ReadWrite` (and `shared_read_views`) -> `WRITE_BACK` / `HOST_CACHED` with explicit invalidation. | ADR-0040 §6; `T956`, `T963`, `T990` |
| **m22** | **MINOR** | ADR-0040 set "0 `depends:` changes / 0 new tasks" as success metric | Replaced in ADR-0040 Consequences and ROADMAP log with disciplined board hygiene: minimal graph changes matching reality (`T921`/`T922` dependencies, Epic `E22.10`, `T322` gate wiring, 0 reqcov gaps). | ADR-0040 Consequences; `spec/ROADMAP.md` |

---

### Part B: Hardware, OS, Driver API Correctness and Platform Coverage (17 Findings)

| ID | Severity | Red-Team Hardware Finding | Architectural Resolution in ADR-0040 Revision & Tasks | Impacted Files & Tasks |
|---|---|---|---|---|
| **1** | **BLOCKER** | `CheckFeatureSupport(D3D12_FEATURE_ARCHITECTURE1)` fails with `E_INVALIDARG` due to uninitialized `NodeIndex` input field | Specified explicit initialization `D3D12_FEATURE_DATA_ARCHITECTURE1 arch = {}; arch.NodeIndex = 0;` (or physical adapter node index from `DeviceId`) before invoking `CheckFeatureSupport`. | ADR-0040 §1; `T962`, `T963`, `T991` |
| **2** | **BLOCKER** | `D3D12_HEAP_TYPE_CUSTOM` + `D3D12_MEMORY_POOL_L0` places ReBAR allocations into system RAM and violates D3D12 non-coherent page rules | Strict architectural separation: UMA uses `CUSTOM` + `MEMORY_POOL_L0`; discrete ReBAR VRAM must reside in **`D3D12_MEMORY_POOL_L1`** with `CPU_PAGE_PROPERTY_WRITE_COMBINE` (`D3D12_HEAP_TYPE_GPU_UPLOAD`). Never use `MEMORY_POOL_L0` for ReBAR. | ADR-0040 §6; `T962`, `T963`, `T991` |
| **3** | **BLOCKER** | `ID3D12Device3::OpenExistingHeapFromAddress` requires `VirtualAlloc` and cannot wrap file mappings (`from_mmap`) | Specified D3D12 dual-path import: `OpenExistingHeapFromAddress` for `VirtualRegion` (`VirtualAlloc`); `ID3D12Device3::OpenExistingHeapFromFileMapping` using Win32 file mapping HANDLE for file-backed mappings; raw pointer views return `GpuError.HostImportUnsupported`. | ADR-0040 §4; `T962`, `T963`, `T991` |
| **4** | **BLOCKER** | Coherence is a per-memory-type property in Vulkan, not per-device; skipping cache maintenance on `CacheCoherentUma` causes silent data corruption | Removed adapter-level coherence bypass. Cache flush/invalidate (`vkFlushMappedMemoryRanges` / `vkInvalidateMappedMemoryRanges`) emitted **if and only if** the allocation's `VkMemoryType` lacks `VK_MEMORY_PROPERTY_HOST_COHERENT_BIT`. | ADR-0040 §6; `T957`, `T962`, `T963`, `T991` |
| **5** | **MAJOR** | Vulkan ReBAR detection conflated the standard 256 MiB PCIe BAR aperture with full Resizable BAR | Vulkan ReBAR detection requires verifying that host-visible local heap budget from `VK_EXT_memory_budget` or heap size is > 256 MiB. If <= 256 MiB, adapter is classified as `DiscretePool` with limited staging aperture. | ADR-0040 §1; `T962`, `T963`, `T989` |
| **6** | **MAJOR** | NVIDIA Grace Hopper / Grace Blackwell physically consists of two NUMA pools (HBM3 + LPDDR5X), not one physical pool | Classified Grace Hopper / MI300A accurately as `CoherentMultiPoolNuma`. Reports two distinct pools (HBM3 high-bandwidth device-local vs LPDDR5X system-shared coherent) with 8x bandwidth divergence. Never combines them into single `unified_pool_bytes`. | ADR-0040 §1; `T962`, `T989` |
| **7** | **MAJOR** | `VK_EXT_external_memory_host` mandates `minImportedHostPointerAlignment` (up to 64 KiB), rejecting 4 KiB page-aligned imports | Required host pointer alignment to `max(page_size(), minImportedHostPointerAlignment)` queried via `VkPhysicalDeviceExternalMemoryHostPropertiesEXT`. Allocation size must also be integer multiple. Misaligned imports fail with `GpuError.HostImportMisaligned`. | ADR-0040 §4; `T962`, `T989`, `T991` |
| **8** | **MAJOR** | Metal `newBufferWithBytesNoCopy` enforces 16 KiB alignment on Apple Silicon and page-multiple length | Enforced Apple Silicon pointer alignment to `vm_page_size` (16 KiB) AND `length` must be an integer multiple of `vm_page_size`. Non-page-multiple files require anonymous padding or return `GpuError.HostImportMisaligned`. | ADR-0040 §4; `T969`, `T989`, `T991` |
| **9** | **MAJOR** | Metal `recommendedMaxWorkingSetSize` ignores iOS/iPadOS Jetsam per-process limits and macOS swap | `recommendedMaxWorkingSetSize` treated as advisory on macOS. On iOS/iPadOS, integrated `os_proc_available_memory()` and GCD `DISPATCH_SOURCE_TYPE_MEMORYPRESSURE` to prevent Jetsam process kills. Hard errors only under `AllocPolicy.StrictBudget`. | ADR-0040 §7; `T962`, `T969`, `T991` |
| **10** | **MAJOR** | Android `AHardwareBuffer` / `gralloc` and Linux `dma-buf` zero-copy paths were missing | Added first-class external memory handle support: `VK_ANDROID_external_memory_android_hardware_buffer` (`AHardwareBuffer`) on Android and `VK_EXT_external_memory_dma_buf` (`dma-buf`) on Linux. | ADR-0040 §4; `T962`, `T989`, `T991` |
| **11** | **MAJOR** | 0-byte copy claim is physically impossible for 2D/3D textures and images due to hardware tiling and swizzling | Explicitly restricted zero-copy elision to linear 1D buffers (`UnifiedBuffer<T>`, `DeviceBuffer<T>`). All 2D/3D textures (`Texture1D/2D/3D`, `DeviceImage`) require GPU layout tiling/swizzling blits even on UMA, with bytes counted in `TransferStats`. | ADR-0040 §3; `T954`, `T956`, `T964`, `T989` |
| **12** | **MAJOR** | Write-Combine reads on non-coherent UMA cause severe CPU throughput collapse for `download` and `shared_read_views` | Introduced `HostAccessPattern`: `WriteOnly` uses `WRITE_COMBINE`; `ReadOnly` / `ReadWrite` (including `shared_read_views`) mandates cached memory (`CPU_PAGE_PROPERTY_WRITE_BACK` on D3D12, `HOST_CACHED` on Vulkan) with explicit invalidation on non-coherent systems. | ADR-0040 §6; `T956`, `T963`, `T990`, `T991` |
| **13** | **MAJOR** | DXGI `QueryVideoMemoryInfo` reports 0 budget for `NON_LOCAL` on UMA, breaking discrete-style staging allocators | Specified that when `is_unified_memory` is true on D3D12, all queries target `DXGI_MEMORY_SEGMENT_GROUP_LOCAL`. `NON_LOCAL` is ignored (reports 0). Registered for WDDM budget change notifications. | ADR-0040 §7; `T962`, `T963`, `T991` |
| **14** | **MAJOR** | Headless CPU mock adapter cannot verify cache invalidation or driver error paths without memory poisoning or software ICDs | Implemented simulated non-coherent cache poisoning in CPU fallback (`MOCK_STALE_CACHE_READ` on un-invalidated reads). Integrated headless CI testing against software ICDs: Microsoft WARP (`d3d10warp.dll`) on Windows and Mesa Lavapipe (`lvp_icd.json`) on Linux. | ADR-0040 §8; `T963`, `T965`, `T992` |
| **15** | **MINOR** | OS memory pressure notification sources were missing across target platforms | Defined normalized formula `usage_ratio = current_allocated_bytes / recommended_max_working_set_bytes` (<75% Normal, 75-90% Warning, >90% Critical). Integrated Apple GCD, Windows WDDM, Linux PSI, and Android `onTrimMemory`. | ADR-0040 §7; `T962`, `T989`, `T991` |
| **16** | **MINOR** | WebGPU cannot query UMA architecture and forbids host pointer imports; missing `mappedAtCreation` fast path | Explicitly specified: WebGPU always reports `DiscretePool` and `supports_host_import = false`. Implemented `GPUBufferDescriptor.mappedAtCreation = true` fast-path for zero-copy initial buffer population. | ADR-0040 §1; `T976`, `T978` |
| **17** | **MINOR** | OpenGL / GLES persistent mapping requires explicit `GL_MAP_COHERENT_BIT` or client memory barriers | Added OpenGL specification: when using `glBufferStorage` with `GL_MAP_PERSISTENT_BIT`, if `GL_MAP_COHERENT_BIT` is unsupported, runtime emits `glMemoryBarrier(GL_CLIENT_MAPPED_BUFFER_BARRIER_BIT)` or `glFlushMappedBufferRange`. | ADR-0040 §1; `T985`, `T987` |

---

## 3. Structural Board & Task Sizing Revisions (Epic E22.10)

To resolve Findings **B5**, **B6**, **M12**, and **M13**, the monolithic UMA extensions previously attached to `T956` and `T963` have been refactored into a dedicated epic:

### Epic `E22.10 Unified Memory Architecture (UMA), Zero-Copy Host Import & Coherency Verification`
- **`T989`** (`axiom-architect`, `model: opus`): *Canonical UMA, Host Import & Memory Topology Specification (SPEC-139)*.
  - Paths: `spec/SPEC-139-unified-memory-architecture.md`.
  - Depends: `[T222, T311, T312, T316, T920, T954, T962]`.
  - Covers: `REQ-OWNER-009`, `REQ-OPT-347`, `REQ-GPU-035`, `REQ-GPU-036`.
- **`T990`** (`axiom-stdlib`, `model: sonnet`): *std.gpu.uma: UnifiedBuffer domain handoff, copy elision & HostImport types*.
  - Paths: `std/gpu/uma`, `tests/run/gpu_uma_transfer`.
  - Depends: `[T222, T311, T312, T316, T921, T922, T956, T989]`.
  - Covers: `REQ-OWNER-009`, `REQ-OPT-347`, `REQ-GPU-035`.
- **`T991`** (`axiom-backend`, `model: sonnet`): *UMA backend drivers: Vulkan, D3D12, Metal, AHardwareBuffer, dma-buf & OS memory pressure*.
  - Paths: `std/sys/gpu/vulkan/uma.ax`, `std/sys/gpu/d3d12/uma.ax`, `std/sys/gpu/metal/uma.ax`, `std/sys/gpu/linux/dmabuf.ax`, `std/sys/gpu/android/ahardwarebuffer.ax`, `tests/run/gpu_uma_driver`.
  - Depends: `[T222, T311, T312, T316, T963, T969, T990]`.
  - Covers: `REQ-OWNER-009`, `REQ-GPU-035`, `REQ-GPU-036`.
- **`T992`** (`axiom-qa`, `model: sonnet`): *UMA conformance: 4-topology test matrix, simulated non-coherent cache poisoning & WARP/Lavapipe CI*.
  - Paths: `tests/conformance/p22/e22_10_uma_conformance`.
  - Depends: `[T222, T311, T312, T316, T957, T965, T970, T991]`.
  - Covers: `REQ-OWNER-009`, `REQ-OPT-347`.

### Gate Integration & Dependency Flow
- **Phase P22 Gate (`T322`)**: Added `T989, T990, T991, T992` to `depends:`, and added ADR-0040 UMA exit criteria to Acceptance.
- **Cross-Phase Prerequisites**: Explicitly wired E21.6 virtual memory dependencies (`T921`, `T922`) to `T955`, `T969`, and `T990`, resolving the hidden dependency gap flagged in **B5**.
- **Requirement Tracking**: Added `REQ-OWNER-009` to `spec/requirements/OWNER.md` and `spec/requirements/CATALOG.md`. All tasks covering UMA list `REQ-OWNER-009` and `REQ-OPT-347` in `covers:`.

---

## 4. Verification & Validation Status

The synthesized files were validated using the project's quality tools:
1. `taskctl.py validate`: Confirmed all 663 tasks valid with 0 errors across all YAML frontmatter headers.
2. `taskctl.py lint`: Confirmed all task files adhere to strict schema rules.
3. `reqcov.py --strict`:
   - Total requirements: 32,309
   - `v1-core`: 5,864 implemented
   - `v1-full`: 6,671 implemented, 2,161 planned
   - `post-v1`: 17,521 epic, 92 planned
   - Gaps: 0 (`COVERAGE OK`)
4. `harness_check.py`: Passed with `HARNESS OK`.

---

## 5. Conclusion

This synthesized revision completely eliminates all semantic, ownership, hardware, OS API, and dependency hazards previously present in ADR-0040. Axiom GPU programs now possess a unified, sound, and mathematically robust zero-copy memory architecture that delivers peak performance on unified platforms while remaining completely portable and race-free on discrete systems.
