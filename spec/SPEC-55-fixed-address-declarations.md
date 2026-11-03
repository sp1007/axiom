# SPEC-55 — Canonical Fixed-Address Declarations (`@at` / `@addr`), MMIO Overlay/Placement & Address Introspection Specification

Status: draft (T525, 2026-11-03)
Owner: axiom-architect
Consolidates: `spec/decisions/ADR-0001-fixed-address-declarations.md (§1–4, §7)`; `spec/requirements/OWNER.md (REQ-OWNER-001..005, REQ-OWNER-008)`; `specs/0044 (§3–16)`; `specs/0071 (§4, §15, §31–32, AMEM-01..15)`; `specs/0072 (AREP-13..22)`; `specs/0097 (AOS-09..12, AOS-26..30)`; `tasks/0328 (§13–16, §37–39, AMEMLOW-41..97)`; `tasks/0339 (ASAFE-20..100)`; `tasks/0476 (§217.75–77)`; `spec/SPEC-02-grammar.md`; `spec/SPEC-04-core-extensibility.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-51-raw-memory-volatile-mmio-layout.md`; `spec/SPEC-52-freestanding-runtime-composition.md`.
Covers: `REQ-OWNER-008`, `REQ-OWNER-003` (and specifies the E13.6 contract for `T526`–`T529`: `REQ-ABI-055`, `REQ-ABI-056`, `REQ-ABI-083`, `REQ-RES-145`, `REQ-CAP-140`, `REQ-CAP-143`).
Consumers: `compiler/hir/`, `compiler/sema/`, `compiler/types/`, `compiler/own/`, `compiler/mir/`, `compiler/verify/`, `compiler/interp/`, `compiler/opt/`, `compiler/lir/`, `compiler/target/x64/`, `compiler/obj/`, `compiler/link/`, `T526`–`T529`, `E13.7` (`T530`–`T533`).

## Tóm tắt

Tài liệu `SPEC-55` chuẩn hóa toàn diện cơ chế khai báo biến tĩnh, mảng, struct, biến cục bộ và hàm trực tiếp tại địa chỉ bộ nhớ cố định hoặc biểu thức địa chỉ động (`@at(<expr>)` và `@addr(<expr>)`), cùng tập phép nội soi địa chỉ (`fn_addr`, `static_addr`, `addr_of`, `address_of`, `address_of_mut`, `fn as usize`) cho phân hệ `E13.6` (Phase `P13`, `ADR-0001 §1–4, §7`, `REQ-OWNER-003`, `REQ-OWNER-008`):
- **Một thuộc tính (`@at` / `@addr`), hai hình thái đặt địa chỉ (`Overlay` vs `Placement`, `ADR-0001 §1`, `REQ-OWNER-003`)**:
  1. **Overlay (Ánh xạ chồng — không có biểu thức khởi tạo `= init` trên `static` / `static mut` / `let` hoặc hàm `extern fn` không thân)**: Đối tượng hoặc hàm đã tồn tại sẵn tại địa chỉ đích (thanh ghi phần cứng MMIO, bảng dữ liệu ROM/bootloader, hàm dịch vụ BIOS/firmware). Trình biên dịch không cấp phát hay phát dữ liệu/mã máy; chính ký hiệu đó mang địa chỉ đích.
  2. **Placement (Đặt cố định — có biểu thức khởi tạo `= init` trên `static` / `static mut` / `let` hoặc có thân hàm `{ ... }` trên `fn`)**: Chương trình định nghĩa dữ liệu hoặc mã lệnh và yêu cầu ảnh thực thi phải đặt chính xác tại địa chỉ ảo/vật lý đó (bảng vector ngắt `VECTORS`, trình xử lý `reset`, tiêu đề firmware). Trình biên dịch phát dữ liệu/mã vào một phân đoạn ghim địa chỉ (`pinned_vma`) để trình liên kết đặt đúng tại địa chỉ đã khai báo.
- **Sử dụng bằng cú pháp Axiom thông thường sau khai báo `unsafe` đúng đắn (`ADR-0001 §2`)**: Từ khóa `unsafe` tại điểm khai báo là điểm ủy thác duy nhất, nơi lập trình viên cam kết địa chỉ, kích thước, căn chỉnh, bố cục và giao thức truy cập là hợp lệ. Mọi phép sử dụng sau đó dùng cú pháp Axiom tự nhiên: đọc/ghi trường (`UART0.ctrl = UartCtrl.ENABLE`, `while (UART0.status & TX_READY) == 0u32 {}`), đánh chỉ số mảng có kiểm tra biên (`VECTORS[3]`), gọi hàm qua ABI đã khai báo (`rom_crc32(buf.ptr(), buf.len())`), và tạo `view`/`mut_view` mang nguồn gốc `fixed` (`let regs = view(UART0)`). Các trường có kiểu `Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, `MmioWO<T>` tự động hạ xuống đúng một lệnh máy đọc/ghi khả biến (`VolatileLoad`/`VolatileStore`) đúng độ rộng phần cứng (`1`, `2`, `4`, `8` byte).
- **Nội soi địa chỉ `REQ-OWNER-008` và biểu thức địa chỉ động (`ADR-0001 §7`, `SPEC-50 AXS-UNS-020..025`)**: Cung cấp `fn_addr(f) -> usize`, `static_addr(s) -> usize`, `addr_of(x) -> usize`, `address_of(v) -> *const T` (`address_of(v) as usize`), `address_of_mut(v) -> *mut T`, và phép ép kiểu `f as usize`. Hỗ trợ biểu thức địa chỉ động kiểu `base + offset` (`let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32`) và bảo đảm đồng nhất thức khứ hồi (`fn_addr(isr) == 0x2000_0000usize`, `static_addr(REG) == base + 0x100`) trên cả trình thông dịch MIR (`--interp`) và mã máy x86-64 native.
- **Kiểm định tĩnh, biểu diễn COFF/ELF, phân đoạn ghim VMA, ảnh nhị phân thô (`--format bin`) và mô hình thiết bị khả lập trình trong Oracle (`ADR-0001 §3–4`)**: Kiểm tra căn chỉnh địa chỉ (`AX_UNSAFE_AT_MISALIGNED` / `AX_UNSAFE_MISALIGNED_AT`), bố cục xác định `@repr(C)` / kiểu nguyên thủy (`AX_UNSAFE_INVALID_AT_LAYOUT`), phát hiện chồng lấp dải địa chỉ trong mô-đun và toàn ảnh liên kết (`AX_UNSAFE_AT_OVERLAP` / `AX_LINK_AT_OVERLAP`), kiểm tra hồ sơ biên dịch (`AX_UNSAFE_AT_HOSTED`), phát ký hiệu tuyệt đối COFF `IMAGE_SYM_ABSOLUTE` (`SectionNumber = -1`) / ELF `SHN_ABS` cho overlay, phân đoạn ghim `pinned_vma` cho placement, xuất ảnh nhị phân phẳng (`RawBinary`), và mô phỏng không gian địa chỉ kèm mô hình thiết bị UART/MMIO/bảng vector trong `--interp`.

---

## 1. Fixed-Address Declarations (`@at` / `@addr`): Overlay vs Placement & Ordinary-Syntax Usage (`AXS-ADR-001`..`005`)

### AXS-ADR-001 — Canonical `@at(<expr>)` and `@addr(<expr>)` Attributes & Two Placement Kinds (`ADR-0001 §1`, `REQ-OWNER-003`, `REQ-OWNER-008`)

1. **Attribute Spelling & Canonical Equivalence (`SPEC-02 AXS-GRM-037`, `SPEC-50 AXS-UNS-023`)**:
   - `@at(<expr>)` and `@addr(<expr>)` are **canonical synonyms** in `axiomc`. Both parse as a single-expression item or statement attribute and lower to the identical `Placement` descriptor in HIR/THIR (`SPEC-04 AXS-EXT-032`).
   - All source examples and diagnostics obey canonical Axiom surface syntax (`REQ-OWNER-001`, `REQ-OWNER-002`): binding and initialization use `=`, paths use `.`, and generic type arguments use `<...>`.
   - In the frozen Stage-0 bootstrap compiler (`bootstrap/axiom0`), `@at(...)` is parsed and rejected at semantic analysis with `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (`data.construct = "@at"`, `data.epic = "E13.6"`, `ADR-0011 §3`). In self-hosted `axiomc` (`T526`+), this bootstrap rejection is removed and full `SPEC-55` checking and lowering apply.
2. **Classification Rule — Overlay vs Placement (`ADR-0001 §1`)**:
   For any declaration carrying `@at(<expr>)` or `@addr(<expr>)`, its `PlacementKind` (`Overlay` vs `Place`) is determined syntactically by the presence or absence of an initializer or function body:

| Target Declaration Form | Initializer / Body Present? | `PlacementKind` | Storage / Code Emitted? | Primary Low-Level Use Cases |
|---|---|---|---|---|
| `@at(E) unsafe static [mut] NAME: T` | No initializer | `Overlay` | **None** (symbol binds to existing address `E`) | MMIO device register blocks, ROM lookup tables, bootloader/hypervisor hand-off structs |
| `@at(E) unsafe static [mut] NAME: T = init` | Has `= init` | `Place` | **Yes** (`size_of<T>()` bytes placed at VMA `E`) | Interrupt vector tables (`VECTORS`), firmware headers, fixed boot configuration blocks |
| `@at(E) let [mut] name: T` | No initializer | `Overlay` | **None** (local aliases address `E`) | Scoped register or shared-memory window overlay inside an `unsafe` function |
| `@at(E) let [mut] name: T = init` | Has `= init` | `Place` (runtime store) | Evaluates `init` and writes `T` to address `E` | Initializing a fixed scratch slot or in-buffer header at a computed offset |
| `@at(E) unsafe extern "<abi>" fn f(...) -> R` | Bodyless (`extern fn`) | `Overlay` | **None** (calls dispatch directly to address `E`) | ROM/BIOS routines (`rom_crc32`), Mask-ROM boot services, fixed kernel jump-table entries |
| `@at(E) [unsafe] fn f(...) -> R { ... }` | Has body `{ ... }` | `Place` | **Yes** (machine code emitted in pinned section at VMA `E`) | Hardware reset handlers (`reset`), fixed-entry ISRs, trampoline stubs |

[ADR-0001 §1; OWNER.md REQ-OWNER-001..004, REQ-OWNER-008; SPEC-02 AXS-GRM-037; SPEC-04 AXS-EXT-032; SPEC-50 AXS-UNS-023]

### AXS-ADR-002 — Overlay Semantics: Existing Memory, MMIO Registers, Bootloader Hand-off & ROM Functions (`ADR-0001 §1`)

1. **Data Overlays (`static`, `static mut`, and bodyless local `let`)**:
   - An overlay `static` or `static mut` declaration has no `= expr` initializer:
     ```axiom
     @repr(C)
     pub struct UartRegs {
         pub ctrl: Mmio<u32>,
         pub status: MmioRO<u32>,
         pub data: Mmio<u8>,
         pub _pad: [3]u8,
     }

     @at(0x4000_1000usize)
     unsafe static mut UART0: UartRegs
     ```
   - **Zero Storage Emission**: The compiler emits **zero** bytes into `.data`, `.rdata`, or `.bss` for `UART0`, and runs **zero** initialization code at startup. Instead, the symbol `UART0` resolves directly to virtual/physical address `0x4000_1000` (as an `IMAGE_SYM_ABSOLUTE` / `SHN_ABS` symbol when the address is a compile-time constant, or through a resolved address slot when the address is dynamic, `AXS-ADR-011`).
   - Definite initialization analysis (`compiler/own/`, `INV-SEM-004`) treats an overlay `static` or `@at(E) let [mut] x: T` as externally initialized by the machine environment at address `E`.
2. **Function Overlays (`extern "<abi>" fn`)**:
   - A bodyless function declaration annotated with `@at(<expr>)` or `@addr(<expr>)` binds a callable function symbol to existing machine code at `<expr>`:
     ```axiom
     @at(0xFFFF_0400usize)
     unsafe extern "C" fn rom_crc32(data: *const u8, len: usize) -> u32
     ```
   - Calling `rom_crc32(ptr, n)` marshals arguments and return values according to the declared calling convention (`extern "C"`, `"system"`, `"axiom"`, or `"interrupt"`) and transfers control to address `0xFFFF_0400usize`.

### AXS-ADR-003 — Placement Semantics: Pinned VMA Storage & Code for Vector Tables, Reset Handlers & Firmware Headers (`ADR-0001 §1`)

1. **Static Data Placements (`static` / `static mut` with `= init`)**:
   - A `static` or `static mut` item with both `@at(<expr>)` / `@addr(<expr>)` and an initializer `= init` defines storage whose initial bytes are evaluated from `init` and placed at address `<expr>`:
     ```axiom
     @at(0x0000_0000usize)
     unsafe static VECTORS: [4]fn() = [reset_isr, nmi_isr, hard_fault_isr, timer_isr]
     ```
   - For compile-time constant addresses in `freestanding`, `kernel`, or `system` builds (`T528`), the compiler emits the initialized bytes into a dedicated pinned section `.at.data.<sym>` (or `.at.rdata.<sym>` for immutable `static`) carrying `pinned_vma = Some(addr)` and implicit `@used` root retention (`SPEC-52 AXS-FRE-014`).
2. **Function Code Placements (`fn` with body `{ ... }`)**:
   - A function definition with a body `{ ... }` and `@at(<expr>)` / `@addr(<expr>)` emits its compiled machine instructions into a dedicated pinned executable section `.at.text.<sym>` with `pinned_vma = Some(addr)`:
     ```axiom
     @at(0x0800_0100usize)
     unsafe fn reset() -> never {
         loop {}
     }
     ```
   - Placed functions receive standard target prologues and epilogues unless additionally annotated with `@naked` (`SPEC-52 AXS-FRE-013`) or `extern "interrupt"` (`SPEC-52 AXS-FRE-015`).

### AXS-ADR-004 — "Use Normally" After an `unsafe` Fixed-Address Declaration: Ordinary Field Access, Indexing, Calls & Fixed-Provenance Views (`ADR-0001 §2`)

1. **Single Trust Point Principle (`ADR-0001 §2`, `tasks/0339`)**:
   - Writing `unsafe` on a fixed-address item declaration (`@at(0x4000_1000) unsafe static mut UART0: UartRegs`, `@at(0x0000_0000) unsafe static VECTORS: [48]fn() = ...`, `@at(0xFFFF_0400) unsafe extern "C" fn rom_crc32(...)`) is the **single trust boundary** where the programmer vouches that the hardware/memory address, size, alignment, layout, and concurrency/register contract are valid.
   - Once declared with `unsafe` at the declaration site, subsequent uses in single-threaded freestanding/system code or on `Volatile`/`Mmio*`/`Atomic`/immutable fields use **ordinary Axiom syntax without repeating `unsafe { ... }` blocks or pointer casts at every access site**:
     ```axiom
     UART0.ctrl = UartCtrl.ENABLE                  // ordinary field assignment -> single volatile store
     while (UART0.status & TX_READY) == 0u32 {}    // ordinary field read -> single volatile load
     let handler = VECTORS[3]                      // bounds-checked array indexing
     let crc = rom_crc32(buf.as_ptr(), buf.len())  // ordinary call (requires unsafe only if callee has raw-ptr preconditions or is not trusted)
     let regs: view<UartRegs> = view(UART0)        // safe view creation with fixed provenance
     ```
   - Note on `unsafe` at declaration vs use site:
     - If a fixed-address `static` or `extern fn` is declared **with** `unsafe` (`@at(...) unsafe static ...`), safe code may read immutable fields, read/write `Volatile<T>` / `Mmio<T>` / `MmioRO<T>` / `MmioWO<T>` / `Atomic<T>` fields, index fixed arrays, and take `view(...)` directly; mutating a plain non-volatile `static mut` in multi-threaded contexts still obeys the concurrency data-race rules (`AXS-ADR-013`).
     - If a fixed-address `static` or `let` is declared **without** the `unsafe` keyword on the declaration (e.g. `@addr(0x2000_0000) static mut REG: u32` per `SPEC-50 AXS-UNS-023`), then either the declaration itself must reside inside an `unsafe` block/function or every direct read/write of `REG` must occur inside an `unsafe` block (`AX_UNSAFE_REQUIRED`).
2. **Capabilities (`view<T>` and `mut_view<T>`) Over Fixed-Address Objects**:
   - Taking `view(UART0)` or `mut_view(UART0)` (or a sub-place `view(UART0.status)`) produces a standard Axiom capability whose region has **`fixed` provenance** (`PlaceBase.FixedStatic(SymbolId)`, `SPEC-04 AXS-EXT-041`) and static lifetime.
   - The capability conflict verifier (`SPEC-11`, `INV-SEM-002`) tracks `view` and `mut_view` borrows of `FixedStatic(SymbolId)` places identically to ordinary statics and locals: two simultaneous overlapping `mut_view` borrows of `UART0` are rejected at compile time with `AX_CAP_CONFLICT_MUT`.

### AXS-ADR-005 — Automatic Volatile/MMIO Field Lowering (`Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, `MmioWO<T>`) (`ADR-0001 §2`, `SPEC-51 AXS-MEM-005..006`)

1. **Field-Type-Driven Register Semantics (`ADR-0001 §2`)**:
   - Hardware register access rules come from the **declared field types** of a fixed-address struct/array, never from call-site pointer casts:
     - Reading a field `obj.reg` of type `Volatile<T>`, `Mmio<T>`, or `MmioRO<T>` automatically unwraps `T` in value position and lowers in `compiler/mir/` to `MirStmtKind.VolatileLoad` of exact byte width `size_of<T>()`.
     - Assigning `obj.reg = val` (where `val: T`) to a field of type `Volatile<T>`, `Mmio<T>`, or `MmioWO<T>` automatically lowers in `compiler/mir/` to `MirStmtKind.VolatileStore` of exact byte width `size_of<T>()`.
     - Compound assignment `obj.reg |= mask` or `obj.reg &= mask` on `Volatile<T>` or `Mmio<T>` lowers to one `VolatileLoad` followed by the ALU operation and one `VolatileStore`.
     - Plain fields (e.g. `u32`, `[16]u8`) inside a fixed-address struct lower to ordinary `Load`/`Store` operations (suitable for ROM tables, bootloader hand-off structs, or SRAM buffers).
2. **Compile-Time Access-Direction Enforcement (`SPEC-51 AXS-MEM-006`)**:
   - Attempting to assign to or call `.write(...)` / `.modify(...)` on a read-only `MmioRO<T>` field (`UART0.status = 0u32`) is rejected at compile time with `AX_TYPE_MMIO_WRITE_READONLY`.
   - Attempting to read from or call `.read()` / `.modify(...)` on a write-only `MmioWO<T>` field (`let x = UART0.tx_strobe`) is rejected at compile time with `AX_TYPE_MMIO_READ_WRITEONLY`.

---

## 2. `REQ-OWNER-008` Address Introspection, Dynamic Address Expressions & Round-Trip Identity (`AXS-ADR-010`..`014`)

### AXS-ADR-010 — Function, Static & Place Address Introspection (`fn_addr`, `static_addr`, `addr_of`, `address_of`, `address_of_mut`, `fn as usize`) (`REQ-OWNER-008`, `ADR-0001 §7`, `SPEC-50 AXS-UNS-020..022`)

To inspect, verify, compute offsets from, and bind `@at` / `@addr` declarations (`OWNER.md REQ-OWNER-008`, `ADR-0001 §7`), `axiomc` provides the following canonical address introspection forms:

| Form | Accepted Operand `x` | Return Type | Safety & Lowering Contract |
|---|---|---|---|
| `fn_addr(f)` | Any `fn`, `unsafe fn`, `extern "<abi>" fn`, `@at`/`@addr` fn, monomorphized `g.<T>`, or `fn(...) -> R` value | `usize` | Safe. Lowers to `MirRvalue.FnAddr(FnId)` (or `FnPtrToInt`); returns the 64-bit code address of `f`. Marks `f` with `address_taken = true`. Rejects capturing closures with `AX_TYPE_MISMATCH`. |
| `static_addr(s)` | Any `static`, `static mut`, `@thread_local static`, or `@at`/`@addr` static `s` | `usize` | Safe. Lowers to `MirRvalue.StaticAddr(SymbolId)`; returns the 64-bit runtime/link-time memory address of `s`. Rejects non-statics with `AX_TYPE_MISMATCH`. |
| `addr_of(x)` | Any function item `f`, static item `s`, or place expression `v` (`let`, `s.field`, `arr[i]`, `*p`) | `usize` | Safe. Unified `usize` address query (`ADR-0001 §7`): dispatches to `fn_addr(x)` for functions, `static_addr(x)` for statics, and `address_of(x) as usize` for places. Rejects rvalue temporaries with `AX_TYPE_NOT_A_PLACE`. |
| `address_of(v)` | Any place expression `v` of type `T` (`let`, `static`, `@at`/`@addr` item, `s.field`, `arr[i]`, `*p`) | `*const T` | Returns `*const T` with provenance of `v` without moving or copying `v`. Safe when immediately cast `address_of(v) as usize`; dereferencing the resulting pointer requires `unsafe`. Sets `address_observable = true`. Rejects temporaries (`address_of(1 + 2)`) with `AX_TYPE_NOT_A_PLACE`. |
| `address_of_mut(v)` | Any mutable place expression `v` (`let mut`, `static mut`, `mut_view` deref, `*mut` deref) | `*mut T` | Requires `unsafe` (or mutable place check `AX_TYPE_ASSIGN_IMMUTABLE` on immutable bindings); returns `*mut T` with `ReadWrite` provenance and sets `address_observable = true`. |
| `f as usize` | Any function item `f` or function pointer `fn(...) -> R` / `extern "<abi>" fn(...) -> R` | `usize` | Safe. Casts a function item or function pointer directly to its `usize` address (`(f as usize) == fn_addr(f)`). |
| `p as usize` | Any raw pointer `p: *const T` or `*mut T` | `usize` | Safe. Exposes the provenance of `p` and returns its numeric `usize` address (`SPEC-50 AXS-UNS-011`). |

[OWNER.md REQ-OWNER-008; ADR-0001 §7; SPEC-50 AXS-UNS-020..022]

### AXS-ADR-011 — Dynamic Address Expressions (`base + offset`) on Scoped/Module `static` and Local `let` Bindings (`REQ-OWNER-008`, `SPEC-50 AXS-UNS-024`)

1. **Address Expression Typing (`<expr>: usize`)**:
   - The expression `<expr>` inside `@at(<expr>)` or `@addr(<expr>)` MUST type-check as `usize` (unsuffixed integer literals unify with `usize` per `SPEC-03 AXS-SEM-020`, and narrower unsigned integers in binary offset expressions promote to `usize` per `SPEC-40 AXS-INT-053`). Any non-`usize` address expression is rejected with `AX_TYPE_MISMATCH`.
2. **Compile-Time Constant vs Dynamic Runtime Address Expressions**:
   - **`PlacementAddr.Const(u64)`**: `<expr>` is a compile-time constant (`0x4000_1000usize`, `PERIPH_BASE + 0x20`). Valid on module-scope and block-scope `static`, `static mut`, `let`, `fn`, and `extern fn`.
   - **`PlacementAddr.Dynamic(ExprId)`**: `<expr>` is computed from runtime or link-time address queries (`fn_addr(foo) + 0x100`, `static_addr(BASE) + offset`, `address_of(buf) as usize + 16`, or `image("mod") + offset` in `E13.7`):
     ```axiom
     let base = fn_addr(foo)
     @addr(base + 0x100)
     static mut REG: u32
     ```
   - **Lowering of Scoped Dynamic `@addr` / `@at` Statics (`T526`, `T528`)**:
     - Each dynamic `@addr(<expr>) static [mut] S: T` lowers to a hidden runtime address slot `__ax_addr_slot_<S>: usize`.
     - When the declaration statement is executed (or during module init for module-scope dynamic expressions), `<expr>` is evaluated to `A: usize` and stored in `__ax_addr_slot_<S>` (and if `= init` is present, `init` is written to `A`).
     - Every subsequent read/write of `S`, `static_addr(S)`, `addr_of(S)`, and `address_of(S)` loads the resolved address `A` from `__ax_addr_slot_<S>`.

### AXS-ADR-012 — Round-Trip Address Equality Invariant (`fn_addr(isr) == 0x2000_0000usize`, `static_addr(REG) == base + 0x100`) (`REQ-OWNER-008`)

For every accepted `@at(E)` or `@addr(E)` declaration where `E` evaluates to `A: usize`, both the MIR oracle (`--interp`) and native x86-64 binaries MUST satisfy the exact round-trip address identities (`SPEC-50 AXS-UNS-025`):
1. **Fixed-Address Function (`@at(A) fn isr(...)` or `@at(A) unsafe extern "C" fn rom_fn(...)`)**:
   $$\text{fn\_addr}(\text{isr}) == A \quad\land\quad \text{addr\_of}(\text{isr}) == A \quad\land\quad (\text{isr as usize}) == A$$
2. **Fixed-Address Static (`@at(A) [unsafe] static [mut] REG: T`)**:
   $$\text{static\_addr}(\text{REG}) == A \quad\land\quad \text{addr\_of}(\text{REG}) == A \quad\land\quad (\text{address\_of}(\text{REG}) \text{ as usize}) == A$$
3. **Fixed-Address Local (`@at(A) let [mut] slot: T`)**:
   $$\text{addr\_of}(\text{slot}) == A \quad\land\quad (\text{address\_of}(\text{slot}) \text{ as usize}) == A$$

### AXS-ADR-013 — Ownership, Capability, Fixed Provenance & Concurrency Rules for Fixed-Address Items (`ADR-0001 §3`, `REQ-ABI-055..056`, `REQ-ABI-083`, `REQ-RES-145`, `REQ-CAP-140`, `REQ-CAP-143`)

1. **Permanent Storage — Never Moved, Never Dropped (`ADR-0001 §3`)**:
   - Fixed-address objects (`@at` / `@addr` `static`, `static mut`, and `let` overlays) represent permanent or externally owned memory locations rooted at `PlaceBase.FixedStatic(SymbolId)` (`SPEC-04 AXS-EXT-041`).
   - Moving a `!Copy` value out of a fixed-address place is rejected at compile time (`AX_MOVE_USE_AFTER_MOVE` / `AX_CTM_STATIC_MOVE_FORBIDDEN`).
   - Fixed-address items **never** execute automatic scope-exit or program-exit `Drop` glue (`ADR-0001 §3`).
   - Copying a `Copy` value out of or into a non-volatile fixed-address place (`REQ-ABI-055`, `REQ-ABI-056`, `REQ-ABI-083`, `REQ-RES-145`) is a semantic ownership transition that does not force redundant stack `memcpy` intermediates when values fit in registers.
2. **Concurrency & DMA Exclusivity (`ADR-0001 §3`, `SPEC-30 AXS-CONC-034`, `SPEC-52 AXS-FRE-005`)**:
   - Accessing a `static mut` fixed-address item in safe code is permitted when: (a) the accessed field is `Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, `MmioWO<T>`, or `Atomic<T>`; (b) the compilation runs in a single-threaded `freestanding` profile; or (c) the access is inside an `unsafe` block. Unsynchronized access to a plain non-volatile `static mut` across concurrent threads in safe code is rejected with `AX_CONC_UNSYNC_STATIC`.
   - When a fixed-address or physical region is bound to an active `DmaTransfer<T>` (`REQ-CAP-140`, `REQ-CAP-143`), CPU `view<T>` and `mut_view<T>` accesses are statically blocked (`AX_CAP_DMA_ACTIVE_CONFLICT`) until `wait_complete()` restores CPU ownership.

### AXS-ADR-014 — Compile-Time Validation: Alignment, Defined Layout (`@repr(C)`), Overlap Detection & Profile Gating (`ADR-0001 §3`, `T526`)

1. **Defined Physical Layout Requirement (`AX_UNSAFE_INVALID_AT_LAYOUT`)**:
   - The type `T` of any `@at(<expr>)` / `@addr(<expr>)` `static`, `static mut`, or `let` declaration MUST have a **defined, fixed physical layout**:
     - primitive scalars (`i8..i128`, `u8..u128`, `isize`, `usize`, `f32`, `f64`, `bool`, `char`), raw pointers (`*const U`, `*mut U`), function pointers (`fn(...) -> R`), SIMD `Vector<E, N>`,
     - `Volatile<U>`, `Mmio<U>`, `MmioRO<U>`, `MmioWO<U>`, `Atomic<U>`, `MaybeUninit<U>`, `ManuallyDrop<U>`,
     - fixed-length arrays `[N]U` or tuples of layout-defined types `U`,
     - structs, fieldless/explicit-repr enums, or unions annotated with `@repr(C)`, `@repr(packed)`, `@repr(packed(N))`, or `@repr(transparent)` whose fields all have defined layout (`ADR-0001 §3`).
   - Applying `@at` / `@addr` to a dynamically sized type (`[U]`, `Str`, `dyn Trait`) or to a default `Repr.Axiom` struct/enum with unspecified field layout (`> 1` non-ZST fields without `@repr(C)` / `@repr(packed)`) is rejected at compile time with `AX_UNSAFE_INVALID_AT_LAYOUT`.
2. **Non-Null & Alignment Verification (`AX_UNSAFE_AT_MISALIGNED` / `AX_UNSAFE_MISALIGNED_AT`)**:
   - When `<expr>` folds to a compile-time constant $A$:
     - For data items of type `T` with alignment $L = \text{align\_of}\langle T \rangle()$, the compiler requires $A \ne 0$ (unless explicitly in a freestanding vector-table placement at `0x0000_0000` with `@at(0x0)` on `static VECTORS`) and $(A \bmod L) == 0$. Specifically, any misaligned address $(A \bmod L) \ne 0$ (or null overlay address $A == 0$ on a non-placement overlay) is rejected at compile time with `AX_UNSAFE_AT_MISALIGNED` (canonical alias `AX_UNSAFE_MISALIGNED_AT`, `data.address = A`, `data.required_align = L`).
3. **Intra-Module & Linker-Wide Address Range Overlap Detection (`AX_UNSAFE_AT_OVERLAP`, `AX_LINK_AT_OVERLAP`)**:
   - Each constant-address `@at(A)` / `@addr(A)` item occupies the half-open interval $[A, A + S)$, where $S = \max(1, \text{size\_of}\langle T \rangle())$ for data items and $S = \text{code\_size}(f)$ (at least 1 byte in `sema`) for functions.
   - If two distinct `@at`/`@addr` items in the same module (neither being an explicit `union`) have overlapping intervals $[A_1, A_1 + S_1) \cap [A_2, A_2 + S_2) \ne \emptyset$, `compiler/sema/` emits `AX_UNSAFE_AT_OVERLAP` (`labels` pointing to the first declaration).
   - Across separately compiled modules/objects, `compiler/link/` checks all placed sections and fixed symbols and emits `AX_LINK_AT_OVERLAP` (or `AX_UNSAFE_AT_OVERLAP`) if any two intervals overlap (`ADR-0001 §3–4`).
4. **Profile & Region Gating (`AX_UNSAFE_AT_HOSTED`)**:
   - Arbitrary constant hardware/physical `@at(0x4000_1000)` overlays and VMA placements are enabled by default in `--profile freestanding`, `--profile kernel`, and `--profile system` (`SPEC-52 AXS-FRE-002`).
   - In `--profile hosted`, an arbitrary raw constant `@at(0x4000_1000)` hardware overlay or pinned placement outside an explicitly mapped/simulated region or module-relative `image(...)` / `fn_addr(...)` / `static_addr(...)` / `address_of(...)` expression is rejected with `AX_UNSAFE_AT_HOSTED` unless `--allow-fixed-addr` (or a test/mapped region) is active (`ADR-0001 §3`).

---

## 3. Pipeline Lowering, Object/Linker Representation & Oracle Device Model (`AXS-ADR-020`..`024`)

### AXS-ADR-020 — HIR/THIR `Placement` Side Table & MIR `FixedStatic` Lowering (`ADR-0001 §4`, `SPEC-04 AXS-EXT-032/041/043`, `T526`)

1. **HIR/THIR Side Table (`compiler/hir/`, `SPEC-04 AXS-EXT-032`)**:
   - Every item or local with `@at(<expr>)` / `@addr(<expr>)` records an entry in the `Placement` extension table keyed by `ItemId` / `HirId`:
     ```axiom
     pub enum PlacementKind {
         Overlay,
         Place,
     }

     pub enum PlacementAddr {
         Const(u64),
         Dynamic(ExprId),
         ImageRel { module_name: Option<StrId>, offset: ExprId }, // E13.7 (SPEC-56)
     }

     pub struct Placement {
         pub kind: PlacementKind,
         pub addr: PlacementAddr,
         pub region: Option<StrId>,
         pub is_unsafe_decl: bool,
     }
     ```
2. **MIR Place & Provenance Lowering (`compiler/mir/`, `SPEC-04 AXS-EXT-041, AXS-EXT-043`)**:
   - Fixed-address statics lower to `PlaceBase.FixedStatic(SymbolId)` carrying `Provenance.Fixed`.
   - Field projections onto `Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, or `MmioWO<T>` inside a `FixedStatic` (or any struct) emit `MirStmtKind.VolatileLoad { dst, src, width, align, addr_space }` and `MirStmtKind.VolatileStore { dst, val, width, align, addr_space }`.
   - `EscapeInfo` (`SPEC-71 AXS-ESC-004`) and `WPO`/`LTO` (`SPEC-75 AXS-LTO-003`) treat every `@at`/`@addr` placement and overlay as `address_observable = true` and as an unstrippable root (`@used`), forbidding dead-global elimination, SROA scalarization, or ICF address merging.

### AXS-ADR-021 — LIR & x86-64 Codegen for Fixed-Address Loads, Stores & Calls (`T528`)

1. **Constant Fixed Address (`PlacementAddr.Const(A)`)**:
   - In `compiler/lir/` and `compiler/target/x64/`, loading the base address of a constant `@at(A)` symbol materializes the 64-bit address via `MOV r64, imm64` (or references the COFF `IMAGE_SYM_ABSOLUTE` / pinned-section symbol).
   - Volatile/MMIO field accesses emit `LirInst.Load` / `LirInst.Store` with `LIR_MEM_FLAG_VOLATILE`, selecting exact-width x86-64 instructions (`MOV r8/m8`, `MOV r16/m16`, `MOV r32/m32`, `MOV r64/m64`, `SPEC-51 AXS-MEM-002`).
   - Calling an `@at(A)` overlay or placed function materializes `A` into a scratch register (`MOV rax, imm64` or loads the placed symbol) and executes `CALL rax` (or direct `CALL rel32` when within 32-bit PC-relative range of a pinned section) using the declared calling convention (`Win64`, `SysV64`, `Axiom`, or `Interrupt`).
2. **Dynamic Fixed Address (`PlacementAddr.Dynamic`)**:
   - Loads the runtime-computed `usize` base address from the internal slot `__ax_addr_slot_<sym>` (`MOV r64, [rip + __ax_addr_slot_<sym>]`) and applies field/element byte offsets directly to `r64`.

### AXS-ADR-022 — Object Model: COFF `IMAGE_SYM_ABSOLUTE` / ELF `SHN_ABS` Symbols & Pinned VMA Sections (`ADR-0001 §4`, `SPEC-04 AXS-EXT-071..072`, `T528`)

1. **Overlays $\rightarrow$ Absolute Object Symbols (`SPEC-04 AXS-EXT-072`)**:
   - For every constant-address `@at(A)` / `@addr(A)` **overlay** (`static`, `static mut`, `extern fn`), `compiler/obj/` emits a symbol table entry with `SymbolSection.Absolute` (`Value = A`):
     - In COFF (`.obj`, `x86_64-windows`): `SectionNumber = -1` (`IMAGE_SYM_ABSOLUTE = 0xFFFF as i16`), `Value = A as u32` (with 64-bit address metadata preserved in the object/linker symbol table for addresses $\ge 2^{32}$).
     - In ELF (`.o`, `x86_64-linux`): `st_shndx = SHN_ABS` (`0xFFF1`), `st_value = A`.
   - Zero section bytes are emitted for overlay symbols.
2. **Placements $\rightarrow$ Pinned VMA Sections (`SPEC-04 AXS-EXT-071`)**:
   - For every constant-address `@at(A)` / `@addr(A)` **placement** (`static` with initializer or `fn` with body), `compiler/obj/` emits a dedicated `Section` with `pinned_vma = Some(A)`:
     - Code placement (`@at(A) fn f`): section `.at.text.<name>` with flags `IMAGE_SCN_CNT_CODE | IMAGE_SCN_MEM_EXECUTE | IMAGE_SCN_MEM_READ`.
     - Read-only static placement (`@at(A) static S = init`): section `.at.rdata.<name>` with flags `IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_MEM_READ`.
     - Mutable static placement (`@at(A) static mut S = init`): section `.at.data.<name>` with flags `IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_WRITE`.

### AXS-ADR-023 — Linker Pinned Section Layout, Cross-Object Overlap Detection & Freestanding Raw-Binary Output (`--format bin`) (`ADR-0001 §4`, `SPEC-04 AXS-EXT-070`, `T528`)

1. **Linker Pinned VMA Resolution & Overlap Verification (`compiler/link/`)**:
   - Before assigning automatic RVAs to unpinned sections (`.text`, `.rdata`, `.data`, `.bss`), the linker collects all input sections carrying `pinned_vma = Some(A)` and all `Absolute` symbols with declared sizes.
   - The linker sorts all pinned ranges $[A_i, A_i + S_i)$ by start address $A_i$ and verifies that no two pinned ranges (and no pinned section vs an unpinned section) overlap; any overlap is rejected with `AX_LINK_AT_OVERLAP` (`data.symbol_a`, `data.symbol_b`, `data.address`).
   - Relocations targeting an `Absolute` symbol or a pinned section resolve to its exact virtual address $A$.
2. **Freestanding Raw-Binary Image Writer (`ImageFormat.RawBinary`, `--format bin`, `T528`)**:
   - In `--profile freestanding` and `--profile kernel`, the driver and linker support `--format bin` (`ImageFormat.RawBinary`, `SPEC-04 AXS-EXT-070`) alongside PE32+ (`--format pe`) and ELF (`--format elf`).
   - Let $A_{\min} = \min_i A_i$ and $A_{\max} = \max_i (A_i + S_i)$ across all emitted loadable sections. `--format bin` writes a flat, headerless binary image of $A_{\max} - A_{\min}$ bytes where every section with VMA $A_i$ is placed at file byte offset $A_i - A_{\min}$ (with gap bytes filled deterministically with `0x00`), suitable for direct flashing to ROM/Flash or loading into a bare-metal emulator.

### AXS-ADR-024 — Oracle (`--interp`) Simulated Address Space & Scriptable MMIO/UART/Vector-Table Device Model (`ADR-0001 §4`, `T527`)

To keep low-level `@at` / `@addr` firmware, vector tables, and MMIO drivers 100% testable under `axiomc run --interp` without physical hardware (`ADR-0001 §4`, `INV-ORACLE-002`):
1. **Sparse Simulated Address Space (`FixedAddrMap` in `compiler/interp/`)**:
   - The MIR interpreter maintains a sparse page/region map covering arbitrary 64-bit `usize` addresses declared via `@at(A)` / `@addr(A)`.
   - Placed statics (`@at(A) static VECTORS = ...`) initialize their bytes at simulated address `A` before entry; placed or overlay functions (`@at(A) fn isr`, `@at(A) extern "C" fn rom_crc32`) register `A <-> FnId` in the interpreter's code address table so both `fn_addr(isr) == A` and indirect calls to `A` dispatch deterministically.
2. **Scriptable MMIO & UART/Vector Device Model (`T527`)**:
   - The oracle includes a deterministic MMIO device model hooking registered peripheral ranges (including the canonical test UART block at `0x4000_1000` and vector table at `0x0000_0000`):
     - Reading `UART0.status` (`MmioRO<u32>` at offset `0x04`) returns `TX_READY` (`1u32`) deterministically (or steps through a scripted FIFO readiness sequence), so polling loops `while (UART0.status & TX_READY) == 0u32 {}` terminate cleanly.
     - Writing a byte `b` to `UART0.data` (`Mmio<u8>` at offset `0x08`) appends `b` to the oracle's deterministic UART TX transcript buffer (and optionally echoes to test stdout / volatile trace).
     - Calling or triggering vector entry `VECTORS[idx]()` dispatches to the handler function placed in the vector table.

---

## 4. Diagnostics, Positive/Negative Canonical Examples & Conformance Matrix (`AXS-ADR-050`..`053`)

### AXS-ADR-050 — Fixed-Address Diagnostic Taxonomy

| Diagnostic Code | Severity | Emitting Stage | Condition |
|---|---|---|---|
| `AX_UNSAFE_AT_MISALIGNED` (alias `AX_UNSAFE_MISALIGNED_AT`) | `error` | `sema` / `types` | Constant `@at(A)` / `@addr(A)` address `A` is not a multiple of `align_of<T>()` (or `A == 0` on a non-vector-table overlay); `data.address`, `data.required_align`. |
| `AX_UNSAFE_AT_OVERLAP` | `error` | `sema` | Two constant `@at` / `@addr` items in the same module have overlapping address ranges $[A_1, A_1 + S_1) \cap [A_2, A_2 + S_2) \ne \emptyset$. |
| `AX_LINK_AT_OVERLAP` | `error` | `link` | Two pinned `@at` / `@addr` sections or symbols across linked objects overlap in VMA space (`ADR-0001 §3–4`). |
| `AX_UNSAFE_INVALID_AT_LAYOUT` | `error` | `sema` / `types` | `@at` / `@addr` applied to a type without a defined fixed layout (e.g., default `Repr.Axiom` multi-field struct without `@repr(C)` / `@repr(packed)`, slice `[T]`, `Str`, or `dyn Trait`). |
| `AX_UNSAFE_AT_HOSTED` | `error` | `sema` / `link` | Arbitrary constant `@at` / `@addr` hardware overlay or pinned VMA placement used in `--profile hosted` outside a mapped/simulated region or `fn_addr`/`static_addr`/`address_of`/`image` expression without `--allow-fixed-addr`. |
| `AX_UNSAFE_REQUIRED` | `error` | `sema` | Accessing a fixed-address binding that was not declared `unsafe`, or reading/writing raw pointers outside an `unsafe` block. |
| `AX_TYPE_MMIO_WRITE_READONLY` | `error` | `typeck` | Assigning to or calling `.write`/`.modify` on a read-only `MmioRO<T>` register field (`SPEC-51 AXS-MEM-006`). |
| `AX_TYPE_MMIO_READ_WRITEONLY` | `error` | `typeck` | Reading from or calling `.read`/`.modify` on a write-only `MmioWO<T>` register field (`SPEC-51 AXS-MEM-006`). |
| `AX_TYPE_NOT_A_PLACE` | `error` | `typeck` | `address_of(e)`, `address_of_mut(e)`, or `addr_of(e)` applied to a temporary rvalue rather than a place or item. |

### AXS-ADR-051 — Canonical Positive Examples (MMIO UART Driver, Vector Table Placement & `REQ-OWNER-008` Round-Trip)

```axiom
use std.core.mem.{Mmio, MmioRO, MmioWO, addr_of, fn_addr, static_addr, address_of}

const TX_READY: u32 = 1u32
const CTRL_ENABLE: u32 = 1u32

@repr(C)
struct UartRegs {
    ctrl: Mmio<u32>,
    status: MmioRO<u32>,
    data: Mmio<u8>,
    _pad: [3]u8,
}

// 1. Overlay: MMIO register block at 0x4000_1000 (no storage emitted)
@at(0x4000_1000usize)
unsafe static mut UART0: UartRegs

// 2. Placement: function & interrupt vector table at fixed addresses
@at(0x2000_0000usize)
fn timer_isr() -> u32 {
    return 0xCAFEu32
}

@at(0x0000_0000usize)
unsafe static VECTORS: [2]fn() -> u32 = [timer_isr, timer_isr]

@entry
pub fn _start() -> i32 {
    // Ordinary-syntax MMIO register access after unsafe @at declaration:
    UART0.ctrl = CTRL_ENABLE
    while (UART0.status & TX_READY) == 0u32 {}
    UART0.data = 0x41u8

    // REQ-OWNER-008 round-trip address introspection & dynamic @addr(base + 0x100):
    assert(fn_addr(timer_isr) == 0x2000_0000usize)
    assert(static_addr(UART0) == 0x4000_1000usize)
    assert(addr_of(VECTORS) == 0x0000_0000usize)

    let base = fn_addr(timer_isr)
    @addr(base + 0x100usize)
    unsafe static mut SCRATCH_REG: u32
    SCRATCH_REG = VECTORS[0]()
    assert(static_addr(SCRATCH_REG) == 0x2000_0100usize)
    assert((address_of(SCRATCH_REG) as usize) == 0x2000_0100usize)
    assert(SCRATCH_REG == 0xCAFEu32)
    return 0
}
```

### AXS-ADR-052 — Canonical Negative Examples

1. **Misaligned Fixed Address (`AX_UNSAFE_AT_MISALIGNED` / `AX_UNSAFE_MISALIGNED_AT`)**:
   `@at(0x4000_1002usize) unsafe static mut BAD_REG: u32` — rejected because `0x4000_1002 % align_of<u32>() != 0`.
2. **Overlapping Fixed-Address Declarations (`AX_UNSAFE_AT_OVERLAP`)**:
   `@at(0x4000_1000usize) unsafe static mut REG_A: [4]u32` (occupies `[0x4000_1000, 0x4000_1010)`) followed by `@at(0x4000_1008usize) unsafe static mut REG_B: u64` (occupies `[0x4000_1008, 0x4000_1010)`) — rejected with `AX_UNSAFE_AT_OVERLAP`.
3. **Layout-Unspecified Struct (`AX_UNSAFE_INVALID_AT_LAYOUT`)**:
   `struct Unrepr { a: u32, b: u8 }` (no `@repr(C)` or `@repr(packed)`) used in `@at(0x4000_2000usize) unsafe static mut S: Unrepr` — rejected with `AX_UNSAFE_INVALID_AT_LAYOUT`.
4. **Writing to Read-Only MMIO Register (`AX_TYPE_MMIO_WRITE_READONLY`)**:
   `UART0.status = 0u32` where `status: MmioRO<u32>` — rejected with `AX_TYPE_MMIO_WRITE_READONLY`.

### AXS-ADR-053 — E13.6 Verification & Conformance Matrix (`T526`–`T529`)

| Task | Verification Target | Certified Invariants & Requirements |
|---|---|---|
| `T526` | `tests/ui/fixed_addr` | HIR/THIR/MIR `Placement` & `FixedStatic` lowering, `fixed` provenance, alignment (`AX_UNSAFE_AT_MISALIGNED`), overlap (`AX_UNSAFE_AT_OVERLAP`), `@repr(C)` layout (`AX_UNSAFE_INVALID_AT_LAYOUT`), profile (`AX_UNSAFE_AT_HOSTED`), `Mmio*<T>` volatile field lowering, and `REQ-OWNER-008` dynamic `@addr(base + 0x100)`. |
| `T527` | `tests/run/fixed_addr_oracle` | Sparse simulated address space in `compiler/interp/`, scriptable UART (`UART0.status`, `UART0.data`) & vector-table device model, ROM function overlay call, and `REQ-OWNER-008` round-trip equality (`fn_addr(isr) == 0x2000_0000usize`). |
| `T528` | `tests/link/fixed_addr` | COFF `IMAGE_SYM_ABSOLUTE` (`SectionNumber = -1`) overlay symbols, pinned VMA sections (`.at.text.*`, `.at.data.*`, `.at.rdata.*`), cross-object linker overlap check (`AX_LINK_AT_OVERLAP`), `--format bin` raw binary emitter, and native x86-64 `fn_addr`/`static_addr`/`address_of` round-trip. |
| `T529` | `tests/conformance/p13/e13_6_fixed_addr` | End-to-end E13.6 conformance suite certifying freestanding `@at` vector table + UART MMIO + ROM callback + `REQ-OWNER-003` & `REQ-OWNER-008` round-trip across `--interp` and native x86-64 (`0 WEAK-NATIVE`). |

## Sources
`spec/decisions/ADR-0001-fixed-address-declarations.md (§1–4, §7)`; `spec/requirements/OWNER.md (REQ-OWNER-001..005, REQ-OWNER-008)`; `specs/0044 (§3–16)`; `specs/0071 (§4, §15, §31–32)`; `specs/0072`; `specs/0097 (AOS-09..12, AOS-26..30)`; `tasks/0328 (§13–16, §37–39, AMEMLOW-41..97)`; `tasks/0339 (ASAFE-20..100)`; `tasks/0476 (§217.75–77)`; `spec/SPEC-02-grammar.md`; `spec/SPEC-04-core-extensibility.md (AXS-EXT-032, AXS-EXT-041, AXS-EXT-043, AXS-EXT-070..072)`; `spec/SPEC-50-unsafe-ub-ffi.md (AXS-UNS-020..025)`; `spec/SPEC-51-raw-memory-volatile-mmio-layout.md (AXS-MEM-001..006)`; `spec/SPEC-52-freestanding-runtime-composition.md (AXS-FRE-010..015)`.
