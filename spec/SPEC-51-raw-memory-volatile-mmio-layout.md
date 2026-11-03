# SPEC-51 — Canonical Raw Memory, Volatile, MMIO, Unions, Packed/Aligned Repr & Address Spaces Specification

Status: draft (T506, 2026-11-03)
Owner: axiom-architect
Consolidates: `specs/0044`; `specs/0067 (§1–41, AREP-01..12)`; `specs/0071 (§1–60, AMEM-01..15)`; `specs/0072 (§1–58, AREP-13..22)`; `specs/0097 (AOS-26..30)`; `specs/0104 (§54)`; `specs/0113 (§122)`; `specs/0119 (§226, §258–259)`; `specs/0128 (§62)`; `specs/0129 (§71)`; `specs/0131 (§65, §80)`; `specs/0132 (§13–16, §62, ADATA-29..31)`; `specs/0133 (§48)`; `specs/0138 (§10, §19, §57)`; `specs/0161 (§30–31)`; `specs/0162 (§9–12, §32)`; `specs/0163 (§1–7)`; `specs/1066 (§2.D)`; `tasks/0328 (§1–40, AMEMLOW-20..100)`; `tasks/0339 (ASAFE-20..100)`; `tasks/0367 (§1–82, AABI-20..70)`; `tasks/0413 (§1–70, AFFI-20..64)`; `tasks/0434 (§92)`; `tasks/0445 (§186.161, AFFI-40..42)`; `tasks/0452 (§193.47, AABI-23..32)`; `tasks/0475 (§216.42–43, ASPEC-40)`; `tasks/0486 (§78–80, ACAP-42..44)`; `tasks/0515 (§1–196, AMEM-20..170)`; `spec/SPEC-03-core-semantics.md`; `spec/SPEC-04-core-extensibility.md`; `spec/SPEC-31-atomics.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/decisions/ADR-0001-fixed-address-declarations.md`.
Covers: `REQ-ABI-063`, `REQ-CORE-449`, `REQ-FFI-099`, `REQ-RES-136`, `REQ-CAP-130`, `REQ-CAP-152` (and specifies the E13.2 contract for `T507`–`T510`: `REQ-ABI-012`, `REQ-ABI-036`, `REQ-ABI-041`, `REQ-ABI-044`, `REQ-ABI-052`, `REQ-ABI-061`, `REQ-ABI-064`, `REQ-ABI-065`, `REQ-ABI-093`, `REQ-ABI-098`, `REQ-ABI-100`, `REQ-ABI-103`, `REQ-FFI-013`, `REQ-FFI-015`, `REQ-FFI-018`, `REQ-FFI-029`, `REQ-FFI-031`, `REQ-FFI-043`, `REQ-FFI-078`, `REQ-FFI-097`, `REQ-FFI-098`, `REQ-RES-135`, `REQ-RES-137`, `REQ-RES-160`, `REQ-RES-161`, `REQ-RES-163`, `REQ-RES-173`, plus `E13.6` `T525`–`T529`).
Consumers: `compiler/ast/`, `compiler/parser/`, `compiler/hir/`, `compiler/sema/`, `compiler/types/`, `compiler/mir/`, `compiler/verify/`, `compiler/interp/`, `compiler/opt/`, `compiler/lir/`, `compiler/abi/`, `compiler/target/x64/`, `std/mem/`, `T507`–`T510`, `T525`–`T529`.

## Tóm tắt

Tài liệu `SPEC-51` chuẩn hóa mô hình truy cập bộ nhớ mức thấp (`raw memory`), ngữ nghĩa đọc/ghi khả biến phần cứng (`volatile_load`, `volatile_store`, `volatile_copy`, hàng rào bộ nhớ `fence`), các kiểu bao thanh ghi MMIO (`Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, `MmioWO<T>`), kiểu hợp nhất không gắn thẻ (`union`), các thuộc tính điều khiển bố cục vật lý (`@repr(C)`, `@repr(packed)`, `@repr(packed(N))`, `@align(N)`), lưu trữ chưa khởi tạo (`MaybeUninit<T>`, `ManuallyDrop<T>`), phép diễn giải lại mẫu bit (`bitcast`), và không gian địa chỉ con trỏ tường minh (`@addr_space(N)`) cho phân hệ `E13.2` (Phase `P13`):
- **Phân tách ba giao thức bộ nhớ (`Ordinary != Atomic != Volatile`, `AMEMLOW-20..48`, `AMEM-74..78`, `REQ-FFI-015`, `REQ-RES-173`)**: Truy cập `volatile` là hiệu ứng bộ nhớ quan sát được dùng cho thanh ghi thiết bị/MMIO, hoàn toàn tách biệt với tính nguyên tử (`Atomic<T>`) hay đồng bộ hóa luồng (`Happens-Before`). Mọi lệnh `volatile_load` và `volatile_store` trên độ rộng vô hướng tự nhiên (`1`, `2`, `4`, `8` byte) bảo đảm: (1) không bị trình tối ưu hóa (`-O1`/`-O2`) loại bỏ (`non-elision`), gộp (`non-coalescing`), hay đảo thứ tự qua các truy cập `volatile`/hàng rào khác; và (2) phát đúng một lệnh máy đúng độ rộng (`MOV r8/r16/r32/r64` trên x86-64), tuyệt đối không xé nhỏ (`non-tearing`).
- **Kiểu bao thanh ghi `Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, `MmioWO<T>` hạ trực tiếp từ phép chiếu trường (`ADR-0001 §2`, `SPEC-04 AXS-EXT-023/043`)**: Sau khi khai báo đúng thanh ghi phần cứng (ví dụ `@at(0x4000_1000) unsafe static mut UART0: UartRegs`), việc đọc/ghi trường thông thường (`UART0.ctrl = v`, `let s = UART0.status`) tự động hạ xuống `MIR_STMT_VOLATILE_LOAD` / `MIR_STMT_VOLATILE_STORE` đúng độ rộng của `T`, kiểm tra quyền đọc/ghi tĩnh trên `MmioRO<T>` (`AX_TYPE_MMIO_WRITE_READONLY`) và `MmioWO<T>` (`AX_TYPE_MMIO_READ_WRITEONLY`), đồng thời cung cấp các phương thức thao tác bitfield tường minh (`read`, `write`, `modify`, `set_bits`, `clear_bits`, `test_bits`, `extract_bits`, `insert_bits`).
- **Kiểu `union` không gắn thẻ an toàn sở hữu (`0072 §1–13`, `AREP-13..16`)**: `union` biểu diễn vùng nhớ chồng lấp có `size = align_up(max_field_size, align)` và `align = max_field_align`, mọi trường đặt tại offset `0`. Để không làm hỏng hệ thống hủy tất định (`Drop`), các trường của `union` bắt buộc phải là kiểu `Copy` hoặc được bọc trong `ManuallyDrop<T>` (`AX_TYPE_UNION_NON_COPY_FIELD`). Khởi tạo `union` (với đúng 1 trường, `AX_TYPE_UNION_INIT_FIELD_COUNT`) và ghi vào trường `Copy` là an toàn; đọc trường của `union` (hoặc ghép mẫu trên trường `union`) bắt buộc nằm trong khối `unsafe` (`AX_UNSAFE_REQUIRED`).
- **Kiểm soát bố cục `@repr(C)`, `@repr(packed)`, `@align(N)`, `bitcast` và không gian địa chỉ (`0067`, `REQ-ABI-063`, `REQ-CORE-449`, `REQ-RES-136`, `REQ-FFI-099`, `REQ-CAP-130`, `REQ-CAP-152`)**: Đóng băng hợp đồng Core ABI tối thiểu (`REQ-CORE-449`) và `@repr(C)` (`REQ-ABI-063`); kiểm định `@align(N)` lũy thừa của 2 (`AX_TYPE_INVALID_ALIGN`) và cấm kết hợp `@repr(packed)` với `@align(N)` trên cùng kiểu (`AX_TYPE_CONFLICTING_REPR`). Trên struct `@repr(packed)` / `@repr(packed(N))`, phép đọc/ghi giá trị trực tiếp (`let x = hdr.b`, `hdr.b = v`) tự động sinh lệnh truy cập lệch căn chỉnh an toàn, nhưng **cấm tuyệt đối** việc tạo `view<T>`, `mut_view<T>`, hoặc con trỏ căn chỉnh `*const T`/`*mut T` trỏ tới trường bị lệch căn chỉnh (`AX_TYPE_UNALIGNED_PACKED_REF`). Con trỏ mang không gian địa chỉ tường minh `@addr_space(N)` không tự động ép kiểu ngầm định sang không gian địa chỉ khác (`AX_TYPE_ADDR_SPACE_MISMATCH`).

---

## 1. Volatile Memory Model, Hardware Barriers & MMIO Register Wrappers (`AXS-MEM-001`..`006`)

### AXS-MEM-001 — Three-Protocol Memory Taxonomy: Ordinary vs Atomic vs Volatile (`AMEMLOW-20..48`, `AMEM-74..78`, `REQ-FFI-015`, `REQ-RES-173`)

Axiom partitions all memory accesses into three mutually exclusive semantic protocols (`tasks/0328 §1–16`, `tasks/0515 §92–94, §136–140`):

1. **Ordinary Memory Access (`Load` / `Store`)**: Subject to capability verification (`SPEC-11`) and full compiler optimization (CSE, GVN, DSE, LICM, SROA, load/store forwarding, vectorization) provided single-thread and `Happens-Before` semantics are preserved (`AMEMLOW-20..26`, `SPEC-70`).
2. **Atomic Memory Access (`Atomic<T>`, `MIR_STMT_ATOMIC`)**: Establishes indivisible read/write/RMW/CAS semantics and inter-thread `Happens-Before` synchronization according to explicit `Ordering` (`Relaxed`, `Acquire`, `Release`, `AcqRel`, `SeqCst`) as specified in `SPEC-31` (`AMEMLOW-28..40`, `AMEM-79..88`).
3. **Volatile Memory Access (`volatile_load`, `volatile_store`, `Volatile<T>`, `Mmio<T>`)**: Models **externally observable machine memory side effects** (memory-mapped I/O registers, DMA status words, shared hardware mailboxes, signal/interrupt state).
   - **Volatile $\ne$ Atomic (`AMEMLOW-41..42`, `AMEMLOW-45..46`, `AMEM-74..75`)**: A volatile access does NOT establish inter-thread `Happens-Before` edges and does NOT synchronize ordinary non-volatile memory across CPU threads.
   - **Mandatory Volatile Mediation for MMIO (`AMEMLOW-47`, `AMEM-132..133`, `REQ-FFI-015`)**: Hardware and MMIO registers accessed directly or across FFI boundaries MUST be mediated through explicit volatile operations (`volatile_load`, `volatile_store`) or volatile-typed register fields (`Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, `MmioWO<T>`), never through ordinary memory loads/stores that the optimizer is permitted to elide or coalesce.
   - **ABI & Optimization Preservation (`REQ-RES-173`)**: Every lowering stage (`THIR -> MIR -> OptIR -> LIR -> ABI -> Machine IR`) MUST preserve ownership, `Drop`, synchronization, atomic, volatile, FFI, async, and address-space semantics without silent downgrading.
[tasks/0328 §1–16, AMEMLOW-20..48; tasks/0515 §92–94, §136–140, AMEM-74..78, AMEM-132..134; 0128 §62; REQ-FFI-015, REQ-RES-173]

### AXS-MEM-002 — Primitive Volatile Intrinsics (`volatile_load`, `volatile_store`, `volatile_copy`, `volatile_set_memory`) & Exact-Width Non-Tearing Guarantees

The module `std.mem` (backed by `@intrinsic` declarations in `std/core/intrinsics.ax`) provides four primitive `unsafe` volatile intrinsics:

| Intrinsic | Canonical Signature | Preconditions & Semantics |
|---|---|---|
| `volatile_load` | `pub unsafe fn volatile_load<T: Copy>(src: *const T) -> T` | Performs one externally observable read of `size_of<T>()` bytes from `src`. Requires `src != null`, `(src as usize) % align_of<T>() == 0`, and initialized valid bits of `T`. |
| `volatile_store` | `pub unsafe fn volatile_store<T: Copy>(dst: *mut T, val: T)` | Performs one externally observable write of `val` (`size_of<T>()` bytes) to `dst`. Requires `dst != null` and `(dst as usize) % align_of<T>() == 0`. Never drops any prior value at `*dst`. |
| `volatile_copy` | `pub unsafe fn volatile_copy<T: Copy>(src: *const T, dst: *mut T, count: usize)` | Copies `count` elements of `T` from `src` to `dst` (overlap-safe) as an observable volatile sequence that cannot be elided by dead-store elimination even if `dst` is never read again in the function. |
| `volatile_set_memory` | `pub unsafe fn volatile_set_memory<T: Copy>(dst: *mut T, byte: u8, count: usize)` | Fills `count * size_of<T>()` bytes at `dst` with `byte` as a non-elidable volatile write effect (suitable for hardware buffer clearing and secure zeroization). |

1. **Type Restriction (`AX_UNSAFE_INVALID_VOLATILE_WIDTH`)**: `T` in `volatile_load<T>` and `volatile_store<T>` MUST satisfy `T: Copy` (`SPEC-10 AXS-OWN-003`). Instantiating a volatile operation or `Volatile<T>` / `Mmio<T>` wrapper with a `!Copy` type (or instantiating `Mmio<T>` / `MmioRO<T>` / `MmioWO<T>` with a type whose byte size is not in `{1, 2, 4, 8}`) is rejected at compile time with `AX_UNSAFE_INVALID_VOLATILE_WIDTH`.
2. **Exact Instruction Width & Non-Tearing Guarantee (`1, 2, 4, 8` bytes)**:
   - When `size_of<T>() == W` with $W \in \{1, 2, 4, 8\}$ and the pointer is naturally aligned to $W$ bytes ($(a \bmod W) == 0$), `volatile_load<T>` and `volatile_store<T>` MUST execute as **exactly one machine load or store instruction of width $W$ bytes**:
     - Width `1` (`u8`, `i8`, `bool`, 1-byte `@repr(C)`/`@repr(transparent)` struct): single 8-bit `MOV r8, m8` / `MOV m8, r8`.
     - Width `2` (`u16`, `i16`, 2-byte struct): single 16-bit `MOV r16, m16` / `MOV m16, r16`.
     - Width `4` (`u32`, `i32`, `f32`, `char`, 4-byte struct): single 32-bit `MOV r32, m32` / `MOV m32, r32`.
     - Width `8` (`u64`, `i64`, `usize`, `isize`, `f64`, `*const U`, `*mut U`, 8-byte struct): single 64-bit `MOV r64, m64` / `MOV m64, r64`.
   - **Strict Rejection of Tearing and Merging**: The compiler backend and peephole optimizer MUST NEVER split a 1-, 2-, 4-, or 8-byte volatile load/store into narrower byte accesses (no byte-by-byte tearing), MUST NEVER widen or coalesce two adjacent 32-bit volatile accesses into one 64-bit or 128-bit SIMD access (`tasks/0515 §149`), and MUST NEVER turn a volatile store into a read-modify-write bitfield instruction unless explicitly written as `modify` in source.
   - For composite `Copy` types with `size_of<T>() > 8` in `Volatile<T>` / `volatile_load` / `volatile_store`, the access lowers to a deterministic in-order sequence of naturally aligned word operations from lowest offset to highest offset without elision.
3. **Oracle (`--interp`) Verification**: In `compiler/interp/`, `volatile_load` and `volatile_store` validate non-nullness, natural alignment (`UB-03`), liveness/MMIO mapping (`UB-01`/`UB-02`), and initialization/bit validity (`UB-04`/`UB-05`), trapping any violation with `AX_UNSAFE_INTERP_UB` (exit code `125`), and record each volatile access in the deterministic volatile effect trace.
[0071 §31–32; tasks/0328 §15–16, §37–39, AMEMLOW-43..48, AMEMLOW-97; tasks/0515 §136–140, §149, AMEM-76..78, AMEM-122; SPEC-04 AXS-EXT-043, AXS-EXT-051]

### AXS-MEM-003 — Optimizer & Backend Non-Elision, Non-Coalescing & Non-Reordering Contract (`T508`)

1. **MIR Representation (`SPEC-04 AXS-EXT-043`)**:
   - Every `volatile_load`, `volatile_store`, and `Volatile<T>` / `Mmio*<T>` field access lowers in `compiler/mir/` to dedicated statements:
     - `MirStmtKind.VolatileLoad { dst: Place, src: Operand, width: u8, align: u8, addr_space: u8 }`
     - `MirStmtKind.VolatileStore { dst: Operand, val: Operand, width: u8, align: u8, addr_space: u8 }`
   - In `EffectInfo` and `MemorySSA` (`SPEC-70 AXS-OPT-013`, `tasks/0515 §94, §109`), every volatile operation carries `EffectSet = { Read, Write, Volatile }` and acts as a `MemoryDef` that clobbers the volatile ordering chain.
2. **Prohibited Optimizations on Volatile Accesses (`SPEC-70 AXS-OPT-021`, `SPEC-71 AXS-ALIAS-006`, `SPEC-72 AXS-LOOP-009`, `SPEC-77 AXS-MCOPT-025`)**:
   - **No Dead-Store or Dead-Load Elimination (`DSE` / `DCE`)**: Two consecutive `volatile_store(p, v1); volatile_store(p, v2)` to the exact same address `p` MUST both be emitted; an unused `let _ = volatile_load(p)` MUST still emit the load instruction (`AMEM-77`, `AMEM-122`).
   - **No Load/Store Forwarding (`GVN` / `CSE`)**: `let a = volatile_load(p); let b = volatile_load(p)` MUST emit two separate machine loads; `volatile_store(p, v); let a = volatile_load(p)` MUST emit the store followed by the load (`tasks/0328 §37`).
   - **No Reordering Across Volatile, Atomic, Fence, or I/O Operations**: The compiler MUST NOT reorder any two volatile accesses relative to each other (even to distinct addresses, because hardware device protocols depend on register access sequence), nor reorder a volatile access across a `compiler_fence`, hardware `fence`, atomic operation, or foreign call (`AMEM-93`).
   - **No Loop Hoisting (`LICM`) or Speculative Execution (`cmov`)**: A volatile load or store inside a loop (such as `while UART0.status & TX_READY == 0 {}`) MUST NOT be hoisted out of the loop by `LICM` and MUST NOT be executed speculatively on an untaken branch (`SPEC-77 AXS-MCOPT-012`).
3. **LIR Flagging (`SPEC-04 AXS-EXT-051`)**: In `compiler/lir/`, volatile loads and stores set `LIR_MEM_FLAG_VOLATILE` (`flags |= 0x1`) on `LirInst.Load` / `LirInst.Store`, which blocks LIR-level CSE, DSE, instruction scheduling across volatile ops, and post-RA peephole load/store elimination.
[0161 §30–31; 0162 §9–12, §32; tasks/0328 §37, AMEMLOW-43..44, AMEMLOW-92..97; tasks/0515 §109, §112–115, §120, AMEM-76..78, AMEM-93, AMEM-122]

### AXS-MEM-004 — Compiler Barriers vs Hardware Memory Barriers (`compiler_fence`, `memory_barrier`, `read_barrier`, `write_barrier`)

Axiom strictly separates **compiler scheduling barriers** from **CPU/hardware memory fences** (`tasks/0328 §13–14 AMEMLOW-90..91`, `tasks/0515 §89–90 AMEM-89..90`, `SPEC-31 AXS-ATM-025/044`):

| Function (`std.mem` / `std.sync.atomic`) | Kind | x86-64 Machine Lowering | Semantics |
|---|---|---|---|
| `compiler_fence(order: Ordering)` | Compiler barrier (`0` machine bytes) | Emits `LirInst.CompilerFence(order)` (`0` encoded bytes) | Prevents the compiler from moving memory reads/writes across the barrier according to `order` (`Acquire`, `Release`, `AcqRel`, `SeqCst`); sufficient for single-CPU interrupt/signal handler ordering. |
| `memory_barrier()` (alias of `fence(Ordering.SeqCst)` / hardware full barrier) | CPU full memory fence | `MFENCE` (`0F AE F0`) | Drains the CPU store buffer and serializes all prior loads and stores before any subsequent load or store executes globally across cores and coherent bus agents. |
| `write_barrier()` (`sfence`) | CPU store fence | `SFENCE` (`0F AE F8`) | Orders all preceding stores (including non-temporal/WC stores and MMIO writes) before any subsequent store becomes globally visible. |
| `read_barrier()` (`lfence`) | CPU load / dispatch serializing fence | `LFENCE` (`0F AE E8`) | Serializes all preceding load instructions before any subsequent instruction executes. |

Volatile accesses alone do **not** emit implicit `MFENCE`/`SFENCE`/`LFENCE` instructions (`AMEM-78`, `AMEMLOW-48`); when a device datasheet or weakly ordered bus requires a hardware barrier between MMIO accesses or between DMA buffer writes and an MMIO doorbell store, systems code calls `write_barrier()` or `memory_barrier()` explicitly.
[tasks/0328 §13–14, §39, AMEMLOW-48, AMEMLOW-90..91; tasks/0515 §139, AMEM-78, AMEM-89..90; SPEC-31 AXS-ATM-025, AXS-ATM-044]

### AXS-MEM-005 — Typed Volatile & MMIO Register Wrappers (`Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, `MmioWO<T>`) & Direct Field Projection Lowering (`ADR-0001 §2`)

In `std/mem/mmio.ax`, Axiom defines four `@repr(transparent)` lang-item wrapper types (`SPEC-04 AXS-EXT-020, AXS-EXT-023, AXS-EXT-043`, `ADR-0001 §2`):

| Wrapper Type (`std.mem`) | Lang Item | Allowed `T` | Access Permissions | Primary Use |
|---|---|---|---|---|
| `Volatile<T>` | `LangItem.Volatile` | `T: Copy` | Read + Write + RMW | Volatile memory cells, shared DMA descriptors, interrupt flags |
| `Mmio<T>` | `LangItem.Mmio` | `T: Copy` with `size_of<T>() in {1, 2, 4, 8}` | Read + Write + RMW | Read/write hardware MMIO registers |
| `MmioRO<T>` | `LangItem.MmioRO` | `T: Copy` with `size_of<T>() in {1, 2, 4, 8}` | **Read-Only** | Hardware status, FIFO count, and ID registers |
| `MmioWO<T>` | `LangItem.MmioWO` | `T: Copy` with `size_of<T>() in {1, 2, 4, 8}` | **Write-Only** | Hardware command, FIFO TX, and clear-on-write strobe registers |

1. **Physical Layout Identity**: Each wrapper has the exact `size_of<T>()` and `align_of<T>()` of its inner type `T` (`@repr(transparent)`) and zero runtime header overhead.
2. **Compiler-Lowered Ordinary Field Access (`ADR-0001 §2`)**:
   - When a struct field `r.reg` has type `Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, or `MmioWO<T>`:
     - Evaluating `r.reg` in a value context (e.g. `let s: u32 = uart.status`, `while (uart.status & TX_READY) == 0u32 {}`) automatically unwraps `T` and lowers in `compiler/mir/` to `VolatileLoad` of width `size_of<T>()` from the address of `r.reg`.
     - Assigning `r.reg = val` where `val: T` (e.g. `uart.ctrl = 1u32`, `uart.tx_data = byte`) automatically lowers in `compiler/mir/` to `VolatileStore` of width `size_of<T>()` to the address of `r.reg`.
     - Compound assignment `r.reg |= mask` on `Volatile<T>` or `Mmio<T>` lowers to one `VolatileLoad` followed by the bitwise operation and one `VolatileStore`.
   - This eliminates pointer-cast and call-site ceremony after an `@at` / `@addr` declaration (`ADR-0001 §2`) while guaranteeing exact single-width volatile instructions.
3. **Prohibition of Ordinary `mut_view<T>` into Inner Storage**: Taking an ordinary `view<T>` or `mut_view<T>` to the inner value `T` inside `Volatile<T>` / `Mmio*<T>` is forbidden (only `view<Mmio<T>>` / `mut_view<Mmio<T>>` or `*mut T` via `.as_ptr()` is permitted), preventing safe code from bypassing volatile access semantics.
[ADR-0001 §2–4; SPEC-04 AXS-EXT-020, AXS-EXT-023, AXS-EXT-043; 0097 AOS-26..30; tasks/0328 §15–16, §39]

### AXS-MEM-006 — Read-Only (`MmioRO<T>`) / Write-Only (`MmioWO<T>`) Enforcement & Register Bit Manipulation API (`T509`)

1. **Compile-Time Direction Enforcement**:
   - Writing to a field or value of type `MmioRO<T>` (`uart.status = 0u32`, `uart.status |= 1u32`, or calling `.write(...)` / `.modify(...)`) is rejected at compile time with `AX_TYPE_MMIO_WRITE_READONLY`.
   - Reading from a field or value of type `MmioWO<T>` (`let x = uart.tx_fifo`, `uart.tx_fifo |= 1u32`, or calling `.read()` / `.modify(...)`) is rejected at compile time with `AX_TYPE_MMIO_READ_WRITEONLY`.
2. **Explicit Method & Bitfield Helper Surface (`std/mem/mmio.ax`, `0067 §11–13`, `0072 §14–17`)**:
   - Axiom deliberately excludes C-style struct bitfields (`a: u8 : 3`) from the Core type system because C bitfield packing, endianness, and RMW atomicity are ABI-fragile (`0067 §11`, `0072 §14–16 AREP-15`). Instead, `Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, and `MmioWO<T>` (and integer bit helpers in `std.mem`) provide explicit, zero-overhead methods:
     - `fn read(self: view<Self>) -> T` (on `Volatile<T>`, `Mmio<T>`, `MmioRO<T>`): single volatile load.
     - `fn write(self: mut_view<Self>, val: T)` (on `Volatile<T>`, `Mmio<T>`, `MmioWO<T>`): single volatile store.
     - `fn modify(self: mut_view<Self>, f: fn(T) -> T)` (on `Volatile<T>`, `Mmio<T>`): performs `let old = self.read(); self.write(f(old))`.
     - Bitmask helpers on integer registers (`T in {u8, u16, u32, u64, usize}`):
       - `fn set_bits(self: mut_view<Self>, mask: T)` $\equiv$ `self.write(self.read() | mask)`
       - `fn clear_bits(self: mut_view<Self>, mask: T)` $\equiv$ `self.write(self.read() & !mask)`
       - `fn test_bits(self: view<Self>, mask: T) -> bool` $\equiv$ `(self.read() & mask) != 0`
       - `pub fn extract_bits<T>(val: T, start: u32, width: u32) -> T` and `pub fn insert_bits<T>(val: T, start: u32, width: u32, field_val: T) -> T` in `std.mem` for multi-bit register fields.
[0067 §11–13; 0072 §14–17 AREP-15; ADR-0001 §2; tasks/0328 §15–16, §30]

---

## 2. Untagged Unions, Uninitialized Storage (`MaybeUninit<T>`, `ManuallyDrop<T>`) & Bitcast Semantics (`AXS-MEM-010`..`015`)

### AXS-MEM-010 — Untagged `union` Declarations & Physical Layout (`0072 §1–13`, `AREP-13`, `T507`)

1. **Syntax & Item Representation (`SPEC-02 AXS-GRM-038`, `SPEC-04 AXS-EXT-021, AXS-EXT-030`)**:
   - An untagged union is declared with the `union` keyword (`ItemKind.Union`, `AdtKind.Union`):
     ```axiom
     @repr(C)
     pub union RegisterValue {
         pub raw: u32,
         pub f: f32,
         pub bytes: [4]u8,
     }
     ```
   - Unlike `enum` (which is a type-safe tagged sum type where the compiler tracks the active discriminant), a `union` has **no implicit discriminant tag, no object header, and no runtime metadata** (`AREP-13`).
2. **Overlapping Storage Layout (`0072 §4, §13`)**:
   - For a `union U` with fields $f_0: T_0, \dots, f_{k-1}: T_{k-1}$:
     - Every field $f_i$ is placed at **byte offset `0`** ($\text{offset}(f_i) = 0$).
     - The natural alignment of `U` is $A = \max(\{1\} \cup \{\text{align\_of}\langle T_i \rangle()\})$ (modified by `@align(N)` or `@repr(packed(N))` if present).
     - The size of `U` is $S = \text{align\_up}(\max(\{0\} \cup \{\text{size\_of}\langle T_i \rangle()\}),\; A)$.
   - Under both default layout and `@repr(C)`, all fields start at offset `0` and share the same $[0, S)$ storage block. A `@repr(C)` union is FFI-safe whenever all of its field types are FFI-safe (`SPEC-50 AXS-UNS-031`).
[0072 §1–4, §13, §57 AREP-13; SPEC-02 AXS-GRM-038; SPEC-04 AXS-EXT-021, AXS-EXT-030]

### AXS-MEM-011 — Union Ownership & Field Type Restrictions (`Copy` or `ManuallyDrop<T>`, `AREP-14`, `T507`)

Because an untagged `union` does not track which variant is currently active at runtime, automatic scope-exit `Drop` cannot know which field to destroy (`0072 §5–6 AREP-14`). Therefore:

1. **Field Constraint (`AX_TYPE_UNION_NON_COPY_FIELD`)**: Every field $f_i: T_i$ of a `union` declaration MUST either:
   - satisfy `T_i: Copy` (`SPEC-10 AXS-OWN-003`), OR
   - be an explicit `ManuallyDrop<U>` wrapper (`AXS-MEM-013`).
   Declaring a `union` field with a `!Copy` type that is not wrapped in `ManuallyDrop<T>` (such as `String`, `Vec<T>`, `Box<T>`, or a struct implementing `Drop`) is rejected at compile time with `AX_TYPE_UNION_NON_COPY_FIELD` (`data.field`, `data.field_type`).
2. **`Copy` and `Drop` Behavior of the Union**:
   - A `union` whose fields are all `Copy` is automatically `Copy` when annotated with `@derive(Copy, Clone)` or when all fields are `Copy` in `@repr(C)`.
   - A `union` never generates automatic per-field `Drop` glue; if cleanup is required for a `ManuallyDrop<U>` variant, the user implements custom `Drop` on the `union` (or enclosing tagged struct) and calls `unsafe { ManuallyDrop.drop(mut_view(self.field)) }`.
[0072 §5–6, §57 AREP-14; SPEC-10 AXS-OWN-003; SPEC-12 AXS-DROP-002]

### AXS-MEM-012 — Union Initialization, Safe Field Writes, `unsafe` Field Reads & Pattern Matching (`0072 §10–12`, `AREP-16`, `T507`)

1. **Single-Field Literal Initialization (`AX_TYPE_UNION_INIT_FIELD_COUNT`)**:
   - A `union` literal initializes **exactly one** field using canonical `=` field syntax:
     ```axiom
     let mut u = RegisterValue { raw = 0x3F80_0000u32 }
     ```
   - Constructing a `union` literal with zero fields or more than one field (`RegisterValue { raw = 1u32, f = 1.0f32 }`) is rejected at compile time with `AX_TYPE_UNION_INIT_FIELD_COUNT`.
   - Union literal construction is **safe** because initializing one field initializes its byte range without reading an unverified interpretation.
2. **Safe Field Writes**:
   - Assigning to a `union` field (`u.raw = 42u32` or `u.f = 1.5f32`) overwrites the overlapping storage without running `Drop` (since all fields are `Copy` or `ManuallyDrop<T>`) and is permitted in **safe** code.
3. **Mandatory `unsafe` for Union Field Reads & Capabilities (`AX_UNSAFE_REQUIRED`)**:
   - Reading any field of a `union` (`let x = u.f`, `u.raw + 1u32`), taking a capability (`view(u.f)`, `mut_view(u.f)`), or pattern matching on a `union` field (`match u { RegisterValue { raw = r } => ... }`) may reinterpret bytes written through another field (`type punning`, `AREP-16`) or read uninitialized trailing bytes of a wider variant.
   - Therefore, reading a `union` field, borrowing a `union` field as `view`/`mut_view`, or matching a `union` pattern outside an `unsafe` context is rejected at compile time with `AX_UNSAFE_REQUIRED` (`data.operation = "union_field"`, `SPEC-50 AXS-UNS-002`).
   - Inside `unsafe` (and under `--interp`), reading a union field `u.f` checks that all bytes $[0, \text{size\_of}\langle T_f \rangle())$ are `Init` (`UB-04`) and satisfy the bit-validity invariant of $T_f$ (`UB-05`, `SPEC-50 AXS-UNS-013`).
[0072 §10–12, §57 AREP-16; SPEC-50 AXS-UNS-002, AXS-UNS-013]

### AXS-MEM-013 — Uninitialized Storage (`MaybeUninit<T>`) & Manual Destruction (`ManuallyDrop<T>`) (`AMEMLOW-60..64`, `AMEM-39..46`, `T509`)

1. **`MaybeUninit<T>` (`std/mem/maybe_uninit.ax`)**:
   - `@repr(transparent)` wrapper `pub union MaybeUninit<T> { uninit: (), value: ManuallyDrop<T> }` with `size_of<MaybeUninit<T>>() == size_of<T>()` and `align_of<MaybeUninit<T>>() == align_of<T>()`.
   - Unlike an ordinary binding `let x: T` (which `compiler/own/` forbids reading before definite initialization, `INV-SEM-004`), a `MaybeUninit<T>` value is considered initialized at the container level while its inner bytes may be `Uninit` (`AMEM-45`).
   - Dropping a `MaybeUninit<T>` is a no-op (never runs `T`'s `Drop`).
   - Canonical API in `std.mem`:
     - `MaybeUninit.uninit() -> MaybeUninit<T>` (safe): creates storage with all bytes marked `Uninit` in `--interp`.
     - `MaybeUninit.zeroed() -> MaybeUninit<T>` (safe): creates storage with all bytes initialized to `0x00`.
     - `MaybeUninit.new(val: T) -> MaybeUninit<T>` (safe): creates storage initialized with `val`.
     - `fn write(self: mut_view<MaybeUninit<T>>, val: T) -> mut_view<T>` (safe): writes `val` into the storage without dropping prior bytes and returns a safe `mut_view<T>`.
     - `fn as_ptr(self: view<MaybeUninit<T>>) -> *const T` and `fn as_mut_ptr(self: mut_view<MaybeUninit<T>>) -> *mut T` (safe).
     - `unsafe fn assume_init(self: MaybeUninit<T>) -> T` (`unsafe`): transfers ownership of the inner `T`. Calling `assume_init()` when any non-padding byte of `T` is `Uninit` (`UB-04`) or when the bytes violate `T`'s bit-validity invariant (`UB-05`, e.g. `MaybeUninit<bool>.zeroed()` is valid `false`, whereas `MaybeUninit<view<i32>>.zeroed().assume_init()` is null-view `UB-05`) traps deterministically in `--interp` with `AX_UNSAFE_INTERP_UB`.
2. **`ManuallyDrop<T>` (`std/mem/manually_drop.ax`)**:
   - `@repr(transparent)` wrapper `pub struct ManuallyDrop<T> { value: T }` with identical size, alignment, and ABI to `T`, but for which automatic compiler `Drop` elaboration is suppressed (`needs_drop<ManuallyDrop<T>>() == false`).
   - Canonical API: `ManuallyDrop.new(val: T) -> ManuallyDrop<T>` (safe), `ManuallyDrop.into_inner(slot: ManuallyDrop<T>) -> T` (safe), `fn deref(self: view<ManuallyDrop<T>>) -> view<T>` (safe), `fn deref_mut(self: mut_view<ManuallyDrop<T>>) -> mut_view<T>` (safe), and `unsafe fn drop(slot: mut_view<ManuallyDrop<T>>)` (`unsafe`, runs `Drop` in place; double-drop or subsequent read is `UB-10`).
[tasks/0328 §24–25, AMEMLOW-60..64; tasks/0515 §151–152, AMEM-39..46; SPEC-50 AXS-UNS-013, AXS-UNS-015]

### AXS-MEM-014 — Padding Non-Semantics, Explicit Endianness & Byte Reinterpretation (`REQ-FFI-031`, `REQ-RES-137`, `REQ-RES-163`, `AREP-08`, `AREP-22`)

1. **Padding Is Not Semantic Data (`REQ-FFI-031`, `REQ-RES-137`, `0072 §26–28 AREP-22`)**:
   - Alignment padding bytes inside a `struct`, `enum`, or `union` do not hold semantic data and are not guaranteed to be initialized or preserved across value moves/copies (`AMEM-152`).
   - Compiler-generated equality (`==`), hashing (`Hash`), and FFI marshalling MUST never treat all `size_of<T>()` raw struct bytes as meaningful (`REQ-FFI-031`, `REQ-RES-138`); structural `==` compares field values, never padding bytes.
2. **Endian Independence & Explicit Boundary Conversion (`REQ-RES-163`, `0067 §24–26 AREP-08`, `0072 §30–31`)**:
   - Ordinary Axiom scalar types (`u16`, `u32`, `u64`, `u128`, etc.) have target-independent mathematical value semantics (`AREP-08`); there is no global `@big_endian` mode (`0067 §25`).
   - Endianness is explicit at serialization, network wire format, device register, and FFI boundaries (`REQ-RES-163`, `AMEMLOW-69..71`, `AMEM-109..110`) via `.to_le_bytes()`, `.to_be_bytes()`, `.to_ne_bytes()`, `from_le_bytes`, `from_be_bytes`, and `byte_swap` (`SPEC-40 AXS-INT-031`).
[0067 §24–26, §39 AREP-08; 0072 §26–31, §57 AREP-22; 0138 §19; tasks/0328 §28–29, AMEMLOW-69..71; tasks/0367 §82; REQ-FFI-031, REQ-RES-137, REQ-RES-163]

### AXS-MEM-015 — `bitcast<From, To>(v: From) -> To` vs Semantic `CAST` (`as`) & Pointer Casts (`REQ-RES-160`, `REQ-RES-161`, `AREP-10`, `AREP-18..19`, `T509`)

1. **Three Distinct Conversion Classes (`REQ-RES-160`, `0067 §35–36 AREP-10`, `0072 §7–9, §51 AREP-18`)**:
   - Axiom forbids an unrestricted C/Rust-style `transmute<A, B>` joker (`ADR-0013 §2`, `0072 §51 AREP-18`) and strictly separates:
     1. **Value Conversion (`CAST`, `as` / `From` / `TryFrom`)**: Converts numeric value (`3i32 as f32 == 3.0f32`), potentially changing bit representation (`SPEC-40 AXS-INT-040`).
     2. **Bit Reinterpretation (`BITCAST`, `std.mem.bitcast<From, To>(v: From) -> To`)**: Reinterprets the exact bit pattern of `v` as type `To` without changing any bits (`bitcast<f32, u32>(1.0f32) == 0x3F80_0000u32`).
     3. **Pointer Reinterpretation (`p as *const U` / `p as *mut U`)**: Reinterprets a machine address while preserving pointer provenance (`SPEC-50 AXS-UNS-011`).
2. **Compile-Time & Validity Preconditions for `bitcast<From, To>` (`REQ-RES-161`, `AX_TYPE_BITCAST_SIZE_MISMATCH`)**:
   - `std.mem.bitcast<From, To>(v: From) -> To` requires at compile time:
     - `size_of<From>() == size_of<To>()` (`AX_TYPE_BITCAST_SIZE_MISMATCH` if sizes differ);
     - Both `From: Copy` and `To: Copy` with defined fixed layout (primitive integers, floats, SIMD `Vector<T, N>`, fixed arrays `[N]T`, or `@repr(C)` / `@repr(transparent)` structs/unions of `Copy` fields; `Repr.Axiom` structs with unspecified layout, `view`/`mut_view`, slices, and `!Copy` types are rejected with `AX_TYPE_BITCAST_SIZE_MISMATCH`).
   - **Safe vs `unsafe` Bitcast**:
     - When every bit pattern of size `size_of<From>()` is a valid representation of `To` (all fixed-width integers `i8..i128`/`u8..u128`/`isize`/`usize`, `f32`/`f64`, SIMD vectors, and arrays/`@repr(C)` structs thereof without padding-to-non-padding reads), `bitcast<From, To>(v)` is **safe**.
     - Reinterpreting raw bytes into a type with restricted bit patterns (`bool`, `char`, `enum`, function pointers) requires `unsafe { std.mem.bitcast_unchecked<From, To>(v) }` (or `union` field read inside `unsafe`) and traps invalid bit patterns with `UB-05` (`AX_UNSAFE_INTERP_UB`) in `--interp` (`0072 §52–54 AREP-19`).
[0067 §35–36, §39 AREP-10; 0072 §7–9, §51–54, §57 AREP-18..19; ADR-0013 §2; tasks/0328 §30; tasks/0367 §82; tasks/0515 AMEM-61..62; REQ-RES-160, REQ-RES-161]

---

## 3. Physical Layout Control (`@repr(C)`, `@repr(packed)`, `@align(N)`), Unaligned Access & Address Spaces (`AXS-MEM-020`..`024`)

### AXS-MEM-020 — Core Representation & ABI Freeze Contract (`REQ-ABI-063`, `REQ-CORE-449`, `REQ-FFI-099`, `REQ-RES-136`, `AREP-01..12`)

1. **Frozen Core ABI & Layout Foundation (`REQ-CORE-449`, `REQ-RES-136`, `REQ-FFI-099`, `SPEC-04 AXS-EXT-025`)**:
   - Before backend code generation, the compiler's layout engine (`compiler/types/` / `layout_of(TypeId)`) deterministically computes for every sized type `T`:
     $$\text{Layout}(T) = \{\text{size}: \text{usize},\; \text{align}: \text{usize},\; \text{stride}: \text{usize},\; \text{fields}: [\text{Offset}],\; \text{abi\_class}: \text{AbiClass}\}$$
     where $\text{align}$ is a positive power of two, $\text{stride} = \text{align\_up}(\text{size}, \text{align})$, and $\text{size} == \text{stride}$ for all standard and `@repr(C)` types (`0067 §8, §21–23`).
   - Alignment is a mandatory component of both physical layout correctness (`REQ-RES-136`, `AREP-06`) and FFI boundary validity (`REQ-FFI-099`, `tasks/0413 §70`).
   - `std.mem` exposes compile-time layout introspection: `size_of<T>() -> usize`, `align_of<T>() -> usize`, `stride_of<T>() -> usize`, and `offset_of(Type, field) -> usize` (valid on `@repr(C)`, `@repr(packed)`, and `@repr(transparent)` structs/unions).
2. **Explicit Representation Matrix (`REQ-ABI-063`, `REQ-ABI-012/044/052/061/064/065/093/098/100/103`, `REQ-FFI-013/018/029/043/078/097`)**:
   - **Default `Repr.Axiom` (`REQ-ABI-044`, `REQ-ABI-061`, `REQ-ABI-093`, `REQ-ABI-103`, `AREP-01..02`)**: Default struct/enum layouts, `pub fn` visibility, closure environments (`REQ-ABI-100`), `async` state machines (`REQ-ABI-100`), and `dyn Trait` fat-pointer metadata (`REQ-ABI-052`, `REQ-ABI-065`, `REQ-FFI-043`) do NOT freeze binary layout or equal C ABI; the compiler may reorder fields or apply niche optimizations (`AREP-05`) as long as boundary contracts are satisfied (`REQ-ABI-061`).
   - **`@repr(C)` (`REQ-ABI-063`, `REQ-FFI-013`, `REQ-FFI-029`, `REQ-ABI-098`)**: Freezes field declaration order, padding, alignment, and size to match the target C ABI algorithm (`offset_i = align_up(offset_{i-1} + size_{i-1}, align_i)`), prohibiting compiler field reordering (`REQ-ABI-063`, `REQ-FFI-029`). Axiom `enum`s are not C integers/unions unless annotated with `@repr(C)` / explicit integer representation (`REQ-FFI-097`).
   - **`@repr(transparent)` (`REQ-ABI-064`, `0067 §5–6`, `AREP-12`)**: Guarantees identical size, alignment, and calling-convention ABI classification to its single non-ZST inner field while preserving nominal type identity (`AX_FFI_INVALID_TRANSPARENT` if $\ne 1$ non-ZST field).
   - **Opaque Foreign Types (`REQ-ABI-012`, `REQ-FFI-078`)**: `extern "C" { type T; }` has unknown internal layout and may only be manipulated behind `*const T` / `*mut T` (`AX_FFI_OPAQUE_BY_VALUE`).
[0067 §1–8, §21–23, §31–39, AREP-01..12; 0104 §54; 0119 §258–259; 0129 §71; 0131 §65, §80; 0132 §13–15, §62 ADATA-29..30; 0133 §48; 0138 §10, §57; 1066 §2.D; tasks/0367 §82; tasks/0413 §70; REQ-ABI-012, REQ-ABI-044, REQ-ABI-052, REQ-ABI-061, REQ-ABI-063, REQ-ABI-064, REQ-ABI-065, REQ-ABI-093, REQ-ABI-098, REQ-ABI-100, REQ-ABI-103, REQ-CORE-449, REQ-FFI-013, REQ-FFI-018, REQ-FFI-029, REQ-FFI-043, REQ-FFI-078, REQ-FFI-097, REQ-FFI-099, REQ-RES-136]

### AXS-MEM-021 — `@align(N)` Over-Alignment Specification (`0067 §7–8`, `SPEC-04 AXS-EXT-021/091`, `T507`)

1. **Syntax & Validation (`AX_TYPE_INVALID_ALIGN`)**:
   - `@align(N)` may be attached to a `struct`, `enum`, or `union` declaration (or field), where `N` is an integer literal or compile-time constant expression.
   - `N` MUST be a positive power of two in the range $1 \le N \le 2^{29}$ ($536\,870\,912$). If `N == 0`, `N` is not a power of two (`(N & (N - 1)) != 0`), or `N > 2^29`, the compiler emits `AX_TYPE_INVALID_ALIGN` (`data.align = N`).
2. **Layout Effect (`0067 §7–8`)**:
   - `@align(N)` **raises** (never lowers) the alignment of the type:
     $$\text{align}(T) = \max(\text{natural\_align}(T),\; N)$$
   - The total size of $T$ is rounded up to a multiple of $\text{align}(T)$:
     $$\text{size}(T) = \text{align\_up}(\text{unpadded\_size}(T),\; \text{align}(T))$$
   - Note (`0067 §7`): If `struct CacheHeader { tag: u32 }` has `@align(64)`, then `align_of<CacheHeader>() == 64` and `size_of<CacheHeader>() == 64` (so arrays `[K]CacheHeader` maintain 64-byte element alignment at every index $i$), while internal field offsets precede trailing tail padding.
   - Attempting to use `@align(N)` to reduce alignment below a field's natural alignment does not shrink alignment; lowering alignment requires `@repr(packed)` or `@repr(packed(N))` (`AXS-MEM-022`).
[0067 §7–8; 0132 §14–16; SPEC-04 AXS-EXT-021, AXS-EXT-091]

### AXS-MEM-022 — `@repr(packed)` and `@repr(packed(N))` Layout Rules (`0067 §9–10`, `AREP-07`, `REQ-ABI-036`, `REQ-ABI-041`, `REQ-FFI-098`, `REQ-RES-135`, `T507`)

1. **Packing Factor $P$**:
   - `@repr(packed)` is shorthand for `@repr(packed(1))` ($P = 1$).
   - `@repr(packed(N))` specifies a maximum field alignment cap $P = N$, where $N$ MUST be a positive power of two ($1 \le N \le 2^{29}$); a non-power-of-two $N$ is rejected with `AX_TYPE_INVALID_ALIGN`.
2. **Field Offset & Total Size Computation**:
   - Fields are laid out in declaration order (`@repr(packed)` implies fixed declaration order like `@repr(C)`):
     - Effective alignment of field $f_i: T_i$ is $a'_i = \min(\text{align\_of}\langle T_i \rangle(),\; P)$.
     - Offset of field $f_i$ is $\text{offset}(f_i) = \text{align\_up}(\text{offset}(f_{i-1}) + \text{size\_of}\langle T_{i-1} \rangle(),\; a'_i)$.
     - Overall alignment of the struct is $A_{\text{struct}} = \min(\max_i \text{align\_of}\langle T_i \rangle(),\; P)$ (which is `1` for `@repr(packed)`).
     - Overall size is $S_{\text{struct}} = \text{align\_up}(\text{offset}(f_{k-1}) + \text{size\_of}\langle T_{k-1} \rangle(),\; A_{\text{struct}})$ (no inter-field or tail padding when $P = 1$).
3. **Conflicting Representation Attributes (`AX_TYPE_CONFLICTING_REPR`, `AX_CONC_INVALID_ATOMIC_ALIGNMENT`)**:
   - Combining `@repr(packed)` / `@repr(packed(N))` with `@align(M)` or `@repr(transparent)` on the same type is contradictory (packing lowers alignment while `@align` raises it) and is rejected at compile time with `AX_TYPE_CONFLICTING_REPR`.
   - Placing an `Atomic<T>` field inside a `@repr(packed)` struct where effective field alignment $< \text{size\_of}\langle T \rangle()$ is rejected with `AX_CONC_INVALID_ATOMIC_ALIGNMENT` (`SPEC-31 AXS-ATM-011`).
[0067 §9–10, §39 AREP-06..07; 0113 §122; 0119 §226, §259; 0132 §16, §62 ADATA-31; tasks/0328 §27 AMEMLOW-67..68; tasks/0367 §82; tasks/0413 §70; REQ-ABI-036, REQ-ABI-041, REQ-FFI-098, REQ-RES-135]

### AXS-MEM-023 — Unaligned Packed Field Projections, Capability/Pointer Prohibition & `read_unaligned` / `write_unaligned` (`REQ-ABI-036`, `REQ-ABI-041`, `REQ-CAP-130`, `REQ-CAP-152`, `T507`, `T508`, `T509`)

1. **When a Packed Field Is Potentially Unaligned**:
   - In a `@repr(packed(P))` struct $S$, a field $f_i: T_i$ is **potentially unaligned** whenever $\text{align\_of}\langle T_i \rangle() > 1$ and either $\text{align\_of}\langle S \rangle() < \text{align\_of}\langle T_i \rangle()$ or $(\text{offset}(f_i) \bmod \text{align\_of}\langle T_i \rangle()) \ne 0$.
   - Conversely, a field with $\text{align\_of}\langle T_i \rangle() == 1$ (such as `u8`, `i8`, `bool`, `[N]u8`, or another `@repr(packed(1))` struct) is always aligned (`1 % 1 == 0`).
2. **Forbidden Capability & Aligned Pointer Creation (`AX_TYPE_UNALIGNED_PACKED_REF`, `REQ-ABI-036`, `REQ-ABI-041`, `0067 §9–10`)**:
   - Because every safe `view<T>`, `mut_view<T>`, and aligned raw-pointer dereference guarantees natural alignment $\text{align\_of}\langle T \rangle()$ (`SPEC-50 AXS-UNS-013`, `REQ-RES-136`, `REQ-FFI-099`), creating a capability or aligned pointer to a potentially unaligned packed field is **statically forbidden**:
     - `view(pkt.unaligned_field)` and `mut_view(pkt.unaligned_field)` are rejected at compile time with `AX_TYPE_UNALIGNED_PACKED_REF` (`data.field`, `data.field_align`, `data.packed_align`).
     - Passing `pkt.unaligned_field` to a parameter expecting an ephemeral `view<T>` or `mut_view<T>` (or calling a method taking `self: view<T>` / `mut_view<T>`) is rejected with `AX_TYPE_UNALIGNED_PACKED_REF` unless copied to a local temporary first (`let tmp = pkt.unaligned_field; f(tmp)`).
     - Taking `address_of(pkt.unaligned_field)` or `address_of_mut(pkt.unaligned_field)` directly as an aligned `*const T` / `*mut T` for normal `*p` dereference is rejected with `AX_TYPE_UNALIGNED_PACKED_REF` (with help `copy the field by value or pass the pointer to std.mem.read_unaligned / write_unaligned`).
3. **Permitted By-Value Reads/Writes & `read_unaligned` / `write_unaligned` (`T508`, `T509`)**:
   - **Direct By-Value Copy Read/Write**: Reading `let v: u32 = pkt.unaligned_field` (where `T_i: Copy`) or writing `pkt.unaligned_field = v` by value does not create an aligned reference; `compiler/mir/` and `compiler/lir/` lower the field load/store with `align = a'_i` (`LirInst.Load { align = 1 }` / `LirInst.Store { align = 1 }`), which x86-64 emits using unaligned-safe scalar instructions (`MOV`, never alignment-faulting `MOVAPS`/`MOVDQA`) and `--interp` executes with alignment check set to $a'_i$ (`0132 §16 ADATA-31`).
   - **Explicit Unaligned Pointer Intrinsics (`std.mem`)**:
     - `pub unsafe fn read_unaligned<T: Copy>(src: *const T) -> T`: reads `size_of<T>()` bytes from `src` assuming alignment `1` (requires `src != null`, live bounds, initialized valid bits of `T`; does **not** require `(src as usize) % align_of<T>() == 0`).
     - `pub unsafe fn write_unaligned<T: Copy>(dst: *mut T, val: T)`: writes `val` (`size_of<T>()` bytes) to `dst` assuming alignment `1` without dropping prior bytes.
4. **Raw/Foreign Pointer to Safe Capability Preconditions (`REQ-CAP-130`, `REQ-CAP-152`)**:
   - Converting any raw pointer (`*const T`, `*mut T`) or foreign FFI pointer into a safe capability (`view<T>`, `mut_view<T>`, `view<[T]>`, `mut_view<[T]>`) is restricted to `unsafe` blocks (`AX_UNSAFE_REQUIRED`, `REQ-CAP-152`).
   - At that boundary, the programmer MUST establish proof of: (a) non-null valid provenance, (b) live allocation bounds and lifetime containment, (c) **natural alignment** `(ptr as usize) % align_of<T>() == 0` (so an unaligned packed pointer can **never** be wrapped into `view<T>` or `mut_view<T>`, `REQ-CAP-130`, `REQ-FFI-099`), (d) initialized valid bit pattern, and (e) for `mut_view<T>`, exclusive mutation access (`REQ-CAP-130`). Once constructed via `MakeView` / `MakeMutView`, ordinary compile-time capability verification resumes (`SPEC-50 AXS-UNS-006`).
[0067 §9–10; 0113 §122; 0119 §226; 0132 §16, §62 ADATA-31; tasks/0328 §26–27, AMEMLOW-65..68; tasks/0413 §70; tasks/0445 §186.161 AFFI-40..42; tasks/0486 §78–80 ACAP-42..44; tasks/0515 AMEM-57..60; REQ-ABI-036, REQ-ABI-041, REQ-CAP-130, REQ-CAP-152, REQ-FFI-098, REQ-FFI-099, REQ-RES-135, REQ-RES-136]

### AXS-MEM-024 — Explicit Target & Device Address Spaces (`@addr_space(N)`, `AX_TYPE_ADDR_SPACE_MISMATCH`, `T507`)

1. **Address Space Model (`SPEC-04 AXS-EXT-020, AXS-EXT-042, AXS-EXT-051`, `tasks/0515 §84–88 AMEM-103..107`)**:
   - Every raw pointer type carries an explicit 8-bit address-space identifier `addr_space: u8` in `TypeKind.RawPtr { mutability, pointee, addr_space }`:

     | `addr_space` ID | Symbolic Name | Domain / Target Meaning |
     |---|---|---|
     | `0` (default) | `Host` / `Generic` | Default flat process virtual address space (`*const T`, `*mut T`) |
     | `1` | `Device` / `Global` | GPU / accelerator global device memory (`E22.2`) |
     | `2` | `Shared` | GPU workgroup shared memory (`E22.2`) |
     | `3` | `Constant` | Read-only constant bank / ROM address space |
     | `4` | `Local` / `Private` | Lane-private / thread-local register-spilled address space |
     | `5` | `Mmio` / `Io` | Non-cached device MMIO / peripheral bus space |
     | `6` | `Physical` | Unmapped physical RAM address space (kernel/bootloader page-table walk) |
     | `7..=255` | Target-Specific | Target-defined segments (e.g., x86-64 `GS = 256 / 7`, `FS = 257 / 8`) |

   - Surface syntax: `@addr_space(N) *const T` and `@addr_space(N) *mut T` (or type alias `type PhysPtr<T> = @addr_space(6) *mut T`), where `N` is an integer literal in `0..=255`. Unannotated `*const T` and `*mut T` always have `addr_space = 0`.
2. **Strict Disjointness & No Implicit Cross-Space Coercion (`AX_TYPE_ADDR_SPACE_MISMATCH`)**:
   - Two pointer types `@addr_space(M) *mut T` and `@addr_space(N) *mut T` with $M \ne N$ are **distinct, incompatible types** (`tasks/0515 §87 AMEM-104..105`).
   - Assigning, passing, or implicitly coercing a pointer of address space $M$ where a pointer of address space $N$ ($M \ne N$) is expected — or attempting to use an ordinary `p as *const U` cast across distinct address spaces — is rejected at compile time with `AX_TYPE_ADDR_SPACE_MISMATCH` (`data.expected_space = N`, `data.found_space = M`).
   - Creating a host `view<T>` or `mut_view<T>` directly from a non-host address-space pointer ($M \in \{1, 2, 4, 6\}$) without an explicit mapping/transfer contract is rejected with `AX_TYPE_ADDR_SPACE_MISMATCH` (`AMEM-105`).
   - Explicit cross-space pointer conversion is permitted **only** inside an `unsafe` block via `std.mem.addr_space_cast<FromPtr, ToPtr>(p: FromPtr) -> ToPtr`, which lowers to `MirCastKind.PtrAddrSpace` (`SPEC-04 AXS-EXT-042`).
[SPEC-04 AXS-EXT-020, AXS-EXT-042, AXS-EXT-051; tasks/0328 §18 AMEMLOW-82..87; tasks/0515 §84–88, AMEM-103..107, AMEM-143]

---

## 4. Diagnostics, Canonical Examples & Requirement Traceability (`AXS-MEM-050`..`053`)

### AXS-MEM-050 — Diagnostic Codes Owned or Referenced by `SPEC-51`

| Code | Area | Sev | Delivering Task | Condition & Normative Rule |
|---|---|---|---|---|
| `AX_TYPE_UNION_NON_COPY_FIELD` | `TYPE` | `error` | `T507` | A field of an untagged `union` is neither `Copy` nor wrapped in `ManuallyDrop<T>` (`AXS-MEM-011`). |
| `AX_TYPE_UNION_INIT_FIELD_COUNT` | `TYPE` | `error` | `T507` | A `union` literal initializes zero fields or more than one field (`AXS-MEM-012`). |
| `AX_TYPE_INVALID_ALIGN` | `TYPE` | `error` | `T507` | `@align(N)` or `@repr(packed(N))` specifies `N` that is `0`, not a power of two, or $> 2^{29}$ (`AXS-MEM-021`, `AXS-MEM-022`). |
| `AX_TYPE_CONFLICTING_REPR` | `TYPE` | `error` | `T507` | Conflicting representation attributes on the same type (e.g., `@repr(packed)` combined with `@align(N)` or `@repr(transparent)`) (`AXS-MEM-022`). |
| `AX_TYPE_UNALIGNED_PACKED_REF` | `TYPE` | `error` | `T507` | Taking `view(s.f)`, `mut_view(s.f)`, or an aligned `*const T` / `*mut T` reference to a potentially unaligned field `f` of a `@repr(packed)` / `@repr(packed(N))` struct (`AXS-MEM-023`). |
| `AX_TYPE_ADDR_SPACE_MISMATCH` | `TYPE` | `error` | `T507` | Implicit conversion or ordinary cast between pointers of different `@addr_space(N)` qualifiers, or creating a host `view`/`mut_view` from an unmapped non-host address space (`AXS-MEM-024`). |
| `AX_TYPE_BITCAST_SIZE_MISMATCH` | `TYPE` | `error` | `T509` | `std.mem.bitcast<From, To>(v)` called when `size_of<From>() != size_of<To>()` or when either type is not bitcast-eligible (`!Copy`, unsized, or `Repr.Axiom` aggregate) (`AXS-MEM-015`). |
| `AX_TYPE_MMIO_WRITE_READONLY` | `TYPE` | `error` | `T508` / `T509` | Writing to or calling `.write`/`.modify` on a read-only `MmioRO<T>` register field (`AXS-MEM-005`, `AXS-MEM-006`). |
| `AX_TYPE_MMIO_READ_WRITEONLY` | `TYPE` | `error` | `T508` / `T509` | Reading from or calling `.read`/`.modify` on a write-only `MmioWO<T>` register field (`AXS-MEM-005`, `AXS-MEM-006`). |
| `AX_UNSAFE_INVALID_VOLATILE_WIDTH` | `UNSAFE` | `error` | `T508` / `T509` | `volatile_load` / `volatile_store` / `Volatile<T>` instantiated with `!Copy`, or `Mmio<T>` / `MmioRO<T>` / `MmioWO<T>` instantiated with `size_of<T>() not in {1, 2, 4, 8}` (`AXS-MEM-002`, `AXS-MEM-005`). |
| `AX_UNSAFE_REQUIRED` | `UNSAFE` | `error` | `T501` / `T507` | Reading or pattern-matching a `union` field (`data.operation = "union_field"`), calling `volatile_load`/`volatile_store`/`read_unaligned`/`write_unaligned`/`assume_init`, or converting a raw pointer to `view`/`mut_view` outside an `unsafe` context (`AXS-MEM-002`, `AXS-MEM-012`, `AXS-MEM-013`, `AXS-MEM-023`). |
| `AX_UNSAFE_INTERP_UB` | `UNSAFE` | `error` | `T502` / `T508` | `--interp` detected misaligned volatile access (`UB-03`), `assume_init` on `Uninit` bytes (`UB-04`), or invalid bit pattern in `union` read / `bitcast_unchecked` / `assume_init` (`UB-05`) (exit code `125`). |

### AXS-MEM-051 — Canonical Positive Examples (`=` and `.` Syntax)

#### Example 1 — `Mmio<T>`, `MmioRO<T>`, `MmioWO<T>` Register Block & Volatile Lowering (`ADR-0001 §2`, `AXS-MEM-001`..`006`)
```axiom
module demo.mmio_uart

use std.mem.Mmio
use std.mem.MmioRO
use std.mem.MmioWO
use std.mem.write_barrier

const STATUS_TX_EMPTY: u32 = 0x0000_0001u32
const CTRL_ENABLE: u32 = 0x0000_0003u32

@repr(C)
pub struct UartRegs {
    pub ctrl: Mmio<u32>,
    pub status: MmioRO<u32>,
    pub tx_data: MmioWO<u8>,
    pub _pad: [3]u8,
    pub baud_div: Mmio<u32>,
}

pub fn uart_send_byte(uart: mut_view<UartRegs>, b: u8) {
    // Ordinary field syntax lowers to 32-bit VolatileStore / VolatileLoad (ADR-0001 §2, AXS-MEM-005):
    uart.ctrl = CTRL_ENABLE
    while (uart.status & STATUS_TX_EMPTY) == 0u32 {
        // Not hoisted out of loop by LICM (AXS-MEM-003)
    }
    // Single 8-bit volatile store (`MOV m8, r8`) to write-only FIFO register:
    uart.tx_data = b
    write_barrier()
}
```

#### Example 2 — Untagged `union`, `@repr(packed)`, `@align(N)`, `MaybeUninit<T>` & `bitcast` (`AXS-MEM-010`..`023`)
```axiom
module demo.layout_union

use std.mem.MaybeUninit
use std.mem.bitcast
use std.mem.size_of
use std.mem.align_of

@repr(C)
pub union WordOverlay {
    pub word: u32,
    pub halves: [2]u16,
    pub float_val: f32,
}

@repr(packed)
pub struct PackedNetHeader {
    pub tag: u8,
    pub seq_le: u32,
    pub flags: u16,
}

@align(64)
@repr(C)
pub struct CacheAlignedCounter {
    pub count: u64,
}

pub fn verify_layout_and_union() -> u32 {
    assert(size_of<PackedNetHeader>() == 7usize)
    assert(align_of<PackedNetHeader>() == 1usize)
    assert(align_of<CacheAlignedCounter>() == 64usize)
    assert(size_of<CacheAlignedCounter>() == 64usize)

    // Safe by-value write and read of unaligned packed fields (AXS-MEM-023):
    let mut hdr = PackedNetHeader { tag = 1u8, seq_le = 0x1122_3344u32, flags = 0x0007u16 }
    let seq_copy: u32 = hdr.seq_le
    hdr.seq_le = seq_copy + 1u32

    // Safe union initialization & field write; unsafe union field read (AXS-MEM-012):
    let mut ov = WordOverlay { float_val = 1.0f32 }
    let raw_bits: u32 = unsafe { ov.word }
    assert(raw_bits == 0x3F80_0000u32)
    assert(bitcast<f32, u32>(1.0f32) == raw_bits)

    // MaybeUninit<T> initialization transition (AXS-MEM-013):
    let mut slot: MaybeUninit<u32> = MaybeUninit.uninit()
    slot.write(hdr.seq_le)
    let init_val: u32 = unsafe { slot.assume_init() }
    return init_val
}
```

### AXS-MEM-052 — Canonical Negative Examples (`=` and `.` Syntax)

```axiom
module demo.layout_rejected

use std.mem.MmioRO
use std.mem.MmioWO
use std.mem.bitcast

// ERROR [AX_TYPE_UNION_NON_COPY_FIELD]: union field `name: String` is `!Copy` and not wrapped in `ManuallyDrop<T>` (AXS-MEM-011)
union BadUnion {
    id: u64,
    name: String,
}

@repr(C)
union FloatBits {
    u: u32,
    f: f32,
}

// ERROR [AX_TYPE_INVALID_ALIGN]: `@align(12)` is not a power of two (AXS-MEM-021)
@align(12)
struct BadAlign {
    x: u32,
}

// ERROR [AX_TYPE_CONFLICTING_REPR]: cannot combine `@repr(packed)` and `@align(16)` on the same struct (AXS-MEM-022)
@repr(packed)
@align(16)
struct ConflictingRepr {
    a: u8,
    b: u32,
}

@repr(packed)
struct PackedPkt {
    kind: u8,
    payload_len: u32,
}

@repr(C)
struct RegBlock {
    status: MmioRO<u32>,
    cmd: MmioWO<u32>,
}

fn rejected_cases(pkt: mut_view<PackedPkt>, regs: mut_view<RegBlock>, dev_p: @addr_space(1) *mut u32) {
    // ERROR [AX_TYPE_UNALIGNED_PACKED_REF]: cannot create `view<u32>` or `mut_view<u32>` to unaligned field of `@repr(packed)` struct (AXS-MEM-023)
    let v_len: view<u32> = view(pkt.payload_len)

    // ERROR [AX_TYPE_UNION_INIT_FIELD_COUNT]: union literal must initialize exactly one field (AXS-MEM-012)
    let fb = FloatBits { u = 1u32, f = 1.0f32 }

    // ERROR [AX_UNSAFE_REQUIRED]: reading a union field requires an `unsafe` block (AXS-MEM-012)
    let leak: u32 = fb.u

    // ERROR [AX_TYPE_MMIO_WRITE_READONLY]: cannot write to read-only `MmioRO<u32>` register (AXS-MEM-006)
    regs.status = 0u32

    // ERROR [AX_TYPE_MMIO_READ_WRITEONLY]: cannot read from write-only `MmioWO<u32>` register (AXS-MEM-006)
    let c: u32 = regs.cmd

    // ERROR [AX_TYPE_BITCAST_SIZE_MISMATCH]: `bitcast` requires identical `size_of` (`4 != 8`) (AXS-MEM-015)
    let bad_bits: u64 = bitcast<u32, u64>(1u32)

    // ERROR [AX_TYPE_ADDR_SPACE_MISMATCH]: cannot implicitly convert `@addr_space(1) *mut u32` to host `*mut u32` (AXS-MEM-024)
    let host_p: *mut u32 = dev_p
}
```

### AXS-MEM-053 — Requirement & Task Traceability Matrix (`T506`–`T510`)

| Requirement IDs | Domain / Summary | Normative Clauses in `SPEC-51` | Implementing / Verifying Tasks |
|---|---|---|---|
| `REQ-ABI-063`, `REQ-CORE-449`, `REQ-FFI-099`, `REQ-RES-136` | Freeze minimal Core ABI (scalars, aggregates, alignment, calling conventions); `@repr(C)` freezes field order, padding, and alignment; alignment is part of physical layout correctness and FFI validity | `AXS-MEM-020`, `AXS-MEM-021`, `AXS-MEM-022`, `AXS-MEM-023` | `T506` (spec), `T507` (sema/layout), `T508` (codegen), `T509` (std), `T510` (conformance) |
| `REQ-CAP-130`, `REQ-CAP-152` | Converting a raw or foreign pointer to `view<T>` / `mut_view<T>` is restricted to `unsafe` blocks and requires proof of validity, provenance, lifetime, natural alignment (forbidding unaligned packed fields), and exclusive mutation for `mut_view` before normal verification resumes | `AXS-MEM-023`, `AXS-MEM-050`, `AXS-MEM-052` | `T506`, `T507`, `T510` |
| `REQ-ABI-036`, `REQ-ABI-041`, `REQ-FFI-097`, `REQ-FFI-098`, `REQ-RES-135` | `@repr(packed)` omits alignment padding, belongs to system/unsafe domain, and cannot create invalid aligned references (`AX_TYPE_UNALIGNED_PACKED_REF`); Axiom enums do not implicitly equal C enums/unions | `AXS-MEM-010`, `AXS-MEM-020`, `AXS-MEM-022`, `AXS-MEM-023` | `T506`, `T507`, `T508`, `T510` |
| `REQ-FFI-015`, `REQ-RES-173` | Hardware and MMIO registers accessed across FFI or `@at` must use explicit volatile operations (`volatile_load`/`volatile_store`, `Volatile<T>`, `Mmio*<T>`); ABI and backend lowering preserve ownership, `Drop`, synchronization, atomic, volatile, FFI, async, and address-space semantics | `AXS-MEM-001`, `AXS-MEM-002`, `AXS-MEM-003`, `AXS-MEM-004`, `AXS-MEM-005`, `AXS-MEM-006` | `T506`, `T508`, `T509`, `T510` |
| `REQ-FFI-031`, `REQ-RES-137`, `REQ-RES-160`, `REQ-RES-161`, `REQ-RES-163` | Padding is not semantic data; `CAST` (`as`) and `BITCAST` (`bitcast`) are distinct; `bitcast` requires equal size and valid representation; endianness is explicit at serialization/device/FFI boundaries | `AXS-MEM-013`, `AXS-MEM-014`, `AXS-MEM-015` | `T506`, `T509`, `T510` |
| `REQ-ABI-012`, `REQ-ABI-044`, `REQ-ABI-052`, `REQ-ABI-061`, `REQ-ABI-064`, `REQ-ABI-065`, `REQ-ABI-093`, `REQ-ABI-098`, `REQ-ABI-100`, `REQ-ABI-103`, `REQ-FFI-013`, `REQ-FFI-018`, `REQ-FFI-029`, `REQ-FFI-043`, `REQ-FFI-078` | Explicit `@repr(C)` / `@repr(transparent)` / `@abi(stable)` vs compiler-controlled default struct, `dyn Trait`, closure, and async state-machine layouts; opaque foreign types hide internal layout | `AXS-MEM-020`, `AXS-MEM-050`, `AXS-MEM-053` | `T506`, `T507`, `T509`, `T510` |

## Sources

- `spec/decisions/ADR-0001-fixed-address-declarations.md` (`§1–7`)
- `spec/decisions/ADR-0013-core-extensibility-and-selfhost-subset.md` (`§2`)
- `docs/base/specs/0044 - AXIOM MEMORY ACCESS, POINTER & ALIASING v0.1.md`
- `docs/base/specs/0067 - Axiom Representation Model v0.1.md` (`§1–41, AREP-01..12`)
- `docs/base/specs/0071 - Axiom Memory Access Model v0.1.md` (`§1–60, AMEM-01..15`)
- `docs/base/specs/0072 - 1. Quyết định lớn union.md` (`§1–58, AREP-13..22`)
- `docs/base/specs/0097` (`AOS-26..30`), `0104` (`§54`), `0113` (`§122`), `0119` (`§226, §258–259`), `0128` (`§62`), `0129` (`§71`), `0131` (`§65, §80`), `0132` (`§13–16, §62, ADATA-29..31`), `0133` (`§48`), `0138` (`§10, §19, §57`), `0161` (`§30–31`), `0162` (`§9–12, §32`), `0163` (`§1–7`), `1066` (`§2.D`)
- `docs/base/tasks/0328 - BOOTSTRAP-069 — Axiom Low-Level Memory, Atomics, Volatile & Machine Access.md` (`§1–40, AMEMLOW-20..100`)
- `docs/base/tasks/0339`, `0367` (`§1–82, AABI-20..70`), `0413` (`§1–70, AFFI-20..64`), `0434` (`§92`), `0445` (`§186.161, AFFI-40..42`), `0452` (`§193.47, AABI-23..32`), `0475` (`§216.42–43, ASPEC-40`), `0486` (`§78–80, ACAP-42..44`)
- `docs/base/tasks/0515 - BOOTSTRAP-256 — AXIOM MEMORY ACCESS, LOADSTORE, ATOMICVOLATILE & MEMORY ORDERING LOWERING.md` (`§1–196, AMEM-20..170`)
- `spec/SPEC-03-core-semantics.md`
- `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-020`..`025`, `AXS-EXT-030`, `AXS-EXT-042`..`043`, `AXS-EXT-051`, `AXS-EXT-091`)
- `spec/SPEC-31-atomics.md` (`AXS-ATM-011`, `AXS-ATM-025`, `AXS-ATM-044`)
- `spec/SPEC-50-unsafe-ub-ffi.md` (`AXS-UNS-001`..`036`)
