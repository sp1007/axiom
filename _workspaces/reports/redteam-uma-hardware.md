# Red-team review — ADR-0040 UMA: Hardware, OS, Driver API Correctness and Platform Coverage

Reviewed: commit `57b7c8e6` (`spec/decisions/ADR-0040-unified-memory-architecture-uma.md`, amendments to `T954`, `T955`, `T956`, `T957`, `T962`, `T963`, `T969`).
Cross-checked against:
- Direct3D 12 Agility SDK & Windows SDK headers (`d3d12.h`, `dxgi1_4.h`), Microsoft Learn D3D12 hardware architecture specifications.
- Vulkan 1.3 Core Specification, `VK_EXT_external_memory_host`, `VK_EXT_memory_budget`, `VK_ANDROID_external_memory_android_hardware_buffer`, `VK_EXT_external_memory_dma_buf`.
- Apple Metal Shading Language & Metal Framework API documentation (`MTLDevice`, `MTLBuffer`).
- Android NDK (`AHardwareBuffer`, `gralloc`), Linux DRM/KMS subsystem (`dma-buf`).
- Hardware architecture whitepapers: NVIDIA Grace Hopper Superchip architecture, Apple Silicon unified memory subsystem, AMD APU & Smart Access Memory (SAM/ReBAR), Intel Arc/Xe unified memory architectures.
- Sibling report: `_workspaces/reports/redteam-uma-semantics.md` (semantics, capability model, and board issues excluded to prevent duplication).

---

## 1. BLOCKER — `CheckFeatureSupport(D3D12_FEATURE_ARCHITECTURE1)` fails with `E_INVALIDARG` due to uninitialized `NodeIndex` input field

**Target.** ADR-0040 Decision §1: "D3D12: `CheckFeatureSupport(D3D12_FEATURE_ARCHITECTURE1)` → `UMA`, `CacheCoherentUMA`."
Also in `T962` scope: "detection rules per backend (D3D12 `D3D12_FEATURE_ARCHITECTURE1` `UMA` / `CacheCoherentUMA`; ...)" and `T963` scope: "D3D12 `CheckFeatureSupport(D3D12_FEATURE_ARCHITECTURE1)`".

**Why.**
In the Direct3D 12 API, `D3D12_FEATURE_DATA_ARCHITECTURE1` is defined in `d3d12.h` as:
```c
typedef struct D3D12_FEATURE_DATA_ARCHITECTURE1 {
  UINT NodeIndex;             // [in] Specifies the physical adapter in multi-adapter operation
  BOOL TileBasedRenderer;     // [out]
  BOOL UMA;                   // [out]
  BOOL CacheCoherentUMA;      // [out]
  BOOL IsolatedMMU;           // [out]
} D3D12_FEATURE_DATA_ARCHITECTURE1;
```
`NodeIndex` is an **explicit input parameter** (`[in]`). Microsoft documentation specifies: *"NodeIndex: In multi-adapter operation, this indicates which physical adapter of the device is of interest."*
If the runtime passes an uninitialized `D3D12_FEATURE_DATA_ARCHITECTURE1` struct (or stack memory with arbitrary values), and `NodeIndex >= pDevice->GetNodeCount()`, `ID3D12Device::CheckFeatureSupport` immediately returns `E_INVALIDARG` (0x80070057) and populates none of the output fields. In linked display adapter (LDA) configurations (e.g. integrated + discrete chiplet or multi-GPU systems), UMA and cache coherence are strictly per-node properties. Querying without explicit `NodeIndex` management breaks adapter initialization.

**Proposed fix (ADR-0040 §1, bullet 1):**
> - D3D12: `D3D12_FEATURE_DATA_ARCHITECTURE1` với `NodeIndex` được khởi tạo bằng index của physical adapter node (`0` trên single-GPU, hoặc `node_index` từ `DeviceId`); gọi `CheckFeatureSupport(D3D12_FEATURE_ARCHITECTURE1, &arch, sizeof(arch))` kiểm tra `arch.UMA` và `arch.CacheCoherentUMA`.

---

## 2. BLOCKER — `D3D12_HEAP_TYPE_CUSTOM` + `D3D12_MEMORY_POOL_L0` places ReBAR allocations into system RAM and violates D3D12 non-coherent page rules

**Target.** ADR-0040 Decision §2: "D3D12: `D3D12_HEAP_TYPE_CUSTOM` + `D3D12_MEMORY_POOL_L0`, `CPU_PAGE_PROPERTY_WRITE_BACK` khi cache-coherent, `WRITE_COMBINE` khi non-coherent; không tạo `UPLOAD` heap trung gian."
Also in `T963` scope: "with `D3D12_HEAP_TYPE_CUSTOM` + `D3D12_MEMORY_POOL_L0` (`WRITE_BACK` when cache-coherent, `WRITE_COMBINE` otherwise, no intermediate `UPLOAD` heap)".

**Why.**
This directive conflates discrete VRAM, ReBAR VRAM, and UMA system RAM in Direct3D 12:
1. **Discrete ReBAR Misplacement:** In D3D12, `D3D12_MEMORY_POOL_L0` is **physical system memory** (RAM over the PCIe bus). On a discrete GPU, the high-speed on-card VRAM is **`D3D12_MEMORY_POOL_L1`**. If an application creates a custom heap with `MEMORY_POOL_L0` on a discrete GPU with ReBAR enabled, the allocation is placed into system RAM, completely bypassing the GPU's dedicated VRAM and suffering PCIe transfer penalties! For host-visible VRAM on ReBAR discrete GPUs, the memory pool must be `D3D12_MEMORY_POOL_L1` with `D3D12_CPU_PAGE_PROPERTY_WRITE_COMBINE` (supported via GPU Upload Heaps / Agility SDK `D3D12_HEAP_TYPE_GPU_UPLOAD` or `D3D12_FEATURE_D3D12_OPTIONS16`).
2. **Invalid Page Property on Non-Coherent UMA:** When `UMA == TRUE` but `CacheCoherentUMA == FALSE`, attempting to create a custom heap with `CPU_PAGE_PROPERTY_WRITE_BACK` in `MEMORY_POOL_L0` causes `CreateHeap` / `CreateCommittedResource` to fail with `E_INVALIDARG` on drivers where write-back caching without CPU snooping is disallowed because D3D12 has no CPU cache invalidation intrinsic for custom heaps.

**Proposed fix (ADR-0040 §2, bullet 1):**
> - D3D12: Phân biệt UMA và ReBAR:
>   - Trên UMA (`UMA == TRUE`): dùng `D3D12_HEAP_TYPE_CUSTOM` + `D3D12_MEMORY_POOL_L0`; `CPU_PAGE_PROPERTY_WRITE_BACK` chỉ khi `CacheCoherentUMA == TRUE`; khi `CacheCoherentUMA == FALSE`, bắt buộc dùng `D3D12_CPU_PAGE_PROPERTY_WRITE_COMBINE` (hoặc `D3D12_HEAP_TYPE_READBACK` / `UPLOAD` có `Map`/`Unmap` range invalidation của D3D12 runtime).
>   - Trên ReBAR (`UMA == FALSE`, ReBAR khả dụng): bộ nhớ host-visible device-local bắt buộc nằm ở `D3D12_MEMORY_POOL_L1` với `CPU_PAGE_PROPERTY_WRITE_COMBINE` (dùng `D3D12_HEAP_TYPE_GPU_UPLOAD` nếu có Agility SDK Options16, hoặc custom heap L1 có CPU access), không bao giờ dùng `MEMORY_POOL_L0`.

---

## 3. BLOCKER — `ID3D12Device3::OpenExistingHeapFromAddress` requires `VirtualAlloc` allocations and cannot wrap file mappings (`from_mmap`)

**Target.** ADR-0040 Decision §4: "Nhập trang host vào GPU không copy (`T954`, `T956`, `T963`, `T969`): `UnifiedBuffer.from_mmap(view<Mmap>)` / `UnifiedBuffer.from_virtual_region(...)` ... qua ... D3D12 `ID3D12Device3.OpenExistingHeapFromAddress`."
Also in `T963` scope: "and `ID3D12Device3.OpenExistingHeapFromAddress` host import".

**Why.**
Microsoft's API contract for `ID3D12Device3::OpenExistingHeapFromAddress` has two strict prerequisites:
1. **Source Allocation Primitive:** Microsoft Learn explicitly specifies: *"pAddress: The memory address passed in must have been allocated using VirtualAlloc or its variants."* It wraps the entire `VirtualAlloc` memory range.
2. **File Mappings Are Incompatible:** On Windows, file-backed memory (`std.vmem.mmap` / `Mmap`) is created via `CreateFileMappingW` and mapped via `MapViewOfFile` / `MapViewOfFile3`. The Windows kernel and graphics memory manager (Dxgkrnl) reject `MapViewOfFile` memory pointers passed to `OpenExistingHeapFromAddress`, returning `E_INVALIDARG`.
3. **Dedicated File Mapping API:** To import file mappings into D3D12, Microsoft provides a completely different API: `ID3D12Device3::OpenExistingHeapFromFileMapping(HANDLE hFileMapping, REFIID riid, void **ppvHeap)`. This requires the Win32 `HANDLE` of the file-mapping object, which cannot be extracted from an arbitrary raw pointer or slice `view<Mmap>`.
4. **Base Address Granularity:** `OpenExistingHeapFromAddress` requires passing the exact base address returned by `VirtualAlloc`. If `from_virtual_region` passes an interior pointer or offset slice, the API fails with `E_INVALIDARG`.

**Proposed fix (ADR-0040 §4, replace D3D12 wording):**
> - D3D12 host import:
>   - Với `VirtualRegion` (cấp phát bởi `VirtualAlloc`): dùng `ID3D12Device3::OpenExistingHeapFromAddress`, yêu cầu địa chỉ là base address của allocation và kích thước khớp nguyên vẹn allocation page size.
>   - Với file-backed `Mmap`: yêu cầu Win32 file-mapping handle và dùng `ID3D12Device3::OpenExistingHeapFromFileMapping`. Nếu chỉ có con trỏ view, trả về `GpuError.HostImportUnsupported` (không thể gọi `OpenExistingHeapFromAddress`).

---

## 4. BLOCKER — Coherence is a per-memory-type property in Vulkan, not per-device; skipping cache maintenance on `CacheCoherentUma` causes silent data corruption

**Target.** ADR-0040 Decision §1: "Phân loại kiến trúc bộ nhớ: `GpuAdapterInfo` có thêm `memory_architecture: GpuMemoryArchitecture` với `Discrete | CacheCoherentUma | NonCoherentUma | ReBarHostVisible`"; Decision §2: "Vulkan: persistent-mapped memory type `DEVICE_LOCAL | HOST_VISIBLE`; tự động `vkFlushMappedMemoryRanges` / `vkInvalidateMappedMemoryRanges` tại các điểm chuyển quyền sở hữu khi memory type không `HOST_COHERENT`"; Decision §3: "...phát barrier / cache maintenance cần thiết... kiểm bằng conformance trong T957"; `T957` scope: "cache maintenance emitted only for `NonCoherentUma`".

**Why.**
In Vulkan, hardware cache coherence is **not an adapter-wide property**; it is defined strictly per `VkMemoryType` within `VkPhysicalDeviceMemoryProperties`.
1. On modern UMA hardware (Intel Iris/Arc iGPU, AMD APU, Qualcomm Adreno, ARM Mali), an integrated GPU typically exposes multiple memory types on its device-local heap:
   - Type 0: `DEVICE_LOCAL | HOST_VISIBLE | HOST_COHERENT` (write-combined/uncached; CPU writes snoop or bypass CPU cache; flush unnecessary);
   - Type 1: `DEVICE_LOCAL | HOST_VISIBLE | HOST_CACHED` (cached in CPU L1/L2 for fast CPU reads, but **NOT** `HOST_COHERENT`; requires explicit `vkFlushMappedMemoryRanges` and `vkInvalidateMappedMemoryRanges`);
   - Type 2: `DEVICE_LOCAL | HOST_VISIBLE | HOST_COHERENT | HOST_CACHED` (cached with hardware LLC/L3 snooping, e.g. Intel processor graphics).
2. If the runtime classifies the device as `CacheCoherentUma` at the adapter level and follows `T957`'s rule ("cache maintenance emitted only for `NonCoherentUma`"), then whenever a buffer is allocated from Type 1 (`HOST_CACHED` without `HOST_COHERENT`), **no flush or invalidate operations will ever be emitted**! The GPU will read stale CPU cache contents, and the CPU will read stale pre-GPU memory contents, leading to nondeterministic data corruption.
3. Cache maintenance in Vulkan must be driven by `!(memory_type.propertyFlags & VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)` on the specific allocation, completely independent of any adapter-level enum.

**Proposed fix (ADR-0040 §3 and `T957` scope):**
> Sửa ADR-0040 §3 và `T957`: Bỏ quy tắc "cache maintenance emitted only for `NonCoherentUma`". Quy định rõ: cache maintenance (`vkFlushMappedMemoryRanges` / `vkInvalidateMappedMemoryRanges`) được phát ra **khi và chỉ khi** memory type của buffer không có cờ `VK_MEMORY_PROPERTY_HOST_COHERENT_BIT`. `CacheCoherentUma` ở cấp device chỉ là tóm tắt cho biết thiết bị có ít nhất một memory type vừa `DEVICE_LOCAL`, vừa `HOST_VISIBLE`, vừa `HOST_COHERENT`.

---

## 5. MAJOR — Vulkan ReBAR detection conflates the standard 256 MiB PCIe BAR aperture with full Resizable BAR

**Target.** ADR-0040 Decision §1: "Vulkan: heap/memory type có `DEVICE_LOCAL | HOST_VISIBLE` (kèm `HOST_COHERENT` / `HOST_CACHED`), `VkPhysicalDeviceType` `INTEGRATED_GPU`; ReBAR khi heap `DEVICE_LOCAL | HOST_VISIBLE` phủ toàn bộ VRAM của GPU rời."

**Why.**
On discrete GPUs where Resizable BAR (AMD SAM / PCIe ReBAR) is **disabled** in the motherboard UEFI, the PCIe standard still exposes a legacy **256 MiB BAR aperture** for CPU access to VRAM.
In Vulkan:
1. Many drivers (e.g. NVIDIA, AMD on Windows/Linux) expose a memory type having `VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT | VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT` pointing to the main VRAM heap. The heap size reported in `VkMemoryHeap.size` is the **entire physical VRAM** (e.g. 16 GiB or 24 GiB), even though only 256 MiB can actually be mapped by the host!
2. If Axiom determines ReBAR simply by checking if a `DEVICE_LOCAL | HOST_VISIBLE` type points to a heap covering total VRAM, it will falsely identify standard 256 MiB BAR systems as full `ReBarHostVisible`.
3. When an application attempts to allocate more than 256 MiB of host-visible memory on such an adapter, `vkAllocateMemory` fails with `VK_ERROR_OUT_OF_DEVICE_MEMORY`.
4. Robust ReBAR detection requires querying `VK_EXT_memory_budget` (`heapBudget[heapIndex]`), checking `VK_KHR_maintenance4`, or verifying through `DXGI_ADAPTER_DESC1` / `QueryVideoMemoryInfo` that the host-accessible local budget is genuinely larger than 256 MiB.

**Proposed fix (ADR-0040 §1, bullet 2):**
> - Vulkan ReBAR detection: Để phân biệt ReBAR thật sự với legacy 256 MiB PCIe BAR aperture, runtime phải kiểm tra: (a) có memory type `DEVICE_LOCAL | HOST_VISIBLE`; (b) kích thước vùng host-visible thực tế (hoặc budget từ `VK_EXT_memory_budget` cho heap đó) phải > 256 MiB (hoặc bằng toàn bộ heap size của VRAM). Nếu host-visible budget <= 256 MiB, adapter chỉ là `Discrete` với limited staging aperture, không gắn cờ `ReBarHostVisible`.

---

## 6. MAJOR — NVIDIA Grace Hopper / Grace Blackwell physically consists of two NUMA pools (HBM3 + LPDDR5X), not one physical pool

**Target.** ADR-0040 Context: "NVIDIA Grace Hopper / Grace Blackwell (NVLink-C2C, cache-coherent) ... Các dòng máy phổ biến có RAM và VRAM là một vùng nhớ vật lý duy nhất". ADR-0040 Decision §1: "`unified_pool_bytes: u64`".

**Why.**
This is an inaccurate hardware architecture premise:
1. An NVIDIA GH200 / GB200 Superchip does **not** have a single unified physical memory pool. It integrates two physically distinct memory subsystems connected by NVLink-C2C:
   - Grace CPU: Up to 480 GiB / 512 GiB of **LPDDR5X** memory (~500 GB/s bandwidth);
   - Hopper GPU: 96 GiB or 144 GiB of **HBM3 / HBM3e** memory (~4,000 GB/s bandwidth).
2. NVLink-C2C provides bidirectional hardware cache coherence and a unified virtual address space via ATS/HMM (Heterogeneous Memory Management), but the underlying hardware is a NUMA topology, not UMA.
3. If Axiom treats Grace Hopper as a single UMA pool and allocates device buffers into system LPDDR5X, GPU compute kernels experience an **8x memory bandwidth degradation** (500 GB/s vs 4,000 GB/s).
4. Reporting a single `unified_pool_bytes` conflates LPDDR5X with HBM3.

**Proposed fix (ADR-0040 Context & §1):**
> Sửa ADR-0040 Context và §1: Phân loại chính xác Grace Hopper / Grace Blackwell là kiến trúc `CoherentNuma` (không phải single-pool UMA). `GpuMemoryTopology` phải báo cáo hai pool riêng biệt: `DeviceLocal` (HBM3, high-bandwidth) và `SystemSharedCoherent` (LPDDR5X qua NVLink-C2C). Zero-copy host sharing chỉ áp dụng khi truy cập vùng LPDDR5X hoặc qua HMM page migration, không gộp dung lượng HBM3 và LPDDR5X vào một số đo `unified_pool_bytes` duy nhất.

---

## 7. MAJOR — `VK_EXT_external_memory_host` mandates `minImportedHostPointerAlignment` (up to 64 KiB), rejecting 4 KiB page-aligned imports

**Target.** ADR-0040 Decision §4: "`UnifiedBuffer.from_mmap(view<Mmap>)` / `UnifiedBuffer.from_virtual_region(...)` (page-aligned...) qua ... Vulkan `VK_EXT_external_memory_host`". `T954`, `T956`, `T963`.

**Why.**
1. ADR-0040 assumes standard OS virtual memory page alignment (4096 bytes on x86_64) is sufficient to import host pages into Vulkan.
2. Under the Vulkan specification for `VK_EXT_external_memory_host`, host pointers passed to `vkGetMemoryHostPointerPropertiesEXT` and `VkImportMemoryHostPointerInfoEXT` **must be aligned to `VkPhysicalDeviceExternalMemoryHostPropertiesEXT::minImportedHostPointerAlignment`**.
3. On AMD GPUs, Mesa RADV/ANV drivers, and various ARM platforms, `minImportedHostPointerAlignment` is frequently **65,536 bytes (64 KiB)**, not 4096 bytes.
4. If an application allocates a 4 KiB-aligned `VirtualRegion` or `Mmap` and passes it to `vkAllocateMemory`, the driver will immediately return `VK_ERROR_INVALID_EXTERNAL_HANDLE`.
5. Furthermore, `allocationSize` must also be rounded up to an integer multiple of `minImportedHostPointerAlignment`, and `vkGetMemoryHostPointerPropertiesEXT` must be invoked to determine which `memoryTypeBits` permit importing that host pointer.

**Proposed fix (ADR-0040 §4 & `T963` scope):**
> Quy định rõ trong ADR-0040 §4 và `T963`: Căn lề của host pointer khi import qua `VK_EXT_external_memory_host` phải đạt `max(page_size(), minImportedHostPointerAlignment)` (truy vấn từ `VkPhysicalDeviceExternalMemoryHostPropertiesEXT`). `VirtualRegion` và `Mmap` dùng để import phải hỗ trợ căn lề 64 KiB. Trước khi cấp phát `VkDeviceMemory`, phải gọi `vkGetMemoryHostPointerPropertiesEXT` để chọn đúng memory type index hợp lệ; nếu pointer không thỏa mãn căn lề hoặc không có memory type tương thích, trả về `GpuError.HostImportUnsupported`.

---

## 8. MAJOR — Metal `newBufferWithBytesNoCopy` enforces 16 KiB alignment on Apple Silicon and page-multiple length, failing on arbitrary file sizes

**Target.** ADR-0040 Decision §4: "`UnifiedBuffer.from_mmap(view<Mmap>)` / `UnifiedBuffer.from_virtual_region(...)` (page-aligned...) qua Metal `newBufferWithBytesNoCopy:length:options:deallocator:`". `T969` scope.

**Why.**
Apple's developer documentation for `-[MTLDevice newBufferWithBytesNoCopy:length:options:deallocator:]` specifies two strict hardware-level constraints:
1. **Pointer Alignment (`vm_page_size`):** The pointer must be aligned to the system virtual memory page boundary. On Apple Silicon (M1–M4, A14–A18), `vm_page_size` is **16,384 bytes (16 KiB)**. Passing a 4096-byte-aligned pointer (e.g. from an x86-oriented allocator or standard file mapping) causes Metal to fail with a validation assertion (`pointer is not page aligned`) and return `nil`.
2. **Length Multiple Constraint:** The `length` parameter **must be an integer multiple of the page size** (`vm_page_size`). If a file-backed `Mmap` represents a file of arbitrary size (e.g. 50,000 bytes), passing 50,000 as `length` will fail Metal validation.
3. If the length is artificially rounded up to 65,536 bytes (4 pages of 16 KiB) to satisfy Metal, the GPU buffer will extend beyond the physical end of the file mapping. Any GPU shader access or CPU prefetch reading into the padding bytes beyond the EOF page will trigger a kernel `EXC_BAD_ACCESS` / `SIGBUS`.

**Proposed fix (ADR-0040 §4 & `T969` scope):**
> Sửa ADR-0040 §4 và `T969`: Host import trên Apple Metal yêu cầu con trỏ căn lề theo `vm_page_size` (16 KiB trên Apple Silicon) và `length` phải là bội số của `vm_page_size`. Với file mapping có kích thước không chẵn trang, file phải được ánh xạ với padding trang hợp lệ (hoặc mapping nặc danh có bảo vệ), nếu không runtime phải từ chối với lỗi `GpuError.HostImportMisaligned` thay vì gọi Metal với length không chẵn trang gây crash.

---

## 9. MAJOR — Metal `recommendedMaxWorkingSetSize` ignores iOS/iPadOS Jetsam per-process limits and macOS swap

**Target.** ADR-0040 Decision §6: "`device.memory_budget()` ... từ `MTLDevice.recommendedMaxWorkingSetSize` ... Cấp phát vượt `recommended_max_working_set_bytes` trên UMA trả `GpuError.OutOfUnifiedMemoryBudget` thay vì để OS kill tiến trình." `T969` scope.

**Why.**
1. On iOS and iPadOS, process termination under memory pressure is governed by the **Jetsam daemon**, which enforces strict per-process memory footprint limits based on hardware generation and provisioning entitlements.
2. `MTLDevice.recommendedMaxWorkingSetSize` reports the device-wide GPU working set (e.g. ~5.5 GiB on an 8 GiB M2 iPad). However, without special entitlements (`com.apple.developer.kernel.increased-memory-limit`), Jetsam will **terminate the application at ~2.5 GiB**!
3. Relying on `recommendedMaxWorkingSetSize` as a safeguard against process kills will fail on iOS: the app will allocate 3.5 GiB (below the 5.5 GiB limit) and Jetsam will kill it with `JETSAM_REASON_MEMORY`.
4. Conversely, on macOS, `recommendedMaxWorkingSetSize` is an advisory performance guideline. macOS supports compressed memory and virtual memory swap; applications (e.g. local LLM inference engines like `llama.cpp`) routinely allocate beyond this size. Returning a hard error `OutOfUnifiedMemoryBudget` artificially breaks valid workloads on macOS.
5. True OS pressure detection on Apple platforms requires monitoring `DISPATCH_SOURCE_TYPE_MEMORYPRESSURE` (via `dispatch_source_create`) or querying `os_proc_available_memory()`.

**Proposed fix (ADR-0040 §6 & `T969` scope):**
> - Trên macOS/iOS: `recommendedMaxWorkingSetSize` chỉ là ngưỡng tham khảo hiệu năng (advisory).
> - Trên iOS/iPadOS: tích hợp `os_proc_available_memory()` và lắng nghe sự kiện từ `dispatch_source_create(DISPATCH_SOURCE_TYPE_MEMORYPRESSURE, ...)` để phát hiện áp lực bộ nhớ (`Normal | Warning | Critical`).
> - Không từ chối cứng cấp phát trên macOS khi vượt `recommendedMaxWorkingSetSize` trừ khi người dùng bật cờ `AllocPolicy.StrictBudget`.

---

## 10. MAJOR — Android `AHardwareBuffer` / `gralloc` and Linux `dma-buf` zero-copy paths are missing

**Target.** ADR-0040 Context (listing Snapdragon, Mali, Adreno on Android/Linux as UMA targets); Decision §4 (limiting zero-copy host import to Metal, Vulkan `VK_EXT_external_memory_host`, and D3D12).

**Why.**
1. On Android devices with Qualcomm Adreno or ARM Mali GPUs, proprietary Vulkan drivers **rarely implement `VK_EXT_external_memory_host`**.
2. The standard, cross-process, and cross-hardware zero-copy mechanism on Android is **`AHardwareBuffer`** (backed by the hardware `gralloc` allocator), accessed in Vulkan via the **`VK_ANDROID_external_memory_android_hardware_buffer`** extension (`VkImportAndroidHardwareBufferInfoANDROID`).
3. On Linux desktop and embedded platforms (Wayland, Mesa, Jetson, V4L2), zero-copy buffer sharing between CPU and GPU is performed via **DRM `dma-buf`** file descriptors using **`VK_EXT_external_memory_dma_buf`** (`VkImportMemoryFdInfoKHR`).
4. Without `AHardwareBuffer` and `dma-buf` support, ADR-0040's claim of zero-copy UMA memory on Android and embedded Linux is entirely inoperable on real hardware.

**Proposed fix (ADR-0040 §4 & `T962`/`T963` scope):**
> Mở rộng Decision §4 trong ADR-0040 và `SPEC-133`:
> - Android: Bổ sung hỗ trợ `VK_ANDROID_external_memory_android_hardware_buffer` và `AHardwareBuffer` cho zero-copy buffer sharing.
> - Linux: Bổ sung hỗ trợ `VK_EXT_external_memory_dma_buf` cho zero-copy import qua file descriptor `dma-buf`.

---

## 11. MAJOR — 0-byte copy claim is physically impossible for 2D/3D textures and images due to hardware tiling and swizzling

**Target.** ADR-0040 Decision §3: "Triệt tiêu copy trong `std.gpu.transfer`: trên thiết bị `is_unified_memory`, `UnifiedBuffer<T>`, `upload`, `download`, `.to(device)` không gọi `memcpy`, chỉ chuyển trạng thái miền sở hữu... Cùng mã nguồn chạy DMA trên GPU rời và 0-byte copy trên UMA; kết quả quan sát được phải giống nhau". `T954` / `T956` scope.

**Why.**
1. ADR-0040 states without qualification that on UMA hardware, `upload`, `download`, and `.to(device)` do not copy bytes (`bytes_copied == 0`).
2. While 1D linear buffers (`UnifiedBuffer<T>`, `DeviceBuffer<T>`) can alias physical RAM, **GPU 2D/3D textures and images cannot**:
   - Modern GPUs (Apple Silicon, Intel iGPU, AMD APU, ARM Mali, Adreno) store textures in proprietary tiled or swizzled micro-tile layouts (e.g. Morton Z-order, Intel Tile4, ARM AFBC) to optimize 2D spatial locality and anisotropic filtering in texture hardware units.
   - Host CPU memory is linear (row-major).
   - Direct sampling from linear memory is either prohibited by the graphics API (D3D12 restricts `D3D12_TEXTURE_LAYOUT_ROW_MAJOR` to staging; Vulkan `VK_IMAGE_TILING_LINEAR` does not support mipmaps, multisampling, or depth/stencil) or incurs severe bandwidth and cache degradation.
3. Uploading an image to a GPU texture or reading back a GPU texture to host memory **strictly requires a layout conversion (tiling / detiling) blit**.
4. Claiming 0-byte copies for all transfers on UMA creates false expectations and will fail conformance if applied to texture or image types.

**Proposed fix (ADR-0040 §3 & `T954`/`T956` scope):**
> Làm rõ trong ADR-0040 §3, `SPEC-131`, và `T956`: Triệt tiêu copy trên UMA **chỉ áp dụng cho linear 1D buffers (`UnifiedBuffer<T>`, `DeviceBuffer<T>`)**. Các tài nguyên dạng texture/image (`DeviceImage`, `Texture2D`) bắt buộc phải thực hiện layout swizzling/tiling thông qua GPU blit/copy engine ngay cả trên UMA, và `TransferStats` sẽ phản ánh số byte được chuyển đổi này.

---

## 12. MAJOR — Write-Combine reads on non-coherent UMA cause severe CPU throughput collapse for `download` and `shared_read_views`

**Target.** ADR-0040 Decision §2: "D3D12: ... `CPU_PAGE_PROPERTY_WRITE_BACK` khi cache-coherent, `WRITE_COMBINE` khi non-coherent; không tạo `UPLOAD` heap trung gian." Decision §5: "Cho phép `shared_read_views() -> (view<T>, DeviceView<T>)` để CPU và GPU cùng đọc đồng thời một địa chỉ vật lý, không copy, không khóa."

**Why.**
1. On non-coherent UMA systems, allocating unified memory with Write-Combine attributes (`WRITE_COMBINE` in D3D12, `HOST_VISIBLE` without `HOST_CACHED` in Vulkan) disables CPU caching for that address range.
2. In CPU microarchitectures (x86_64 and ARM64), CPU reads from Write-Combined memory **do not use L1/L2/L3 caches and do not prefetch**. Each read triggers unaligned bus transactions. Read throughput drops by **90% to 99%** (typically 10–50 MB/s instead of 50–100 GB/s)!
3. ADR-0040 promotes CPU read access via:
   - `download` copy elision (CPU reads directly from the mapped device buffer);
   - `shared_read_views()` (concurrent CPU and GPU reads of the same physical address).
4. If a buffer is allocated as `WRITE_COMBINE`, any CPU algorithm performing read operations through `download` or `shared_read_views()` will encounter catastrophic performance degradation, appearing as a complete system stall.
5. In D3D12, when `CacheCoherentUMA == FALSE`, CPU cache invalidation for readback memory is only supported via `ID3D12Resource::Map` / `Unmap` range invalidation; persistent mapping of cached memory without `Map`/`Unmap` is not architecturally coherent.

**Proposed fix (ADR-0040 §2 & §5):**
> Bổ sung thuộc tính truy cập host (`HostAccessPattern = WriteOnly | ReadOnly | ReadWrite`):
> - `WriteOnly` (CPU ghi, GPU đọc): Sử dụng `WRITE_COMBINE` / uncached host-visible.
> - `ReadOnly` / `ReadWrite` (GPU ghi, CPU đọc, hoặc `shared_read_views`): Bắt buộc dùng memory type có CPU caching (`CPU_PAGE_PROPERTY_WRITE_BACK` trên D3D12, `HOST_CACHED` trên Vulkan) kèm theo lệnh invalidation tường minh (`vkInvalidateMappedMemoryRanges` trên Vulkan, hoặc `Map`/`Unmap` range trên D3D12). Nếu phần cứng không hỗ trợ cached host-visible, phải ghi rõ cảnh báo hiệu năng đọc của CPU.

---

## 13. MAJOR — DXGI `QueryVideoMemoryInfo` reports 0 budget for `NON_LOCAL` on UMA, breaking discrete-style staging allocators

**Target.** ADR-0040 Decision §6: "`device.memory_budget()` ... từ `IDXGIAdapter3.QueryVideoMemoryInfo`". `T963` scope.

**Why.**
1. In DXGI 1.4 (`IDXGIAdapter3::QueryVideoMemoryInfo`), the caller must pass a `DXGI_MEMORY_SEGMENT_GROUP`:
   - `DXGI_MEMORY_SEGMENT_GROUP_LOCAL` (0);
   - `DXGI_MEMORY_SEGMENT_GROUP_NON_LOCAL` (1).
2. On discrete GPUs:
   - `LOCAL` represents dedicated on-card VRAM;
   - `NON_LOCAL` represents system RAM allocated for GPU staging.
3. On UMA adapters (Intel iGPU, AMD APU, Qualcomm Snapdragon X):
   - The entire shared system RAM is exposed under **`DXGI_MEMORY_SEGMENT_GROUP_LOCAL`**!
   - `DXGI_MEMORY_SEGMENT_GROUP_NON_LOCAL` reports a `Budget` of **0 bytes** and `CurrentUsage` of **0 bytes**!
4. If a runtime written with discrete assumptions queries `NON_LOCAL` to check available staging or host-shared memory on an integrated GPU, it receives a budget of 0 bytes, triggering false out-of-memory errors.
5. In addition, on UMA adapters, the `Budget` under `DXGI_MEMORY_SEGMENT_GROUP_LOCAL` is dynamic and managed by WDDM based on OS memory pressure; applications must register for `RegisterVideoMemoryBudgetChangeNotificationEvent` to track changes safely.

**Proposed fix (ADR-0040 §6 & `T963` scope):**
> Quy định rõ trong ADR-0040 §6 và `SPEC-133`: Khi `is_unified_memory` là true trên D3D12:
> - Mọi truy vấn `QueryVideoMemoryInfo` phải nhắm vào `DXGI_MEMORY_SEGMENT_GROUP_LOCAL`;
> - Bỏ qua hoặc coi `DXGI_MEMORY_SEGMENT_GROUP_NON_LOCAL` là không áp dụng (trả về 0);
> - Đăng ký lắng nghe sự kiện thay đổi ngân sách qua `IDXGIAdapter3::RegisterVideoMemoryBudgetChangeNotificationEvent`.

---

## 14. MAJOR — Headless CPU mock adapter cannot verify cache invalidation or driver error paths without memory poisoning or software ICDs

**Target.** ADR-0040 Consequences: "CI headless kiểm UMA bằng mock adapter của CPU fallback (`memory_architecture` có thể cấu hình)..."; `T957` scope: "Verify UMA conformance on mock `Discrete`, `CacheCoherentUma`, `NonCoherentUma`, and `ReBarHostVisible` adapters"; `T963` scope.

**Why.**
1. The CPU fallback backend executes entirely within host CPU threads using system RAM. Because CPU cores share L3 cache and hardware coherency protocols, memory written by one host thread is **always hardware cache-coherent** with another host thread.
2. A pure software mock adapter cannot naturally trigger or observe:
   - Stale cache reads caused by missing `vkFlushMappedMemoryRanges` / `vkInvalidateMappedMemoryRanges`;
   - Host import alignment rejections (`minImportedHostPointerAlignment` = 64 KiB or `vm_page_size` = 16 KiB);
   - Page faults on truncated mmap files;
   - Driver memory allocation rejections under WDDM / Jetsam pressure.
3. If conformance tests in `T957` pass solely because the mock adapter sets `TransferStats.bytes_copied = 0` and records dummy flags, the tests provide no verification of actual driver interaction.
4. Robust headless testing requires:
   - Emulated cache poisoning in the mock adapter (e.g. marking memory as stale/poisoned until an explicit invalidate call occurs);
   - Running real driver entry points in CI against software ICDs: **Microsoft WARP (`d3d10warp.dll`)** on Windows and **Mesa Lavapipe (`VK_ICD_FILENAMES=.../lvp_icd.json`)** on Linux.

**Proposed fix (ADR-0040 Consequences, `T957` & `T963` scope):**
> Bổ sung vào `T957` và `T963`:
> 1. Mock adapter của CPU fallback phải có chế độ giả lập non-coherent cache: khi "GPU" ghi dữ liệu, buffer được đánh dấu là `PoisonedForCpu` cho đến khi `cache_invalidate` được gọi; nếu CPU đọc trước khi invalidate, test báo lỗi `MOCK_STALE_CACHE_READ`.
> 2. Bổ sung kiểm thử CI trên software rasterizer thực thụ: Microsoft WARP (`d3d10warp.dll`) trên Windows và Mesa Lavapipe trên Linux để kiểm tra đường dẫn gọi API D3D12/Vulkan thật mà không cần card đồ họa vật lý.

---

## 15. MINOR — OS memory pressure notification sources are missing across target platforms

**Target.** ADR-0040 Decision §6: "`device.memory_budget() -> GpuMemoryBudget { ... pressure: Normal | Warning | Critical }` từ `MTLDevice.recommendedMaxWorkingSetSize`, `IDXGIAdapter3.QueryVideoMemoryInfo`, `VK_EXT_memory_budget`."

**Why.**
The three cited GPU APIs do not provide a 3-state `pressure: Normal | Warning | Critical` enum:
- Metal's `MTLDevice` has no pressure callbacks;
- `IDXGIAdapter3` provides budget change notification events, not a 3-state enum;
- `VK_EXT_memory_budget` reports raw byte arrays (`heapBudget`, `heapUsage`) without pressure classification.
Furthermore, on mobile/desktop OSes, memory pressure originates from operating system daemons, not graphics APIs:
- Linux / Android: Pressure Stall Information (PSI via `/proc/pressure/memory`) and Android `ComponentCallbacks2.onTrimMemory(level)`;
- Windows: WDDM budget change events and `QueryVideoMemoryInfo`;
- Apple: Grand Central Dispatch `DISPATCH_SOURCE_TYPE_MEMORYPRESSURE`.

**Proposed fix (ADR-0040 §6 & `SPEC-133`):**
> Quy định rõ công thức ánh xạ áp lực bộ nhớ:
> - Tính tỷ lệ `usage_ratio = current_allocated_bytes / recommended_max_working_set_bytes`;
> - Gán `pressure`: `Normal` (< 75%), `Warning` (75%–90%), `Critical` (> 90%);
> - Tích hợp nguồn sự kiện OS: GCD memory pressure trên macOS/iOS, WDDM budget change event trên Windows, và PSI `/proc/pressure/memory` hoặc `onTrimMemory` trên Linux/Android.

---

## 16. MINOR — WebGPU cannot query UMA architecture and forbids host pointer imports; missing `mappedAtCreation` fast path

**Target.** ADR-0040 Decision §1: "WebGPU / OpenGL / CPU fallback: báo cáo bảo thủ `Discrete` trừ khi backend xác nhận được UMA."

**Why.**
1. The W3C WebGPU specification intentionally omits memory architecture queries (`GPUAdapterInfo` has no memory topology fields) to prevent client fingerprinting. WebGPU cannot "xác nhận được UMA" through any standard API.
2. WebGPU strictly disallows importing raw host pointers (`from_mmap` cannot exist in WebGPU).
3. However, WebGPU provides an explicit zero-copy initialization mechanism: `GPUBufferDescriptor.mappedAtCreation = true`. This allows direct population of buffer memory at creation without intermediate staging buffer allocation.

**Proposed fix (ADR-0040 §1 & `T976` scope):**
> Xác định rõ: Backend WebGPU **luôn luôn báo cáo `Discrete`** và `supports_host_import = false` do giới hạn sandbox của W3C WebGPU. Bổ sung fast-path cho WebGPU: sử dụng `mappedAtCreation = true` khi khởi tạo buffer để triệt tiêu staging copy trung gian khi nạp dữ liệu ban đầu.

---

## 17. MINOR — OpenGL / GLES persistent mapping requires explicit `GL_MAP_COHERENT_BIT` or client memory barriers

**Target.** ADR-0040 Decision §1: "OpenGL: báo cáo bảo thủ `Discrete` trừ khi backend xác nhận được UMA." §2: (No OpenGL / GLES persistent mapping mentioned).

**Why.**
Modern OpenGL (4.4+) and OpenGL ES (3.1+ with `GL_EXT_buffer_storage`) support persistent memory mapping via `glBufferStorage`:
- If `GL_MAP_COHERENT_BIT` is supported and set, memory writes are automatically coherent.
- If `GL_MAP_COHERENT_BIT` is not supported (common on mobile GLES), the application must explicitly call `glMemoryBarrier(GL_CLIENT_MAPPED_BUFFER_BARRIER_BIT)` or `glFlushMappedBufferRange` after CPU writes, and before CPU reads.

**Proposed fix (ADR-0040 §2 & `T985` scope):**
> Bổ sung vào Decision §2 cho OpenGL / GLES: Khi backend OpenGL sử dụng `glBufferStorage` với `GL_MAP_PERSISTENT_BIT`, nếu thiếu `GL_MAP_COHERENT_BIT`, runtime phải phát `glMemoryBarrier(GL_CLIENT_MAPPED_BUFFER_BARRIER_BIT)` hoặc `glFlushMappedBufferRange` tại các điểm đồng bộ chuyển miền.

---

FINDINGS: 17 (B=4 M=10 m=3)
