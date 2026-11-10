# Red-team review — ADR-0040 UMA: language semantics, ownership/capability fit, board consistency

Reviewed: commit `57b7c8e6` (`spec/decisions/ADR-0040-unified-memory-architecture-uma.md`, amendments to
`T954`, `T955`, `T956`, `T957`, `T962`, `T963`, `T969`, `spec/ROADMAP.md`, `spec/INDEX.md`).
Cross-checked against `CLAUDE.md`, `spec/ROADMAP.md` (P21/P22), `spec/decisions/ADR-0011-diagnostic-code-taxonomy.md`,
`spec/diagnostics.md` §3, `spec/decisions/ADR-0038-*.md`, `spec/SPEC-10-ownership.md`, `spec/SPEC-11-capability.md`,
`spec/invariants.md` (`INV-DET-*`), `spec/requirements/CATALOG.md`, `spec/requirements/OWNER.md`, `T920`–`T923`,
`T950`–`T988`, `T321`, `T322`.

Angle: language semantics, ownership/capability model fit, plan/board consistency. No spec/task file was edited.

---

## 1. BLOCKER — "Copy elision" of `upload` / `download` contradicts value semantics; "identical observable results" is false as written

**Target.** ADR-0040 Decision §3: "trên thiết bị `is_unified_memory`, `UnifiedBuffer<T>`, `upload`, `download`, `.to(device)`
không gọi `memcpy`, chỉ chuyển trạng thái miền sở hữu `HostExclusive ↔ DeviceExclusive ↔ SharedRead` … kết quả quan sát được
phải giống nhau". Same text in `T954` scope bullet ("`upload` / `download` / `.to(device)` only change the domain state …") and
`T956` scope bullet ("`UnifiedBuffer<T>` and `std/gpu/transfer` elide copies on `is_unified_memory` devices") and `T956`
acceptance ("`upload` / `download` / `.to(device)` report `TransferStats.bytes_copied == 0` with results identical to the
`Discrete` path").

**Why.** `upload(src: view<[T]>, dst: mut_view<DeviceBuffer<T>>)` and `download(...)` are *copy* operations between two
distinct owned allocations (`T956` scope: `DeviceBuffer<T>` owns device storage; the host slice remains owned by the caller).
After `upload`, the caller may legally mutate or drop the host source; after `download`, the caller may legally mutate the
host destination while the device buffer is reused. If the runtime skips the copy and aliases the two allocations, the next host
write becomes visible to the device (or vice versa) — an observable divergence from the discrete path, i.e. exactly the
non-determinism the ADR claims to exclude. Zero-copy is only sound where the *source is consumed or the buffer identity is the
same object* (REQ-OPT-347: "Zero-copy data paths … require compile-time proofs of capability non-aliasing and lifetime
validity"; REQ-COL-074 / ADATA-93: zero-copy APIs prefer views and Move semantics). `TransferStats.bytes_copied == 0` for
`upload`/`download` is therefore an unachievable acceptance criterion unless the semantics are silently changed.

**Proposed fix (ADR-0040 §3, replace the first sentence):**
> 3. **Zero-copy chỉ khi ngữ nghĩa cho phép (`SPEC-131`, `T954`, `T956`)**: `upload` / `download` / `device_copy` luôn là phép
> copy giữa hai vùng sở hữu riêng (giữ nguyên ngữ nghĩa trên mọi kiến trúc; trên UMA chúng là `memcpy` RAM→RAM, không có staging
> buffer thứ hai). Copy được triệt tiêu **chỉ** cho các phép chuyển miền trên cùng một đối tượng hoặc tiêu thụ nguồn:
> (a) acquire/release miền của cùng một `UnifiedBuffer<T>`; (b) `.to(device)` / `.to_async(device)` nhận `self` theo giá trị
> (nguồn bị move, không còn quan sát được); (c) `UnifiedBuffer.into_device(self) -> DeviceBuffer<T>` /
> `DeviceBuffer.into_host(self) -> UnifiedBuffer<T>` khi `memory_architecture` cho phép. Mọi phép khác giữ copy.

and in `T956` acceptance replace "`upload` / `download` / `.to(device)` report `TransferStats.bytes_copied == 0`" with
"`UnifiedBuffer` domain acquire/release and by-value `.to(device)` / `into_device` report `TransferStats.bytes_copied == 0`;
`upload` / `download` report exactly `len * size_of::<T>()` bytes on every architecture (no staging copy on UMA)".

---

## 2. BLOCKER — The CPU↔GPU race rule is framed as UMA-specific, but compile-time legality cannot depend on the runtime adapter

**Target.** ADR-0040 §5 "Kiểm tra data-race CPU↔GPU ở compile time … với `UnifiedBuffer<T>` … (chẩn đoán mới
`AX_GPU_UMA_HOST_DEVICE_RACE`)"; `T955` scope "Enforce UMA CPU↔GPU race freedom on `UnifiedBuffer<T>` (ADR-0040 §5)";
`T957` scope "rejection of host/device write races (`AX_GPU_UMA_HOST_DEVICE_RACE`)" listed only under "UMA conformance".

**Why.** The memory architecture is only known after `DeviceManager.enumerate()` at run time (`T962`/`T963`); the compiler
compiles one binary that runs on discrete, ReBAR and UMA adapters alike. So the rule either (a) applies to *all* programs
(then it is not UMA-specific and must be named/specified as a general rule), or (b) depends on the machine (impossible at
compile time, and it would make program legality machine-dependent, violating the ADR's own portability claim and
`INV-DET-001`). The same hazard also exists on discrete hardware: `PinnedHostBuffer<T>` (`T956`) is DMA-read/written
asynchronously by the GPU, ReBAR host-visible VRAM is CPU-writable while a kernel runs, and `UnifiedBuffer<T>` already
requires explicit acquire/release on every architecture (`0139 §XX.12-14`, REQ-GPU-035, REQ-SIMD-147 / ANUM-82 "Unified memory
does not imply synchronization").

**Proposed fix (ADR-0040 §5, replace):**
> 5. **Quy tắc truy cập host↔device độc lập phần cứng (`SPEC-131`, `T955`)**: áp dụng cho mọi bộ nhớ mà cả host và device đều
> truy cập được — `UnifiedBuffer<T>`, `PinnedHostBuffer<T>`, buffer nhập từ `mmap` / `VirtualRegion`, và vùng `ReBarHostVisible`
> được ánh xạ — trên **mọi** `GpuMemoryArchitecture`: không được có `mut_view` phía host đồng thời với một thao tác GPU đang bay
> (in-flight) trên cùng đối tượng, và ngược lại. Tính hợp lệ của chương trình không phụ thuộc máy chạy; `memory_architecture`
> chỉ ảnh hưởng chi phí (copy, cache maintenance), không ảnh hưởng tính hợp lệ.

Rename the diagnostic accordingly (see finding 11) and move the `T957` negative test out of the "UMA conformance" bullet into
the general negative-rejection bullet so it runs against every mock adapter.

---

## 3. BLOCKER — `HostExclusive ↔ DeviceExclusive ↔ SharedRead` is a second ownership/typestate model, contrary to REQ-CONC-095/096 and AGPU-20

**Target.** ADR-0040 §3 "chỉ chuyển trạng thái miền sở hữu `HostExclusive ↔ DeviceExclusive ↔ SharedRead`"; `T954` scope
"only change the domain state `HostExclusive ↔ DeviceExclusive ↔ SharedRead`"; `T955` scope "reject a live host
`mut_view<T>` while an un-awaited `GpuEvent` accesses the same buffer".

**Why.** Axiom has exactly one ownership model: place states `UNINIT/OWNED/MOVED/PARTIAL` (`SPEC-10` AXS-OWN-001) plus
capabilities `view`/`mut_view` with the conflict matrix and owner-outlives (`SPEC-11` AXS-CAP-003/004/006). REQ-CONC-096
("MUST NOT define separate ownership systems for threads, async tasks, and GPU invocations"), REQ-CONC-095 (no separate
`SharedRef`-like pointer kinds) and `T957`'s own bullet ("without introducing a second ownership model (`AGPU-20`, `AGPU-50`)")
all forbid a parallel three-state domain machine. As written, the ADR does not say whether the domain state is (i) a static
typestate checked by the compiler (then it duplicates the capability checker), or (ii) a runtime field (then
"compile-time" race freedom is not decidable, because which buffers an un-awaited `GpuEvent` touches is a runtime fact unless
the event *carries the capability*). `T955` cannot be implemented unambiguously.

**Proposed fix.** Add to ADR-0040 a normative mapping and make the domain state driver-internal bookkeeping only:
> **Ánh xạ vào mô hình sở hữu duy nhất (bắt buộc).** `HostExclusive` = host giữ `OWNED` hoặc `mut_view`; `DeviceExclusive` =
> giá trị đã được **move** vào một thao tác GPU in-flight (`InFlight<B>` do `dispatch` / `*_async` trả về); `SharedRead` = đồng thời
> có `view<T>` phía host và `DeviceView<T>` cùng nguồn gốc (quy tắc read/read của AXS-CAP-003). Trạng thái miền trong runtime chỉ
> dùng để phát barrier / flush / invalidate, không phải nguồn sự thật về tính hợp lệ. Vi phạm được báo bằng chẩn đoán capability
> hiện có (`AX_CAP_CONFLICT_MUT`, `AX_CAP_CONFLICT_READ`, `AX_OWN_USE_AFTER_MOVE`-tương đương, `AX_CAP_OUTLIVES_OWNER`) kèm note GPU.

and in `T955` replace "reject a live host `mut_view<T>` while an un-awaited `GpuEvent` accesses the same buffer and vice
versa" with "model in-flight GPU access as ownership transfer into `InFlight<B>` (or as a capability stored in the event per
AXS-CAP-006) so that the existing `own.ax` / `cap.ax` checks reject host access; no separate domain-state analysis".

---

## 4. MAJOR — Event-held capabilities collide with async rules, `Drop`, and the failure path of `.wait()`

**Target.** `T955` scope (race rule keyed on "un-awaited `GpuEvent`"); `T956` scope "`GpuEvent` … blocking
`.wait() -> Result<Unit, GpuError>` … optional non-mandatory `Future` adapter `.into_future()`"; ADR-0040 §5.

**Why.** If the race check is implemented as "`GpuEvent` stores a `mut_view`/`view` of the buffer" (the only static encoding
of "the event accesses the same buffer"), then `event.into_future().await` holds a view-containing composite across an
`.await` and is rejected by `AX_ASYNC_VIEW_ACROSS_AWAIT` (`spec/diagnostics.md`, T417, SPEC-33 AXS-ASY-034) — making the
GPU-async adapter (REQ-GPU-034) unusable for exactly the zero-copy buffers ADR-0040 promotes. Further gaps: (a) dropping a
`GpuEvent` without `.wait()` ends the borrow while the GPU may still write; (b) `.wait()` returning `Err(GpuError.DeviceLost)`
— is the buffer released, poisoned, or still borrowed? A `Result<Unit, _>` loses the buffer on error if it was moved in.

**Proposed fix (add to `T954` scope after the UMA bullet):**
> Specify in-flight access as ownership transfer: `dispatch` / `upload_async` / `download_async` on host-visible buffers take the
> buffer by value and return `InFlight<B>`; `InFlight<B>.wait(self) -> (B, Result<Unit, GpuError>)` returns the buffer on both
> success and failure (contents unspecified after `DeviceLost`, but ownership preserved); `Drop for InFlight<B>` blocks until
> completion (deterministic, no detached GPU writes); `InFlight<B>` contains no views and is therefore legal across `.await`
> (`AXS-ASY-034`). Add UI tests: await across in-flight, drop-without-wait, wait-error ownership recovery.

---

## 5. BLOCKER — Hidden cross-phase dependency: `T956` (and `T955`, `T969`) need P21 `T921`/`T922` but have no `depends:` edge, and P22 does not depend on the P21 gate

**Target.** `T956` scope "`UnifiedBuffer.from_mmap` / `from_virtual_region` zero-copy page import (E21.6 `T921`/`T922`
mappings …)"; `T955` scope "reject `munmap` / drop of a mapping imported via `UnifiedBuffer.from_mmap`"; `T969` scope
"import page-aligned `mmap` / `VirtualRegion` memory"; ADR-0040 §9/Consequences "0 thay đổi `depends:`".
Board facts: `T956 depends: [T222, T311, T312, T316, T955]`; `T955 depends: [T222, T311, T312, T316, T952, T954]`;
`T969 depends: [T222, T311, T312, T316, T668a, T956, T967, T968]`; `T322 depends` lists no P21 task; ROADMAP §2 table:
"P22 … needs P11, P12, P16" (not P21). `T921`/`T922 depends: [T221, T311, T313, …]`.

**Why.** The scheduler may start `T955`/`T956`/`T969` before `std/vmem/region` and `std/vmem/mmap` (`VirtualRegion`, `Mmap`,
`MmapMut`, `MmapCow`, `page_size()`) exist; the agent would either invent those types inside `std/gpu/*` (path violation +
duplicate API) or fail QA. This is precisely a hidden dependency. `T922` even lists "GPU device memory mappings (`P22 E22.2`)"
as out of scope, confirming the hand-off direction.

**Proposed fix (frontmatter):** `T955 depends: [T222, T311, T312, T316, T952, T954, T922]`;
`T956 depends: [T222, T311, T312, T316, T955, T921, T922]`; `T969 depends: [..., T922]`; and add to ADR-0040 Consequences:
"Thay đổi `depends:` duy nhất: `T955`/`T956`/`T969` → `T921`/`T922` (E21.6); ROADMAP P22 row 'needs P11, P12, P16, E21.6'."
Alternatively move all `from_mmap`/`from_virtual_region` work into a new task that depends on `T922` and `T956` (see 13).

---

## 6. BLOCKER — Dependency inversion: `T956`/`T957` consume `GpuMemoryArchitecture`, mock adapters and `device.memory_budget()` that are specified in `T962` and implemented in `T963`, while `T963` depends on `T956`

**Target.** `T956` scope "`device.memory_budget() -> GpuMemoryBudget { … }`"; `T956` acceptance "On a mock
`CacheCoherentUma` / `NonCoherentUma` adapter …"; `T957` scope "on mock `Discrete`, `CacheCoherentUma`, `NonCoherentUma`,
and `ReBarHostVisible` adapters"; `T963` scope "CPU fallback exposing a configurable mock `GpuMemoryArchitecture`";
ADR-0040 §1 "Phân loại kiến trúc bộ nhớ (`SPEC-133`, `T962`, `T963`)".
Board facts: `T963 depends: [..., T956, T960, T962, T966]`; `T956`/`T957` do not depend on `T962`/`T963`;
`T962 depends: [..., T958]`, `T958 depends: [..., T954]`; `T956 paths: [std/gpu/mem, std/gpu/transfer, std/gpu/event, …]`
(no `std/device`, no `std/sys/gpu/cpu_fallback`).

**Why.** The mock adapter, `GpuAdapterInfo.memory_architecture`, and the device object that owns `memory_budget()` are
produced by `T963` (paths `std/device`, `std/sys/gpu/cpu_fallback`), which runs *after* `T956`/`T957`. `T956` cannot meet
its acceptance without writing into `T963`'s paths; `T957` cannot run its four-adapter conformance. Likewise SPEC-131 (`T954`)
must normatively use an enum that the ADR assigns to SPEC-133 (`T962`), which is specified later (`T954 → T958 → T962`).

**Proposed fix.** (a) Define `GpuMemoryArchitecture`, `GpuMemoryBudget` and the *semantic* rules in SPEC-131 (`T954`);
SPEC-133 (`T962`) only specifies per-backend detection. Edit ADR-0040 §1/§6 to say "(`SPEC-131` định nghĩa kiểu; `SPEC-133`
quy tắc phát hiện)". (b) In `T956`, replace "`device.memory_budget()`" with "the backend-neutral `MemoryArchitectureProvider`
trait and an in-library `MockMemoryArchitecture` used by tests" and keep real `memory_budget()` in `T963` (add
`std/device` budget to `T963` acceptance). (c) Move the four-adapter UMA conformance bullet from `T957` to `T965`
(`depends` already includes `T957`, `T964`) or add `T963` to `T957 depends`.

---

## 7. MAJOR — `UnifiedBuffer.from_mmap(view<Mmap>)` is under-typed: read-only capability vs GPU writes, owning vs borrowing type, and byte→`T` reinterpretation

**Target.** ADR-0040 §4 "`UnifiedBuffer.from_mmap(view<Mmap>)` / `UnifiedBuffer.from_virtual_region(...)` … Buffer nhập vào
giữ khoản mượn trên mapping gốc"; `T954` scope "(page-aligned, borrowing the source mapping, …)"; `T956` scope.

**Why.** (a) `view<Mmap>` is a shared read capability (`SPEC-11` AXS-CAP-001); returning a `UnifiedBuffer<T>` whose device side
can be bound as `DeviceMutView<T>` lets a kernel write through a read-only capability — an aliasing violation. Writable import
needs `mut_view<MmapMut>` (exclusive). (b) `UnifiedBuffer<T>` is an *owning* type in `T956` (alloc + `Drop` frees). A value that
sometimes owns and sometimes borrows cannot be checked by AXS-CAP-006 (stored-view outlives is a property of the *type*); the
borrow must be visible in a distinct type, otherwise drop of the import frees/unmaps memory it does not own. (c) `Mmap` exposes
`view<u8>` (`T920`/`T922`); producing `UnifiedBuffer<T>` reinterprets bytes as `T` — needs an alignment check
(`offset % align_of::<T>() == 0`, `len % size_of::<T>() == 0`) and a bit-validity bound (`T: PlainData`-style marker per
`SPEC-51`), or it is an unchecked `bitcast`.

**Proposed fix (ADR-0040 §4, replace the API sentence):**
> `HostImport.read<T: PlainData>(src: view<Mmap>) -> Result<ImportedView<T>, GpuError>` (GPU chỉ được bind dạng
> `DeviceView<T>`), `HostImport.write<T: PlainData>(src: mut_view<MmapMut>) -> Result<ImportedMutView<T>, GpuError>`, và
> `HostImport.region<T: PlainData>(src: mut_view<VirtualRegion>, offset, len)`. `ImportedView`/`ImportedMutView` là kiểu chứa
> stored view (AXS-CAP-006) nên không thể sống lâu hơn mapping (`AX_CAP_OUTLIVES_OWNER`), không giải phóng bộ nhớ khi drop;
> kiểm tra căn lề theo `align_of::<T>()` và độ dài bội số `size_of::<T>()`, lỗi `GpuError.HostImportMisaligned`.

Update `T954`/`T956`/`T969` wording from `UnifiedBuffer.from_mmap` to the new names.

---

## 8. MAJOR — Host-import hazards not specified: file truncation (SIGBUS / device fault), `MmapCow`, `protect`/`decommit` while imported, alignment stricter than page size, backend import restrictions

**Target.** ADR-0040 §4; `T955` scope "reject `munmap` / drop of a mapping imported …"; `T963` scope
"`ID3D12Device3.OpenExistingHeapFromAddress` host import; … `VK_EXT_external_memory_host` import"; `T969` scope
"`newBufferWithBytesNoCopy:length:options:deallocator:`".

**Why.**
- *Truncation:* another process can truncate the file behind a file-backed `Mmap`; the CPU gets SIGBUS / `EXCEPTION_IN_PAGE_ERROR`,
  the GPU gets a page fault that typically surfaces as device loss for the *whole* device (all other buffers). Borrow checking cannot
  prevent external truncation.
- *`MmapCow`:* GPU writes through an IOMMU mapping do not take CPU copy-on-write faults; depending on OS/driver the pages are
  either unshared at import time or GPU writes reach shared page-cache pages (modifying the file for other mappers). Must be either
  forbidden or defined.
- *`VirtualRegion.protect` / `decommit` / `unlock_pages`:* changing CPU page protection or decommitting while the GPU holds the
  range gives OS/driver-specific results (GPU may keep writing to pinned pages, or fault). `T921` does not state whether
  `protect` takes `mut_view<VirtualRegion>`; if it takes `view`, it does not conflict with the import borrow.
- *Alignment:* "page-aligned" is insufficient: Vulkan requires `minImportedHostPointerAlignment` (can exceed 4 KiB), Metal no-copy
  buffers need page-aligned pointer **and** length (16 KiB pages on Apple Silicon).
- *D3D12:* `OpenExistingHeapFromAddress` is documented for memory allocated by `VirtualAlloc` (not file-mapping views); file-backed
  import on D3D12 needs a different path (newer `OpenExistingHeapFromFileMapping`) or must return `HostImportUnsupported`.
  (Verify against current Microsoft docs before freezing SPEC-133.)

**Proposed fix (add to ADR-0040 §4 and `T954` scope):**
> Nhập trang host: (i) chỉ chấp nhận vùng đã commit với quyền RW (hoặc R cho `HostImport.read`); `VirtualRegion.protect`,
> `decommit`, `unlock_pages` nhận `mut_view<VirtualRegion>` nên bị chặn khi còn import (AXS-CAP-003); (ii) `MmapCow` bị từ chối
> (`GpuError.HostImportUnsupported`) trừ khi gọi `MmapCow.make_private_resident()` trước; (iii) mapping theo file chỉ nhập được
> sau khi khóa kích thước file (Windows: mở với share mode không cho ghi; POSIX: tài liệu hóa rủi ro, lỗi GPU do truncate trả về
> `GpuError.DeviceLost` có `cause = HostPageFault`, không UB ngôn ngữ); (iv) căn lề = `max(page_size(), backend_import_alignment)`
> cho cả địa chỉ và độ dài, truy vấn được qua `device.host_import_alignment()`; (v) D3D12 chỉ nhập vùng `VirtualRegion`, mapping
> theo file trả `HostImportUnsupported` trừ khi có API file-mapping.

Add matching negative tests to `T955` (protect/decommit while imported) and run tests to `T956`/`T963`/`T969`.

---

## 9. MAJOR — Hardware-dependent API outcomes need an explicit portability contract (`from_mmap`, `shared_read_views`, `TransferStats`)

**Target.** ADR-0040 §3 "Có `TransferStats` (số byte thật sự được copy)"; §4 "Trả về `GpuError.HostImportUnsupported` khi backend
không hỗ trợ"; §5 "Cho phép `shared_read_views() -> (view<T>, DeviceView<T>)` để CPU và GPU cùng đọc đồng thời một địa chỉ vật
lý"; Consequences "cùng một chương trình … vẫn chạy đúng trên GPU rời".

**Why.** (a) `TransferStats.bytes_copied` is an observable value that differs per machine; if it is "observable result", the
ADR's identical-results claim is false; it must be classified like timing (non-semantic). (b) `from_mmap` succeeds or fails depending
on driver extensions — acceptable only as a documented fallible capability query, with a portable fallback the user writes; the
deterministic oracle (`--interp`, `INV-DET-003`) must pick a fixed answer. (c) `shared_read_views` is phrased as "cùng một địa chỉ
vật lý" (UMA-only); on discrete it is unspecified whether it fails, copies, or reads pinned host memory over PCIe. Legality must be
identical everywhere; a discrete GPU can read host-visible memory directly, so the API can be universal with differing cost.

**Proposed fix (new ADR-0040 §7 "Hợp đồng khả chuyển"):**
> (1) Tập chương trình hợp lệ không phụ thuộc phần cứng. (2) Mọi API trong ADR này có trên mọi kiến trúc; khác biệt chỉ ở chi phí:
> `shared_read_views` trên `Discrete` dùng bộ nhớ host pinned GPU đọc qua bus (không copy), không bao giờ lỗi vì kiến trúc.
> (3) Lỗi phụ thuộc phần cứng chỉ có ở API năng lực tường minh: `HostImport.*` (truy vấn trước bằng `device.supports_host_import()`),
> và lỗi ngân sách (finding 10). (4) `TransferStats` là bộ đếm hiệu năng, không thuộc "kết quả quan sát được"; conformance so sánh
> nội dung buffer, không so sánh `TransferStats` giữa kiến trúc. (5) Oracle `--interp` và `cpu_fallback` dùng kiến trúc mặc định cố
> định (`CacheCoherentUma`, `supports_host_import = true`), chỉ đổi qua cờ/biến cấu hình được khai báo là input (INV-DET-001).

---

## 10. MAJOR — `OutOfUnifiedMemoryBudget` as a hard limit at `recommended_max_working_set_bytes` is UMA-only, nondeterministic, and defeats the motivating example

**Target.** ADR-0040 §6 "Cấp phát vượt `recommended_max_working_set_bytes` trên UMA trả `GpuError.OutOfUnifiedMemoryBudget`";
`T956` scope/acceptance; `T969` scope "allocations beyond the budget return `GpuError.OutOfUnifiedMemoryBudget`".

**Why.** (a) Error set differs by architecture (discrete returns some other error or succeeds), so the same allocation has
different failure modes per machine. (b) `recommendedMaxWorkingSetSize` / `QueryVideoMemoryInfo.Budget` / `VK_EXT_memory_budget`
are *advisory* and change dynamically with other processes; Metal itself allows exceeding them. A hard refusal makes the Context
example ("Nạp mô hình AI 30 GB" on a 32/64 GB machine) fail on machines where the OS would happily serve it. (c) It is unspecified
whether host-imported pages (finding 7) count toward the budget (they are already resident RAM). (d) The check is TOCTOU (budget
changes between query and allocate).

**Proposed fix (replace ADR-0040 §6 last sentence):**
> Một lỗi duy nhất trên mọi kiến trúc: `GpuError.OutOfDeviceMemory { requested, budget: GpuMemoryBudget }`. Chính sách
> `AllocPolicy = Advisory | StrictBudget` (mặc định `Advisory`: chỉ cấp phát thất bại khi driver từ chối; `pressure` báo
> `Warning`/`Critical`); `StrictBudget` từ chối khi vượt `recommended_max_working_set_bytes` (best-effort, không đảm bảo chống
> OOM-kill). Trang nhập từ host không tính vào `current_allocated_bytes` nhưng tính vào `resident_shared_bytes`.

---

## 11. MAJOR — Diagnostic naming/registration: hardware word in the code name, overlap with existing CAP codes, not registered, and missing registry lock

**Target.** ADR-0040 §5 "(chẩn đoán mới `AX_GPU_UMA_HOST_DEVICE_RACE`)"; `T955` scope/acceptance; `T954` scope "Update
`spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`" (unchanged); `T955 locks: [compiler/semantics/own.ax,
compiler/semantics/cap.ax, compiler/mir/verifier.ax, compiler/lir/lir.ax]`.

**Why.** (a) ADR-0011 / AXD-010 requires `AX_<AREA>_<NAME>`; the `GPU` area does not exist yet — `spec/diagnostics.md` §3
lists `AX_GPU_` among groups "with no area in v0.1", to be added by editing §3 and §11 first (AXD-022); `T950` is the task that
registers `AX_GPU_*`. Fine in order (`T954` depends on `T950`), but ADR-0040 should say so. (b) Per finding 2 the rule is not
UMA-specific; per finding 3 the conflict is an ordinary capability conflict, so `AX_CAP_CONFLICT_MUT` / `AX_CAP_CONFLICT_READ`
/ `AX_CAP_OUTLIVES_OWNER` (already registered and reused across domains, e.g. E16.5 JNI) are the canonical codes; a new code is
justified only if the payload differs (e.g. names the in-flight op). (c) `spec/diagnostics.md` has no entry; `T954` acceptance
does not require registering it, so `harness_check`/golden code list (INV-DIAG-002) will not catch it. (d) `T955` adds a code but
does not lock the registry source; `T951` locks `compiler/diag/codes.ax`, while `spec/diagnostics.md` §3 refers to
`compiler/diag/code.ax` — a path-spelling inconsistency to resolve while fixing this.

**Proposed fix.** ADR-0040 §5: "Vi phạm báo bằng `AX_CAP_CONFLICT_MUT` / `AX_CAP_CONFLICT_READ` với note `gpu_in_flight` (payload
`data.gpu_op`); nếu cần mã riêng thì là `AX_GPU_HOST_DEVICE_ACCESS_CONFLICT` (vùng `GPU` do `T950` lập), đăng ký append-only trong
`spec/diagnostics.md` bởi `T954`." `T954` acceptance: add "`spec/diagnostics.md` registers every new `AX_GPU_*` code used by
SPEC-131 (including the host/device access conflict) with emitting task `T955`." `T955 locks`: add the actual registry file
(`compiler/diag/codes.ax` or `compiler/diag/code.ax`, whichever exists).

---

## 12. MAJOR — Scope added without acceptance criteria in `T954`, `T957`, `T962`, `T963`, `T969`

**Target.** Diff of `57b7c8e6`: only `T955` and `T956` changed `## Acceptance`. `T954`/`T962` acceptance still only checks
file existence + reqcov; `T963` acceptance still "DeviceManager enumeration … buffer upload/download, and compute dispatch";
`T969` acceptance still the pre-ADR line "Apple Silicon unified memory mode correctly detects zero-copy capability"; `T957`
added a scope bullet but no acceptance line.

**Why.** QA gates on acceptance (CLAUDE.md: tasks close only via `taskctl accept` after QA). New scope with no acceptance is
unverifiable and will be silently dropped or argued about at gate time.

**Proposed fix.** Add:
- `T954`: "- [ ] SPEC-131 contains numbered `AXS-GMEM-*` rules for: the ownership mapping of domain states (finding 3),
  copy-elision legality (finding 1), host import typing/hazards (findings 7–8), portability contract (finding 9), budget policy
  (finding 10), each with positive/negative examples."
- `T962`: "- [ ] SPEC-133 specifies per-backend detection tables for `GpuMemoryArchitecture` and budget sources, including
  WebGPU/OpenGL/CPU-fallback defaults."
- `T963`: "- [ ] `tests/run/gpu_host_driver` verifies `memory_architecture` reporting, zero-copy heap selection, flush/invalidate only
  on non-`HOST_COHERENT` types (via driver trace), host import success/`HostImportUnsupported`, and `memory_budget()` on the mock
  adapter for every architecture value."
- `T969`: replace the old UMA line with "- [ ] `CacheCoherentUma` reported on Apple Silicon; `HostImport` of a page-aligned
  `VirtualRegion` works without allocation; `memory_budget()` mirrors `recommendedMaxWorkingSetSize`."
- `T957`: "- [ ] UMA conformance cases pass on all four mock architectures with identical buffer contents."

---

## 13. MAJOR — Task sizing: `T956` and `T963` (both `model: sonnet`) are now oversized; "no new tasks" is a constraint, not a justification

**Target.** ADR-0040 Tóm tắt "Không thêm task mới"; Consequences "0 task mới, 0 thay đổi `depends:`"; `T956` scope (DeviceBuffer
family + transfers + multi-GPU peer + `ShardedDeviceBuffer` + collectives + events + UMA elision + host import + budget);
`T963` scope (std.device + Vulkan + D3D12 + CPU fallback + UMA detection/heaps/import/budgets on two APIs).

**Why.** Each of these already spans several subsystems; adding UMA (with the hidden P21 dependency and the inversion in
findings 5–6) makes them the likeliest QA-failure / requeue (>3 attempts → blocked) tasks of E22.2/E22.4. The "no new tasks / no
depends changes" constraint is what forced the hidden edges.

**Proposed fix.** Amend ADR-0040 to create a dedicated slice (either new epic `E22.10 Unified Memory` or suffixed tasks):
`T956a` "UMA: domain acquire/release elision, `HostImport`, `TransferStats`" (`depends: [T956, T922, T963]`, paths
`std/gpu/uma`, `tests/run/gpu_uma`); `T963a` "UMA drivers: D3D12/Vulkan zero-copy heaps, host import, budgets"
(`depends: [T963]`); conformance merged into `T965` or `T957a`. Remove the UMA bullets from `T956`/`T963` accordingly and keep
`T954`/`T955` spec/verifier bullets (rewritten per findings 1–4). Wire the new tasks into `T322 depends`.

---

## 14. MAJOR — Traceability: the owner request is not recorded in `OWNER.md`, no `REQ-*` covers UMA, and relevant existing requirements are not cited

**Target.** ADR-0040 Tóm tắt (owner quote "thêm vấn đề về gpu, một số hệ điều hành và dòng máy tính có bộ nhớ unified …");
Consequences "`reqcov.py --strict` … phải giữ 0 gaps"; unchanged `covers:` on all seven tasks; `spec/requirements/OWNER.md`
(no UMA entry; last is `REQ-OWNER-008`).

**Why.** CLAUDE.md: owner requirements in `OWNER.md` must not be dropped silently — an owner directive that is not a `REQ-OWNER-*`
row is invisible to `reqcov.py`, so "0 gaps" is vacuous. Existing catalogue rows that directly constrain this design are not cited:
REQ-SIMD-147/REQ-SIMD-309 (ANUM-82 "Unified memory does not imply synchronization"), REQ-OPT-347 (zero-copy requires compile-time
non-aliasing/lifetime proofs), REQ-CONC-096 (single ownership model), REQ-CAP-139-style "zero-copy views shall not outlive backing
storage".

**Proposed fix.** Add `| REQ-OWNER-009 | gpu | v1-full | On machines where RAM and VRAM are one physical pool (Apple Silicon, APU/iGPU,
Grace/MI300A, Snapdragon/Mali), Axiom GPU programs use the shared memory without redundant copies, with the same program valid on
discrete GPUs | owner 2026-11-10; ADR-0040 | T954, T955, T956, T957, T962, T963, T969 |` to `OWNER.md`; add `REQ-OWNER-009`
and `REQ-OPT-347` to the relevant `covers:`; cite REQ-SIMD-147 and REQ-CONC-096 in ADR-0040 Sources.

---

## 15. MAJOR — `GpuMemoryArchitecture` conflates orthogonal axes and duplicates truth (`is_unified_memory`)

**Target.** ADR-0040 §1 "`memory_architecture: GpuMemoryArchitecture` với `Discrete | CacheCoherentUma | NonCoherentUma |
ReBarHostVisible`, cùng `is_unified_memory: bool` và `unified_pool_bytes: u64`"; Context "NVIDIA Grace Hopper / Grace Blackwell
(NVLink-C2C, cache-coherent)" listed as one physical pool.

**Why.** Three independent properties are folded into one enum: (1) shared physical pool vs separate VRAM, (2) host coherence,
(3) host-visible device-local memory (ReBAR). Grace Hopper has *two* pools (HBM on the GPU, LPDDR on the CPU) that are mutually
coherent — not "one pool", so `unified_pool_bytes` is ill-defined; Vulkan reports coherence per *memory type*, so one adapter can
expose both coherent and non-coherent host-visible types. `is_unified_memory` stored alongside the enum allows inconsistent states
(e.g. `ReBarHostVisible` + `true`).

**Proposed fix (ADR-0040 §1):**
> `GpuMemoryTopology { shared_physical_pool: bool, host_coherent_device_memory: bool, host_visible_device_local_bytes: u64,
> pools: Vec<GpuMemoryPool { kind: DeviceLocal | SystemShared | SystemRemoteCoherent, bytes: u64, numa_node: Option<u32> }> }`;
> `GpuMemoryArchitecture` giữ làm tóm tắt dẫn xuất (method `architecture()`), `is_unified_memory()` là method dẫn xuất, không phải
> trường lưu. Grace Hopper / MI300A phân loại theo `pools`.

---

## 16. MAJOR — Mixed iGPU (UMA) + dGPU in one process is unspecified

**Target.** `T962` scope ("… or use both GPUs concurrently in the same process", `MultiGpuGroup`); `T956`
(`peer_copy`, `ShardedDeviceBuffer`, collectives); ADR-0040 (no mention of multi-adapter).

**Why.** Typical laptop: Intel/AMD iGPU (UMA) + NVIDIA dGPU. Open questions affecting typing and legality: which `DeviceId` owns a
`UnifiedBuffer` (it is system RAM, accessible by both); is the dGPU reading an iGPU-owned unified buffer a "peer access"
(`can_access_peer`, REQ-GPU-063) or a pinned-host access; does `ShardedDeviceBuffer` across `{iGPU, dGPU}` elide copies for the
iGPU shard only; the iGPU budget competes with CPU RAM while the dGPU's does not; `MultiGpuGroup.all_compute_capable()` mixes
architectures in collectives.

**Proposed fix (add to `T954` UMA bullet):**
> Specify multi-adapter UMA: a `UnifiedBuffer<T>`/host import is owned by the host domain and *bound* per device
> (`bind_to(device) -> DeviceView<T>`), so iGPU and dGPU may both read it under the same capability rules; dGPU access to
> host-shared memory is a pinned-host access, not peer access (REQ-GPU-063 unaffected); `ShardedDeviceBuffer` and collectives
> apply elision per shard according to each device's topology; budgets are reported per device and `SystemShared` pools are
> flagged as shared with the CPU.

---

## 17. MINOR — Tensors (`ATENSOR`) and AI/MMA tasks are not wired to the zero-copy contract

**Target.** ADR-0040 §3 mentions `.to(device)` / `tensor.to(device)`; `T980` (`SPEC-137` GPU AI tensor/MMA), `T981`, `T982`
not amended; REQ-GPU-061 ("Tensor storage domains … shall remain distinct … explicit transfer operations").

**Why.** Under finding 1, `tensor.to(device)` may elide only if it consumes `self`; the tensor API's receiver mode is not stated.
The main UMA use case in the ADR Context (mmap-loaded 30 GB model weights) lives in the AI stack (`T980`–`T982`), which does not
reference ADR-0040, so weight loading will default to copies.

**Proposed fix.** Add to `T980` scope: "Tensor `.to(device)` / `.to_async(device)` take `self` by value (copy-elided on shared-pool
devices per ADR-0040 §3); `Tensor.from_host_import(ImportedView<T>, shape)` for read-only mmap-loaded weights without copy;
cite ADR-0040 in `spec:`." State in ADR-0040 §3 that REQ-GPU-061 remains satisfied because domain change stays explicit.

---

## 18. MINOR — WebGPU, OpenGL, software rasterizer and CPU fallback defaults are inconsistent or missing

**Target.** ADR-0040 §1 "WebGPU / OpenGL / CPU fallback: báo cáo bảo thủ `Discrete` trừ khi backend xác nhận được UMA"; `T963` "CPU
fallback exposing a configurable mock `GpuMemoryArchitecture`"; `T976`/`T978` (WebGPU), `T985`/`T987` (OpenGL), `T974`
(software rasterizer) not amended.

**Why.** The CPU fallback and software rasterizer *are* literally shared-memory devices; reporting `Discrete` forces needless copies
in the deterministic oracle and contradicts `T963`'s "configurable mock". WebGPU (`mapAsync`, wasm32 linear memory) can never do
host import; OpenGL has persistent coherent mapping (`GL_MAP_PERSISTENT_BIT | GL_MAP_COHERENT_BIT`, ARB_buffer_storage) — the
backend specs should say what they report and that `HostImport.*` returns `HostImportUnsupported`.

**Proposed fix.** ADR-0040 §1: "CPU fallback / software rasterizer: `CacheCoherentUma` (shared_physical_pool = true) theo mặc định,
cấu hình được cho CI; WebGPU: `Discrete`, `supports_host_import() = false`; OpenGL: `Discrete`, có thể dùng persistent mapping như
`ReBarHostVisible`-tương đương khi có `ARB_buffer_storage`." Add one-line references to ADR-0040 in `T976`, `T978`, `T985`, `T987`,
`T974` scopes.

---

## 19. MINOR — "Cache maintenance emitted only for `NonCoherentUma`" is untestable without a specified trace hook; ReBAR copy accounting undefined

**Target.** `T957` scope "cache maintenance emitted only for `NonCoherentUma`"; ADR-0040 §3 `TransferStats`.

**Why.** No task specifies how conformance observes flush/invalidate calls (driver trace, `TransferStats.cache_ops`, replay log).
For `ReBarHostVisible`, a CPU write into BAR-mapped VRAM is a bus transfer — is it counted in `bytes_copied`? Tests will encode
arbitrary choices.

**Proposed fix.** In `T956`/`T963` scope: "`TransferStats { bytes_copied, bytes_written_over_bus, cache_flushes, cache_invalidates }`
recorded by every backend including the mock; ReBAR host writes count as `bytes_written_over_bus`, not `bytes_copied`." Update the
`T957` bullet to assert on these fields.

---

## 20. MINOR — Downstream runtime/conformance tasks not updated (`T964`, `T965`, `T970`, `T322`)

**Target.** `T964` (`RenderGraph` compute/transfer/render DAG), `T965` (E22.4 oracle conformance), `T970` (Metal conformance), `T322`
gate — none reference ADR-0040.

**Why.** `RenderGraph` transfer nodes are where copy elision and barrier insertion actually happen in practice; `T965`/`T970` are the
only real-hardware conformance points; the gate cannot check UMA exit criteria it does not list.

**Proposed fix.** `T964` scope: "transfer nodes on shared-pool devices lower to domain transitions + barriers per ADR-0040 §3";
`T965`/`T970` acceptance: "UMA cases from SPEC-131 pass on available real hardware and on all mock architectures";
`T322`: add "ADR-0040 UMA exit criteria" to the gate checklist (and the new tasks from finding 13 to `depends:`).

---

## 21. MINOR — `WRITE_COMBINE` for non-coherent UMA makes host reads (`shared_read_views`, readback) pathologically slow

**Target.** ADR-0040 §2 "`CPU_PAGE_PROPERTY_WRITE_BACK` khi cache-coherent, `WRITE_COMBINE` khi non-coherent"; `T963` same.

**Why.** Write-combined memory is uncached for CPU reads; the ADR simultaneously promotes CPU+GPU concurrent reads
(`shared_read_views`) and download elision on the same memory. The page property must follow the declared host access pattern, not
only coherence.

**Proposed fix.** ADR-0040 §2: "Chọn thuộc tính trang theo `HostAccess = WriteOnly | ReadBack | ReadWrite` khai báo khi cấp phát:
`WriteOnly` → `WRITE_COMBINE`; `ReadBack`/`ReadWrite` → `WRITE_BACK` (non-coherent thì kèm flush/invalidate tường minh)."
Add `HostAccess` to `UnifiedBuffer.alloc` in `T956`.

---

## 22. MINOR — ADR-0040 sets "0 `depends:` changes / 0 new tasks" as a success metric

**Target.** ADR-0040 Tóm tắt "Không đổi `depends:`, không đổi gate `T322`"; Consequences "Quản lý: 0 task mới, 0 thay đổi `depends:`";
ROADMAP log row 2026-11-10 "no new tasks, no `depends:` changes".

**Why.** Board structure should follow the dependency graph, not the reverse; this metric directly caused findings 5, 6, 13 and 20.
Recording it as a virtue in the ROADMAP history will be copied by future expansions.

**Proposed fix.** Replace in ADR-0040 Consequences: "Quản lý: thay đổi board tối thiểu nhưng đúng đồ thị phụ thuộc — thêm cạnh
`T955`/`T956`/`T969` → `T921`/`T922`, tách `T956a`/`T963a`, nối vào `T322`; `reqcov.py --strict` và `harness_check.py` giữ 0 gaps
với `REQ-OWNER-009`." Update the ROADMAP log row to match.

---

FINDINGS: 22 (B=5 M=11 m=6)
