# ADR-0040 — Unified Memory Architecture (UMA), Zero-Copy Host Import & Coherency Verification: Bộ nhớ hợp nhất và nhập bộ nhớ host độc lập phần cứng

Status: accepted (2026-11-10, architect; owner-delegated decision, synthesized revision resolving Red-Team semantics & hardware findings)

## Tóm tắt
- **Yêu cầu của chủ dự án**: "thêm vấn đề về gpu, một số hệ điều hành và dòng máy tính có bộ nhớ unified bao gồm cả ram và vram là 1" — được ghi nhận chính thức thành `REQ-OWNER-009`.
- **Mục tiêu sửa đổi**: Giải quyết triệt để 100% của 39 phát hiện từ hai báo cáo Red-Team (`redteam-uma-semantics.md`: 5 BLOCKER, 11 MAJOR, 6 MINOR; `redteam-uma-hardware.md`: 4 BLOCKER, 10 MAJOR, 3 MINOR).
- **8 Nguyên tắc kiến trúc vàng**:
  1. **Tính hợp lệ của chương trình không bao giờ phụ thuộc vào phần cứng runtime (`B2`)**: Bộ quy tắc kiểm tra an toàn truy cập host↔device áp dụng đồng nhất trên mọi máy (`DiscretePool`, `UnifiedSystemPool`, `CoherentMultiPoolNuma`, `ReBarHostVisible`). Sự khác biệt phần cứng chỉ thay đổi chi phí thực thi (DMA copy vs rào cản bộ nhớ / đồng bộ cache), tuyệt đối không làm thay đổi tính hợp lệ lúc biên dịch.
  2. **Không tạo mô hình sở hữu thứ hai (`B3`, `M4`)**: Loại bỏ hoàn toàn typestate máy ba trạng thái độc lập (`HostExclusive ↔ DeviceExclusive ↔ SharedRead`). Ánh xạ toàn bộ hành vi vào mô hình sở hữu (`OWNED`, `view<T>`, `mut_view<T>`) và token chuyển quyền sở hữu `InFlight<B>` duy nhất của Axiom (`REQ-CONC-095`, `REQ-CONC-096`). Thao tác GPU in-flight tiêu thụ bộ nhớ theo giá trị và trả lại qua `InFlight<B>.wait(self) -> (B, Result<Unit, GpuError>)` trên cả đường thành công và lỗi (bảo toàn quyền sở hữu kể cả khi `DeviceLost`). `Drop` cho `InFlight<B>` chặn deterministic, không có view bên trong nên hợp lệ qua điểm `.await` (`AXS-ASY-034`). Rào cản bộ nhớ và bảo trì cache ở driver chỉ là chi tiết hạ tầng, không phải typestate ngôn ngữ.
  3. **Triệt tiêu copy bảo toàn ngữ nghĩa giá trị (`B1`, `m17`, Hardware Finding 11)**: `upload`, `download`, `device_copy` luôn là phép copy giữa hai vùng sở hữu riêng biệt (giữ nguyên ngữ nghĩa giá trị trên mọi kiến trúc; trên UMA chúng là `memcpy` RAM→RAM, không có staging buffer thứ hai). Copy được triệt tiêu **chỉ** cho các phép chuyển miền trên cùng một đối tượng hoặc tiêu thụ nguồn theo giá trị: (a) acquire/release miền của cùng một `UnifiedBuffer<T>`; (b) `.into_device(self)` / `.into_host(self)`; (c) `.to(device)` / `.to_async(device)` nhận `self` theo giá trị (nguồn bị move, tiêu thụ place cũ theo `REQ-OPT-347`); (d) `shared_read_views()`. Triệt tiêu copy tuyến tính **chỉ áp dụng cho 1D linear buffer**; các tài nguyên dạng ảnh/texture 2D/3D (`DeviceImage`, `Texture2D`) bắt buộc phải thực hiện layout swizzling/tiling thông qua GPU blit/copy engine ngay cả trên UMA. `TransferStats` ghi nhận chính xác `bytes_copied == len * size_of::<T>()` cho `upload`/`download`, và `bytes_copied == 0` cho chuyển miền by-move.
  4. **Phân loại cấu trúc liên kết bộ nhớ trực giao (`M15`, Hardware Findings 4, 5, 6)**: Thay thế enum 4 nhánh gộp (`Discrete | CacheCoherentUma | NonCoherentUma | ReBarHostVisible`) bằng các trường mô tả trực giao trên `GpuAdapterInfo`: `memory_topology: GpuMemoryTopology = DiscretePool | UnifiedSystemPool | CoherentMultiPoolNuma`, cờ per-heap / per-memory-type `HeapFlags = DeviceLocal | HostVisible | HostCoherent | HostCached`, kích thước `rebar_aperture_bytes: u64` phân biệt Resizable BAR thực sự với legacy 256 MiB PCIe BAR aperture, và phân loại chính xác NVIDIA Grace Hopper / AMD MI300A là kiến trúc `CoherentMultiPoolNuma` (GPU HBM3 và CPU LPDDR5X kết nối qua NVLink-C2C/Infinity Fabric là hai pool riêng có độ chênh lệch băng thông 8x).
  5. **Nhập bộ nhớ host an toàn kiểu & xử lý rủi ro hệ điều hành (`M7`, `M8`, Hardware Findings 3, 7, 8, 10)**: Cung cấp API `HostImport`: `HostImport.read<T: PlainData>(src: view<Mmap>) -> Result<ImportedDeviceView<T>, GpuError>`, `HostImport.write<T: PlainData>(src: mut_view<MmapMut>) -> Result<ImportedDeviceMutView<T>, GpuError>`, và `HostImport.region<T: PlainData>(src: mut_view<VirtualRegion>, offset: usize, len: usize) -> Result<ImportedDeviceMutView<T>, GpuError>`, cùng hỗ trợ Android `AHardwareBuffer` (`VK_ANDROID_external_memory_android_hardware_buffer`) và Linux `dma-buf` (`VK_EXT_external_memory_dma_buf`). `ImportedDeviceView`/`MutView` là kiểu non-owning chứa stored view mượn từ mapping gốc (`AXS-CAP-006`), ngăn chặn tĩnh `munmap`/`decommit`/`protect` khi GPU còn dùng (`AX_CAP_OUTLIVES_OWNER`). Căn lề runtime đạt `max(page_size(), minImportedHostPointerAlignment)` (64 KiB trên Vulkan/Mesa, 16 KiB trên Apple Silicon Metal; độ dài phải là bội số của 16 KiB trên Metal). D3D12 dùng `OpenExistingHeapFromFileMapping` cho Win32 file mapping vs `OpenExistingHeapFromAddress` cho `VirtualAlloc`. Từ chối `MmapCow` mutable GPU import.
  6. **Độ chính xác API phần cứng (Hardware Findings 1, 2, 9, 12, 13, 14, 15, 16, 17)**:
     - D3D12: Khởi tạo tường minh `D3D12_FEATURE_DATA_ARCHITECTURE1.NodeIndex = 0` (hoặc node index từ `DeviceId`) trước khi gọi `CheckFeatureSupport`.
     - D3D12 Heaps: Phân biệt rõ UMA (`D3D12_HEAP_TYPE_CUSTOM` + `D3D12_MEMORY_POOL_L0`) và ReBAR (`D3D12_MEMORY_POOL_L1` với `CPU_PAGE_PROPERTY_WRITE_COMBINE` qua `D3D12_HEAP_TYPE_GPU_UPLOAD`; tuyệt đối không dùng `MEMORY_POOL_L0` cho ReBAR VRAM).
     - Thuộc tính trang host: `HostAccessPattern = WriteOnly | ReadOnly | ReadWrite`. `WriteOnly` dùng `WRITE_COMBINE` / uncached; `ReadOnly`/`ReadWrite` (kể cả `shared_read_views`) bắt buộc dùng memory type có CPU caching (`CPU_PAGE_PROPERTY_WRITE_BACK` trên D3D12, `HOST_CACHED` trên Vulkan) kèm rào cản / invalidate tường minh trên phần cứng non-coherent để ngăn chặn sụt giảm 90–99% thông lượng đọc của CPU.
     - Vulkan: Phát flush/invalidate (`vkFlushMappedMemoryRanges` / `vkInvalidateMappedMemoryRanges`) khi và chỉ khi memory type của allocation thiếu cờ `VK_MEMORY_PROPERTY_HOST_COHERENT_BIT`.
     - DXGI: Trên UMA, toàn bộ bộ nhớ được ánh xạ dưới `DXGI_MEMORY_SEGMENT_GROUP_LOCAL`; bỏ qua `NON_LOCAL` (luôn trả về 0).
     - Ngân sách bộ nhớ thống nhất: Một lỗi duy nhất `GpuError.OutOfDeviceMemory { requested_bytes: u64, budget: GpuMemoryBudget }` với `AllocPolicy = Advisory | StrictBudget`. Tích hợp nguồn áp lực OS (Apple GCD `DISPATCH_SOURCE_TYPE_MEMORYPRESSURE` + `os_proc_available_memory` chống iOS Jetsam kill, Android `onTrimMemory`, Windows WDDM budget change events, Linux PSI).
  7. **Hợp đồng khả chuyển & kiểm thử headless (Finding 14, M9)**: Oracle `--interp` và CPU fallback dùng cấu hình mặc định cố định `UnifiedSystemPool`. Mock adapter của CPU fallback hỗ trợ giả lập non-coherent cache poisoning (`MOCK_STALE_CACHE_READ` nếu CPU đọc trước khi invalidate). Headless CI kiểm thử trên software ICDs thật: Microsoft WARP (`d3d10warp.dll`) trên Windows và Mesa Lavapipe (`lvp_icd.json`) trên Linux.
  8. **Cơ cấu board & Epic chuyên biệt `E22.10` (`B5`, `B6`, `M13`, `m22`)**: Tách toàn bộ phạm vi UMA chuyên sâu khỏi `T956` và `T963` thành Epic mới: **`E22.10 Unified Memory Architecture (UMA), Zero-Copy Host Import & Coherency Verification`** gồm 4 task (`T989`–`T992`) nối vào gate `T322`. Thiết lập phụ thuộc chuẩn xác đến E21.6 `T921`/`T922` cho các tác vụ nhập bộ nhớ ảo; giữ `reqcov.py --strict` 0 gaps với `REQ-OWNER-009` và `REQ-OPT-347`.

---

## Context
Các dòng phần cứng hiện đại ngày càng hội tụ bộ nhớ giữa CPU và GPU, nhưng kiến trúc vật lý và ngữ nghĩa cache rất đa dạng:
1. **Apple Silicon M1–M4 (macOS), A14–A18 (iOS/iPadOS)**: Bộ nhớ vật lý chia sẻ 100% (`UnifiedSystemPool`), hardware cache-coherent cấp chip, trang ảo 16 KiB (`vm_page_size = 16384`), bộ nhớ có thể vượt `recommendedMaxWorkingSetSize` trên macOS nhờ swap/compression nhưng bị giám sát gắt gao bởi tiến trình Jetsam trên iOS/iPadOS.
2. **AMD Ryzen APU / Strix Halo, Intel Core Ultra / Lunar Lake**: CPU và iGPU chia sẻ DDR5/LPDDR5 qua LLC/IOMMU (`UnifiedSystemPool`). Trên Vulkan/D3D12 hỗ trợ bộ nhớ persistent mapped host-visible device-local; một số memory type hỗ trợ CPU snooping (`HOST_COHERENT`), trong khi một số memory type cached đòi hỏi flush/invalidate tường minh.
3. **NVIDIA Grace Hopper (GH200) / Grace Blackwell (GB200) & AMD Instinct MI300A**: Tích hợp CPU và GPU qua bus liên kết coherent tốc độ cao (NVLink-C2C 900 GB/s hoặc Infinity Fabric). Đây **không phải là single-pool UMA**: hệ thống gồm hai pool vật lý riêng biệt (`CoherentMultiPoolNuma`): LPDDR5X trên CPU (~500 GB/s) và HBM3/HBM3e trên GPU (~4,000 GB/s). Truy cập chéo là cache-coherent nhưng chênh lệch băng thông 8x; việc gộp chung dung lượng vào một số đo duy nhất là sai lầm kỹ thuật nghiêm trọng.
4. **Qualcomm Snapdragon X Elite / Adreno & ARM Mali trên Android/Linux**: Bộ nhớ vật lý chia sẻ nhưng thường **non-coherent** giữa CPU L2 và GPU shader cores. Đòi hỏi quản lý invalidate cache khắt khe khi CPU đọc lại dữ liệu; cơ chế chia sẻ zero-copy chuẩn trên Android là `AHardwareBuffer` (`gralloc`), trên Linux là `dma-buf`.
5. **GPU rời có Resizable BAR (AMD Smart Access Memory / PCIe ReBAR)**: Không phải UMA (VRAM nằm trên card riêng), nhưng CPU có thể ánh xạ trực tiếp toàn bộ VRAM qua PCIe aperture (`ReBarHostVisible`). Trên bo mạch không bật ReBAR, chuẩn PCIe vẫn để lại một cửa sổ legacy 256 MiB BAR, không được nhầm lẫn với ReBAR toàn phần.

Hậu quả nếu coi mọi GPU là GPU rời hoặc áp dụng trừu tượng UMA ngây thơ:
- Sao chép thừa RAM→RAM tốn gấp đôi bộ nhớ và nghẽn băng thông memory bus.
- Ghi đè bộ nhớ đang được GPU đọc do copy elision sai ngữ nghĩa giá trị.
- Crash phần cứng do import vùng nhớ sai căn lề (Mesa Vulkan đòi hỏi tới 64 KiB; Metal đòi hỏi 16 KiB và độ dài bội số 16 KiB).
- Sụp đổ 90–99% hiệu năng đọc của CPU khi dùng thuộc tính Write-Combine cho các vùng đọc lại (`shared_read_views`, readback).
- Bị OS kill đột ngột (iOS Jetsam, Linux OOM-killer) do thiếu tích hợp cảnh báo áp lực bộ nhớ OS.
- Kiểm thử headless CI bị rỗng (vacuous pass) vì CPU fallback thuần không bắt được lỗi thiếu invalidate cache của phần cứng non-coherent.

---

## Options
1. **Giữ nguyên bản nháp sơ khai (UMA chỉ là fast-path riêng của Metal trong `T969` hoặc cờ boolean gộp)** — *Bị loại*: Bỏ sót Windows / Linux / Android UMA, conflate các thuộc tính độc lập, chứa 39 lỗi ngữ nghĩa và API phần cứng đã bị Red-Team chỉ rõ.
2. **Ẩn giấu hoàn toàn kiến trúc phần cứng sau tầng trừu tượng tự động** — *Bị loại*: Vi phạm nguyên tắc chi phí tường minh của Axiom (không có chi phí ẩn); ngăn cản lập trình viên khai thác tối đa năng lực zero-copy khi nạp mô hình AI hàng chục GB.
3. **Mô hình kiến trúc trực giao, ánh xạ sở hữu chuẩn Axiom, zero-copy bảo toàn giá trị, API phần cứng chuẩn xác và thành lập Epic chuyên biệt E22.10 (Chọn)**: Giải quyết toàn diện 100% 39 phát hiện Red-Team, chuẩn hóa cấu trúc board và đáp ứng xuất sắc chỉ thị của Chủ dự án.

---

## Decision

### 1. Phân loại cấu trúc liên kết bộ nhớ trực giao (`SPEC-131`, `SPEC-133`, `SPEC-139`)
Thay thế enum gộp 4 nhánh bằng mô tả cấu trúc trực giao:
```axiom
enum GpuMemoryTopology {
    DiscretePool,                // VRAM rời riêng biệt qua PCIe bus
    UnifiedSystemPool,           // RAM hệ thống dùng chung vật lý (Apple Silicon, APU, Lunar Lake, Snapdragon)
    CoherentMultiPoolNuma,       // Hai pool vật lý riêng biệt (HBM3 + LPDDR5X) kết nối coherent qua NVLink-C2C/Infinity Fabric
}

struct GpuMemoryHeapInfo {
    index: usize,
    size_bytes: u64,
    flags: HeapFlags,            // DeviceLocal | HostVisible | HostCoherent | HostCached
    numa_node: Option<u32>,
}

struct GpuAdapterMemoryInfo {
    topology: GpuMemoryTopology,
    is_unified_memory: bool,     // helper method: topology != DiscretePool
    rebar_aperture_bytes: u64,   // > 256 MiB mới xác nhận là ReBAR toàn phần
    heaps: Vec<GpuMemoryHeapInfo>,
}
```
**Quy tắc phát hiện per-backend (`SPEC-133` §4, `SPEC-139` §2)**:
- **Direct3D 12**:
  - Khởi tạo tường minh struct: `D3D12_FEATURE_DATA_ARCHITECTURE1 arch = {}; arch.NodeIndex = 0;` (hoặc `node_index` từ `DeviceId`).
  - Gọi `CheckFeatureSupport(D3D12_FEATURE_ARCHITECTURE1, &arch, sizeof(arch))`. Nếu `arch.UMA == TRUE`: `topology = UnifiedSystemPool`.
  - Kiểm tra ReBAR: Trên adapter discrete (`arch.UMA == FALSE`), truy vấn `DXGI_ADAPTER_DESC1` và `QueryVideoMemoryInfo` trên `DXGI_MEMORY_SEGMENT_GROUP_LOCAL`. Nếu CPU host-visible aperture > 256 MiB (268,435,456 bytes), ghi nhận `rebar_aperture_bytes` tương ứng.
- **Vulkan**:
  - Duyệt `VkPhysicalDeviceMemoryProperties`: kiểm tra từng memory heap và memory type.
  - Phân loại `UnifiedSystemPool` khi `VkPhysicalDeviceType == VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU` và có heap vừa `DEVICE_LOCAL` vừa `HOST_VISIBLE`.
  - Phân loại `CoherentMultiPoolNuma`: nhận diện Grace Hopper / MI300A qua PCI IDs (`0x10DE` / `0x1002`) và kiến trúc NUMA báo cáo từ driver; ghi nhận pool HBM3 và pool LPDDR5X tách biệt.
  - Phân biệt ReBAR: Memory type `DEVICE_LOCAL | HOST_VISIBLE` trên dGPU phải có kích thước heap hoặc budget từ `VK_EXT_memory_budget` > 256 MiB. Nếu <= 256 MiB, đây chỉ là legacy BAR aperture, gắn `DiscretePool` với staging giới hạn.
- **Apple Metal**:
  - `MTLDevice.hasUnifiedMemory == true` -> `UnifiedSystemPool` (cache-coherent).
- **WebGPU / OpenGL / CPU Fallback**:
  - WebGPU: luôn báo cáo `DiscretePool`, `supports_host_import = false` do sandbox W3C. Hỗ trợ fast-path `GPUBufferDescriptor.mappedAtCreation = true`.
  - OpenGL: báo cáo `DiscretePool`. Khi có `GL_ARB_buffer_storage` / persistent mapping: sử dụng cờ `GL_MAP_PERSISTENT_BIT`; nếu thiếu `GL_MAP_COHERENT_BIT`, phát `glMemoryBarrier(GL_CLIENT_MAPPED_BUFFER_BARRIER_BIT)` hoặc `glFlushMappedBufferRange`.
  - CPU Fallback & Software Rasterizer: mặc định `UnifiedSystemPool` (`host_coherent = true`), có cờ cấu hình mock adapter cho CI.

### 2. Ánh xạ vào mô hình sở hữu duy nhất của Axiom & `InFlight<B>` (`SPEC-131`, `SPEC-139`)
Loại bỏ hoàn toàn máy trạng thái miền riêng biệt (`REQ-CONC-096`). Quy định ánh xạ chuẩn:
- **HostExclusive**: Host sở hữu giá trị (`OWNED`) hoặc đang giữ `mut_view<T>`.
- **DeviceExclusive**: Bộ nhớ đã được chuyển quyền sở hữu (move) vào thao tác GPU in-flight thông qua kiểu bao bọc `InFlight<B>`:
  ```axiom
  struct InFlight<B> {
      handle: GpuInFlightHandle,
      buffer: B,                 // Buffer được move vào đây, không thể truy cập từ host khi in-flight
  }

  impl<B> InFlight<B> {
      fn wait(self) -> (B, Result<Unit, GpuError>);
      fn is_completed(view<Self>) -> bool;
  }
  ```
  - `InFlight<B>.wait(self)` trả lại quyền sở hữu của buffer `B` trên **cả hai nhánh Ok và Err** (kể cả khi `GpuError.DeviceLost`, nội dung có thể mất nhưng place không bị rò rỉ).
  - `Drop for InFlight<B>` tự động đồng bộ chặn (deterministic blocking wait) trước khi giải phóng, ngăn chặn GPU ghi vào bộ nhớ đã bị thu hồi.
  - `InFlight<B>` không chứa view nội bộ, hoàn toàn hợp lệ khi nắm giữ xuyên qua điểm `.await` trong async task (`SPEC-33` AXS-ASY-034).
- **SharedRead**: Đồng thời tồn tại host `view<T>` và `DeviceView<T>` cùng nguồn gốc (tuân thủ quy tắc read-read của `SPEC-11` AXS-CAP-003).

### 3. Triệt tiêu copy bảo toàn ngữ nghĩa giá trị & `TransferStats` (`SPEC-131`, `T956`, `T990`)
- **Bảo toàn ngữ nghĩa giá trị**: `upload(src: view<[T]>, dst: mut_view<DeviceBuffer<T>>)` và `download(...)` luôn là phép sao chép dữ liệu giữa hai vùng nhớ độc lập. Trên UMA, runtime thực hiện `memcpy` trực tiếp trong RAM (không cấp phát staging buffer trung gian), nhưng **không bao giờ aliasing hai place khác nhau**.
- **Điều kiện triệt tiêu copy (Zero-Copy Elision)**:
  1. Handoff miền trên cùng một đối tượng `UnifiedBuffer<T>`: chuyển đổi quyền truy cập giữa host và device không copy dữ liệu.
  2. Phép chuyển đổi by-move: `UnifiedBuffer.into_device(self) -> DeviceBuffer<T>` và `DeviceBuffer.into_host(self) -> UnifiedBuffer<T>`.
  3. Tensor / Buffer `.to(device)` / `.to_async(device)` nhận `self` theo giá trị (place cũ bị tiêu thụ theo `REQ-OPT-347`).
  4. `shared_read_views() -> (view<T>, DeviceView<T>)`.
- **Loại trừ Texture / Ảnh 2D/3D (Hardware Finding 11)**:
  Triệt tiêu copy trên UMA **chỉ áp dụng cho 1D linear buffer**. Các tài nguyên dạng `Texture1D/2D/3D`, `DeviceImage` có layout phần cứng dạng micro-tiled / Morton Z-swizzled. Mọi thao tác tải ảnh lên texture hoặc đọc texture về host bắt buộc phải chạy layout conversion blit của GPU engine ngay cả trên UMA.
- **Bộ đếm hiệu năng `TransferStats`**:
  ```axiom
  struct TransferStats {
      bytes_copied: u64,             // Số byte thực sự copy (RAM->RAM hoặc PCIe)
      bytes_written_over_bus: u64,   // Số byte CPU ghi qua ReBAR aperture
      cache_flushes: u32,            // Số lần phát flush cache CPU
      cache_invalidates: u32,        // Số lần phát invalidate cache CPU
  }
  ```
  `TransferStats` là số liệu profiling hiệu năng, không thuộc kết quả quan sát ngữ nghĩa của chương trình.

### 4. Nhập bộ nhớ host an toàn kiểu & xử lý rủi ro hệ điều hành (`SPEC-131`, `SPEC-139`, `T990`, `T991`)
Thay thế hàm `UnifiedBuffer.from_mmap` bằng API nhập trang có kiểu chuẩn xác:
```axiom
struct HostImport;

impl HostImport {
    fn read<T: PlainData>(src: view<Mmap>) -> Result<ImportedDeviceView<T>, GpuError>;
    fn write<T: PlainData>(src: mut_view<MmapMut>) -> Result<ImportedDeviceMutView<T>, GpuError>;
    fn region<T: PlainData>(src: mut_view<VirtualRegion>, offset: usize, len: usize) -> Result<ImportedDeviceMutView<T>, GpuError>;
}
```
**Các ràng buộc an toàn bắt buộc**:
1. **Kiểm tra căn lề và độ dài (Hardware Findings 7, 8)**:
   - Địa chỉ bắt đầu phải thỏa mãn: `addr % max(page_size(), device.min_host_import_alignment()) == 0`.
   - Trên Vulkan: `min_host_import_alignment` lấy từ `VkPhysicalDeviceExternalMemoryHostPropertiesEXT::minImportedHostPointerAlignment` (có thể lên tới 64 KiB trên Mesa/AMD).
   - Trên Apple Silicon Metal: con trỏ bắt buộc căn lề `vm_page_size` (16 KiB) và `length` **bắt buộc là bội số của `vm_page_size`**. Nếu file mapping có kích thước không chẵn trang, phải có anonymous padding hợp lệ, nếu không trả về `GpuError.HostImportMisaligned`.
   - Kiểm tra kiểu dữ liệu: `offset % align_of::<T>() == 0` và `len % size_of::<T>() == 0`; kiểu `T` phải thỏa mãn ràng buộc `PlainData` (`SPEC-51`).
2. **Xử lý rủi ro hệ điều hành (Semantics Finding 8, Hardware Finding 3)**:
   - **Cấm `MmapCow`**: Giao diện GPU DMA không kích hoạt CPU Copy-on-Write page fault. Nhập `MmapCow` trả về `GpuError.HostImportUnsupported` trừ khi được chuyển thành private resident trước.
   - **Bảo vệ trang `VirtualRegion`**: Các phương thức `protect`, `decommit`, `unlock_pages` nhận `mut_view<VirtualRegion>`. Khi một `ImportedDeviceView` đang tồn tại (nắm giữ borrow trên mapping), quy tắc capability borrow (`AXS-CAP-003`) sẽ tĩnh loại trừ việc gọi các hàm thay đổi bảo vệ trang này (`AX_CAP_CONFLICT_MUT`).
   - **Cắt ngắn file (File Truncation)**: Trên Windows, file mapping được mở với share mode từ chối ghi bên ngoài; trên POSIX, nếu file bị cắt ngắn ngoài ý muốn dẫn đến bus fault của GPU, driver bắt lỗi và trả về `GpuError.DeviceLost { cause: GpuDeviceLossCause.HostPageFault }`, loại trừ Undefined Behavior.
   - **Direct3D 12 Host Import (Hardware Finding 3)**:
     - Với `VirtualRegion` (`VirtualAlloc`): dùng `ID3D12Device3::OpenExistingHeapFromAddress`.
     - Với file-backed `Mmap`: bắt buộc dùng Win32 file mapping HANDLE qua `ID3D12Device3::OpenExistingHeapFromFileMapping`. Nếu chỉ có con trỏ thô, trả về `GpuError.HostImportUnsupported`.
   - **Android & Linux Zero-Copy (Hardware Finding 10)**:
     - Android: Bổ sung hỗ trợ `VK_ANDROID_external_memory_android_hardware_buffer` (`AHardwareBuffer`).
     - Linux: Bổ sung hỗ trợ `VK_EXT_external_memory_dma_buf` (`dma-buf`).

### 5. Quy tắc chống race host↔device độc lập phần cứng & chẩn đoán (`SPEC-131`, `SPEC-139`, `T955`)
- **Nguyên tắc độc lập phần cứng (`B2`)**: Áp dụng cho mọi vùng nhớ mà cả host và device đều có thể truy cập — `UnifiedBuffer<T>`, `PinnedHostBuffer<T>`, host import, và `ReBarHostVisible` mapped memory — trên **tất cả** các kiến trúc.
- **Quy tắc**: Không được tồn tại đồng thời `mut_view` phía host với một thao tác GPU in-flight trên cùng một place, và ngược lại.
- **Báo lỗi chẩn đoán (`M11`)**:
  - Vi phạm được báo bằng mã capability chuẩn: `AX_CAP_CONFLICT_MUT` hoặc `AX_CAP_CONFLICT_READ` kèm note chẩn đoán `gpu_in_flight` (payload `data.gpu_op`).
  - Đăng ký mã chẩn đoán chính thức trong nhóm `GPU`: `AX_GPU_HOST_DEVICE_ACCESS_CONFLICT` trong `spec/diagnostics.md` §3 và §11 (do task `T954` đăng ký, `T955` phát ra, lock `compiler/diag/code.ax` và `compiler/diag/format.ax`).
  - Cho phép `shared_read_views() -> (view<T>, DeviceView<T>)` trên mọi kiến trúc (trên `DiscretePool`, driver sử dụng pinned host memory truy cập qua PCIe bus mà không báo lỗi kiến trúc).

### 6. Thuộc tính trang host & phòng chống sụt giảm hiệu năng đọc (`SPEC-133`, `SPEC-139`, Hardware Findings 2, 12)
Khi cấp phát bộ nhớ host-visible, bắt buộc khai báo mẫu truy cập host:
```axiom
enum HostAccessPattern {
    WriteOnly,     // CPU ghi tuần tự, GPU đọc (Upload) -> WRITE_COMBINE / Uncached
    ReadOnly,      // GPU ghi, CPU đọc (Readback) -> WRITE_BACK / HOST_CACHED
    ReadWrite,     // CPU và GPU cùng đọc/ghi hoặc shared_read_views -> WRITE_BACK / HOST_CACHED
}
```
- **Phòng chống sụp đổ hiệu năng đọc (Hardware Finding 12)**: CPU đọc từ bộ nhớ `WRITE_COMBINE` bị vô hiệu hóa cache L1/L2/L3 và bộ prefetcher, làm thông lượng đọc giảm 90% đến 99%. Do đó, `ReadOnly` và `ReadWrite` bắt buộc phải sử dụng trang nhớ cached (`CPU_PAGE_PROPERTY_WRITE_BACK` trên D3D12, `HOST_CACHED` trên Vulkan).
- **Đồng bộ cache trên phần cứng Non-Coherent (Hardware Finding 4)**:
  - Khi memory type thiếu cờ `VK_MEMORY_PROPERTY_HOST_COHERENT_BIT`:
    * Sau khi CPU ghi: phát `vkFlushMappedMemoryRanges`.
    * Trước khi CPU đọc: phát `vkInvalidateMappedMemoryRanges`.
  - Trên D3D12: thực hiện invalidation thông qua `ID3D12Resource::Map` / `Unmap` subresource range.
- **Direct3D 12 Custom Heap vs ReBAR (Hardware Finding 2)**:
  - Trên UMA (`arch.UMA == TRUE`): Sử dụng `D3D12_HEAP_TYPE_CUSTOM` + `D3D12_MEMORY_POOL_L0`.
  - Trên ReBAR (`arch.UMA == FALSE`, có ReBAR): Bắt buộc cấp phát trong **`D3D12_MEMORY_POOL_L1`** với `CPU_PAGE_PROPERTY_WRITE_COMBINE` (dùng `D3D12_HEAP_TYPE_GPU_UPLOAD` trên Agility SDK hoặc custom heap L1). **Tuyệt đối không dùng `MEMORY_POOL_L0` cho ReBAR VRAM**.

### 7. Ngân sách bộ nhớ thiết bị thống nhất & tích hợp áp lực hệ điều hành (`SPEC-133`, `SPEC-139`, `T962`, `T991`)
- **Lỗi thống nhất trên mọi kiến trúc (`M10`)**:
  Loại bỏ mã lỗi riêng `OutOfUnifiedMemoryBudget`. Mọi kiến trúc sử dụng chung:
  ```axiom
  enum GpuError {
      OutOfDeviceMemory { requested_bytes: u64, budget: GpuMemoryBudget },
      HostImportUnsupported,
      HostImportMisaligned,
      DeviceLost { cause: GpuDeviceLossCause },
  }
  ```
- **Chính sách cấp phát (`AllocPolicy`)**:
  - `Advisory` (mặc định): Cấp phát chỉ thất bại khi driver hoặc kernel từ chối. Vượt ngưỡng khuyến nghị chỉ kích hoạt cảnh báo áp lực `pressure: Warning | Critical`.
  - `StrictBudget`: Chủ động từ chối cấp phát khi tổng bộ nhớ vượt `recommended_max_working_set_bytes`.
- **Tích hợp nguồn áp lực hệ điều hành (Hardware Findings 9, 13, 15)**:
  - **Tỷ lệ áp lực**: `usage_ratio = current_allocated_bytes / recommended_max_working_set_bytes`. `Normal` (< 75%), `Warning` (75%–90%), `Critical` (> 90%).
  - **Windows**: Lắng nghe sự kiện qua `IDXGIAdapter3::RegisterVideoMemoryBudgetChangeNotificationEvent`. Trên UMA, toàn bộ truy vấn ngân sách nhắm vào `DXGI_MEMORY_SEGMENT_GROUP_LOCAL` (`NON_LOCAL` luôn trả về 0, Hardware Finding 13).
  - **macOS / iOS**: Tích hợp Grand Central Dispatch `DISPATCH_SOURCE_TYPE_MEMORYPRESSURE`. Trên iOS/iPadOS, truy vấn `os_proc_available_memory()` để chặn đứng việc bị tiến trình Jetsam kill.
  - **Linux / Android**: Giám sát Pressure Stall Information (PSI qua `/proc/pressure/memory`) trên Linux và `ComponentCallbacks2.onTrimMemory` trên Android.

### 8. Hợp đồng khả chuyển (Portability Contract) & Kiểm thử CI không phụ thuộc GPU vật lý (`SPEC-139`, `T992`)
1. **Hợp đồng khả chuyển (`M9`)**:
   - Mọi chương trình Axiom hợp lệ đều biên dịch và chạy đúng trên mọi kiến trúc đồ họa.
   - Các API `UnifiedBuffer`, `shared_read_views`, `HostImport` tồn tại trên tất cả nền tảng; khác biệt duy nhất nằm ở chi phí thực thi và năng lực driver.
   - Oracle `--interp` và CPU software fallback luôn sử dụng topology chuẩn xác định (`UnifiedSystemPool`, `host_coherent = true`, `supports_host_import = true`).
2. **Kiểm thử Headless CI không phụ thuộc GPU vật lý (Hardware Finding 14)**:
   - **Giả lập Non-Coherent Cache Poisoning**: CPU fallback backend có chế độ kiểm thử bộ nhớ non-coherent: khi GPU ảo ghi dữ liệu, vùng nhớ được đánh dấu `PoisonedForCpu`. Nếu CPU đọc dữ liệu trước khi lệnh `cache_invalidate` được phát ra, bài test sẽ báo lỗi ngay lập tức (`MOCK_STALE_CACHE_READ`).
   - **Chạy trên Software ICD thật trong CI**: Sử dụng **Microsoft WARP (`d3d10warp.dll`)** trên Windows và **Mesa Lavapipe (`VK_ICD_FILENAMES=.../lvp_icd.json`)** trên Linux để xác minh toàn bộ các lệnh D3D12 và Vulkan UMA thực thụ mà không cần card màn hình vật lý.

---

## Consequences
- **Tích cực**:
  - Giải quyết triệt để 100% của 39 phát hiện Red-Team (22 về ngữ nghĩa & 17 về phần cứng).
  - Tạo nền tảng zero-copy vững chắc cho AI/LLM inference tải mô hình 30+ GB thẳng từ file mmap vào bộ nhớ chia sẻ mà không tốn thêm 1 byte RAM.
  - Đảm bảo tính độc lập phần cứng: mã nguồn hợp lệ chạy an toàn từ iPhone/iPad, Mac Apple Silicon, laptop Windows Copilot+ (Snapdragon X / Lunar Lake / Strix Halo), máy chủ Grace Hopper / MI300A cho đến GPU rời cao cấp.
- **Cơ cấu Board & Quản lý Task (`B5`, `B6`, `M13`, `m22`)**:
  - Không nhồi nhét quá tải vào `T956` và `T963`.
  - Thành lập Epic mới **`E22.10 Unified Memory Architecture (UMA), Zero-Copy Host Import & Coherency Verification`** với 4 task chuẩn kích thước:
    * `T989`: Canonical UMA, Host Import & Memory Topology Specification (`SPEC-139`).
    * `T990`: `std.gpu.uma`: `UnifiedBuffer` domain handoff, copy elision & `HostImport` types.
    * `T991`: UMA backend drivers: Vulkan, D3D12, Metal, `AHardwareBuffer`, `dma-buf` & OS memory pressure.
    * `T992`: UMA conformance: 4-topology test matrix, simulated non-coherent cache poisoning & WARP/Lavapipe CI.
  - Sửa đổi đồ thị phụ thuộc chuẩn xác: Thêm cạnh phụ thuộc từ các task host import (`T955`, `T969`, `T990`) sang các task quản lý bộ nhớ ảo của P21 (`T921`, `T922`), và cập nhật dòng P22 trong `spec/ROADMAP.md` phản ánh `needs P11, P12, P16, E21.6`.
  - Nối `T989`–`T992` vào gate `T322`.
  - Đăng ký `REQ-OWNER-009` trong `spec/requirements/OWNER.md` và `spec/requirements/CATALOG.md`; bảo toàn `reqcov.py --strict` 0 gaps và `harness_check.py` PASS.

---

## Sources
- `docs/base/specs/0139 - Part XX — GPU · Accelerator · Device Memory · Kernel.md` §XX.6–18, §XX.29–44
- `docs/base/specs/0096 - Axiom — Heterogeneous Computing, GPU & Accelerator v0.1.md`
- `docs/base/tasks/0626 - BOOTSTRAP-367.md`, `docs/base/tasks/0843`, `docs/base/tasks/0845`, `docs/base/tasks/0846`
- Microsoft Learn: Direct3D 12 Hardware Architecture, `D3D12_FEATURE_DATA_ARCHITECTURE1`, Custom Heaps, `ID3D12Device3::OpenExistingHeapFromFileMapping`
- Khronos Vulkan 1.3 Specification: `VK_EXT_external_memory_host`, `VK_EXT_memory_budget`, `VK_ANDROID_external_memory_android_hardware_buffer`, `VK_EXT_external_memory_dma_buf`
- Apple Developer Documentation: Metal Feature Set Tables, `MTLDevice.hasUnifiedMemory`, `newBufferWithBytesNoCopy:length:options:deallocator:`
- Linux Kernel DRM/KMS `dma-buf` Subsystem; Android NDK `AHardwareBuffer` specification
- NVIDIA Grace Hopper Superchip Architecture Whitepaper; AMD CDNA3 / MI300A Architecture Whitepaper
- `_workspaces/reports/redteam-uma-semantics.md` (22 findings resolved)
- `_workspaces/reports/redteam-uma-hardware.md` (17 findings resolved)
- Requirements: `REQ-OWNER-009`, `REQ-OPT-347`, `REQ-SIMD-147` (ANUM-82), `REQ-CONC-096`, `REQ-COL-074`
