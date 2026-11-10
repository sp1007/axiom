# ADR-0040 — Unified Memory Architecture (UMA): RAM và VRAM hợp nhất trên mọi OS / phần cứng

Status: accepted (2026-11-10, architect; owner-delegated decision)

## Tóm tắt
- Chủ dự án yêu cầu: "thêm vấn đề về gpu, một số hệ điều hành và dòng máy tính có bộ nhớ unified bao gồm cả ram và vram là 1".
- Kế hoạch P22 hiện tại (ADR-0038, `T954`–`T957`, `T962`–`T963`, `T969`) chỉ gắn khái niệm bộ nhớ hợp nhất với Apple Silicon (`MTLDevice.hasUnifiedMemory`) và mặc định mô hình GPU rời (RAM ↔ VRAM qua PCIe, có staging copy). Trên máy UMA, mô hình này nhân đôi bộ nhớ và tốn băng thông copy từ RAM sang chính RAM.
- Quyết định: đưa UMA thành khái niệm hạng nhất, độc lập backend, trong `SPEC-131` / `SPEC-133` và các task P22 liên quan, gồm 6 hạng mục: (1) phân loại `GpuMemoryArchitecture`; (2) cấp phát zero-copy trên D3D12 / Vulkan / Metal; (3) tự động triệt tiêu copy trong `std.gpu.transfer`; (4) nhập trang `mmap` / `VirtualRegion` thẳng vào GPU; (5) kiểm tra data-race CPU↔GPU ở compile time trên vùng nhớ chung; (6) ngân sách bộ nhớ hợp nhất và áp lực RAM của OS.
- Không thêm task mới; mở rộng phạm vi và tiêu chí nghiệm thu của `T954`, `T955`, `T956`, `T957`, `T962`, `T963`, `T969`. Không đổi `depends:`, không đổi gate `T322`.

## Context
Các dòng máy phổ biến có RAM và VRAM là **một vùng nhớ vật lý duy nhất**:
- Apple Silicon M1–M4 (macOS), A14–A18 (iOS/iPadOS) — cache-coherent.
- AMD Ryzen APU / Strix Halo, AMD Instinct MI300A; Intel Core Ultra / Lunar Lake Arc iGPU (Windows/Linux).
- NVIDIA Grace Hopper / Grace Blackwell (NVLink-C2C, cache-coherent), NVIDIA Jetson (Linux).
- Qualcomm Snapdragon X Elite / Adreno (Windows on ARM), ARM Mali / Immortalis, Adreno trên Android/Linux — thường là UMA nhưng cache CPU và GPU không tự đồng bộ (non-coherent).
- Card rời có Resizable BAR / AMD Smart Access Memory: không phải UMA, nhưng CPU ánh xạ được toàn bộ VRAM (`DEVICE_LOCAL | HOST_VISIBLE`).

Hệ quả nếu coi mọi GPU là GPU rời:
1. `upload` / `download` / `tensor.to(device)` copy dữ liệu từ RAM sang RAM, tốn gấp đôi bộ nhớ.
2. Nạp mô hình AI 30 GB qua `mmap` rồi cấp `DeviceBuffer` 30 GB sẽ làm cạn RAM trên máy 32/64 GB.
3. Cấp phát VRAM quá mức trên máy UMA trực tiếp lấy RAM của OS (iOS Jetsam, Linux OOM killer, Windows paging) mà không có tín hiệu cảnh báo.
4. Bộ nhớ chung nhưng không có đồng bộ thì vẫn có data race phần cứng giữa CPU và GPU; trên thiết bị non-coherent còn đọc phải dữ liệu cũ trong cache.

## Options
1. **Giữ nguyên (UMA chỉ là fast-path riêng của Metal trong `T969`)** — *Bị loại*: bỏ sót Windows / Linux / Android UMA, code người dùng phải tự rẽ nhánh theo backend.
2. **Tự động ẩn mọi khác biệt, không cho người dùng biết kiến trúc bộ nhớ** — *Bị loại*: vi phạm nguyên tắc chi phí tường minh (không có chi phí ẩn); người dùng cần biết để chọn chiến lược (ví dụ chia sẻ đọc đồng thời CPU+GPU).
3. **UMA là khái niệm hạng nhất: phân loại tường minh, API thống nhất, runtime tự bỏ copy khi an toàn, compiler kiểm tra quyền truy cập theo miền (Chọn)**.

## Decision
1. **Phân loại kiến trúc bộ nhớ (`SPEC-133`, `T962`, `T963`)**: `GpuAdapterInfo` có thêm `memory_architecture: GpuMemoryArchitecture` với `Discrete | CacheCoherentUma | NonCoherentUma | ReBarHostVisible`, cùng `is_unified_memory: bool` và `unified_pool_bytes: u64`. Nguồn phát hiện:
   - D3D12: `CheckFeatureSupport(D3D12_FEATURE_ARCHITECTURE1)` → `UMA`, `CacheCoherentUMA`.
   - Vulkan: heap/memory type có `DEVICE_LOCAL | HOST_VISIBLE` (kèm `HOST_COHERENT` / `HOST_CACHED`), `VkPhysicalDeviceType` `INTEGRATED_GPU`; ReBAR khi heap `DEVICE_LOCAL | HOST_VISIBLE` phủ toàn bộ VRAM của GPU rời.
   - Metal: `MTLDevice.hasUnifiedMemory`.
   - WebGPU / OpenGL / CPU fallback: báo cáo bảo thủ `Discrete` trừ khi backend xác nhận được UMA.
2. **Cấp phát zero-copy theo backend (`T963`, `T969`)**:
   - D3D12: `D3D12_HEAP_TYPE_CUSTOM` + `D3D12_MEMORY_POOL_L0`, `CPU_PAGE_PROPERTY_WRITE_BACK` khi cache-coherent, `WRITE_COMBINE` khi non-coherent; không tạo `UPLOAD` heap trung gian.
   - Vulkan: persistent-mapped memory type `DEVICE_LOCAL | HOST_VISIBLE`; tự động `vkFlushMappedMemoryRanges` / `vkInvalidateMappedMemoryRanges` tại các điểm chuyển quyền sở hữu khi memory type không `HOST_COHERENT`.
   - Metal: `MTLResourceStorageModeShared`.
3. **Triệt tiêu copy trong `std.gpu.transfer` (`SPEC-131`, `T954`, `T956`)**: trên thiết bị `is_unified_memory`, `UnifiedBuffer<T>`, `upload`, `download`, `.to(device)` không gọi `memcpy`, chỉ chuyển trạng thái miền sở hữu `HostExclusive ↔ DeviceExclusive ↔ SharedRead` và phát barrier / cache maintenance cần thiết. Cùng mã nguồn chạy DMA trên GPU rời và 0-byte copy trên UMA; kết quả quan sát được phải giống nhau (kiểm bằng conformance trong `T957`). Có `TransferStats` (số byte thật sự được copy) để test khẳng định 0 byte trên UMA.
4. **Nhập trang host vào GPU không copy (`T954`, `T956`, `T963`, `T969`)**: `UnifiedBuffer.from_mmap(view<Mmap>)` / `UnifiedBuffer.from_virtual_region(...)` (page-aligned, liên kết E21.6 `T921`/`T922`) qua Metal `newBufferWithBytesNoCopy:length:options:deallocator:`, Vulkan `VK_EXT_external_memory_host`, D3D12 `ID3D12Device3.OpenExistingHeapFromAddress`. Trả về `GpuError.HostImportUnsupported` khi backend không hỗ trợ; không âm thầm copy. Buffer nhập vào giữ khoản mượn trên mapping gốc nên mapping không thể bị `munmap` / drop khi GPU còn dùng.
5. **Kiểm tra data-race CPU↔GPU ở compile time (`SPEC-131`, `T955`)**: với `UnifiedBuffer<T>`, verifier từ chối giữ `mut_view<T>` phía host khi còn `GpuEvent` chưa `.wait()` truy cập cùng buffer, và ngược lại (chẩn đoán mới `AX_GPU_UMA_HOST_DEVICE_RACE`). Cho phép `shared_read_views() -> (view<T>, DeviceView<T>)` để CPU và GPU cùng đọc đồng thời một địa chỉ vật lý, không copy, không khóa.
6. **Ngân sách bộ nhớ hợp nhất (`SPEC-133`, `T956`, `T962`, `T963`)**: `device.memory_budget() -> GpuMemoryBudget { unified_pool_total_bytes, recommended_max_working_set_bytes, current_allocated_bytes, pressure: Normal | Warning | Critical }` từ `MTLDevice.recommendedMaxWorkingSetSize`, `IDXGIAdapter3.QueryVideoMemoryInfo`, `VK_EXT_memory_budget`. Cấp phát vượt `recommended_max_working_set_bytes` trên UMA trả `GpuError.OutOfUnifiedMemoryBudget` thay vì để OS kill tiến trình.

## Consequences
- Tích cực: cùng một chương trình Axiom tận dụng zero-copy trên MacBook/iPhone/iPad, laptop Windows APU / Lunar Lake / Snapdragon X, Android, máy chủ Grace Hopper / MI300A, mà vẫn chạy đúng trên GPU rời. Không thêm phụ thuộc bên thứ ba.
- Chi phí: tăng phạm vi `T954`–`T957`, `T962`, `T963`, `T969`; CI headless kiểm UMA bằng mock adapter của CPU fallback (`memory_architecture` có thể cấu hình), phần cứng thật chỉ kiểm khi có.
- Quản lý: 0 task mới, 0 thay đổi `depends:`; `reqcov.py --strict` và `harness_check.py` phải giữ 0 gaps.

## Sources
- `docs/base/specs/0139 - Part XX — GPU · Accelerator · Device Memory · Kernel.md` §XX.12–14 (UnifiedBuffer, đồng bộ miền tường minh)
- `docs/base/specs/0096 - Axiom — Heterogeneous Computing, GPU & Accelerator v0.1.md`
- `docs/base/tasks/0626 - BOOTSTRAP-367.md`, `docs/base/tasks/0843`, `docs/base/tasks/0845`, `docs/base/tasks/0846`
- ADR-0038 (Metal / UnifiedBuffer Apple Silicon), ADR-0039
