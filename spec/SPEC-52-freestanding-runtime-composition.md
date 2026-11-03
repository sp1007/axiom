# SPEC-52 — Canonical Freestanding Execution, Modular Runtime Composition, Profiles, `@entry` & Runtime Capability Graph Specification

Status: draft (T511, 2026-11-03)
Owner: axiom-architect
Consolidates: `specs/0097 (§1–60, AOS-01..35)`; `specs/0104 (§54)`; `specs/0111 (§47)`; `specs/0119 (§233, §259, AFFI-20..21)`; `specs/0129 (§76–77, §101, ATYPE-46..47)`; `specs/0131 (§67, §88, AFN-54)`; `specs/0138 (§100, AFFI-27, Part XX)`; `specs/0143 (Part XXIV §1–65, ARUNTIME-20..63)`; `specs/0163 (§6)`; `specs/0230 (§6)`; `tasks/0358 (§1–35, AINIT-20..80)`; `tasks/0359 (§1–51, ARUNTIME-20..90)`; `tasks/0367 (§82, AABI-20..70)`; `tasks/0370 (§1–42, ARUNTIME-20..57)`; `tasks/0413 (§70)`; `tasks/0445 (§186.161, AFFI-30..33)`; `tasks/0455 (§1–47, ART-20..50)`; `tasks/0465 (§206.24, ANET2-44..45)`; `tasks/0471 (§212.1–100, AKERNEL-20..70)`; `spec/SPEC-03-core-semantics.md`; `spec/SPEC-04-core-extensibility.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-51-raw-memory-volatile-mmio-layout.md`.
Covers: `REQ-ABI-031`, `REQ-ABI-102` (and specifies the E13.3 contract for `T512`–`T515`: `REQ-ABI-055`, `REQ-ABI-056`, `REQ-ABI-078`, `REQ-ABI-083`, `REQ-CAP-140`, `REQ-CAP-143`, `REQ-FFI-005`, `REQ-FFI-006`, `REQ-FFI-008`, `REQ-FFI-009`, `REQ-FFI-020`, `REQ-FFI-024`, `REQ-FFI-058`, `REQ-FFI-066`, `REQ-FFI-080`, `REQ-FFI-121`, `REQ-RES-145`, `REQ-RES-170`).
Consumers: `compiler/driver/`, `compiler/hir/`, `compiler/sema/`, `compiler/types/`, `compiler/mir/`, `compiler/opt/`, `compiler/lir/`, `compiler/abi/`, `compiler/target/x64/`, `compiler/obj/`, `compiler/link/`, `std/core/`, `std/alloc/`, `T512`–`T515`.

## Tóm tắt

Tài liệu `SPEC-52` chuẩn hóa mô hình hợp thành runtime theo mô-đun (`modular runtime composition`), bốn hồ sơ biên dịch (`--profile hosted|freestanding|kernel|system`), phân tầng thư viện chuẩn (`std.core`, `std.alloc`, `std`), quy tắc khởi tạo tĩnh tất định không có hàm tạo toàn cục ẩn, hệ thống thuộc tính mức hệ thống (`@entry`, `@panic_handler`, `@global_allocator`, `@naked`, `@section("...")`, `@used`, `@no_mangle`), quy ước gọi hàm ngắt phần cứng (`extern "interrupt"`), và đồ thị năng lực runtime (`Runtime Capability Graph`) cho phân hệ `E13.3` (Phase `P13`):
- **Không có runtime nguyên khối; ABI của runtime được định phiên bản độc lập (`0143 §1–4`, `0104 §54`, `ARUNTIME-20..25`, `ART-20..50`, `REQ-ABI-031`, `REQ-FFI-066`, `INV-SEM-005`)**: Axiom không có thư viện `libaxiom_runtime` bắt buộc. Runtime là tập hợp các thành phần độc lập (`Startup`, `Panic`, `HeapAlloc`, `Unwind`, `Tls`, `Thread`, `Blocking`, `AsyncReactor`, `OsIo`, `OsEnvProcess`, `GpuRuntime`, `Reflect`) chỉ được liên kết khi thực sự khả đạt từ gốc ngữ nghĩa của chương trình sau khi tối ưu hóa. ABI của các thành phần runtime được định phiên bản tách biệt với Core ABI (`REQ-ABI-031`), và cùng một mô hình ngữ nghĩa Axiom duy nhất áp dụng xuyên suốt mọi miền thực thi (`hosted`, `freestanding`, `kernel`, `system`, `interrupt`, `device`/`GPU` — không tạo phương ngữ thứ hai, `REQ-FFI-066`).
- **Bốn hồ sơ biên dịch (`--profile hosted|freestanding|kernel|system`) và phân tầng `std.core` / `std.alloc` / `std` (`0097`, `tasks/0370`, `tasks/0455`, `tasks/0471`)**: Hồ sơ `freestanding` và `kernel` loại bỏ hoàn toàn sự phụ thuộc ngầm vào hệ điều hành, CRT (`msvcrt`/`ucrt`/`libc`), và `kernel32.dll` (`0` DLL import trong ảnh PE32+ xuất ra ở `T513`). Tầng `std.core` (`Option`, `Result`, slice/view, `Str`, `iter`, `cmp`, `hash`, `num`, `mem`, `ptr`, `atomic`, `fmt` vào bộ đệm cố định) hoạt động 100% không cần OS hay heap; `std.alloc` khả dụng khi người dùng đăng ký `@global_allocator` hoặc truyền bộ cấp phát cục bộ (`T514`).
- **Điểm vào `@entry`, `@panic_handler`, `@global_allocator`, `@naked`, `@section`, `@used` và miền thực thi ngắt `extern "interrupt"` (`REQ-ABI-102`, `REQ-ABI-078`, `T512`–`T514`)**: Trong `freestanding`/`kernel`, `@entry` đặt trực tiếp điểm vào ảnh thực thi không qua stub `main` của OS; `@naked` tắt sinh prologue/epilogue; `@section("...")` và `@used` điều khiển bố cục phân đoạn COFF/ELF và giữ gốc chống cắt bỏ (`COMDAT` GC). Trình xử lý ngắt phần cứng `extern "interrupt"` bảo toàn tập thanh ghi theo bảng dữ liệu `CallingConventionDescription` (`REQ-ABI-078`), thoát bằng `IRETQ`, và **cấm tuyệt đối** cấp phát heap ngầm, chặn (`blocking`), tạo luồng, gọi I/O hệ điều hành, hoặc `.await` trực tiếp hay bắc cầu (`AX_UNSAFE_INTERRUPT_FORBIDDEN_OP`, `REQ-ABI-102`).
- **Đồ thị năng lực runtime (`RuntimeCapabilityGraph`) và hợp đồng sở hữu bộ cấp phát ngoại lai / DMA (`tasks/0359`, `REQ-CAP-140`, `REQ-CAP-143`, `REQ-FFI-005..121`)**: Trình biên dịch tính bao đóng bắc cầu các năng lực runtime trên đồ thị lời gọi sau tối ưu hóa để loại bỏ các thành phần không còn dùng tới và từ chối tại thời điểm biên dịch mọi năng lực bị cấm bởi hồ sơ (`AX_DRIVER_PROFILE_FORBIDDEN_CAP`). Đồng thời, quyền sở hữu vùng cấp phát ngoại lai (`ForeignBox<T, A>`) và bộ đệm truyền DMA (`DmaBuffer<T>` khóa quyền ghi CPU `mut_view` khi truyền thiết bị đang hoạt động) được mô hình hóa tường minh bằng kiểu và capability.

---

## 1. Modular Runtime Composition, Compilation Profiles & Standard Library Layering (`AXS-FRE-001`..`005`)

### AXS-FRE-001 — Composable Runtime Architecture, Separate Runtime ABI Versioning & Unified Semantic Model (`ARUNTIME-20..63`, `ART-20..50`, `REQ-ABI-031`, `REQ-FFI-066`)

1. **No Monolithic Runtime (`0143 §1`, `tasks/0359 §1`, `INV-SEM-005`)**:
   - Axiom has no mandatory monolithic runtime library (`libaxiom_runtime.a`, `axiom-runtime.dll`), no garbage collector, no implicit background worker threads, and no mandatory C runtime (`msvcrt`, `ucrt`, `glibc`).
   - Instead, runtime support is factored into orthogonal, independently linkable runtime capabilities (`AXS-FRE-020`). A compiled binary links **only** the minimal closure of runtime components transitively required by its post-optimization reachable code (`ARUNTIME-21..22`, `ARUNTIME-63`).
2. **Separate Runtime ABI Versioning (`0104 §54`, `tasks/0455 ART-40, ART-50`, `REQ-ABI-031`)**:
   - The binary interface of optional runtime components (`Runtime ABI`: startup adapter entry points, panic hook descriptor `PanicInfo`, global allocator dispatch table, unwinder personality, thread/async reactor vtables) is versioned separately from the Core language type/layout ABI (`REQ-ABI-031`, `AXD-063`).
   - Every separately compiled runtime object or dynamic runtime plugin embeds an explicit `AXIOM_RUNTIME_ABI_VERSION: u32` contract (`v1 = 0x0001_0000u32`); replacing or linking a runtime component with a mismatched ABI version is rejected at link/load time without requiring changes to Core language semantics (`ART-39..40`).
3. **One Language Semantic Model Across All Execution Domains (`0138 Part XX`, `tasks/0471 AKERNEL-24, AKERNEL-67`, `REQ-FFI-066`)**:
   - Axiom maintains **one** core type, ownership, capability (`view<T>` / `mut_view<T>`), initialization, and `Drop` model across `hosted`, `freestanding`, `kernel`, `system`, `interrupt`, and `device`/`GPU` domains (`REQ-FFI-066`). Profiles and execution domains restrict *which platform/runtime capabilities are available*, never redefining Core language semantics or bypassing the MIR ownership/capability verifier (`AKERNEL-24`, `AKERNEL-58`).
[0104 §54; 0138 Part XX; 0143 §1–4, §63–65 ARUNTIME-20..63; tasks/0359 ARUNTIME-20..90; tasks/0370 ARUNTIME-20..57; tasks/0455 ART-20..50; tasks/0471 AKERNEL-20..24, AKERNEL-58, AKERNEL-67; REQ-ABI-031, REQ-FFI-066; INV-SEM-005]

### AXS-FRE-002 — Compilation Profiles (`--profile hosted|freestanding|kernel|system`, `SPEC-04 AXS-EXT-062`, `T512`)

The compilation session carries an explicit `Profile` selected via `--profile <name>` on the CLI or `profile = "<name>"` under `[package]` / `[target]` in `axiom.toml` (defaulting to `hosted`). Any unknown profile name is rejected with `AX_DRIVER_INVALID_PROFILE` (exit code `2`):

| Profile | Entry Convention | Default OS / CRT Imports | Allowed `std` Layers | Primary Target Domains |
|---|---|---|---|---|
| `hosted` (default) | `fn main()` via `axiom_start` stub (`AXS-SEM-080`) | On-demand OS imports (`KERNEL32.dll` on Windows x64; no CRT required) | `std.core`, `std.alloc`, full `std` (`io`, `fs`, `net`, `thread`, `async`, `os`) | CLI tools, applications, servers, compiler (`axiomc`) |
| `freestanding` | `@entry fn ...` direct image entry (`AXS-FRE-010`) | **Zero** implicit OS, CRT, or `kernel32.dll` imports (`T513`) | `std.core`; `std.alloc` (only if `@global_allocator` or local arena is supplied) | Bare-metal firmware, bootloaders, DSP/crypto modules, embedded RTOS |
| `kernel` | `@entry fn ...` direct image entry (`AXS-FRE-010`) | **Zero** implicit user-space OS or CRT imports | `std.core`; `std.alloc` (with kernel `@global_allocator`); `@at`/`@addr` & `extern "interrupt"` enabled | OS kernels, hypervisors, ring-0 / EL1 executives |
| `system` | `fn main()` or `@entry fn ...` | Explicit `@link` system libraries / syscalls only; no monolithic runtime | `std.core`, `std.alloc`, explicit `std.os` / driver bindings | Low-level system daemons, device drivers, minimal OS services |

[0097 §1–11, §60 AOS-01..35; 0143 §2–7; tasks/0370 §4; tasks/0455 §6, ART-48; tasks/0471 §1–4, AKERNEL-20..26; SPEC-04 AXS-EXT-062]

### AXS-FRE-003 — Standard Library Three-Layer Architecture (`std.core`, `std.alloc`, `std`) (`tasks/0455 §47`, `T514`)

To guarantee that freestanding and kernel programs never pull in hidden OS or heap dependencies (`ARUNTIME-22..25`, `AKERNEL-20..23`), `std/` is strictly partitioned into three dependency-ordered layers:

1. **Layer 1 — `std.core` (Zero-OS, Zero-Heap Foundation)**:
   - Modules: `std.core.option` (`Option<T>`), `std.core.result` (`Result<T, E>`), `std.core.cmp`, `std.core.ops`, `std.core.num`, `std.core.mem` (`size_of`, `align_of`, `offset_of`, `MaybeUninit<T>`, `ManuallyDrop<T>`, `Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, `MmioWO<T>`, `bitcast`), `std.core.ptr`, `std.core.slice`, `std.core.str`, `std.core.iter`, `std.core.hash`, `std.core.atomic` (`Atomic<T>`, `Ordering`, fences), `std.core.fmt` (fixed-buffer `BufWriter` formatting without heap allocation), `std.core.future` (`Future`, `Poll`, `Waker`, `Context`), and `std.core.panic` (`PanicInfo`).
   - **Dependency Invariant**: `std.core` MUST NOT reference `std.alloc`, `std.os`, `std.io`, `std.fs`, `std.net`, `std.thread`, `host.heap_*`, `host.io_*`, or any `@link` external OS symbol. Every `std.core` item is unconditionally available in all four profiles (`hosted`, `freestanding`, `kernel`, `system`).
2. **Layer 2 — `std.alloc` (Explicit Allocation Layer)**:
   - Modules: `std.alloc.Allocator`, `std.alloc.GlobalAlloc`, `std.alloc.Layout`, `std.alloc.Arena`, `std.alloc.FixedBufAllocator`, `std.alloc.ForeignBox<T, A>`, `std.boxed.Box<T>`, `std.vec.Vec<T>`, `std.string.String`, `std.collections.*`, `std.sync.Arc<T>`, `std.rc.Rc<T>`.
   - Depends only on `std.core`. Collections and smart pointers parameterized by an explicit local `Allocator` (`FixedBufAllocator` over a `[N]u8` buffer) require **zero** global heap runtime capability; APIs using the default global allocator require `RuntimeCap.HeapAlloc` (satisfied by `@global_allocator` in `freestanding`/`kernel` or default OS heap in `hosted`).
3. **Layer 3 — Hosted Platform & I/O Layer (`std.os`, `std.io`, `std.fs`, `std.net`, `std.thread`, `std.process`, `std.env`, `std.time`, `std.async`)**:
   - Wraps target OS syscalls and platform APIs (`0097 AOS-02`). Importing (`use std.os.*`, `use std.fs.*`, `use std.net.*`, `use std.process.*`, `use std.thread.*`) in `--profile freestanding` or `--profile kernel` is rejected at compile time with `AX_NAME_FREESTANDING_FORBIDDEN_IMPORT`.
[0097 §1, §11, AOS-01..02; 0143 §3–4, §28–35; tasks/0359 §3–4; tasks/0455 §47; tasks/0471 AKERNEL-20..23]

### AXS-FRE-004 — Static Storage, Constant Initialization & Prohibition of Hidden Global Constructors (`tasks/0358 AINIT-20..80`, `T513`)

1. **`const` vs `static` Storage Identity (`AINIT-20..23`, `SPEC-04 AXS-EXT-024, AXS-EXT-030, AXS-EXT-041`)**:
   - `const NAME: T = expr` defines a compile-time constant value inlined at use sites without mandatory storage identity.
   - `static NAME: T = expr` and `static mut NAME: T = expr` (`ItemKind.Static`, `PlaceBase.Static(SymbolId)`) define program-lifetime storage placed in `.rdata` (immutable `static`), `.data` (mutable `static mut` with non-zero initial bytes), or `.bss` (all-zero initial bytes, occupying `0` file bytes in the image per `AINIT-69..70`).
2. **Mandatory Compile-Time Initialization & Zero Global Constructors (`AINIT-24..31`, `ARUNTIME-29..34`)**:
   - Every module-scope `static` and `static mut` initializer MUST be a compile-time constant expression evaluated by the const-evaluator (`AINIT-24..25`). A non-constant initializer on `static` is rejected at compile time.
   - Axiom has **no implicit C++-style global constructors or destructors** (`AINIT-29..30`, `AINIT-55..56`). Importing a module never executes runtime initialization code (`AINIT-27`), and static initialization semantics never depend on module import order, source file order, or object link order (`AINIT-28`, `AINIT-76..77`).
   - Runtime on-demand initialization is expressed explicitly via `std.sync.OnceCell<T>` / `Lazy<T>`, which initializes on first access and traps deterministically on recursive initialization cycles (`AINIT-32..34`, `AINIT-60`).
[0143 §9–15, ARUNTIME-29..34; tasks/0358 §1–12, §35 AINIT-20..80; tasks/0455 ART-35..38; tasks/0471 AKERNEL-27]

### AXS-FRE-005 — Explicit Foreign Allocation Domains (`ForeignBox<T, A>`), DMA Buffer Ownership (`DmaBuffer<T>`) & Move/Copy Lowering (`T513`, `T514`)

1. **Explicit Foreign Allocator Domains (`REQ-FFI-005`, `REQ-FFI-006`, `REQ-FFI-008`, `REQ-FFI-009`, `REQ-FFI-020`, `REQ-FFI-024`, `REQ-FFI-058`, `REQ-FFI-080`, `REQ-FFI-121`, `REQ-RES-170`)**:
   - Foreign raw pointers (`*const T`, `*mut T`) never imply automatic ownership (`REQ-FFI-121`), and the compiler NEVER guesses or infers compatibility between foreign allocation domains (`malloc`/`free`, Win32 `HeapAlloc`, kernel pool, device buffers) and Axiom's allocator (`REQ-FFI-005..009`, `REQ-FFI-020`, `REQ-FFI-024`, `REQ-FFI-058`, `REQ-FFI-080`, `REQ-RES-170`).
   - `std.alloc.ForeignBox<T, A: ForeignDeleter>` encapsulates an owned pointer allocated by foreign domain `A` (`pub trait ForeignDeleter { unsafe fn free(ptr: *mut u8); }`), running `A.free(self.ptr as *mut u8)` deterministically on `Drop` without mixing allocator heaps (`T514`).
2. **Physical Addresses & DMA Buffer Ownership (`DmaBuffer<T>`, `DmaTransfer<T>`, `REQ-CAP-140`, `REQ-CAP-143`, `tasks/0465 ANET2-44..45`, `tasks/0471 AKERNEL-34..37`)**:
   - Physical memory addresses (`PhysAddr` / `@addr_space(6)`) remain distinct from safe Axiom pointers (`REQ-CAP-143`, `SPEC-51 AXS-MEM-024`).
   - `std.mem.DmaBuffer<T>` tracks CPU vs hardware device ownership (`T513`, `T514`): starting a device transfer (`dma_buf.start_transfer(phys_addr) -> DmaTransfer<T>`) moves the `DmaBuffer<T>` into an active `DmaTransfer<T>` token, **statically prohibiting any CPU `mut_view<T>` or `view<T>` access** while the DMA transfer is in flight (`REQ-CAP-140`, `AKERNEL-35`) and keeping the buffer allocation valid and pinned until `transfer.wait_complete() -> DmaBuffer<T>` issues the required memory/cache barrier (`write_barrier` / `memory_barrier`) and restores CPU ownership (`REQ-CAP-143`, `AKERNEL-36..37`).
3. **Register Scalarization & Zero Mandatory Physical Copy on `Move`/`Copy` (`REQ-ABI-055`, `REQ-ABI-056`, `REQ-ABI-083`, `REQ-RES-145`)**:
   - Semantic `Move` (ownership transfer, `ATYPE-46`, `REQ-ABI-055`), semantic `Copy` (`ATYPE-47`, `REQ-ABI-056`), and returning owned values (`REQ-RES-145`) are semantic ownership transitions and MUST NOT mandate physical memory copies (`memcpy`) when values can be kept in registers, scalarized (`SROA`), constructed in-place (`RVO`/`NRVO`), or passed/returned in registers per the Target ABI (`REQ-ABI-083`, `T513`).
[0111 §47; 0119 §233, §259 AFFI-20..21; 0129 §76–77, §101 ATYPE-46..47; 0131 §67, §88 AFN-54; 0138 §100 AFFI-27; 0230 §6; tasks/0367 §82; tasks/0413 §70; tasks/0445 §186.161 AFFI-30..33; tasks/0465 §206.24 ANET2-44..45; tasks/0471 §212.11–14 AKERNEL-34..37; REQ-ABI-055, REQ-ABI-056, REQ-ABI-083, REQ-CAP-140, REQ-CAP-143, REQ-FFI-005..009, REQ-FFI-020, REQ-FFI-024, REQ-FFI-058, REQ-FFI-080, REQ-FFI-121, REQ-RES-145, REQ-RES-170]

---

## 2. Entry Points, Panic/Allocator Hooks, Section/Symbol Attributes & Interrupt Calling Conventions (`AXS-FRE-010`..`016`)

### AXS-FRE-010 — Hosted `fn main` vs Freestanding `@entry` Contract (`0143 §5–8`, `0097 AOS-09..11`, `tasks/0358 AINIT-51..54`, `T512`, `T513`)

1. **Hosted Entry (`--profile hosted`, `SPEC-03 AXS-SEM-080`)**:
   - In `hosted` executables, the root module defines `fn main()` (returning `()`, `i32`, `u32`, or `never`). The linker synthesizes the `axiom_start` startup adapter, which calls `main` and passes its return code to the OS process exit ABI (`KERNEL32.dll!ExitProcess` on Windows x64).
2. **Freestanding & Kernel Entry (`@entry`, `SPEC-04 AXS-EXT-032, AXS-EXT-091`)**:
   - In `--profile freestanding` and `--profile kernel` executable builds, `main` is not implicitly recognized; the program MUST define **exactly one** function annotated with `@entry`:
     ```axiom
     @entry
     pub fn _start() -> i32 {
         return 0
     }
     ```
   - **Validation (`AX_TYPE_ENTRY_MISSING`, `AX_TYPE_DUPLICATE_ENTRY`, `AX_TYPE_ENTRY_SIGNATURE`)**:
     - If an executable build under `freestanding` or `kernel` has zero `@entry` functions, `compiler/sema/` emits `AX_TYPE_ENTRY_MISSING`.
     - If more than one `@entry` function is defined across the compilation graph, `compiler/sema/` emits `AX_TYPE_DUPLICATE_ENTRY` (`labels` at the first `@entry`).
     - An `@entry` function MUST NOT have generic type/const parameters, MUST NOT be `async`, and MUST have one of the canonical entry signatures:
       - `fn() -> never`, `fn() -> i32`, `fn() -> u32`, or `fn() -> usize` (parameterless bare-metal / freestanding test entry);
       - `fn(arg0: usize) -> never` or `fn(arg0: *const u8, arg1: *const u8) -> usize` (bootloader / kernel handoff or UEFI `efi_main` signature).
       Any other signature is rejected with `AX_TYPE_ENTRY_SIGNATURE`.
   - **Direct Linker Lowering (`T513`)**: The linker sets the image entry point (`PE32+ OptionalHeader.AddressOfEntryPoint`) directly to the `@entry` function symbol and suppresses the hosted `axiom_start` stub. When `@entry` returns `i32` / `u32` on x86-64 Windows (`T513`, `T515`), `RET` returns `EAX` directly to the OS loader thread thunk without importing `kernel32.dll`.
[0097 AOS-09..11; 0143 §5–8, ARUNTIME-26..28; tasks/0358 AINIT-51..54; tasks/0455 ART-26..27; tasks/0471 §212.3–5, AKERNEL-25..26; SPEC-03 AXS-SEM-080; SPEC-04 AXS-EXT-032, AXS-EXT-091]

### AXS-FRE-011 — Pluggable `@panic_handler` Contract (`0143 §36–41`, `ARUNTIME-41..47`, `T512`, `T514`)

1. **`PanicInfo` Descriptor (`std/core/panic.ax`)**:
   ```axiom
   @repr(C)
   pub struct PanicInfo {
       pub message: Str,
       pub file: Str,
       pub line: u32,
       pub col: u32,
   }
   ```
2. **Handler Selection & Signature Validation (`AX_TYPE_INVALID_PANIC_HANDLER`, `AX_TYPE_DUPLICATE_PANIC_HANDLER`)**:
   - In `hosted` builds, `std` provides the default abort panic handler (`panic: <message>\n` to stderr, exit code `101`, `SPEC-03 AXS-SEM-071`) unless overridden.
   - In `freestanding` and `kernel` builds, user code may define at most one `@panic_handler` function:
     ```axiom
     @panic_handler
     fn handle_panic(info: view<PanicInfo>) -> never {
         loop {}
     }
     ```
   - `@panic_handler` MUST be a non-generic, non-`async` function with signature `fn(view<PanicInfo>) -> never` or `fn() -> never`. Any other signature (or returning a type other than `never`) is rejected with `AX_TYPE_INVALID_PANIC_HANDLER`. Defining more than one `@panic_handler` in a binary is rejected with `AX_TYPE_DUPLICATE_PANIC_HANDLER`.
   - If a `freestanding` or `kernel` binary has no user `@panic_handler`, compiler-inserted and explicit panics lower to the minimal target hardware trap stub (`UD2` / exit code `101` in `--interp` and test harness mode) without pulling in `std.io` or `kernel32.dll`.
[0143 §36–41, ARUNTIME-41..47; tasks/0359 ARUNTIME-46..47; tasks/0370 ARUNTIME-46; tasks/0471 §212.15–16]

### AXS-FRE-012 — Pluggable `@global_allocator` & `std.alloc.Allocator` Contract (`0143 §28–35`, `ARUNTIME-37..40`, `T512`, `T514`)

1. **`Layout` and `Allocator` / `GlobalAlloc` Traits (`std/alloc/mod.ax`)**:
   ```axiom
   @derive(Copy, Clone, Eq, PartialEq)
   @repr(C)
   pub struct Layout {
       pub size: usize,
       pub align: usize,
   }

   pub trait Allocator {
       unsafe fn alloc(self: mut_view<Self>, layout: Layout) -> *mut u8
       unsafe fn dealloc(self: mut_view<Self>, ptr: *mut u8, layout: Layout)
   }

   pub trait GlobalAlloc {
       unsafe fn alloc(self: view<Self>, layout: Layout) -> *mut u8
       unsafe fn dealloc(self: view<Self>, ptr: *mut u8, layout: Layout)
   }
   ```
2. **`@global_allocator` Registration & Validation (`AX_TYPE_INVALID_GLOBAL_ALLOCATOR`, `AX_TYPE_DUPLICATE_GLOBAL_ALLOCATOR`)**:
   - Applying `@global_allocator` to a module-scope `static` item (`@global_allocator static ALLOC: BumpAlloc = ...`) binds all global heap allocation requests (`RuntimeCap.HeapAlloc`) in the binary to `ALLOC.alloc` and `ALLOC.dealloc`.
   - Applying `@global_allocator` to a non-`static` item or to a `static` whose type does not implement `GlobalAlloc` (or `Allocator`) is rejected with `AX_TYPE_INVALID_GLOBAL_ALLOCATOR`.
   - Defining more than one `@global_allocator` in a binary is rejected with `AX_TYPE_DUPLICATE_GLOBAL_ALLOCATOR`.
[0143 §28–35, ARUNTIME-37..40; tasks/0359 ARUNTIME-41; tasks/0455 §9, ART-28; tasks/0471 AKERNEL-22, AKERNEL-50]

### AXS-FRE-013 — `@naked` Functions (`SPEC-04 AXS-EXT-054`, `T512`, `T513`)

1. **Semantics**: A function annotated with `@naked` (`fn_flags.is_naked = true`) instructs `compiler/target/x64/frame.ax` to emit **zero** prologue and **zero** epilogue instructions (no `push rbp`, no `sub rsp, N`, no callee-saved register saves, no stack probe `__chkstk`, and no implicit trailing `ret` when the body ends with a diverging transfer).
2. **Compile-Time Restrictions (`AX_TYPE_INVALID_NAKED_FN`)**:
   - A `@naked` function MUST be declared `unsafe fn` (or `@entry` / `extern "interrupt"` in low-level boot stubs) and MUST NOT be `async`.
   - A `@naked` function body MUST NOT allocate stack-spilled local variables (`FrameLayout.local_stack_size == 0`) or pass/receive stack-allocated aggregates that require a compiler-managed frame pointer. Violating any `@naked` constraint is rejected with `AX_TYPE_INVALID_NAKED_FN`.
[SPEC-04 AXS-EXT-054; tasks/0471 §212.4–5]

### AXS-FRE-014 — `@section("...")`, `@used`, and `@no_mangle` Placement & Retention Contracts (`SPEC-04 AXS-EXT-071..072`, `T512`, `T513`)

1. **Custom Section Placement (`@section("name")`, `AX_TYPE_INVALID_SECTION`)**:
   - `@section("name")` may be attached to a `fn` or `static` item, placing its emitted machine code or initialized data bytes into a COFF/ELF section named `"name"` (`SectionKind.Custom(name)` with executable flags for `fn`, read-only data flags for `static`, and read-write data flags for `static mut`).
   - Validation: `name` MUST be a non-empty ASCII string literal (`1..=64` bytes) containing no NUL (`\0`) or control characters, and `@section` MUST NOT be applied to local `let` bindings, parameters, or type declarations (`AX_TYPE_INVALID_SECTION`).
2. **Dead-Strip / Section GC Root Retention (`@used`, `SPEC-75 AXS-LTO-003, AXS-LTO-020`)**:
   - `@used` may be attached to a `static` or `fn` item (`AX_TYPE_INVALID_SECTION` if applied to a local or type).
   - An item marked `@used` is registered as an unconditional reachability root in `WPO` (`compiler/opt/wpo.ax`), runtime capability discovery, and linker `COMDAT` section garbage collection (`compiler/link/`), guaranteeing that its symbol and custom section bytes (e.g., multiboot headers, interrupt vector tables, firmware descriptors) are never stripped even when unreferenced by code.
3. **Unmangled Symbol Identity (`@no_mangle`, `SPEC-50 AXS-UNS-032`)**:
   - `@no_mangle` on a non-generic `fn` or `static` emits the item's source identifier verbatim as its object symbol name (`AX_FFI_GENERIC_EXPORT` if generic).
[SPEC-04 AXS-EXT-071, AXS-EXT-072; SPEC-50 AXS-UNS-032; SPEC-75 AXS-LTO-003, AXS-LTO-020; tasks/0358 AINIT-66..67; tasks/0471 AKERNEL-63]

### AXS-FRE-015 — Hardware Interrupt Calling Convention (`extern "interrupt"`, `InterruptFrame`, `REQ-ABI-102`, `REQ-ABI-078`, `T512`, `T513`)

1. **Syntax & `InterruptFrame` Layout (`SPEC-04 AXS-EXT-022, AXS-EXT-052`)**:
   - Hardware interrupt and CPU exception handlers are declared with the `"interrupt"` ABI string:
     ```axiom
     @repr(C)
     pub struct InterruptFrame {
         pub rip: u64,
         pub cs: u64,
         pub rflags: u64,
         pub rsp: u64,
         pub ss: u64,
     }

     extern "interrupt" fn timer_isr(frame: view<InterruptFrame>) { ... }
     extern "interrupt" fn page_fault_isr(frame: view<InterruptFrame>, error_code: u64) { ... }
     ```
   - Accepted parameter lists for `extern "interrupt" fn` (`AX_FFI_BAD_TYPE` otherwise): `()`, `(frame: view<InterruptFrame>)`, `(frame: *const InterruptFrame)`, `(frame: view<InterruptFrame>, error_code: u64)`, or `(frame: *const InterruptFrame, error_code: u64)`. The return type MUST be `()` or `never`.
2. **Data-Driven Register Preservation & `IRETQ` Epilogue (`0163 §6`, `REQ-ABI-078`, `T513`, `T514`)**:
   - Caller-saved and callee-saved register sets are defined strictly as target metadata in `CallingConventionDescription` inside `TargetDesc` (`0163 §6`, `REQ-ABI-078`), never hard-coded inside the register allocator.
   - For `CallConv.Interrupt` on `x86_64`, **all** general-purpose registers (`RAX`, `RCX`, `RDX`, `RBX`, `RBP`, `RSI`, `RDI`, `R8`–`R15`) belong to the preserved set: `compiler/target/x64/frame.ax` saves every GPR modified by the handler (or clobbered by a call inside the handler), aligns `RSP` to 16 bytes before any inner call, restores all saved GPRs in reverse order, and terminates the epilogue with `IRETQ` (`48 CF`) instead of `RET`.
[0097 AOS-27; 0163 §6; tasks/0471 §212.9–14, AKERNEL-28, AKERNEL-30, AKERNEL-47; SPEC-04 AXS-EXT-022, AXS-EXT-052; REQ-ABI-078, REQ-ABI-102]

### AXS-FRE-016 — Interrupt Execution Domain Restrictions: Prohibition of Allocation, Blocking & `await` (`REQ-ABI-102`, `AKERNEL-28..29`, `T512`)

Every `extern "interrupt"` function executes in `ExecutionDomain.Interrupt` (`tasks/0471 §212.10–13`). To prevent deadlocks, unbounded latency, and reentrancy corruption in interrupt context (`REQ-ABI-102`, `AKERNEL-28..29`), `compiler/sema/` enforces over the transitive call graph rooted at each `extern "interrupt"` function:

1. **No `async` or `.await`**: An `extern "interrupt"` function cannot be declared `async` (`AX_ASYNC_EXTERN_ABI`) and cannot evaluate `.await` (`AX_ASYNC_AWAIT_OUTSIDE_ASYNC` / `AX_UNSAFE_INTERRUPT_FORBIDDEN_OP`).
2. **No Implicit or Global Heap Allocation (`REQ-ABI-102`)**: Directly or transitively requiring `RuntimeCap.HeapAlloc` (`Box.new`, `Vec.push`, `String`, `host.heap_alloc`, or `@global_allocator` calls) inside an `extern "interrupt"` handler is rejected at compile time with `AX_UNSAFE_INTERRUPT_FORBIDDEN_OP` (`data.capability = "heap_alloc"`, `data.callee`). Pre-allocated static ring buffers and fixed-capacity `FixedBufAllocator` arenas do not require `RuntimeCap.HeapAlloc` and are permitted.
3. **No Blocking, Thread Creation, or Hosted OS I/O (`REQ-ABI-102`)**: Directly or transitively requiring `RuntimeCap.Blocking` (`Mutex.lock`, `RwLock.write`, `Condvar.wait`, `Thread.sleep`, `JoinHandle.join`), `RuntimeCap.Thread` (`thread.spawn`), `RuntimeCap.AsyncReactor` (`block_on`), or `RuntimeCap.OsIo` (`std.io`, `std.fs`, `std.net`) inside an `extern "interrupt"` handler is rejected at compile time with `AX_UNSAFE_INTERRUPT_FORBIDDEN_OP` (`data.capability = "blocking" | "thread" | "async_reactor" | "os_io"`). Lock-free `Atomic<T>` operations, `Volatile<T>`/`Mmio*<T>` register accesses, and interrupt-masked spinlocks are permitted.
[0097 AOS-27; tasks/0471 §212.9–13, AKERNEL-28..29; REQ-ABI-102]

---

## 3. Compile-Time Runtime Capability Graph & Profile Verification (`AXS-FRE-020`..`023`)

### AXS-FRE-020 — Canonical Runtime Capability Set (`RuntimeCap`, `tasks/0359 §1–8 ARUNTIME-20..90`, `tasks/0455 ART-20..50`, `T512`)

The compiler models runtime dependencies as a closed bitset of 12 semantic runtime capabilities (`RuntimeCap`):

| `RuntimeCap` Variant | String Key (`data.capability`) | Semantic Operations Introducing the Capability |
|---|---|---|
| `Startup` | `"startup"` | Hosted `fn main` startup adapter (`axiom_start` + OS process termination) |
| `Panic` | `"panic"` | `panic(...)`, `assert(...)`, `unreachable()`, checked arithmetic/bounds/shift/`char` failure edges (`MirTerminator.Assert`) |
| `Unwind` | `"unwind"` | Stack unwinding cleanup landing pads under `--panic=unwind` (`E13.5`) |
| `HeapAlloc` | `"heap_alloc"` | Global heap allocation (`host.heap_alloc`, `host.heap_realloc`, `host.heap_free`, `Box`, `Vec`, `String` using global allocator) |
| `Tls` | `"tls"` | `@thread_local static` items and `std.thread.LocalKey<T>` accesses |
| `Thread` | `"thread"` | OS thread creation and management (`std.thread.spawn`, `host.thread_*`) |
| `Blocking` | `"blocking"` | OS thread parking, blocking locks, condition variables, `Thread.sleep`, synchronous blocking wait (`host.park`, `Mutex.lock`) |
| `AsyncReactor` | `"async_reactor"` | Hosted event loop / `Reactor` / multi-thread `Executor` (`host.aio_*`, `std.async`) |
| `OsIo` | `"os_io"` | Hosted console, filesystem, pipe, and socket operations (`std.io`, `std.fs`, `std.net`, `host.print`, `host.file_*`, `host.net_*`) |
| `OsEnvProcess` | `"os_env_process"` | Process arguments, environment variables, system clock, and child processes (`std.env`, `std.process`, `std.time`, `host.args`, `host.exit`) |
| `GpuRuntime` | `"gpu_runtime"` | Host GPU device discovery, queue submission, and buffer mapping (`std.gpu`) |
| `Reflect` | `"reflect"` | Opt-in runtime reflection metadata tables |

[0143 §1, §63–65; tasks/0359 §1–8, §51 ARUNTIME-20..55; tasks/0370 §2–3; tasks/0455 §1–2, ART-20..34]

### AXS-FRE-021 — Post-Optimization Transitive Discovery & Dead Runtime Elimination (`tasks/0359 §5–7 ARUNTIME-23..30`, `T512`)

1. **Semantic Usage Over Module Imports (`ARUNTIME-22..23`, `ART-24`)**:
   - Runtime capabilities are derived from **reachable operations** in the program, never merely from module `use` statements (`tasks/0359 §3`), `Atomic<T>` instructions (`ARUNTIME-49`, `ART-47`), or pure `async fn` / `Future` state-machine construction polled with a custom bare-metal waker (`ARUNTIME-46..47`, `ARUNTIME-50`, `ART-46`).
2. **Transitive Call-Graph Closure**:
   - Let $\text{Roots}$ be the set of entry and retention roots of the artifact:
     $$\text{Roots} = \{\text{main or } \text{@entry}\} \cup \{f \mid f \text{ has } \text{@export or @used}\} \cup \{h \mid h \text{ is } \text{extern "interrupt"}\}$$
   - For each function $f$, $\text{DirectCap}(f) \subseteq \text{RuntimeCap}$ is the union of capabilities introduced by statements, terminators, and intrinsic/host calls in $f$'s body.
   - The transitive capability requirement $\text{TransCap}(f)$ is the least fixed point over the call graph:
     $$\text{TransCap}(f) = \text{DirectCap}(f) \cup \bigcup_{(f \to g) \in \text{CallEdges}} \text{TransCap}(g)$$
   - The binary's required runtime closure is $\text{BinaryCap} = \bigcup_{r \in \text{Roots}} \text{TransCap}(r)$.
3. **Post-Optimization Recomputation (`tasks/0359 §5–6`, `ARUNTIME-25, ARUNTIME-29`)**:
   - When semantic optimization (`SROA`, escape-driven stack promotion `SPEC-71 AXS-ESC-010`, const-folding, BCE `SPEC-72 AXS-BCE-003`, dead branch elimination, WPO `SPEC-75 AXS-LTO-003`) eliminates an allocation (`Box.new(42)` promoted to a scalar register) or proves a bounds/overflow `Assert` unreachable, recomputing $\text{BinaryCap}$ on Verified MIR removes `HeapAlloc` or `Panic` from the final link closure (`ARUNTIME-27..30`).
   - Conversely, profile legality checks in `compiler/sema/` (`T512`) reject forbidden source-level calls in reachable functions deterministically at compile time (`INV-SEM-002`: profile legality never depends on optimization level).
[tasks/0359 §3–7, §51 ARUNTIME-22..30, ARUNTIME-46..50, ARUNTIME-74; tasks/0455 §2–3, ART-22..24, ART-41, ART-46..47]

### AXS-FRE-022 — Profile Capability Policy Matrix & Compile-Time Rejection (`AX_DRIVER_PROFILE_FORBIDDEN_CAP`, `T512`)

Each compilation profile enforces the following capability policy over every function reachable from $\text{Roots}$:

| `RuntimeCap` | `hosted` | `freestanding` | `kernel` | `system` |
|---|---|---|---|---|
| `Startup` (hosted stub) | Allowed | **Forbidden** | **Forbidden** | Optional (`main` or `@entry`) |
| `Panic` | Allowed (default OS stderr abort) | Allowed (`@panic_handler` or trap stub) | Allowed (`@panic_handler` or kernel halt) | Allowed |
| `HeapAlloc` | Allowed (default OS heap) | **Requires `@global_allocator`** | **Requires `@global_allocator`** | Allowed (OS or `@global_allocator`) |
| `Tls` | Allowed | **Forbidden** (unless target TLS hook provided) | **Forbidden** (use per-CPU GS/FS base) | Allowed |
| `Thread` | Allowed | **Forbidden** | **Forbidden** (kernel defines own scheduler) | Allowed |
| `Blocking` (OS park) | Allowed | **Forbidden** | **Forbidden** | Allowed |
| `AsyncReactor` (OS I/O) | Allowed | **Forbidden** (core `Future` / custom poll allowed) | **Forbidden** (core `Future` / custom poll allowed) | Allowed |
| `OsIo` | Allowed | **Forbidden** | **Forbidden** | Allowed |
| `OsEnvProcess` | Allowed | **Forbidden** | **Forbidden** | Allowed |
| `Unwind` | Optional (`E13.5`) | **Forbidden** | **Forbidden** | Optional (`E13.5`) |

If any function $r \in \text{Roots}$ in `--profile freestanding` or `--profile kernel` transitively requires a **Forbidden** capability (or requires `HeapAlloc` when no `@global_allocator` is declared in the build), the compiler emits `AX_DRIVER_PROFILE_FORBIDDEN_CAP` with `data.profile`, `data.capability`, and a call-chain note tracing $r \to \dots \to f$.
[0097 AOS-10..13, AOS-26..30; 0143 §2–8, §28–49; tasks/0359 ARUNTIME-56..65, ARUNTIME-84..87; tasks/0370 §4; tasks/0455 ART-34, ART-48; tasks/0471 AKERNEL-20..29]

### AXS-FRE-023 — CRT-Free & Zero-DLL-Import Native Image Emission (`T513`, `T515`, `INV-SEM-005`)

1. **Zero Implicit Imports in `--profile freestanding` and `--profile kernel`**:
   - When linking an executable under `--profile freestanding` or `--profile kernel` that contains no explicit `@link("...")` extern blocks, `compiler/link/` MUST emit **zero** DLL import descriptors (`.idata` / PE Data Directory `[1]` `Import Table` RVA = `0`, Size = `0`).
   - Inspecting the resulting PE32+ executable with `objdump -p` (or the internal COFF/PE verifier) shows **no `DLL Name:` entries** (not even `KERNEL32.dll` or `msvcrt.dll`).
2. **Entry & Section Layout (`T513`)**:
   - `OptionalHeader.AddressOfEntryPoint` is bound directly to the RVA of the `@entry` symbol.
   - Custom `@section("name")` items are emitted into dedicated COFF/PE sections in deterministic sorted order after standard `.text`, `.rdata`, `.data`, and `.bss` sections, and `@used` symbols are marked as live roots before `COMDAT` dead-section elimination runs.
[0263; ROADMAP R6; SPEC-04 AXS-EXT-071..074; tasks/0359 ARUNTIME-54..58; tasks/0370 ARUNTIME-26..27, ARUNTIME-57; tasks/0471 AKERNEL-63, AKERNEL-69; INV-SEM-005]

---

## 4. Diagnostics, Canonical Examples & Requirement Traceability (`AXS-FRE-050`..`053`)

### AXS-FRE-050 — Diagnostic Codes Owned or Referenced by `SPEC-52`

| Code | Area | Sev | Delivering Task | Condition & Normative Rule |
|---|---|---|---|---|
| `AX_DRIVER_INVALID_PROFILE` | `DRIVER` | `error` | `T512` | Unknown `--profile <name>` or `axiom.toml` `profile` value outside `{hosted, freestanding, kernel, system}` (exit code `2`; `AXS-FRE-002`). |
| `AX_DRIVER_PROFILE_FORBIDDEN_CAP` | `DRIVER` | `error` | `T512` | A reachable function in `--profile freestanding` or `--profile kernel` transitively requires a forbidden runtime capability (`os_io`, `os_env_process`, `thread`, `blocking`, `async_reactor`, `tls`, `unwind`, or `heap_alloc` without `@global_allocator`) (`AXS-FRE-022`). |
| `AX_NAME_FREESTANDING_FORBIDDEN_IMPORT` | `NAME` | `error` | `T512` | Importing a hosted Layer-3 OS module (`std.os`, `std.io`, `std.fs`, `std.net`, `std.process`, `std.thread`, `std.env`, `std.time`) under `--profile freestanding` or `--profile kernel` (`AXS-FRE-003`). |
| `AX_TYPE_ENTRY_MISSING` | `TYPE` | `error` | `T512` | Executable compiled under `--profile freestanding` or `--profile kernel` defines no `@entry` function (`AXS-FRE-010`). |
| `AX_TYPE_DUPLICATE_ENTRY` | `TYPE` | `error` | `T512` | More than one `@entry` function is defined in the compilation unit (`AXS-FRE-010`). |
| `AX_TYPE_ENTRY_SIGNATURE` | `TYPE` | `error` | `T512` | `@entry` function is generic, `async`, or has a parameter/return signature outside the allowed entry contract (`AXS-FRE-010`). |
| `AX_TYPE_INVALID_PANIC_HANDLER` | `TYPE` | `error` | `T512` | `@panic_handler` function is generic, `async`, or does not have signature `fn(view<PanicInfo>) -> never` / `fn() -> never` (`AXS-FRE-011`). |
| `AX_TYPE_DUPLICATE_PANIC_HANDLER` | `TYPE` | `error` | `T512` | More than one `@panic_handler` function is defined in the binary (`AXS-FRE-011`). |
| `AX_TYPE_INVALID_GLOBAL_ALLOCATOR` | `TYPE` | `error` | `T512` / `T514` | `@global_allocator` is attached to a non-`static` item or a type not implementing `GlobalAlloc` / `Allocator` (`AXS-FRE-012`). |
| `AX_TYPE_DUPLICATE_GLOBAL_ALLOCATOR` | `TYPE` | `error` | `T512` / `T514` | More than one `@global_allocator` item is defined in the binary (`AXS-FRE-012`). |
| `AX_TYPE_INVALID_NAKED_FN` | `TYPE` | `error` | `T512` / `T513` | `@naked` function is not declared `unsafe`, is `async`, or allocates local stack frame slots (`AXS-FRE-013`). |
| `AX_TYPE_INVALID_SECTION` | `TYPE` | `error` | `T512` / `T513` | `@section("...")` or `@used` applied to a non-`fn`/non-`static` item, or `@section` given an empty/invalid section name (`AXS-FRE-014`). |
| `AX_UNSAFE_INTERRUPT_FORBIDDEN_OP` | `UNSAFE` | `error` | `T512` | An `extern "interrupt"` handler directly or transitively performs heap allocation (`heap_alloc`), blocking (`blocking`), thread creation (`thread`), `.await` (`async`), or OS I/O (`os_io`) (`REQ-ABI-102`, `AXS-FRE-016`). |
| `AX_CAP_DMA_ACTIVE_CONFLICT` | `CAP` | `error` | `T513` / `T514` | Attempting CPU `view<T>` or `mut_view<T>` access to a `DmaBuffer<T>` while an in-flight `DmaTransfer<T>` owns the buffer (`REQ-CAP-140`, `REQ-CAP-143`, `AXS-FRE-005`). |

### AXS-FRE-051 — Canonical Positive Examples (`=` and `.` Syntax)

#### Example 1 — Freestanding Boot Binary with `@entry`, `@panic_handler`, `@section`, `@used`, and `std.core` (`AXS-FRE-002`..`014`)
```axiom
// Compiled with: axiomc build --profile freestanding boot.ax
module demo.freestanding_boot

use std.core.option.Option
use std.core.panic.PanicInfo
use std.core.atomic.Atomic
use std.core.atomic.Ordering

@repr(C)
pub struct BootHeader {
    pub magic: u32,
    pub flags: u32,
}

@section(".boot.hdr")
@used
pub static BOOT_HDR: BootHeader = BootHeader {
    magic = 0x1BAD_B002u32,
    flags = 0x0000_0003u32,
}

static IRQ_TICKS: Atomic<u64> = Atomic.new(0u64)

@repr(C)
pub struct InterruptFrame {
    pub rip: u64,
    pub cs: u64,
    pub rflags: u64,
    pub rsp: u64,
    pub ss: u64,
}

// Interrupt handler preserves all GPRs, returns via IRETQ, and uses only lock-free atomics (AXS-FRE-015..016):
pub extern "interrupt" fn timer_irq(frame: view<InterruptFrame>) {
    let _ = IRQ_TICKS.fetch_add(1u64, Ordering.Relaxed)
}

@panic_handler
fn on_panic(info: view<PanicInfo>) -> never {
    loop {}
}

@entry
@no_mangle
pub fn _start() -> i32 {
    let opt = Option.Some(BOOT_HDR.magic)
    match opt {
        Option.Some(m) => {
            if m == 0x1BAD_B002u32 {
                return 0
            }
            return 1
        }
        Option.None => return 2,
    }
}
```

#### Example 2 — Custom Static Bump `@global_allocator`, `ForeignBox<T, A>`, and `DmaBuffer<T>` (`AXS-FRE-005`, `AXS-FRE-012`)
```axiom
module demo.freestanding_alloc_dma

use std.alloc.GlobalAlloc
use std.alloc.Layout
use std.alloc.ForeignBox
use std.alloc.ForeignDeleter
use std.mem.DmaBuffer

pub struct StaticBumpAlloc {
    pub base: usize,
    pub limit: usize,
}

impl GlobalAlloc for StaticBumpAlloc {
    unsafe fn alloc(self: view<StaticBumpAlloc>, layout: Layout) -> *mut u8 {
        return self.base as *mut u8
    }
    unsafe fn dealloc(self: view<StaticBumpAlloc>, ptr: *mut u8, layout: Layout) {
    }
}

@global_allocator
static KERNEL_ALLOC: StaticBumpAlloc = StaticBumpAlloc {
    base = 0x0020_0000usize,
    limit = 0x0040_0000usize,
}

pub struct FirmwarePoolDeleter {}

impl ForeignDeleter for FirmwarePoolDeleter {
    unsafe fn free(ptr: *mut u8) {
        // Explicit foreign pool release without mixing with KERNEL_ALLOC (REQ-FFI-058)
    }
}

pub fn run_dma_cycle(mut dma_buf: DmaBuffer<[64]u32>) -> DmaBuffer<[64]u32> {
    {
        let mut cpu_view = dma_buf.as_mut_view()
        cpu_view[0] = 0xCAFE_BABEu32
    }
    // Submitting transfer consumes `dma_buf` so CPU `mut_view` is impossible while DMA is active (REQ-CAP-140):
    let transfer = dma_buf.start_transfer(0x8000_0000usize)
    let completed_buf = transfer.wait_complete()
    return completed_buf
}
```

### AXS-FRE-052 — Canonical Negative Examples (`=` and `.` Syntax)

```axiom
// Compiled with: axiomc check --profile freestanding bad_freestanding.ax
module demo.freestanding_rejected

// ERROR [AX_NAME_FREESTANDING_FORBIDDEN_IMPORT]: hosted OS module `std.fs` cannot be imported in `--profile freestanding` (AXS-FRE-003)
use std.fs.File
use std.boxed.Box

@repr(C)
pub struct InterruptFrame {
    pub rip: u64,
    pub cs: u64,
    pub rflags: u64,
    pub rsp: u64,
    pub ss: u64,
}

// ERROR [AX_UNSAFE_INTERRUPT_FORBIDDEN_OP]: interrupt handler cannot allocate on the heap (`Box.new`) or block (`REQ-ABI-102`, AXS-FRE-016)
pub extern "interrupt" fn bad_irq_handler(frame: view<InterruptFrame>) {
    let b = Box.new(42i32)
}

// ERROR [AX_TYPE_INVALID_NAKED_FN]: `@naked` function must be declared `unsafe fn` and cannot allocate local stack variables (AXS-FRE-013)
@naked
pub fn bad_naked() -> i32 {
    let local_arr: [16]i32 = [0; 16]
    return local_arr[0]
}

// ERROR [AX_TYPE_ENTRY_SIGNATURE]: `@entry` function cannot have generic type parameters (AXS-FRE-010)
@entry
pub fn bad_entry<T>() -> i32 {
    return 0
}
```

### AXS-FRE-053 — Requirement & Task Traceability Matrix (`T511`–`T515`)

| Requirement IDs | Domain / Summary | Normative Clauses in `SPEC-52` | Implementing / Verifying Tasks |
|---|---|---|---|
| `REQ-ABI-031`, `REQ-FFI-066` | Runtime ABI is versioned separately from Core ABI; one unified Axiom semantic model applies across all execution profiles and domains (`hosted`, `freestanding`, `kernel`, `system`, `interrupt`, `GPU`) without creating a separate dialect | `AXS-FRE-001`, `AXS-FRE-002`, `AXS-FRE-020`, `AXS-FRE-021`, `AXS-FRE-022` | `T511` (spec), `T512` (driver/sema), `T515` (conformance) |
| `REQ-ABI-102`, `REQ-ABI-078` | Hardware interrupt handlers (`extern "interrupt"`) declare explicit calling-convention and execution-domain contracts, use ABI metadata-driven register preservation (`CallingConventionDescription`) and `IRETQ`, and forbid implicit heap allocation, blocking, or `await` | `AXS-FRE-015`, `AXS-FRE-016`, `AXS-FRE-050`, `AXS-FRE-052` | `T511`, `T512` (sema), `T513` (backend `IRETQ`), `T514`, `T515` |
| `REQ-ABI-055`, `REQ-ABI-056`, `REQ-ABI-083`, `REQ-RES-145` | Semantic `Move`, `Copy`, and owned value returns do not mandate physical memory copies; small aggregates pass/return in registers per Target ABI; CRT-free `@entry`, `@naked`, `@section`, and `@used` native image emission | `AXS-FRE-004`, `AXS-FRE-005`, `AXS-FRE-010`, `AXS-FRE-013`, `AXS-FRE-014`, `AXS-FRE-023` | `T511`, `T513`, `T515` |
| `REQ-CAP-140`, `REQ-CAP-143` | Physical addresses remain distinct from safe Axiom capabilities; `DmaBuffer<T>` and `DmaTransfer<T>` track CPU vs device ownership, prohibiting CPU mutable access while DMA transfers are active and keeping buffers valid until completion | `AXS-FRE-005`, `AXS-FRE-050`, `AXS-FRE-051` | `T511`, `T513`, `T514`, `T515` |
| `REQ-FFI-005`, `REQ-FFI-006`, `REQ-FFI-008`, `REQ-FFI-009`, `REQ-FFI-020`, `REQ-FFI-024`, `REQ-FFI-058`, `REQ-FFI-080`, `REQ-FFI-121`, `REQ-RES-170` | FFI raw pointers do not imply ownership; foreign and Axiom allocation domains are never mixed or guessed automatically; `ForeignBox<T, A>` enforces explicit foreign deleter contracts | `AXS-FRE-003`, `AXS-FRE-005`, `AXS-FRE-012`, `AXS-FRE-051` | `T511`, `T514`, `T515` |

## Sources

- `docs/base/specs/0097 - Axiom — OS, Platform, Freestanding & Hardware Model v0.1.md` (`§1–60, AOS-01..35`)
- `docs/base/specs/0104 - Axiom — ABI Stability, FFI, Versioning & Binary Compatibility v0.1.md` (`§54`)
- `docs/base/specs/0111` (`§47`), `0119` (`§233, §259, AFFI-20..21`), `0129` (`§76–77, §101, ATYPE-46..47`), `0131` (`§67, §88, AFN-54`), `0138` (`§100, AFFI-27, Part XX`), `0163` (`§6`), `0230` (`§6`)
- `docs/base/specs/0143 - Part XXIV — Runtime · Startup · HostedFreestanding · Optional Runtime.md` (`§1–65, ARUNTIME-20..63`)
- `docs/base/tasks/0358 - BOOTSTRAP-099 — Axiom Initialization, Static Storage, Global State & Program Entry.md` (`§1–35, AINIT-20..80`)
- `docs/base/tasks/0359 - BOOTSTRAP-100 — Axiom Runtime Capability Graph & Runtime Dependency Elimination.md` (`§1–51, ARUNTIME-20..90`)
- `docs/base/tasks/0367` (`§82, AABI-20..70`), `0413` (`§70`), `0445` (`§186.161, AFFI-30..33`), `0465` (`§206.24, ANET2-44..45`)
- `docs/base/tasks/0370 - BOOTSTRAP-111 — Runtime Composition, Startup & Platform System Layer.md` (`§1–42, ARUNTIME-20..57`)
- `docs/base/tasks/0455 - BOOTSTRAP-196 — Runtime Composition, Startup, Minimal Runtime & Freestanding Execution.md` (`§1–47, ART-20..50`)
- `docs/base/tasks/0471 - BOOTSTRAP-212 — Real-Time, Embedded, KernelOS Development & Bare-Metal Axiom.md` (`§212.1–100, AKERNEL-20..70`)
- `spec/SPEC-03-core-semantics.md` (`AXS-SEM-070`..`082`)
- `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-022`, `AXS-EXT-024`, `AXS-EXT-030`..`032`, `AXS-EXT-041`, `AXS-EXT-052`, `AXS-EXT-054`, `AXS-EXT-060`..`062`, `AXS-EXT-070`..`074`, `AXS-EXT-091`)
- `spec/SPEC-50-unsafe-ub-ffi.md` (`AXS-UNS-020`..`036`)
- `spec/SPEC-51-raw-memory-volatile-mmio-layout.md` (`AXS-MEM-001`..`024`)
