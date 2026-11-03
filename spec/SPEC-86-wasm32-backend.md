# SPEC-86 — Canonical WASM32 Stack-Machine Backend, CFG Stackification, Binary `.wasm` & WASI Specification

Status: draft (T673, 2026-11-04)
Owner: axiom-architect
Consolidates: `0220 (§1–4, §10, §16, §18, §28–39 AOS-20..40)`; `tasks/0453 (§194.1–44 ATARGET-20..50, esp. §194.36)`; `tasks/0518 (§151 AMACHINE-90)`; `tasks/0522 (header)`; `tasks/0523 (§1–156 AWASM-20..95)`; `tasks/0524 (§112 ABACKEND-79, ABACKEND-89..92)`; `tasks/0784 (§562.5, §562.29–34, §562.77–99, §562.141–145, §562.153, §562.165, §562.174–186, §562.191–193, §562.200)`; `spec/SPEC-04-core-extensibility.md`; `spec/SPEC-30-concurrency.md`; `spec/SPEC-31-atomics.md`; `spec/SPEC-32-threads-sync.md`; `spec/SPEC-40-integers.md`; `spec/SPEC-41-floating-point.md`; `spec/SPEC-42-simd.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-51-raw-memory-volatile-mmio-layout.md`; `spec/SPEC-52-freestanding-runtime-composition.md`; `spec/SPEC-53-safety-profiles-capability-security.md`; `spec/SPEC-54-panic-unwinding.md`; `spec/SPEC-60-comptime-2-0.md`; `spec/SPEC-63-dyn-trait-vtables.md`; `spec/SPEC-81-target-desc-isa-conformance.md`; `spec/SPEC-85-android-aarch64-jni.md`.
Covers: `REQ-TGT-079`, `REQ-TGT-207`..`225` (and specifies the E16.6 contract for `T674`, `T675`, `T676`: `REQ-TGT-226`..`284`, `REQ-TGT-304`, cross-referencing `SPEC-85` for `REQ-TGT-230, 270, 272, 273, 282`).
Consumers: `compiler/target/wasm32/isel`, `compiler/abi/wasm32`, `compiler/target/wasm32/encode`, `compiler/obj/wasm`, `compiler/link/wasm`, `std/sys/wasi`, `tests/mc/wasm32_stackify`, `tests/obj/wasm`, `tests/conformance/p16/e16_6_wasm32`, `T674`, `T675`, `T676`, `T686`, `T687`.

## Tóm tắt

Tài liệu `SPEC-86` chuẩn hóa kiến trúc backend máy ngăn xếp ảo **WebAssembly 32-bit (`WASM32`)** tự thân hoàn toàn (không phụ thuộc LLVM, Binaryen, `wasm-ld` hay `wasi-libc`) cho phân hệ `E16.6` (`T673`–`T676`, Phase `P16`), chứng minh `Axiom LIR` độc lập hoàn toàn với cả máy thanh ghi (`x86_64`, `aarch64`, `riscv64`) lẫn máy ngăn xếp ảo (`wasm32`):
1. **Phân loại đích máy ảo (`TargetFamily.VirtualMachine`), hai hồ sơ `wasm32-freestanding` & `wasm32-wasi`, `DataLayout` 32-bit và mô hình bộ nhớ kép (`0523 §1–10, §51–56, §68–87, §120–124, §132–135, §146–155 AWASM-20..36`, `0518 §151 AMACHINE-90`, `REQ-TGT-079`, `REQ-TGT-207..225`)**: WASM là một họ đích backend độc lập, tuyệt đối không làm biến dạng mô hình ngữ nghĩa Core hay ép `MIR`/`OptIR`/`Axiom LIR` mang cấu trúc ngăn xếp. `wasm32` có `usize = 32` bit (`align = 4`), little-endian, trang bộ nhớ tuyến tính `64 KiB` (`65536` byte), con trỏ béo 8 byte (`{ptr: u32, meta: u32}`), tách bạch nghiêm ngặt biến cục bộ WASM có kiểu không lấy được địa chỉ (`i32`, `i64`, `f32`, `f64`, `v128`) với ngăn xếp bóng (`shadow stack`) căn chỉnh 16 byte trong `LinearMemory` do `global 0: mut i32 $__stack_pointer` quản lý, kèm quy tắc căn chỉnh `memarg.align` (`@repr(packed)` `align = 0`) và phân vùng `.rodata`/`.data`/`.bss`/TLS theo hồ sơ. Offset số nguyên trong `LinearMemory` không tự động mang provenance hay quyền `view`/`mut_view`; `BCE` bắt buộc có chứng minh mức Axiom (`Certainty.Proven`, không được bỏ kiểm tra biên chỉ vì trang WASM có trap); `memory.grow`, `atomic.*`, `Send` và `Share` giữ nguyên mọi bất biến an toàn của Axiom.
2. **Tái cấu trúc CFG tùy ý thành luồng điều khiển có cấu trúc (`block`/`loop`/`if-else`/`br_table`), hợp thức hóa vòng lặp đa điểm vào bất khả quy và stackification SSA (`0523 §11–27, §136–139, §155 AWASM-65..70`, `0524 §112 ABACKEND-79`, `T674`)**: Sau khi hoàn tất mọi tối ưu hóa ngữ nghĩa trên `Verified MIR` và `OptIR`, `compiler/target/wasm32/isel` phân tích thứ tự `RPO`, cây thống trị (`dominator tree`) và `SCC` để chuyển mọi CFG `LIR` khả quy thành `block`/`loop`/`if-else`/`br`/`br_if`/`br_table`, đồng thời hợp thức hóa tất định mọi chu trình đa điểm vào bất khả quy thông qua biến điều phối `$irr_state: i32` + một `loop` duy nhất kích thước tuyến tính `O(|S| + |E|)`. Các biểu thức SSA dùng một lần được đẩy trực tiếp lên ngăn xếp toán hạng ảo khi và chỉ khi bảo toàn thứ tự tác dụng phụ, phép kiểm tra tràn/chia 0 và rào cản bộ nhớ; các giá trị sống lâu hơn được gộp màu tất định vào local WASM cùng kiểu.
3. **Quy ước gọi `CallConv.Wasm` (WebAssembly Basic C ABI), bảng hàm gián tiếp `__indirect_function_table`, thuộc tính `@wasm_import`/`@wasm_export` và hạ bậc `panic` theo hồ sơ (`0523 §28–42, §88–99, §109–117, §125–131, §155 AWASM-41..55`, `T674`)**: `compiler/abi/wasm32` truyền trực tiếp các vô hướng (`i32`, `i64`, `f32`, `f64`, `v128`), tách tham số `i128`/`u128` thành cặp `(lo: i64, hi: i64)` nhưng trả về `i128`/`u128` và kiểu hợp thành đa trường qua con trỏ ẩn `sret: i32` ở tham số `0`, truyền tham số hợp thành bằng con trỏ vào bản sao trên `shadow stack`, và hạ bậc hàm biến tham `extern "C" fn(..., ...)` thành con trỏ `va_list: i32`. Khe `0` của `table 0: funcref` luôn để trống (`null`) để bắt lỗi gọi con trỏ hàm rỗng; `wasm32-freestanding` hạ bậc `panic` thành `@panic_handler` hoặc `unreachable` không cần import host, còn `wasm32-wasi` ghi thông điệp lỗi ra `stderr` (`fd = 2`) qua `wasi_snapshot_preview1.fd_write` rồi gọi `proc_exit(101)`.
4. **Bộ mã hóa nhị phân `.wasm`, bộ kiểm định nội bộ `verify_wasm`, định dạng đối tượng khả định vị (`linking` v2 + `reloc.CODE`/`reloc.DATA`), trình liên kết tĩnh `.wasm` và tầng hệ thống `std.sys.wasi` (`0220 §10`, `0523 §43–50, §100–108, §140–156 AWASM-37..40, 56..64, 71..95`, `T675`, `T676`)**: `compiler/target/wasm32/encode` bắt buộc chạy bộ kiểm định ngăn xếp kiểu đa hình `verify_wasm` trước khi ghi bất kỳ byte `.wasm` nào ra đĩa (tuyệt đối không dựa vào công cụ ngoài). `compiler/obj/wasm` và `compiler/link/wasm` phát sinh file đối tượng `.wasm` (custom section `linking` v2 đứng trước `reloc.CODE`/`reloc.DATA` có header `(target_section_index, reloc_count)`, kho lưu trữ GNU `ar` `.a` tất định) và liên kết tĩnh thành mô-đun `.wasm` tất định từng byte với thu gom rác theo gốc xuất (`_start`, `_initialize`, `@export`/`@wasm_export`, `@used`). `std/sys/wasi` hiện thực hóa giao diện host `SPEC-04 AXS-EXT-110` trên `wasi_snapshot_preview1` thuần túy dựa trên capability thư mục mở sẵn (`fd_prestat_get`, tuyệt đối không giả định quyền đường dẫn gốc ngầm định) cùng bộ cấp phát trang 64 KiB `memory.grow` thuần Axiom.

---

## 1. WASM Target Classification, Descriptors, `DataLayout`, Feature DAG & Dual-Storage Memory Model (`AXS-WASM-001`..`010`)

**AXS-WASM-001 — Virtual-Machine Target Classification, `TargetId.Wasm32Freestanding` & `TargetId.Wasm32Wasi` Descriptors, CLI Normalization & `TargetFingerprint` (`REQ-TGT-079`, `REQ-TGT-207`..`209`, `REQ-TGT-216`, `REQ-TGT-266`, `0523 §1–4, §86, §148–156 AWASM-20..21, AWASM-27, AWASM-77`, `0784 §562.5, §562.77, §562.85, §562.98, §562.141–145`, `SPEC-04` AXS-EXT-060..062, `SPEC-81` AXS-TGTD-002..003).**
1. **Virtual-Machine Target Family (`0523 §1–4, §155 AWASM-20`, `0522` header, `REQ-TGT-207`..`209`)**:
   - WebAssembly is classified in `compiler/target/` under `TargetFamily.VirtualMachine` (`AWASM-20`, `REQ-TGT-209`) — a portable typed virtual stack-machine target with its own binary module, relocation, linking, and host-capability execution contract (`0523 §1`, `REQ-TGT-208`).
   - WebAssembly is **never** a Core language semantic model: frontend parsing, name resolution, type checking, ownership/capability verification, `Verified MIR`, `OptIR`, and `Axiom LIR` remain 100% independent of both physical register files (`x86_64`, `aarch64`, `riscv64`) and virtual operand stacks (`wasm32`) (`0522` header, `REQ-TGT-207`, `AWASM-21`). Lowering into WASM value, local, control-flow, and linear-memory representations occurs strictly inside the WASM machine backend (`0518 §151 AMACHINE-90`, `REQ-TGT-079`).
2. **Concrete `TargetDesc` Records Refining `SPEC-81` `AXS-TGTD-002` (`0453 §194.36`, `0220 §10`, `0523 §43–45, §148–150`)**:
   - The `Wasm32` family entry in `SPEC-81` `AXS-TGTD-002` instantiates into two concrete `TargetDesc` records sharing `Arch.Wasm32`, `CallConv.Wasm` (canonical spelling of `SPEC-81` `CallConv.WasmBasic`), `ObjectFormat.Wasm`, `ArchiveFormat.GnuAr`, and `ImageFormat.Wasm`:

| Field | `wasm32-freestanding` | `wasm32-wasi` |
|---|---|---|
| `TargetId` | `TargetId.Wasm32Freestanding` | `TargetId.Wasm32Wasi` |
| Canonical `--target` | `wasm32-freestanding` | `wasm32-wasi` |
| Accepted CLI aliases | `wasm32-unknown-unknown`, `wasm32-none`, and `--target wasm32` when combined with `--profile freestanding` | `wasm32` (default hosted profile), `wasm32-unknown-wasi`, `wasm32-wasip1` |
| `(Arch, Os, Env)` | `(Arch.Wasm32, Os.None, Env.None)` | `(Arch.Wasm32, Os.Wasi, Env.WasiP1)` |
| Default `Profile` | `Profile.Freestanding` (`std.core`, optional `std.alloc` with `@global_allocator`; zero WASI/OS imports) | `Profile.Hosted` (`std.core` + `std.alloc` + `std` backed by `std/sys/wasi` over `wasi_snapshot_preview1`) |
| Default `PanicStrategy` | `PanicStrategy.Abort` (`@panic_handler` or `unreachable`) | `PanicStrategy.Abort` (`fd_write(2, ...)` + `proc_exit(101)`) |
| Entry symbol (`--kind exe`) | `@entry` function exported as `_start` (or custom `@wasm_export`) | Synthesized `_start () -> ()` calling `main` then `proc_exit` |

   - Passing an unrecognized `--target` string emits `AX_DRIVER_UNKNOWN_TARGET` (`SPEC-04` AXS-EXT-061).
3. **`wasm32` vs `wasm64` Address-Width Orthogonality (`0523 §86, §155 AWASM-27`, `0784 §562.85`, `REQ-TGT-216`)**:
   - `wasm32` (`32`-bit linear-memory indices, `i32` pointers, 4 GiB max linear memory) and reserved future `wasm64` (`memory64`, `64`-bit linear-memory indices, `i64` pointers) differ solely in physical pointer/index bit-width (`DataLayout.pointer_width_bits`), never in Core Axiom pointer provenance, `view`/`mut_view` capability rules, or slice semantics (`AWASM-27`, `REQ-TGT-216`).
4. **`TargetFingerprint` Cache Isolation (`0523 §155 AWASM-77`, `0784 §562.5, §562.141–145`, `REQ-TGT-266`, `SPEC-81` AXS-TGTD-003)**:
   - On WASM targets, the 128-bit BLAKE3 `TargetFingerprint` hashes `(target_id, arch, os, env, ptr_bits = 32, endian = Little, call_conv = Wasm, active_features_bitmask, memory_sharing_mode, low_guard_bytes, profile, panic_strategy)`. Incremental query caches (`.axiom-cache`), `.axmi` interfaces, and relocatable `.wasm` objects never collide across `wasm32-freestanding` vs `wasm32-wasi`, unshared vs `+atomics` shared memory, or distinct feature sets (`AWASM-77`, `REQ-TGT-266`; mismatch diagnosed via `AX_LINK_ARTIFACT_TARGET_MISMATCH`).

**AXS-WASM-002 — `wasm32` `DataLayout` (`32`-Bit `usize`, Little-Endian, 64 KiB Pages & `8`-Byte Fat Pointers) (`REQ-TGT-079`, `REQ-TGT-216`, `0523 §5–10, §86–87, §132`, `0784 §562.84–85, §562.174–175`).**
1. **Scalar, Pointer & Fat-Pointer Layout Table**:
   - `DataLayout` for both `TargetId.Wasm32Freestanding` and `TargetId.Wasm32Wasi` fixes `endian = Endian.Little`, `pointer_width_bits = 32`, `wasm_page_bytes = 65536` (`64 KiB = 0x10000`), and `stack_align_bytes = 16`:

| Axiom Type Category | Size (bytes) | Alignment (bytes) | WASM Value / Linear-Memory Representation |
|---|---|---|---|
| `()`, `[0]T`, empty `struct` | `0` | `1` | Zero-sized (`ZST`); omitted in WASM locals and signatures |
| `bool`, `i8`, `u8` | `1` | `1` | `i32` in locals/stack (`0`/`1` for `bool`); 1 byte in `LinearMemory` |
| `i16`, `u16` | `2` | `2` | `i32` in locals/stack; 2 bytes little-endian in `LinearMemory` |
| `i32`, `u32`, `char`, `usize`, `isize` | `4` | `4` | `i32` in locals/stack; 4 bytes little-endian in `LinearMemory` |
| `*const T`, `*mut T`, thin `view<T>`/`mut_view<T>`/`Box<T>` (`T: Sized`) | `4` | `4` | `i32` unsigned byte offset in `memory 0` |
| `fn(A...) -> R` (`FnPtr`, non-capturing) | `4` | `4` | `i32` unsigned slot index in `table 0` (`__indirect_function_table`) |
| `i64`, `u64` | `8` | `8` | `i64` in locals/stack; 8 bytes (`align = 8`) in `LinearMemory` |
| `f32` / `f64` | `4` / `8` | `4` / `8` | IEEE-754 `f32` / `f64` (`SPEC-41`) |
| `i128`, `u128` | `16` | `16` | `(lo: i64, hi: i64)` limb pair; 16 bytes (`align = 16`) in `LinearMemory` |
| `Vector<T, N>` (128-bit total) | `16` | `16` | `v128` (`+simd128`) or scalarized; 16 bytes (`align = 16`) in `LinearMemory` |
| `Str`, `view<[T]>`, `mut_view<[T]>` | `8` | `4` | `{ ptr: u32 (offset +0), len: u32 (offset +4) }` |
| `view<dyn Trait>`, `mut_view<dyn Trait>`, `Box<dyn Trait>` | `8` | `4` | `{ data_ptr: u32 (offset +0), vtable_ptr: u32 (offset +4) }` (`SPEC-63` adapted to 32-bit `usize`) |

**AXS-WASM-003 — Explicit WASM Feature Set, Implication DAG & Opcode Gating (`REQ-TGT-250`, `REQ-TGT-251`, `0523 §57–59, §146–147, §155 AWASM-61..62`, `0784 §562.29–34, §562.87–91`, `SPEC-81` AXS-TGTD-007..008).**
1. **Baseline & Optional Feature Registry (`AWASM-61`, `REQ-TGT-250`)**:
   - Every WASM compilation unit carries an explicit `TargetFeatureSet` (`--target-feature=+feat,-feat` and per-function `@target_feature("feat")`, accepting both `_` and `-` separators, e.g., `bulk_memory` and `bulk-memory`):
     - **Mandatory baseline features** (enabled by default on both `wasm32-freestanding` and `wasm32-wasi`): `mutable_globals` (imported/exported mutable `$__stack_pointer`), `sign_ext` (`i32.extend8_s`, `i32.extend16_s`, `i64.extend8_s`/`16_s`/`32_s`), and `nontrapping_fptoint` (`i32.trunc_sat_f32_s`/`u`, `i32.trunc_sat_f64_s`/`u`, `i64.trunc_sat_*`). Attempting to disable a mandatory baseline feature (`-mutable_globals`, `-sign_ext`, `-nontrapping_fptoint`) is rejected with `AX_TARGET_UNKNOWN_FEATURE`.
     - **Optional target features & implication DAG**:
       - `bulk_memory`: enables `memory.copy` (`0xFC 0x0A`), `memory.fill` (`0xFC 0x0B`), `memory.init` (`0xFC 0x08`), `data.drop` (`0xFC 0x09`), `table.copy`/`init`/`elem.drop`, and `DataCount` (`section 12`);
       - `simd128`: enables `v128` (`0x7B`) locals/parameters/results and `0xFD`-prefix 128-bit SIMD instructions;
       - `relaxed_simd` $\implies$ `simd128`;
       - `atomics` $\iff$ `threads` $\implies$ `bulk_memory`: enables `0xFE`-prefix `*.atomic.*`, `atomic.fence`, and `memory.atomic.wait32`/`wait64`/`notify`, and requires `shared` linear memory limits (`flags = 0x03` with an explicit maximum page count `--wasm-max-memory`);
       - `multivalue`: enables multi-result block and internal function signatures;
       - `reference_types`: enables `funcref`/`externref` locals, multi-table indexing, and `table.get`/`set`/`grow`/`size`/`fill`;
       - `tail_call`: enables `return_call` (`0x12`) and `return_call_indirect` (`0x13`);
       - `exception_handling`: reserved low-level target feature; never alters Core Axiom error semantics (`AWASM-54`).
2. **Rejection or Legal Fallback When Features Are Absent (`AWASM-62`, `REQ-TGT-251`)**:
   - The backend **never** emits an opcode outside the active `TargetFeatureSet` (`verify_wasm` enforces this hard gate, `AXS-WASM-026`). When an optional feature is disabled:
     - `ptr_copy` / `ptr_copy_nonoverlapping` / `ptr_write_bytes` expand to deterministic word/byte loops when `-bulk_memory` is active, and lower to `memory.copy` / `memory.fill` when `+bulk_memory` is active;
     - `Vector<T, N>` operations scalarize cleanly when `-simd128` is active (`SPEC-81` AXS-TGTD-029);
     - Calling a `@target_feature("simd128")` or `@target_feature("atomics")` function or target-gated WASM intrinsic from a caller lacking that feature outside `unsafe` emits `AX_TARGET_FEATURE_MISMATCH`;
     - Contradictory flags (e.g., `+atomics,-bulk_memory`, `+relaxed_simd,-simd128`, or `+atomics` with `--wasm-no-max-memory`) emit `AX_TARGET_FEATURE_CONFLICT`, and operations that cannot be legally expanded on the active profile/feature set (such as multi-threaded `memory.atomic.wait32` under `-atomics`, or hardware CPU interrupt handlers `extern "interrupt"` / `@naked` register-asm on `wasm32`) emit `AX_TARGET_UNSUPPORTED_OP`.

**AXS-WASM-004 — Dual-Storage Architecture: Non-Addressable WASM Locals vs Explicit `LinearMemory` Shadow Stack (`REQ-TGT-079`, `REQ-TGT-212`, `REQ-TGT-215`, `REQ-TGT-220`, `REQ-TGT-271`, `0523 §5–16, §77–81, §155 AWASM-23, AWASM-26, AWASM-31, AWASM-82`, `0784 §562.78–80, §562.84`).**
1. **Two Disjoint Physical Storage Domains (`AWASM-23, 26`, `REQ-TGT-212, 215`)**:
   - **Domain A — WASM Typed Locals & Virtual Operand Stack**: WASM function locals (`i32`, `i64`, `f32`, `f64`, `v128`) and transient operand-stack values are purely backend representations (`AWASM-23`, `REQ-TGT-212`). Because WebAssembly provides no instruction to compute the address of a WASM local or operand-stack slot, values in Domain A are **provably alias-free** with respect to all `LinearMemory` loads, stores, and foreign host accesses.
   - **Domain B — Explicit WASM `LinearMemory` (`memory 0`)**: Byte-addressable storage (`AWASM-26`, `REQ-TGT-215`) holding static data segments (`.rodata`, `.data`, `.bss`), the downward-growing 16-byte-aligned **shadow stack** tracked by mutable `global 0` (`$__stack_pointer: mut i32`), and the upward-growing dynamic heap starting at `__heap_base`.
2. **Address Observability & Pinning Rules (`AWASM-31, 82`, `REQ-TGT-220, 271`, `SPEC-71`)**:
   - Non-address-taken scalars and `SROA`-scalarized aggregates reside exclusively in Domain A (WASM locals / operand stack).
   - A local variable or temporary is allocated in Domain B (`LinearMemory` shadow-stack frame) **if and only if** its address or in-memory byte layout is required: (i) `address_of(place)` / `address_of_mut(place)` is taken; (ii) an unpromoted `view<T>`, `mut_view<T>`, or dynamic indexing operation requires a `LinearMemory` address; (iii) `CallConv.Wasm` (`AXS-WASM-019`) requires passing or returning an aggregate (`sret`) or variadic `va_list` buffer via `LinearMemory`; or (iv) a pointer into the object is exposed across an FFI/host import or export boundary (`AWASM-82`, `REQ-TGT-271`).
   - Once an allocation's `LinearMemory` address is externally observed or borrowed by a live `view`/`mut_view`/raw pointer, backend passes MUST NOT eliminate its store, reuse its stack slot during its live range, or relocate the allocation (`AWASM-31, 82`, `REQ-TGT-220, 271`).

**AXS-WASM-005 — Canonical `wasm32` Linear-Memory Address Map (`0523 §5–10, §83–84`, `0784 §562.84, §562.92`).**
1. **Deterministic Four-Region Partition of `memory 0`**:
   - Static linking (`compiler/link/wasm`, `AXS-WASM-028`) lays out `memory 0` in ascending unsigned 32-bit byte offsets with zero overlap:
     ```text
     0x0000_0000  +---------------------------------------------------------------+
                  | 1. Reserved Null-Guard Region [0 .. low_guard_end)            |
                  |    (64 KiB = 0x10000 default on wasm32-wasi;                  |
                  |     1024 B = 0x0400 default on wasm32-freestanding / -Oz;     |
                  |     configurable via --wasm-low-guard=<bytes>, >= 16)         |
     low_guard    +---------------------------------------------------------------+
                  | 2. Static Segments: .rodata (vtables, UTF-8 literals),        |
                  |    .data (initialized statics), .bss (zero-initialized)       |
     __data_end   +---------------------------------------------------------------+ (16B aligned)
     __stack_low  | 3. Shadow Stack [__stack_low .. __stack_high)                 |
                  |    Grows DOWNWARD from $__stack_pointer = __stack_high        |
                  |    (1 MiB = 0x100000 default on wasm32-wasi;                  |
                  |     64 KiB = 0x10000 default on wasm32-freestanding;          |
                  |     configurable via --stack-size=<bytes>, 16B multiple)      |
     __stack_high +---------------------------------------------------------------+ == __heap_base (16B aligned)
     __heap_base  | 4. Dynamic Heap [__heap_base .. memory.size * 65536)          |
                  |    Grows UPWARD in 64 KiB pages via memory.grow 0             |
                  +---------------------------------------------------------------+
     ```
   - Offset `0` is **never** assigned to any valid Axiom static, shadow-stack slot, or heap allocation, preserving `null()`/`null_mut()` (`0`) non-aliasing invariants (`SPEC-50` AXS-UNS-010). Initial `memory 0` `min` pages equal `ceil(__heap_base / 65536)`.

**AXS-WASM-006 — Provenance, Ownership, `view`/`mut_view` Capabilities & `memory.grow` Invalidation (`REQ-TGT-213`..`214`, `REQ-TGT-217`..`219`, `0523 §73–82, §133–135, §155 AWASM-24..25, AWASM-28..30`, `SPEC-10`, `SPEC-11`, `SPEC-50`, `SPEC-53`).**
1. **Linear-Memory Offset $\ne$ Axiom Pointer or Provenance (`AWASM-24..25`, `REQ-TGT-213..214`)**:
   - Numeric WASM linear-memory byte offsets (`u32`, `usize`) are plain integers, **not** Axiom capabilities or provenanced pointers (`AWASM-24`, `REQ-TGT-213`).
   - Casting an integer offset to `*const T` or `*mut T` inside `unsafe` does **not** synthesize Axiom allocation provenance (`AWASM-25`, `REQ-TGT-214`, `SPEC-50` AXS-UNS-011), and attempting to construct `view<T>` or `mut_view<T>` from an integer offset or raw pointer without an explicit `unsafe` capability boundary (`MakeView`/`MakeMutView`) is rejected at compile time with `AX_SEC_CAPABILITY_FORGERY` or `AX_UNSAFE_REQUIRED` (`SPEC-53` AXS-SEC-004).
2. **Active Ownership & Capability Separation After Lowering (`AWASM-28..29`, `REQ-TGT-217..218`)**:
   - Move/copy tracking (`SPEC-10`), deterministic `Drop` (`SPEC-12`), and `view<T>`/`mut_view<T>` aliasing rules (`SPEC-11`) remain 100% enforced on WASM (`AWASM-28`, `REQ-TGT-217`).
   - Although `view<[T]>` and `mut_view<[T]>` both lower physically to `{ ptr: i32, len: i32 }` (and thin `view<T>`/`mut_view<T>` both lower to `i32`), `OptIR`, `MemorySSA`, and `AliasInfo` preserve their distinct read-only vs exclusive-write semantic capabilities (`AWASM-29`, `REQ-TGT-218`): identical physical bit-width never grants mutation through `view<T>`.
3. **`memory.grow` Storage & Host-View Invalidation Contract (`AWASM-30`, `REQ-TGT-219`)**:
   - Executing `memory.grow 0` preserves all existing WASM linear-memory byte contents and numeric `i32` offsets in `[0 .. old_pages * 65536)`, **but**:
     - Reallocating a growable Axiom container (`Vec<T>`, `String`, `HashMap<K, V>`) moves elements to a new heap block and remains statically forbidden while any element `view`/`mut_view` is live (`AX_CAP_CONTAINER_RELOC`, `SPEC-11`);
     - On JS/browser or embedding hosts using unshared `WebAssembly.Memory`, `memory.grow` detaches previously acquired host `ArrayBuffer` / typed-array views; host glue and FFI wrappers MUST treat any WASM call that may allocate (`MayAlloc`) as invalidating cached host buffer views and re-read `exports.memory.buffer` (`AWASM-30`, `REQ-TGT-219`).

**AXS-WASM-007 — Bounds-Check Elimination (`BCE`) Proof Requirement & Trap-vs-Semantic-Verification Separation (`REQ-TGT-221`, `REQ-TGT-222`, `0523 §28, §70–72, §155 AWASM-32..33`, `SPEC-25`, `SPEC-72`).**
1. **No Implicit Reliance on WASM Page Traps for `BCE` (`AWASM-32`, `REQ-TGT-221`)**:
   - WASM hardware/VM out-of-bounds memory traps trigger **only** when `effective_addr + access_width > memory.size * 65536` — an out-of-bounds slice index `s[i]` (`i >= s.len`) routinely lands inside an adjacent live shadow-stack frame, `.data` static, or heap object within the same allocated 64 KiB page without trapping!
   - Consequently, `BCE` (`SPEC-72`) on `wasm32` MUST NEVER omit an Axiom array/slice/`Str` bounds check on the pretext that WASM memory is sandboxed (`AWASM-32`, `REQ-TGT-221`); a bounds check is elided **if and only if** `RangeInfo` / `SCEV` proves `0 <= idx < len` with `Certainty.Proven` (`SPEC-25` AXS-PCT-010).
2. **WASM Traps Never Replace Axiom Semantic Verification or Panic Contracts (`AWASM-33`, `REQ-TGT-222`)**:
   - WASM execution traps (`unreachable`, `call_indirect` signature mismatch, out-of-bounds memory access) are low-level VM aborts and NEVER substitute for compile-time Axiom type, ownership, capability, or MIR verification (`AWASM-33`, `REQ-TGT-222`), nor may checked arithmetic/division/bounds failures on `wasm32-wasi` silently emit raw VM traps without executing the contracted Axiom panic path (`AXS-WASM-017`, `AXS-WASM-024`).

**AXS-WASM-008 — WASM Atomics, `Send`/`Share` Concurrency Rules & Host Synchronization (`REQ-TGT-223`..`225`, `REQ-TGT-260`, `0523 §51–56, §120–124, §155 AWASM-34..36, AWASM-71`, `0784 §562.89`, `SPEC-30`, `SPEC-31`).**
1. **Atomic Lowering & `Ordering` Preservation (`AWASM-34`, `REQ-TGT-223`)**:
   - Under `+atomics` (`+threads`), `Atomic<T>` (`1`, `2`, `4`, `8` bytes at natural alignment `2^align == width`) lowers exclusively to `0xFE`-prefix WebAssembly atomic instructions (`i32.atomic.load`/`8_u`/`16_u`, `i64.atomic.load`, `*.atomic.store*`, `*.atomic.rmw.{add,sub,and,or,xor,xchg}*`, `*.atomic.rmw.cmpxchg*`) and `atomic.fence 0x00` (`0xFE 0x03 0x00`), which provide sequentially consistent (`SeqCst`) ordering that soundly satisfies Axiom `Relaxed`, `Acquire`, `Release`, `AcqRel`, and `SeqCst` (`AWASM-34`, `REQ-TGT-223`; `futex_wait`/`futex_wake` map to `memory.atomic.wait32` [`0xFE 0x01`] / `memory.atomic.notify` [`0xFE 0x00`]). Atomic operations are **never** lowered to non-atomic `load`/`store` under `+atomics`.
2. **`Shared` Memory $\ne$ `Share`, Worker Threads $\ne$ Relaxed `Send`, and Explicit Host Sync (`AWASM-35..36, 71`, `REQ-TGT-224..225, 260`)**:
   - Declaring WASM `memory 0` as `shared` (`limits.flags = 0x03`, `SharedArrayBuffer`) does **not** make non-`Share` Axiom types (`Rc<T>`, `RefCell<T>`, unsynchronized raw pointers, `JLocal`) implement `Share` (`AWASM-35`, `REQ-TGT-224`), and spawning Web Workers or WASI threads enforces full `Send` / `Share` trait bounds (`AX_CONC_NOT_SEND`, `AX_CONC_NOT_SHARE`; `AWASM-36`, `REQ-TGT-225`).
   - Host-side synchronization (JS `Atomics.notify`, host locks, `postMessage`) establishes Axiom `Happens-Before` edges only at explicit `Atomic` operations or `MaySync` FFI calls (`AWASM-71`, `REQ-TGT-260`).

**AXS-WASM-009 — WASM `memarg` Alignment Hints vs Axiom Alignment & `@repr(packed)` Unaligned Access (`REQ-TGT-079`, `REQ-TGT-215`, `0523 §68–69`, `0784 §562.84`, `SPEC-51` AXS-MEM-021..023).**
1. **WASM `memarg.align` Encoding & Legality**:
   - Every WASM `LinearMemory` load/store encodes `memarg = (align: u32, offset: u32)` where `align` is the base-2 logarithm ($2^{\text{align}}$ bytes) of guaranteed access alignment: non-atomic loads/stores require $2^{\text{align}} \le \text{access\_bytes}$ (emitting natural alignment $\text{align} = \log_2(\text{access\_bytes})$ for naturally aligned Axiom places), whereas `0xFE`-prefix `*.atomic.*` instructions require exact natural alignment $2^{\text{align}} = \text{access\_bytes}$ (unaligned atomic accesses trap in the VM and are statically prevented by `Atomic<T>` alignment invariants, `SPEC-31`).
2. **`@repr(packed)` & Unaligned Raw Accesses**:
   - Unaligned loads/stores on `@repr(packed)` / `@repr(packed(N))` fields or explicit unaligned raw-pointer intrinsics (`read_unaligned` / `write_unaligned`, `SPEC-51` AXS-MEM-023) emit WASM loads/stores with `memarg.align = log2(guaranteed_align)` (`align = 0`, i.e., 1-byte alignment, when `guaranteed_align == 1`), while taking an aligned `view<T>`, `mut_view<T>`, or `*const T`/`*mut T` to an unaligned `@repr(packed)` field remains rejected at compile time with `AX_TYPE_UNALIGNED_PACKED_REF` (`0523 §68–69`, `SPEC-51` AXS-MEM-023).

**AXS-WASM-010 — Static Segment Materialization (`.rodata` / `.data` / `.bss`) & Platform-Layered `@thread_local` TLS Lowering (`REQ-TGT-079`, `REQ-TGT-215`, `REQ-TGT-223`, `0523 §83–85`, `0784 §562.84, §562.89, §562.98`, `SPEC-32` AXS-SYNC-010, `SPEC-60` AXS-CTM-030..033).**
1. **Compile-Time Evaluated Static Segments (`0523 §83–84`, `SPEC-60` AXS-CTM-032)**:
   - Immutable `static` items, UTF-8 string literals, and `dyn Trait` vtables materialize in `.rodata`; mutable or interior-mutable initialized `static` items materialize in `.data` (emitted as active WASM `Data` segments in `section 11`); and zero-initialized `static` items materialize in `.bss` (occupying `[__bss_start .. __data_end)` in `memory 0`, zero-initialized by WebAssembly linear-memory allocation with zero `Data` section payload bytes). Non-const static initializers remain rejected with `AX_CTM_NON_CONST_STATIC_INIT`.
2. **Platform-Layered `@thread_local` TLS Without Core WASM TLS Assumptions (`0523 §85`, `0784 §562.89, §562.98`)**:
   - Core Axiom makes zero assumption of native WebAssembly TLS instructions: under single-threaded unshared memory (`-atomics`), `@thread_local static` items lower directly to `.data`/`.bss` instance slots; under `+atomics` (`+threads`, shared `memory 0`), `@thread_local static` items are placed in a passive `Data` segment template (`.tdata` + zero-filled `.tbss` of total size `__tls_size` and alignment `__tls_align`), addressed via `global.get $__tls_base + tls_offset`, and initialized per worker thread via exported `__wasm_init_tls(tls_block_ptr: i32)` (`memory.init` + `memory.fill`).

---

## 2. Arbitrary LIR CFG Structuring, Irreducible Loop Legalization & SSA-to-Operand-Stack Stackification (`AXS-WASM-011`..`018`)

**AXS-WASM-011 — Backend-Only Lowering Pipeline: MIR & LIR Independence from WASM Stack & Structured Control Flow (`REQ-TGT-207`, `REQ-TGT-210`..`211`, `REQ-TGT-254`..`255`, `REQ-TGT-304`, `0523 §11–20, §136–139, §155 AWASM-21..22, AWASM-65..66`, `0524 §112 ABACKEND-79`, `0784 §562.77–81`).**
1. **Strict Phase Ordering**:
   - The compilation pipeline on `wasm32` executes in exact order:
     ```text
     Verified MIR (arbitrary CFG)
       -> OptIR (SSA + MemorySSA, target-independent semantic optimizations)
       -> ABI LIR (CallConv.Wasm classification, sret / shadow-stack slot insertion)
       -> Axiom LIR (target-neutral virtual registers + arbitrary basic-block CFG)
       -> WASM Legalizer (i128 limb pairs, div/rem pre-checks, feature-gated expansions)
       -> CFG Structurer (reducible + irreducible LIR CFG -> WASM block/loop/if/br_table)
       -> SSA Stackifier & Local Coalescer (single-use stack trees + typed local coloring)
       -> verify_wasm (mandatory internal polymorphic operand-stack & index validator)
       -> Binary .wasm Encoder / Object Writer / Static Linker
     ```
2. **Zero Contamination Above Backend (`AWASM-21..22, 65..66`, `ABACKEND-79`, `REQ-TGT-210..211, 254..255, 304`)**:
   - `Verified MIR`, `OptIR`, and `Axiom LIR` retain arbitrary basic-block CFGs (`Goto`, `SwitchInt`, `Call`, `Assert`) and virtual registers (`AWASM-21, 66`, `REQ-TGT-210, 255`).
   - Structured control flow (`block`/`loop`/`if`) is strictly a `wasm32` backend representation (`AWASM-65`, `ABACKEND-79`, `REQ-TGT-254, 304`), and operand-stack stackification runs strictly **after** all semantic and `OptIR` optimizations have completed (`AWASM-22`, `REQ-TGT-211`).

**AXS-WASM-012 — Deterministic CFG Analysis & PHI Parallel-Copy Resolution (`REQ-TGT-256`, `0523 §19–27, §138, §155 AWASM-67`, `0784 §562.81–82`, `compiler/target/wasm32/isel`).**
1. **Deterministic Graph Discovery**:
   - For each `LIR` function body, `compiler/target/wasm32/isel` computes:
     1. **Reverse Post-Order (`RPO`)** `rpo[B] in 0 .. N-1` breaking successor ties in fixed terminator operand order (`then` before `else`, `SwitchInt` case order before `default`);
     2. **Immediate Dominator Tree (`idom`)** via Cooper-Harvey-Kennedy fixed-point iteration over `RPO`;
     3. **Back-edges & Natural Loops**: an edge `u -> h` is a natural loop back-edge iff `h` dominates `u`; `LoopBody(h)` is the backward-reachable set from `{ u | u -> h }` stopping at `h`, nested from outermost to innermost by header dominance depth;
     4. **Forward Merge Set**: blocks `M` with $\ge 2$ forward incoming edges (`rpo[u] < rpo[M]`).
2. **Cycle-Safe PHI / Block-Parameter Elimination (`AWASM-67`, `REQ-TGT-256`)**:
   - Before structured emission, every multi-predecessor join's parallel value transfers `(dst_1, ..., dst_k) = (src_1, ..., src_k)` along incoming edge `u -> v` are sequentialized into an ordered list of typed local copies on that edge. Any cyclic permutation (such as `(a, b) = (b, a)` on a loop back-edge) allocates one fresh typed scratch local `$tmp` of matching `ValType` to break the cycle without clobbering live values.

**AXS-WASM-013 — Reducible CFG Structuring Algorithm (`block` / `loop` / `if-else` / `br` / `br_if` / `br_table`) (`REQ-TGT-256`, `REQ-TGT-304`, `0523 §19–27, §138, §155 AWASM-67`, `0784 §562.81–82`).**
1. **WASM Label Polarity Invariant**:
   - Branching `br $depth` to an enclosing `block $B` or `if` transfers control **forward** to the `end` of `$B` (`break` semantics); branching `br $depth` to an enclosing `loop $L` transfers control **backward** to the beginning of `$L` (`continue` semantics).
2. **Deterministic Scope Placement Rules (`Stackifier`)**:
   - Traversing blocks in ascending `RPO` order `B_0, B_1, ..., B_{N-1}` while maintaining an explicit active control stack `CtrlScopes`:
     1. **Closing forward merges**: Immediately before emitting block `M`, close (`end`) every open `block $M` scope whose target merge block is `M`.
     2. **Opening loop headers**: If `B` is the header of natural loop `L` whose body spans `max_rpo(L)`, emit `loop $L (blocktype empty)` so every internal back-edge `u -> B` inside `L` branches to `$L` via `br $depth($L)` / `br_if $depth($L)`.
     3. **Opening forward merge scopes**: For every forward merge target `M` (`rpo[M] > rpo[B]`) whose lowest common dominator of forward predecessors is `B` (sorted in **descending** `rpo[M]` order so nearer merges nest inside farther merges), emit `block $M (blocktype empty)`.
     4. **Structured `if-else` diamonds & triangles**: When `B` ends in a conditional branch `(cond, T_then, T_else)` where `B` strictly dominates `T_then` (and `T_else` for a diamond) and no external edges enter the branch regions before their post-dominator `M`, emit `(cond) if (result <ty>?) <then_region> else <else_region> end` directly rather than an extra outer `block` + `br_if`.
     5. **Multi-way `SwitchInt` (`br_table`)**: When `B` ends in `SwitchInt(discr, [(v_0, T_0), ..., (v_{K-1}, T_{K-1})], default = T_def)` with $K \ge 4$ and $\frac{K}{v_{\max} - v_{\min} + 1} \ge 0.40$, normalize `idx = wrapping_sub(discr, v_min)` as `i32`, open nested `block` scopes for any distinct targets not already in `CtrlScopes`, and emit `br_table $depth(target(0)) ... $depth(target(range-1)) $depth(T_def)` in `O(1)` dispatch time. Sparse `SwitchInt` terminators lower to a balanced binary comparison tree (`i32.lt_s`/`i64.lt_s` + `if`/`br_if`).
     6. **Closing loop bodies**: Immediately after emitting block `B`, close (`end`) every open `loop $L` scope for which `rpo[B] == max_rpo(L)` (inserting an explicit terminal `br` or `unreachable` when `B` does not fall through).

**AXS-WASM-014 — Deterministic Irreducible Multi-Entry Loop Legalization (`REQ-TGT-257`, `0523 §22–24, §138, §155 AWASM-68`, `0784 §562.83, §562.200 #74`).**
1. **Detection & Linear-Size `$irr_state` Dispatch Transformation (`AWASM-68`, `REQ-TGT-257`)**:
   - WebAssembly bytecode cannot directly encode an irreducible cycle (a strongly connected component `S` with $m \ge 2$ distinct entry blocks `E = [e_0, e_1, ..., e_{m-1}]`, sorted by `rpo[e_0] < rpo[e_1] < ...`, where none of the `e_k` dominates all others).
   - Before running `AXS-WASM-013` on `S`, `compiler/target/wasm32/isel` runs Tarjan's SCC over non-dominated back/cross-edges and rewrites each irreducible SCC `S` deterministically in `O(|S| + |E|)` size (avoiding exponential node cloning):
     1. Allocate one function-local state variable `$irr_state: i32` per irreducible nesting depth;
     2. Create a single synthetic reducible loop header `H_irr` dominating all blocks in `S`;
     3. Rewrite every external entry edge `p -> e_k` (`p not in S`) and every internal cycle edge `q -> e_k` (`q in S` not dominated by `e_k`) to execute its PHI parallel copies (`AXS-WASM-012`), set `(local.set $irr_state (i32.const k))`, and branch to `H_irr`;
     4. Inside `loop $H_irr`, emit `(local.get $irr_state)` followed by a nested `block` tower + `br_table` dispatching `0 -> e_0`, `1 -> e_1`, ..., `m-1 -> e_{m-1}`.
   - Repeating from innermost to outermost SCC yields a 100% reducible CFG while preserving exact Axiom evaluation order, memory effects, loop termination, and `Drop` destructor execution order (`AWASM-67..68`, `REQ-TGT-256..257`).

**AXS-WASM-015 — Single-Use SSA Expression-Tree Stackification & Side-Effect Commutativity Rules (`REQ-TGT-258`, `0523 §11–18, §139, §155 AWASM-69`, `0784 §562.79–80`).**
1. **Virtual Operand-Stack Tree Scheduling (`AWASM-69`, `REQ-TGT-258`)**:
   - Within each basic block, an SSA definition `I_def: v = op(x_1, ..., x_r)` with `use_count(v) == 1` whose sole user `I_use` resides in the **same** basic block (and inside the same structured sub-scope) is sunk and emitted inline as an operand-stack expression subtree at `I_use`'s operand position — completely eliminating `local.set` and `local.get` traffic — **if and only if** `I_def` legally commutes past every intervening instruction `J` in `(I_def, I_use)`:
     1. **Pure arithmetic/bitwise/SIMD ops** (`Effect = Pure`): commute past `J` iff `J` does not overwrite any local read by `I_def`'s expression subtree and `I_def` cannot trap (`i32.div_*`/`rem_*` never commute past an earlier panic/call barrier);
     2. **Linear-memory loads (`ReadMem`)**: commute past `J` iff `J` has zero `WriteMem` alias overlap (`AliasResult.NoAlias` in `SPEC-71`), zero `Volatile`, zero `Atomic` `Acquire`/`Release`/`SeqCst` barrier, zero `Call` with `MayWrite`/`MaySync`, and zero mutation of `$__stack_pointer`;
     3. **Strict Barriers (`No-Reorder`)**: panicking assertions (`Assert` overflow/divzero/bounds/shift), `WriteMem`, `VolatileLoad`/`VolatileStore`, `Atomic*`/`Fence`, and `Call`/`CallIndirect` NEVER reorder past another side-effecting or potentially-panicking instruction, strictly preserving Axiom left-to-right operand evaluation (`SPEC-03` AXS-SEM-041).
2. **Opportunistic `local.tee` Peephole**:
   - When `use_count(v) >= 2` and `v`'s first use consumes the top of the operand stack immediately after `I_def`, the stackifier emits `local.tee $loc(v)` (`0x22`) in place of `local.set $loc(v)` (`0x21`) + `local.get $loc(v)` (`0x20`).

**AXS-WASM-016 — Typed WASM Local Allocation, Liveness Coalescing & Debug Source Provenance (`REQ-TGT-212`, `REQ-TGT-259`, `REQ-TGT-263`, `0523 §13–14, §103–104, §139, §155 AWASM-23, AWASM-70, AWASM-74`, `0784 §562.80, §562.191–193`).**
1. **Type-Partitioned Linear-Scan Local Coloring (`AWASM-23, 70`, `REQ-TGT-212, 259`)**:
   - All non-stackified SSA virtual registers, loop-carried values, PHI parallel-copy temporaries, and `$irr_state` dispatchers are partitioned by exact WASM `ValType` (`i32 = 0x7F`, `i64 = 0x7E`, `f32 = 0x7D`, `f64 = 0x7C`, `v128 = 0x7B`).
   - Within each `ValType` partition, `compiler/target/wasm32/isel` computes exact structured live intervals (extending loop-live intervals across the full `[loop_start, loop_end]` range of every enclosing `loop`) and performs deterministic linear-scan coloring (`lowest available slot index` tie-break). Two SSA values share a WASM local **only** when they have the identical `ValType` and strictly disjoint live intervals (`AWASM-70`, `REQ-TGT-259`).
   - Allocated locals are compressed into run-length `(count: u32, valtype: u8)` declarations at the start of the `Code` body (`section 10`) in canonical type order `[i32, i64, f32, f64, v128]`. WASM guarantees zero-initialization of all declared non-parameter locals on function entry.
2. **Debug Source Provenance Preservation (`AWASM-74`, `REQ-TGT-263`, `SPEC-04` AXS-EXT-040/054)**:
   - Every WASM instruction retains the originating MIR/LIR `Span`, and `var_debug_info` maps source bindings to `(WasmLocalIdx | ShadowStackFrameOffset, live_range)` so `compiler/target/wasm32/encode` emits accurate `(code_section_offset, Span)` line mappings, WASM `name` custom section entries (function and local names in debug builds), and DWARF `.debug_*` custom sections (`AWASM-74`, `REQ-TGT-263`).

**AXS-WASM-017 — Scalar Integer, Overflow, Division Pre-Check, `128`-Bit & IEEE-754 Float Lowering (`REQ-TGT-079`, `REQ-TGT-222`, `0523 §60–67, §155 AWASM-33`, `0784 §562.79`, `SPEC-03` AXS-SEM-032, `SPEC-40`, `SPEC-41`, `SPEC-81` AXS-TGTD-030..033).**
1. **Narrow & Word Integer Lowering (`i8..u64`, `isize`, `usize`, `bool`, `char`)**:
   - `i8`, `u8`, `i16`, `u16`, and `bool` reside in `i32` locals/stack slots: narrow loads use `i32.load8_s`/`u` and `i32.load16_s`/`u`; narrow stores use `i32.store8` and `i32.store16`; wrapping narrow arithmetic canonicalizes high bits via baseline `+sign_ext` (`i32.extend8_s`, `i32.extend16_s`) for signed types and `i32.and` (`0xFF`, `0xFFFF`) for unsigned types.
   - All five `SPEC-40` integer arithmetic families are lowered without hardware condition flags (`SPEC-81` AXS-TGTD-028/030):
     - Unsigned `a + b` overflow predicate: `i32.lt_u(i32.add(a, b), a)` (and `i64.lt_u` for `u64`);
     - Signed `a + b` overflow predicate: `i32.lt_s(i32.and(i32.xor(sum, a), i32.xor(sum, b)), 0)` (analogously for `sub` and `i64`-widened `i32` multiplication / 64x64->128 limb check for `i64` multiplication);
     - Shift counts `k` in default checked `<<`/`>>` explicitly verify `k < bit_width` (`i32.ge_u` -> panic branch) because WASM `i32.shl`/`i64.shl` silently masks shift counts modulo `32`/`64`!
2. **Mandatory Pre-Check Before Trapping WASM Division/Remainder (`SPEC-81` AXS-TGTD-033, `AWASM-33`, `REQ-TGT-222`)**:
   - WebAssembly `i32.div_s`, `i32.div_u`, `i64.div_s`, `i64.div_u`, and `i32`/`i64.rem_*` trap directly in the VM on `divisor == 0` and on signed `INT_MIN / -1` (`div_s` traps, whereas WASM `i32.rem_s(INT_MIN, -1)` evaluates to `0` without trapping!).
   - To preserve exact Axiom semantics (`SPEC-40` AXS-INT-021, `SPEC-03` AXS-SEM-032: **both** `INT_MIN / -1` and `INT_MIN % -1` panic in Axiom!), `compiler/target/wasm32/isel` **always** emits explicit pre-check branches (`divisor == 0` and, for signed `div` **and** `rem`, `dividend == INT_MIN && divisor == -1`) targeting the Axiom panic cold block before executing the WASM divide/remainder instruction.
3. **`i128` / `u128` Two-Limb Legalization & IEEE-754 Floating-Point Lowering (`SPEC-40`, `SPEC-41`)**:
   - `i128`/`u128` legalize into `(lo: i64, hi: i64)` little-endian limb pairs (`add128`: `lo = i64.add(a_lo, b_lo)`, `carry = i64.extend_i32_u(i64.lt_u(lo, a_lo))`, `hi = i64.add(i64.add(a_hi, b_hi), carry)`; `sub128` via `i64.lt_u(a_lo, b_lo)` borrow; `mul128`/`div128`/`rem128` via deterministic 64-bit routines).
   - `f32` and `f64` lower directly to strict IEEE-754 WASM instructions (`f32.add`, `f64.mul`, `f64.div`, `f64.sqrt`, `f64.abs`, `f64.neg`, `f64.copysign`, `f64.floor`, `f64.ceil`, `f64.trunc`, `f64.nearest`), with zero unsafe fast-math reassociation (`SPEC-41`), and saturating float-to-int `as` casts lower directly to baseline `+nontrapping_fptoint` `i32`/`i64.trunc_sat_f32`/`f64_{s,u}` (`0xFC 0x00..0x07`).

**AXS-WASM-018 — WASM `simd128` Vector Lowering & Non-Contamination of Core `Vector<T, N>` (`REQ-TGT-238`, `REQ-TGT-239`, `0523 §57–59, §155 AWASM-49..50`, `0784 §562.88`, `SPEC-42`, `SPEC-43`).**
1. **Semantic Independence of `Vector<T, N>` (`AWASM-49..50`, `REQ-TGT-238..239`)**:
   - WASM `simd128` never redefines Core `Vector<T, N>` lane semantics, alignment, or overflow/NaN rules (`AWASM-49`, `REQ-TGT-238`), and neither fixed-128-bit WASM SIMD nor scalable-vector models contaminate Core IR (`AWASM-50`, `REQ-TGT-239`).
2. **Concrete `+simd128` Mapping**:
   - When `+simd128` is enabled, 128-bit `Vector<T, N>` values lower to WASM `v128` (`0x7B`) and `0xFD`-prefix SIMD128 instructions (`v128.load`, `v128.store`, `v128.const`, `i8x16`/`i16x8`/`i32x4`/`i64x2`/`f32x4`/`f64x2` lane arithmetic, comparisons, `i8x16.shuffle`, `i8x16.swizzle`, `v128.bitselect` for `Mask<N>.select`). Note that WASM `i8x16.swizzle` zeroes lanes with index `>= 16`, while constant two-input `shuffle` uses `i8x16.shuffle imm[16]`. `256`-bit and `512`-bit portable vectors split deterministically into `2` or `4` `v128` halves (`SPEC-43`), and `-simd128` builds legalize all vector operations to scalar loops (`AXS-WASM-003`).

---

## 3. WebAssembly Basic C ABI (`CallConv.Wasm`), Indirect Dispatch, FFI Attributes & Panic Lowering (`AXS-WASM-019`..`024`)

**AXS-WASM-019 — `CallConv.Wasm` (WebAssembly Basic C ABI) Parameter, Return, `sret` & Variadic Classification (`REQ-TGT-240`..`242`, `0523 §88–99, §155 AWASM-51..53`, `0784 §562.92, §562.98`, `SPEC-04` AXS-EXT-052, `SPEC-81` AXS-TGTD-011, `compiler/abi/wasm32`).**
1. **Canonical Parameter & Return Classification Table (`CallConv.Wasm` / `extern "C"` / `extern "wasm"`)**:
   - Both `wasm32-freestanding` and `wasm32-wasi` implement the official **WebAssembly Basic C ABI** (`WasmScalarOrIndirect` in `SPEC-81` AXS-TGTD-011) so Axiom binaries interoperate 100% cleanly with `wasi_snapshot_preview1`, host embedders, and C/Rust/Zig `wasm32` objects:

| Type Class | As Parameter | As Return Value |
|---|---|---|
| Zero-sized (`()`, `[0]T`, empty `struct`) | Omitted (`0` WASM params) | WASM empty result `[]` |
| `bool` | Direct `i32` (`0` or `1`, caller zero-extended) | Direct `[i32]` (`0` or `1`) |
| `i8`, `i16` / `u8`, `u16` | Direct `i32` (caller sign-extended via `i32.extend8_s`/`16_s` for signed; zero-extended via `i32.and` for unsigned) | Direct `[i32]` (callee sign/zero-extended) |
| `i32`, `u32`, `char`, `usize`, `isize`, `*const T`, `*mut T`, thin `view<T>`/`mut_view<T>`/`Box<T>` (`T: Sized`), `FnPtr` | Direct `i32` | Direct `[i32]` |
| `i64`, `u64` | Direct `i64` | Direct `[i64]` |
| `f32` / `f64` | Direct `f32` / `f64` | Direct `[f32]` / `[f64]` |
| 128-bit `Vector<T, N>` (with `+simd128`) | Direct `v128` | Direct `[v128]` |
| `i128`, `u128` | Split into **two** direct `i64` params `(lo: i64, hi: i64)` (little-endian limb order) | Indirect `sret: i32` hidden param `0` (16-byte-aligned caller shadow-stack slot), WASM result `[]` |
| Trivial single-scalar wrapper (`@repr(transparent)` or `struct` with exactly 1 non-ZST scalar leaf and natural alignment) | Unwrapped recursively and passed directly as that single WASM scalar (`i32`/`i64`/`f32`/`f64`/`v128`) | Unwrapped recursively and returned directly as `[scalar]` |
| Multi-field or non-scalar aggregate (`struct` with $\ge 2$ non-ZST fields, `union`, payload `enum`, `[N]T` with $N \ge 2$, over-aligned `@align(N)`, two-word `{ptr, meta}` structs; `AWASM-51`) | Copied by caller into a temporary shadow-stack slot aligned to `max(align_of<T>(), 4)` and passed as `ptr: i32` | Indirect `sret: i32` hidden param `0` (`align_of<T>()`-aligned caller shadow-stack slot), WASM result `[]` (`AWASM-52`) |

   - **Hidden `sret` Isolation (`AWASM-52`, `REQ-TGT-241`)**: Indirect `sret: i32` return passing is strictly a `compiler/abi/wasm32` lowering detail; Axiom source signatures, MIR semantics, and `RVO` rules (`SPEC-73`) remain pure return-by-value (`AWASM-52`). Closed-world internal Axiom-ABI functions (`abi = Axiom`, non-exported, address-not-taken) MAY additionally scalarize two-word `Str` / `view<[T]>` pairs (`(ptr: i32, len: i32)`) across parameters, and under `+multivalue` across internal returns, provided `.axmi` `AbiFingerprint` records the exact rule (`AWASM-77`).
2. **Variadic `extern "C" fn(fixed..., ...)` ABI (`AWASM-53`, `REQ-TGT-242`)**:
   - Under `CallConv.Wasm`, an `extern "C"` variadic declaration lowers its fixed parameters per the table above and appends **one** trailing WASM parameter `va_list: i32`. At each call site, the caller packs all variadic arguments sequentially into its 16-byte-aligned shadow-stack frame at natural alignment (`min 4` bytes; `8` bytes for `i64`/`f64`; `16` bytes for `i128`/`v128`, applying standard C variadic promotions `bool`/`i8`/`u8`/`i16`/`u16 -> i32` and `f32 -> f64`) and passes the buffer's `i32` base offset (or `0` when zero variadic arguments are supplied). Variadic handling never leaks into Core Axiom function semantics (`AWASM-53`, `REQ-TGT-242`; non-`extern "C"` variadics remain rejected via `AX_FFI_VARIADIC_NOT_EXTERN_C`).

**AXS-WASM-020 — Shadow-Stack Frame Prologue, Epilogue & Stack Overflow Hygiene (`0523 §6, §14, §88–93`, `0784 §562.80, §562.92`).**
1. **Zero-Overhead Leaf/Local-Only Functions**:
   - Any function whose locals and temporaries all reside in Domain A (`shadow_frame_bytes == 0`, `AXS-WASM-004`) emits **zero** `global.get`/`global.set` instructions on `$__stack_pointer`.
2. **16-Byte-Aligned Shadow-Stack Prologue & Epilogue**:
   - When `shadow_frame_bytes > 0`, let `F = (shadow_frame_bytes + 15) & ~15`:
     - **Prologue**: `$fp = i32.sub(global.get $__stack_pointer, i32.const F)`, stored into a dedicated `i32` WASM local `$fp`; if the function executes any `call` or `call_indirect` (or when `--stack-check` is active), emit `global.set $__stack_pointer, $fp` immediately in the prologue (with `--stack-check` emitting `if (i32.lt_u($fp, i32.const __stack_low)) { unreachable }` prior to writing into the frame);
     - **Epilogue**: Every `return` / function-exit path restores `global.set $__stack_pointer, i32.add($fp, i32.const F)` before returning.

**AXS-WASM-021 — Direct `call` vs `call_indirect`, `__indirect_function_table` (`slot 0 = null`), Closures & `8`-Byte `dyn Trait` Fat Pointers (`REQ-TGT-231`..`234`, `0523 §30–40, §155 AWASM-42..45`, `0784 §562.86`, `SPEC-63`).**
1. **Direct vs Indirect Call Lowering (`AWASM-42..44`, `REQ-TGT-231..233`)**:
   - Statically resolved calls and monomorphized generic calls lower directly to `call $func_idx` (`0x10`) (`AWASM-44`, `REQ-TGT-233`).
   - Explicit dynamic dispatch (`FnPtr` invocation, type-erased closures, `dyn Trait` virtual method calls) lowers to `call_indirect (type $sig_idx) (table 0)` (`0x11 <sig_idx:uleb> 0x00`), popping the `i32` table index from the top of the operand stack after all ABI arguments (`AWASM-43`, `REQ-TGT-232`).
   - Function references (`fn(A...) -> R`) are plain 32-bit `u32`/`i32` slot indices into `table 0: funcref` (`__indirect_function_table`) with **zero object headers** (`AWASM-42`, `REQ-TGT-231`):
     - **Slot `0` Null Trap Guard**: `table 0` index `0` is **strictly reserved uninitialized (`ref.null func`)**; active `Element` segments (`section 9`) start at table index `1` (`offset = i32.const 1`), ensuring that calling a null `FnPtr` (`0`) deterministically traps in every WASM VM;
     - **Unique Canonical Slot Assignment**: Each address-taken function receives at most one canonical slot index in `[1 .. table_len - 1]`, preserving function-pointer equality (`f as usize == g as usize`, `AMACHINE-79`).
2. **Zero-Heap Closure Lowering & `32`-Bit `dyn Trait` Vtable Adaptation (`AWASM-45`, `REQ-TGT-234`, `SPEC-63`)**:
   - Closures never incur mandatory heap allocation on WASM (`AWASM-45`, `REQ-TGT-234`): non-capturing closures coerce directly to a `FnPtr` table index (`i32`); capturing closures lower to inline value structs `{ captures... }` on WASM locals / shadow stack.
   - Adapting `SPEC-63` (`AXS-DYN-010`, `AXS-DYN-020`) to `wasm32` (`usize = 4` bytes): `view<dyn Trait>`, `mut_view<dyn Trait>`, and `Box<dyn Trait>` are **8-byte** (`size = 8, align = 4`) `{ data_ptr: u32, vtable_ptr: u32 }` fat pointers, and `.rodata` `VTable<T, P>` descriptors are 4-byte-aligned arrays of `(3 + S + M)` 32-bit words `[drop_in_place_table_idx: u32, size: u32, align: u32, super_vtables: [S]u32, method_table_indices: [M]u32]` relocated via `R_WASM_TABLE_INDEX_I32` (for function slots) and `R_WASM_MEMORY_ADDR_I32` (for supertrait vtable pointers).

**AXS-WASM-022 — `async`/`await` State Machines, Zero WASM-GC Dependency, Foreign `funcref`/`externref` Handles & Component Model / WIT Layering (`REQ-TGT-230`, `REQ-TGT-235`..`237`, `REQ-TGT-268`..`270`, `REQ-TGT-272`..`273`, `REQ-TGT-282`, `0523 §41–42, §109–117, §125–131, §155 AWASM-41, AWASM-46..48, AWASM-79..81, AWASM-83..84, AWASM-93`, `0784 §562.87, §562.97`).**
1. **Stackless `Future` State Machines & Zero WASM-GC Requirement (`AWASM-46..47`, `REQ-TGT-235..236`)**:
   - `async fn` and `async { ... }` lower on `wasm32` to the identical compiler-synthesized stackless `Future<T>` state-machine structs used on native targets (`SPEC-33`), requiring **neither** host JS `Promise` integration, Binaryen Asyncify, nor WASM stack-switching proposals (`AWASM-46`, `REQ-TGT-235`).
   - Core Axiom execution on `wasm32` requires **zero WebAssembly GC (`wasm-gc`)** heap types (`structref`, `arrayref`, `i31ref`) (`AWASM-47`, `REQ-TGT-236`): all Axiom values use deterministic `Drop` (`SPEC-12`) in WASM locals or `LinearMemory`.
2. **Opaque `funcref` / `externref` Foreign Handle Semantics (`AWASM-41, 48, 81, 83..84`, `REQ-TGT-230, 237, 270, 272..273`, `SPEC-85` AXS-JNI-001)**:
   - Under `+reference_types`, WASM `funcref` (`0x70`) and `externref` (`0x6F`) values represent opaque host/platform handles that cannot be stored in byte-addressable `LinearMemory` (residing only in WASM locals or reference `Table` slots) and are **never** Core Axiom references (`view<T>`, `mut_view<T>`), raw pointers (`*const T`), or provenance-bearing offsets (`AWASM-48, 83..84`, `REQ-TGT-237, 272..273`; cross-domain handle non-equivalence shared with `SPEC-85` `AXS-JNI-001`).
   - Host-imported resources (`externref` table handles, WASI descriptors, JS/DOM handles) carry explicit ownership/`Drop` release contracts (`AWASM-41`, `REQ-TGT-230`, `SPEC-85`), are `!Send` and `!Share` by default (`AX_CONC_NOT_SEND`, `AX_CONC_NOT_SHARE`), and host-invoked WASM callbacks (`@wasm_export` / `FnPtr` table callbacks) strictly preserve resource release and FFI no-unwind abort barriers across normal returns, `?`, and panics (`AWASM-81`, `REQ-TGT-270`).
3. **WebAssembly Component Model & `WIT` Adapter Layering & FFI Safety Invariance (`AWASM-79..80, 93`, `REQ-TGT-268..269, 282`)**:
   - WebAssembly Component Model Canonical ABI lifting/lowering (`cabirealloc`, flattened scalar/pointer records) and `WIT` (`*.wit`) interface bindings reside strictly in an explicit ABI/platform binding layer above Core Axiom (`AWASM-79`, `REQ-TGT-268`). `WIT` type mappings (`string`, `list<T>`, `result<T, E>`, `own<R>`, `borrow<R>`) NEVER redefine Core Axiom `Str`, `String`, `Vec<T>`, `Result<T, E>`, or `view<T>` (`AWASM-80`, `REQ-TGT-269`), and adding WASM features (`@wasm_import`/`@wasm_export`, `+reference_types` handles, Component Model/`WIT` adapters) NEVER requires changing Core Axiom `unsafe` / FFI safety semantics (`AWASM-93`, `REQ-TGT-282`, shared with `SPEC-85`).

**AXS-WASM-023 — Explicit WASM Module Import/Export Attributes (`@wasm_import`, `@wasm_export`), Host Effect Contracts & Imported Memory Rules (`REQ-TGT-227`..`229`, `REQ-TGT-245`..`246`, `REQ-TGT-261`..`262`, `0523 §44, §46–50, §107–108, §155 AWASM-38..40, AWASM-56..57, AWASM-72..73`, `0784 §562.94–96`).**
1. **Two-Level WASM Import Contract (`@wasm_import`, `AWASM-38..39, 57, 72..73`, `REQ-TGT-227..228, 246, 261..262`)**:
   - WebAssembly imports carry a two-level `(module_name, field_name)` namespace (`section 2`). On `wasm32`:
     - `@wasm_import(module = "<mod>", name = "<field>")` (or positional `@wasm_import("<mod>", "<field>")`) on a body-less declaration inside an `extern "C"` (or `extern "wasm"`) block binds the declaration to WASM import `(module = "<mod>", name = "<field>")` (`AWASM-57`, `REQ-TGT-246`).
     - An unannotated `extern "C" { fn foo(...) }` declaration defaults to `(module = "env", name = "foo")` (or `module = "<lib>"` when the enclosing block carries `@link("<lib>")`).
     - Browser/JS APIs, host embedder callbacks, and raw `wasi_snapshot_preview1` imports are explicit `unsafe` FFI boundaries (`AX_UNSAFE_REQUIRED` when called outside `unsafe`, `AWASM-38, 73`, `REQ-TGT-227, 262`); host/WASI capabilities are **never** implicitly injected into `sandbox` or `freestanding` code (`AWASM-72`, `REQ-TGT-261`, `AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN`, `AX_DRIVER_PROFILE_FORBIDDEN_CAP`).
     - Unannotated host imports carry all five conservative FFI effects (`MayRead`, `MayWrite`, `MayEscape`, `MayPanic`, `MaySync`, plus `MayAlloc` wrt host buffer detachment; `AWASM-39`, `REQ-TGT-228`, `SPEC-54` AXS-PAN-023).
2. **Explicit WASM Export Contract (`@wasm_export` / `@export`, `AWASM-56`, `REQ-TGT-245`)**:
   - `@wasm_export("<name>")` or `@wasm_export` (defaulting to the item's identifier, synonymous on `wasm32` with `@export("<name>")` / `@export`) on a monomorphic `fn` or `static` emits an entry in WASM `Export` (`section 7`) and registers the symbol as a mandatory linker GC root (`AWASM-56`, `REQ-TGT-245`).
   - Attaching `@wasm_import` to a function with a body or outside an `extern` block, attaching `@wasm_export` to a non-`fn`/non-`static`, `async fn`, or `gen fn`, or passing an empty `""` module/export string emits `AX_FFI_INVALID_WASM_ATTR`; generic `@wasm_export` / `@export` emits `AX_FFI_GENERIC_EXPORT`; duplicate export names in the same linked module emit `AX_LINK_DUPLICATE_EXPORT`.
3. **Imported Linear Memory (`--wasm-import-memory`, `AWASM-40`, `REQ-TGT-229`)**:
   - By default, linked `.wasm` images define internal `memory 0` and export it as `"memory"`. When `--wasm-import-memory` is specified, `memory 0` is imported from `("env", "memory")` (or `--wasm-memory-import=<mod>:<name>`): imported memory is **never** assumed to be exclusively Axiom-owned outside `[low_guard_end .. __heap_base)` and pages explicitly acquired via `memory.grow`, so host-shared regions outside Axiom allocations require `unsafe` raw-pointer contracts (`AWASM-40`, `REQ-TGT-229`).

**AXS-WASM-024 — Profile-Driven Panic Lowering & Absence of WASM-Exception Semantic Leakage (`REQ-TGT-243`, `REQ-TGT-244`, `0523 §28–29, §127–128, §155 AWASM-54..55`, `0784 §562.91`, `SPEC-52`, `SPEC-54`).**
1. **No Axiom Exception Model from WASM `exception_handling` (`AWASM-54`, `REQ-TGT-243`)**:
   - Enabling low-level WASM `exception_handling` never introduces source-level `try`/`catch`/`throw` exceptions into Axiom (`AWASM-54`, `REQ-TGT-243`, `SPEC-54` AXS-PAN-021).
   - Both `wasm32-freestanding` and `wasm32-wasi` default to `--panic abort`; passing `--panic unwind` on `wasm32` without a target unwind runtime is rejected at driver startup with `AX_DRIVER_INVALID_PANIC_STRATEGY` (`SPEC-54` AXS-PAN-002; `--profile freestanding` also enforces `AX_DRIVER_PROFILE_FORBIDDEN_CAP`).
2. **Profile-Specific Abort Lowering (`AWASM-55`, `REQ-TGT-244`)**:
   - **`wasm32-freestanding`**: Every `panic(msg)` and failed compiler `Assert` invokes the user's `@panic_handler` (`SPEC-52` AXS-FRE-011), or when using the default freestanding abort stub, emits WASM `unreachable` (`0x00`) directly with **zero** host/WASI imports.
   - **`wasm32-wasi`**: Every `panic(msg)` and failed compiler `Assert` routes to `__ax_wasm_panic_abort(msg_ptr: i32, msg_len: i32) -> never`, which constructs three stack-allocated `ciovec` entries (`"panic: "`, `msg`, `"\n"`, zero heap allocation), calls `wasi_snapshot_preview1.fd_write(2, iov_ptr, 3, nwritten_ptr)`, calls `wasi_snapshot_preview1.proc_exit(101)`, and terminates with `unreachable` (`0x00`). Every `@wasm_export` / `extern "C"` boundary enforces the `SPEC-54` `AXS-PAN-020` no-unwind barrier.

---

## 4. Binary `.wasm` Module & Relocatable Object Format, Pre-Emission `verify_wasm`, Static Linker & `std.sys.wasi` (`AXS-WASM-025`..`029`)

**AXS-WASM-025 — Binary `.wasm` Module Container, LEB128/SLEB128 Encoding & Canonical Section Order (`REQ-TGT-208`, `REQ-TGT-248`..`249`, `0523 §100–105, §142–145, §155 AWASM-59..60`, `0784 §562.99, §562.153`, `compiler/target/wasm32/encode`).**
1. **8-Byte Module Header & Integer/Float Byte Encodings**:
   - Every `.wasm` object and linked image begins with exact 8-byte header `00 61 73 6D 01 00 00 00` (`magic = "\0asm"`, `version = 1`).
   - Non-relocatable integers, vector lengths, and section byte lengths encode as minimal-length **ULEB128** (`u32` $\le 5$ bytes, `u64` $\le 10$ bytes) or **SLEB128** (`i32.const` $\le 5$ bytes, `i64.const` $\le 10$ bytes, signed `s33` `blocktype`: `0x40` empty, `0x7F` `i32`, `0x7E` `i64`, `0x7D` `f32`, `0x7C` `f64`, `0x7B` `v128`, or non-negative `s33` `TypeIdx`). `f32.const` and `f64.const` encode raw 4-byte and 8-byte little-endian IEEE-754 bit patterns (`SPEC-41`). Relocatable fields in `--kind obj` use fixed 5-byte `0x80`-padded ULEB128/SLEB128 or 4-byte `I32` slots (`AXS-WASM-027`).
2. **Strict WebAssembly Binary Section Order**:
   - Known sections (`id in 1..12`) are emitted at most once and strictly in W3C WebAssembly binary order (note `DataCount = 12` **must** precede `Code = 10`):
     `1: Type` $\to$ `2: Import` $\to$ `3: Function` $\to$ `4: Table` $\to$ `5: Memory` $\to$ `6: Global` $\to$ `7: Export` $\to$ `8: Start` (omitted in WASI/ABI images, which export `_start` or `_initialize`) $\to$ `9: Element` $\to$ `12: DataCount` (emitted iff `+bulk_memory` passive data ops appear) $\to$ `10: Code` $\to$ `11: Data`.
   - Custom sections (`id = 0`, payload = `name: vec(byte)` + bytes) — `linking`, `reloc.<sec>`, `.axmeta` (`SPEC-24`), `name`, `.debug_*`, `producers` — carry zero runtime execution semantics and are cleanly removable without altering program behavior (`AWASM-59`, `REQ-TGT-248`).

**AXS-WASM-026 — Mandatory Internal Pre-Emission WASM Bytecode Validator (`verify_wasm`) (`REQ-TGT-252`, `REQ-TGT-253`, `0523 §140–141, §155 AWASM-63..64`, `0784 §562.182`, `compiler/target/wasm32/encode`).**
1. **Self-Contained Pre-Emission Gate (`AWASM-63..64`, `REQ-TGT-252..253`)**:
   - `compiler/target/wasm32/encode` and `compiler/link/wasm` run the built-in `verify_wasm` validator in-memory on **every** relocatable `.wasm` object and **every** linked `.wasm` binary prior to writing output bytes (`AWASM-63`, `REQ-TGT-252`). `axiomc` never depends on `wasm-validate`, `wasmtime`, Binaryen, or any external tool to detect invalid WASM (`AWASM-64`, `REQ-TGT-253`).
2. **Polymorphic Operand-Stack, Control-Frame & Index Verification Rules**:
   - `verify_wasm` enforces the full W3C WebAssembly Core validation specification plus active `TargetFeatureSet` gating:
     1. **Module & Index-Space Bounds**: verifies canonical W3C binary section order `1..9, 12 (DataCount), 10 (Code), 11 (Data)` with at most one occurrence of each known section (`DataCount = 12` precedes `Code = 10`, and in relocatable `--kind obj` modules every `reloc.*` custom section appears after the `linking` custom section), `Function.len == Code.len`, `DataCount == Data.len` (when present), `Memory` `min <= max` (`max <= 65536` pages = 4 GiB, `shared` requires explicit `max`), valid `TypeIdx`, `FuncIdx` (`imports.funcs + defined.funcs`), `TableIdx`, `MemIdx`, `GlobalIdx` (mutations allowed only when `mut == 0x01`), `ElemIdx`, `DataIdx`, and constant-initializer legality (`i32.const`/`i64.const`/`f32.const`/`f64.const`/`v128.const`/`ref.null`/`ref.func`/`global.get` of imported immutable global + `0x0B end`).
     2. **Structured `CtrlStack` & Polymorphic `ValStack`**: for every function body, initializes `ValStack = []` and pushes root `CtrlFrame { opcode = Func, start_types = [], end_types = sig.results, height = 0, unreachable = false }`:
        - Pushing/popping checks exact operand types above `ctrl.height`; when `ctrl.unreachable == true`, popping at `ValStack.len == ctrl.height` synthesizes polymorphic `Unknown` matching any single required `ValType` (type-polymorphic dead code after `unreachable`, `br`, `br_table`, `return`);
        - `block`/`loop`/`if` pop `start_types` and push a new `CtrlFrame`; `else` requires `ctrl.opcode == If`, verifies `ValStack[ctrl.height..] == end_types`, resets `ValStack` to `ctrl.height + start_types`, and clears `unreachable = false`; `if` without `else` requires `start_types == end_types`; `end` (`0x0B`) verifies `ValStack[ctrl.height..] == end_types`, pops the frame, and pushes `end_types`;
        - `br $l` / `br_if $l` / `br_table $l_0 .. $l_k $l_def` verify every label `$l < CtrlStack.len`, resolve `label_types($l)` = `frame.start_types` when `frame.opcode == Loop` and `frame.end_types` otherwise, verify `ValStack` supplies `label_types($l)`, and for `br_table` verify `label_types($l_i) == label_types($l_def)` for all $0 \le i \le k$.
     3. **Locals, `memarg` Alignment & Feature Gate**: verifies `local.{get,set,tee} $idx` bounds and `ValType`, verifies `2^(memarg.align) <= access_bytes` on all loads/stores and `2^(memarg.align) == access_bytes` on all `0xFE` `*.atomic.*` ops, and rejects any opcode/type whose required feature (`simd128`, `bulk_memory`, `atomics`, `multivalue`, `reference_types`, `tail_call`) is absent from `TargetFeatureSet`.
   - **Diagnostics**: invalid WASM IR supplied directly to `verify_wasm` in negative verifier tests emits `AX_VERIFY_WASM_ILLEGAL` (`data.rule`, `data.opcode`, `data.func`); a `verify_wasm` failure on compiler-lowered code emits `AX_ICE_INTERNAL` (`data.stage = "wasm_verify"`, exit code `3`, `AXD-042`).

**AXS-WASM-027 — Relocatable `.wasm` Object Format (`linking` v2 + `reloc.CODE` / `reloc.DATA`) & Deterministic GNU `ar` Archives (`REQ-TGT-208`, `REQ-TGT-249`, `0523 §100–102, §142–143`, `0784 §562.99, §562.179–181`, `compiler/obj/wasm`, `T675`).**
1. **Relocatable Object Schema (`--kind obj`)**:
   - `compiler/obj/wasm` emits a `verify_wasm`-valid `.wasm` object importing `("env", "__linear_memory")`, `("env", "__indirect_function_table")`, and `("env", "__stack_pointer")`, subdividing data into per-item segments (`.rodata.<sym>`, `.data.<sym>`, `.bss.<sym>`) for section GC, and appending the WebAssembly `linking` (`version = 2`) custom section followed strictly **after** `linking` by `reloc.<NAME>` custom sections (`reloc.CODE` for `Code` `section 10`, `reloc.DATA` for `Data` `section 11`, and `reloc.<debug_sec>` such as `reloc..debug_info` / `reloc..debug_line` when DWARF custom sections carry relocations):
     - `linking` subsections: `WASM_SEGMENT_INFO = 5` `(name, p2align, flags)`, `WASM_INIT_FUNCS = 6` `(priority, sym_idx)`, `WASM_COMDAT_INFO = 7` (generic deduplication), and `WASM_SYMBOL_TABLE = 8` (`SYMTAB_FUNCTION = 0`, `SYMTAB_DATA = 1`, `SYMTAB_GLOBAL = 2`, `SYMTAB_SECTION = 3`, `SYMTAB_TABLE = 5`; flags `WEAK = 0x01`, `LOCAL = 0x02`, `HIDDEN = 0x04`, `UNDEFINED = 0x10`, `EXPORTED = 0x20`, `EXPLICIT_NAME = 0x40`, `NO_STRIP = 0x80`).
     - **`reloc.<NAME>` Binary Payload Layout (`reloc.CODE`, `reloc.DATA`, `reloc.<debug_sec>`)**: Every `reloc.<NAME>` custom section (`id = 0`) payload begins with header **`(target_section_index: uleb32, reloc_count: uleb32)`** (where `target_section_index` is the 0-based module section index of the relocated section across known + custom sections) followed immediately by `reloc_count` relocation entries `(type: u8, offset: uleb32, sym_or_type_idx: uleb32, [addend: sleb32])` (with `offset` relative to the start of the target section's payload):
       - **Entries WITHOUT trailing `addend` (`type in {0, 1, 2, 6, 7}`)**: 5-byte padded ULEB128/SLEB128 code/type/global relocs `R_WASM_FUNCTION_INDEX_LEB = 0`, `R_WASM_TABLE_INDEX_SLEB = 1`, `R_WASM_TYPE_INDEX_LEB = 6`, `R_WASM_GLOBAL_INDEX_LEB = 7`, and 4-byte little-endian `u32` data table-slot reloc `R_WASM_TABLE_INDEX_I32 = 2` (vtable/`FnPtr` slots);
       - **Entries WITH mandatory trailing `addend: sleb32` (`type in {3, 4, 5, 8, 9}`)**: 5-byte padded ULEB128/SLEB128 memory-address relocs `R_WASM_MEMORY_ADDR_LEB = 3` (`+ addend: sleb32`) and `R_WASM_MEMORY_ADDR_SLEB = 4` (`+ addend: sleb32`), and 4-byte little-endian `u32` address/offset relocs `R_WASM_MEMORY_ADDR_I32 = 5` (`+ addend: sleb32`), `R_WASM_FUNCTION_OFFSET_I32 = 8` (`+ addend: sleb32`), and `R_WASM_SECTION_OFFSET_I32 = 9` (`+ addend: sleb32`).
2. **Deterministic Static Archives (`--kind lib`, `.a`)**:
   - `compiler/obj/wasm` packages relocatable `.wasm` objects into standard deterministic GNU `ar` archives (`!<arch>\n`, `/` big-endian symbol directory indexing defined `WASM_SYMBOL_TABLE` globals, `mtime = 0`, `uid = 0`, `gid = 0`, `mode = 0644`; malformed archives emit `AX_LINK_BAD_ARCHIVE`).

**AXS-WASM-028 — Self-Contained Static `.wasm` Linker, Export-Rooted Dead-Code/Data/Runtime GC, Stripping & Byte-Identical Determinism (`REQ-TGT-245`..`249`, `REQ-TGT-267`, `0523 §29, §105–108, §143–145, §155 AWASM-56..60, AWASM-78`, `0784 §562.96, §562.99, §562.153, §562.180–181`, `compiler/link/wasm`, `T675`).**
1. **Native Static Linking Pipeline (`compiler/link/wasm`)**:
   - Links relocatable `.wasm` objects and `.a` archives directly into standalone `.wasm` executables (`--kind exe`, command module) or libraries/reactors (`--kind dll`, reactor module) without `wasm-ld`:
     1. **Input & Target Verification**: validates `\0asm` v1 headers, `linking` v2 tables (`AX_LINK_BAD_OBJECT`, `AX_LINK_BAD_ARCHIVE`), and `TargetFingerprint` compatibility (`AX_LINK_ARTIFACT_TARGET_MISMATCH`).
     2. **Symbol Resolution**: resolves `WASM_SYMBOL_TABLE` definitions across objects and archives (`Strong` overrides `Weak`; duplicate `Strong` emits `AX_LINK_DUPLICATE_SYMBOL`; unresolved non-import emits `AX_LINK_UNDEFINED_SYMBOL`; cross-object `FuncType` or symbol-kind mismatch emits `AX_LINK_ABI_MISMATCH`; duplicate export names emit `AX_LINK_DUPLICATE_EXPORT`).
     3. **Export-Rooted Mark-Sweep GC (`AWASM-56..58, 78`, `REQ-TGT-245..247, 267`)**: seeds live reachability strictly from: (i) `_start` (`--kind exe`) or `_initialize` (`--kind dll`); (ii) `@wasm_export` / `@export` items (`AWASM-56`, `REQ-TGT-245`); (iii) `@used` / `WASM_SYM_NO_STRIP` items and `WASM_INIT_FUNCS`; and (iv) `@reflect(runtime)` metadata roots (`AWASM-78`, `REQ-TGT-267`). Unreached functions, `.rodata`/`.data`/`.bss` segments, unreferenced two-level host/WASI imports (`AWASM-57`, `REQ-TGT-246`), and unused runtime subsystems (heap allocator when `heap_alloc` is unreachable, WASI stdio/filesystem tables when unused, 128-bit/float helpers when unused; `AWASM-58`, `REQ-TGT-247`) are completely eliminated.
     4. **Index Assignment, Layout & Relocation Patching**: deduplicates `Type` (`section 1`) signatures in canonical structural order; orders `FuncIdx` (`live_imports` followed by `live_defined_funcs` in deterministic symbol/CGU order); assigns `__indirect_function_table` slots `1 .. K` (`slot 0 = null`); computes `AXS-WASM-005` linear-memory layout (`$__stack_pointer`, `__data_end`, `__heap_base`, exporting `"memory"` unless `--wasm-import-memory`); patches all `R_WASM_*` relocations using minimal ULEB128/SLEB128 in final code (emitting `AX_LINK_RELOC_OUT_OF_RANGE` on 32-bit overflow); strips `linking` and `reloc.*` sections (and `name`/`.debug_*`/`.axmeta` under `--strip-all` while keeping all exports/FFI/reflection roots intact, `AWASM-78`); and runs `verify_wasm` (`AXS-WASM-026`) on the linked module.
2. **Byte-for-Byte Deterministic `.wasm` Output (`AWASM-60`, `REQ-TGT-249`, `INV-DET-001`)**:
   - Identical inputs, options, and target flags produce byte-for-byte identical `.wasm` binaries across runs, `--jobs 1` vs `--jobs N`, and host operating systems (`Windows`, `Linux`, `macOS`), with zero timestamps, host paths, or hash-seed nondeterminism.

**AXS-WASM-029 — `std.sys.wasi` (`wasi_snapshot_preview1`) Platform Contract, Preopened Directory Capabilities & `memory.grow` Page Allocator (`REQ-TGT-226`, `REQ-TGT-261`, `0220 §10, §39 AOS-20..40`, `0523 §43, §45, §148–149, §155 AWASM-37, AWASM-72`, `0784 §562.93, §562.95`, `std/sys/wasi`, `T675`).**
1. **WASI Platform Boundary & `_start` Entry (`AWASM-37`, `REQ-TGT-226`)**:
   - `wasi_snapshot_preview1` is the hosted OS/platform ABI of `TargetId.Wasm32Wasi` implemented solely inside `std/sys/wasi` behind `SPEC-04` `AXS-EXT-110` (`host.*`), never leaking WASI struct layouts into Core or `std.core` (`AWASM-37`, `REQ-TGT-226`).
   - For `--kind exe` on `wasm32-wasi`, the linker synthesizes exported `_start () -> ()`, which: (1) scans preopened directory descriptors `fd = 3, 4, ...` via `fd_prestat_get(fd, prestat_ptr)` + `fd_prestat_dir_name(fd, buf, name_len)` until `EBADF (8)` (`__wasi_preopentype_dir = 0`); (2) invokes user `main` (`fn() -> i32` or `fn()` returning `0`); and (3) calls `wasi_snapshot_preview1.proc_exit(code)` followed by `unreachable`.
2. **Canonical `wasi_snapshot_preview1` Import Surface & `AXS-EXT-110` Mapping**:
   - All WASI pointers and `size` values are 32-bit `u32` (`i32` in WASM signatures); `ciovec` / `iovec` is `@repr(C) struct { pub buf: u32, pub buf_len: u32 }` (`size = 8, align = 4`), `filestat` (`__wasi_filestat_t`) is 64 bytes (`align = 8`: `+0 dev: u64`, `+8 ino: u64`, `+16 filetype: u8` + `7` padding bytes `+17..+23`, `+24 nlink: u64`, **`+32 size: u64`**, `+40 atim: u64`, `+48 mtim: u64`, `+56 ctim: u64`), and `dirent` (`__wasi_dirent_t`) is 24 bytes (`align = 8`: `+0 d_next: u64`, `+8 d_ino: u64`, `+16 d_namlen: u32`, `+20 d_type: u8` + `3` padding bytes):

| `host.*` Intrinsic (`AXS-EXT-110`) | `wasi_snapshot_preview1` Import(s) & Lowering |
|---|---|
| `heap_alloc`, `heap_realloc`, `heap_free` | Pure-Axiom segregated free-list + bump allocator in `std/sys/wasi/heap.ax` over `[__heap_base ..)` growing in 64 KiB pages via `memory.grow 0` (`-1` $\to$ `null_mut()`); **zero** `wasi-libc` / C `dlmalloc` |
| `stdio(0\|1\|2)` | Returns `0i64` (`stdin`), `1i64` (`stdout`), `2i64` (`stderr`) |
| `read` / `write` | `fd_read(fd, &iov, 1, &nread)` / `fd_write(fd, &ciov, 1, &nwritten)` |
| `close` / `file_size` | `fd_close(fd)` / `fd_filestat_get(fd, &st)` reading `st.size` (`u64` at **`+32`**) |
| `open`, `remove`, `mkdir`, `dir_open` | Resolved strictly against preopened `(dirfd, prefix)` table (`3` below) $\to$ `path_open`, `path_unlink_file`, `path_create_directory` |
| `metadata(path, path_len, out)` | Resolved against preopened `(dirfd, prefix)` table $\to$ `path_filestat_get(dirfd, LOOKUPFLAGS_SYMLINK_FOLLOW = 1, rel_ptr, rel_len, &st)`: maps `__wasi_filetype_t` (`u8` at `+16`) as `REGULAR_FILE (4)` $\to$ `out[0] = 1u64`, `DIRECTORY (3)` $\to$ `out[0] = 2u64`, all other `filetype` values $\to$ `out[0] = 3u64` (`SPEC-04` `AXS-EXT-110`), and writes `out[1] = st.size` (`u64` at **`+32`**) |
| `dir_next` / `dir_close` | `fd_readdir(dirfd, buf, cap, cookie, &bufused)` skipping `"."` and `".."` / `fd_close(dirfd)` |
| `args_count`, `arg`, `exe_path` | `args_sizes_get` + `args_get` (`exe_path` returns `argv[0]` when `argc >= 1`, else `-1` `NotFound`) |
| `env_get` | `environ_sizes_get` + `environ_get` matching `<NAME>=<VALUE>` |
| `monotonic_ns` / `thread_sleep_ns` | `clock_time_get(CLOCK_MONOTONIC = 1, 1, &ts)` / `poll_oneoff` relative clock subscription (`tag = 0`) |
| `exit(code)` | `proc_exit(code)` + `unreachable` |

3. **Zero Ambient Authority — Capability-Scoped Path Resolution & Deterministic Errno Mapping (`AWASM-72`, `REQ-TGT-261`, `0220 §10`)**:
   - WASI provides **zero** ambient host root filesystem (`/`): `std/sys/wasi` matches every path against the longest matching preopened directory capability `(dirfd, dir_prefix)` discovered at startup, strips the matched prefix, normalizes `.` segments, and **rejects** any `..` traversal escaping above `dir_prefix` with `-2` (`PermissionDenied`, WASI `ENOTCAPABLE = 76`) and any path matching zero preopened capabilities with `-1` (`NotFound`) — never fabricating raw integer `fd` values (`AWASM-72`, `REQ-TGT-261`).
   - Non-zero `__wasi_errno_t` values map deterministically to negated `AXS-EXT-110` error kinds (`SPEC-03` AXS-SEM-003): `ENOENT (44)` $\to$ `-1`; `EACCES (2)` / `EPERM (63)` / `EROFS (69)` / `ENOTCAPABLE (76)` $\to$ `-2`; `EEXIST (20)` $\to$ `-3`; `EBADF (8)` / `EILSEQ (25)` / `EINVAL (28)` / `ENOTDIR (54)` / `EISDIR (31)` $\to$ `-4`; `ETIMEDOUT (73)` $\to$ `-5`; all other non-zero codes $\to$ `-9` (`Other`). Unshared baseline `wasm32-wasi` returns `-9` (`Other`) on `thread_spawn` (enabled under `+threads` / `wasi-threads`).

---

## 5. Conformance Architecture, Diagnostics, Canonical Examples & E16.6 Traceability (`AXS-WASM-030`..`034`)

**AXS-WASM-030 — E16.6 Backend Conformance, Reference-Execution Equivalence & Cross-Target Core Invariance (`REQ-TGT-264`..`265`, `REQ-TGT-274`..`284`, `0523 §151–156 AWASM-75..76, AWASM-85..95`, `0524 §112 ABACKEND-89..92`, `0784 §562.165, §562.182–186`, `SPEC-81` AXS-TGTD-040..044, `T676`).**
1. **Reference-Execution Equivalence, Target-Optimization Invariance & WAT Structural Inspection (`AWASM-75..76`, `REQ-TGT-264..265`, `SPEC-81` AXS-TGTD-043, `0524 §112 ABACKEND-89..92`)**:
   - **Equivalence to Reference Execution (`AWASM-75`, `REQ-TGT-264`)**: WASM code generation MUST be semantically equivalent to the reference interpreter (`--interp`) across all observable outcomes (`stdout`, `stderr` panic prefix, exit code, `Drop` order).
   - **Target-Optimization Invariance (`AWASM-76`, `REQ-TGT-265`)**: WASM target-specific optimizations (single-use operand-stack expression-tree sinking, `local.tee` coalescing, linear-scan local coloring, zero-frame leaf `$__stack_pointer` elision, `+bulk_memory` / `+simd128` selection) MUST NOT alter Core Axiom semantics.
   - **Target-Independent Test Authority vs WAT Inspection (`SPEC-81` AXS-TGTD-043, `0524 §112 ABACKEND-89..92`)**: Semantic conformance tests remain strictly target-independent; disassembled WebAssembly text (`inspect --emit=wasm-wat` / `tests/mc/wasm32_stackify` / `tests/obj/wasm`) validates structural lowering quality (`block`/`loop`/`if`/`br_table` nesting, `$irr_state` irreducible dispatch, `local.tee`/operand-stack tree scheduling, `CallConv.Wasm` `sret` & `(i64, i64)` `i128` splitting, and `linking` v2 + `reloc.CODE`/`reloc.DATA` relocations) without acting as the semantic authority.
2. **Mandatory E16.6 Cross-Target & Core-Invariance Conformance Guarantees (`AWASM-85..95`, `REQ-TGT-274..284`, `T676`)**:
   - `tests/conformance/p16/e16_6_wasm32` (`T676`) certifies end-to-end across `wasm32-freestanding` and `wasm32-wasi` that:
     1. **Common `TargetBackend` Conformance (`AWASM-85`, `REQ-TGT-274`)**: Both `TargetId.Wasm32Freestanding` and `TargetId.Wasm32Wasi` pass the common `SPEC-81` `TargetBackend` conformance tests;
     2. **Native-vs-WASM Observable Agreement (`AWASM-86`, `REQ-TGT-275`)**: Native register implementations (`x86_64`, `aarch64`) and WASM stack-machine implementations agree on all observable program semantics;
     3. **Physical Representation vs Semantic Equivalence (`AWASM-87`, `REQ-TGT-276`)**: Differences in physical representation (`32`-bit vs `64`-bit `usize`, `8`-byte vs `16`-byte fat pointers, Domain A WASM locals vs physical registers, `LinearMemory` shadow stack vs hardware `RSP`/`SP`) are physical ABI/layout differences, not semantic differences in safe Core Axiom;
     4. **Zero WASM-Specific Core v1 Syntax (`AWASM-88`, `REQ-TGT-277`)**: Core v1 requires no WASM-specific syntax constructs (target bindings use standard `@wasm_import`, `@wasm_export`, and `@target_feature` attributes);
     5. **Core Semantic Non-Contamination Across Ownership, Traits, Async, Numerics & FFI (`AWASM-89..93`, `REQ-TGT-278..282`)**: Supporting WASM and optional WASM target features (`+bulk_memory`, `+simd128`, `+atomics`, `+multivalue`, `+reference_types`, `+tail_call`, `+exception_handling`) requires zero changes to Core ownership/capability/`Drop` semantics (`AWASM-89`, `REQ-TGT-278`), trait and `dyn Trait` semantics (`AWASM-90`, `REQ-TGT-279`), `async`/`await` `Future` semantics (`AWASM-91`, `REQ-TGT-280`), checked/wrapping/saturating/overflowing `i8..u128` and IEEE-754 `f32`/`f64` numeric semantics (`AWASM-92`, `REQ-TGT-281`), or `unsafe`/FFI safety semantics (`AWASM-93`, `REQ-TGT-282`, cross-verified with `SPEC-85` `T672`);
     6. **Frontend-Independent Backend Replaceability (`AWASM-94`, `REQ-TGT-283`)**: The WASM backend remains cleanly replaceable behind the `Axiom LIR` / `TargetBackend` boundary without changing frontend parsing, name resolution, type checking, capability checking, or `Verified MIR`;
     7. **`Axiom LIR` Portability Validation (`AWASM-95`, `REQ-TGT-284`)**: Lowering arbitrary reducible and irreducible `Axiom LIR` CFGs and virtual-register programs to `wasm32` validates the architecture-neutral portability of `Axiom LIR` across register and virtual-stack machines;
     8. **Validator, Feature-Gate, Determinism & WASI Differential Execution (`AWASM-60..64`, `0784 §562.165, §562.182–186`)**: Cross-build hosts unconditionally run `verify_wasm` (`AXS-WASM-026`), negative feature/capability/bytecode-validator tests, binary section/relocation/export/import structural assertions, and byte-for-byte determinism checks (`AXS-WASM-028`); when a WASI runtime (`wasmtime` or `wasmer`) is present in `PATH`, the suite executes compiled `.wasm` modules and verifies `0 WEAK-NATIVE` differential parity (`stdout` + exit code, including `"Xin chào thế giới\n"` and preopened directory I/O) against `--interp` and `x86_64`.

**AXS-WASM-031 — Diagnostic Codes Owned or Referenced by `SPEC-86` (`spec/diagnostics.md` §3, §10, §11).**

| Code | Area | Sev | Delivering Task | Condition & Normative Rule |
|---|---|---|---|---|
| `AX_FFI_INVALID_WASM_ATTR` | `FFI` | `E` | `T674`/`T675` | `@wasm_import` placed outside an `extern` declaration or on a function with a body, `@wasm_export` placed on a non-`fn`/non-`static`, `async fn`, or `gen fn`, or empty/ill-formed `module`/`name` string (`AXS-WASM-023`) |
| `AX_VERIFY_WASM_ILLEGAL` | `VERIFY` | `E` | `T675` | Hand-constructed or deserialized WASM module/function IR in a `verify_wasm` negative test violates operand-stack typing, structured control-flow label/arity rules, index bounds, `memarg` alignment (`2^align > width`, or `!= width` for atomics), or active `TargetFeatureSet` gating (`data.rule`, `data.opcode`, `data.func`; `AXS-WASM-026`) |
| `AX_TARGET_UNKNOWN_FEATURE` | `TARGET` | `E` | `T476`/`T654`/`T674` | Unknown WASM feature name or attempt to disable mandatory WASM baseline features (`-mutable_globals`, `-sign_ext`, `-nontrapping_fptoint`) (`AXS-WASM-003`) |
| `AX_TARGET_FEATURE_CONFLICT` | `TARGET` | `E` | `T654`/`T674`/`T675` | Contradictory WASM feature/memory flags (`+atomics,-bulk_memory`, `+relaxed_simd,-simd128`, or `+atomics` without `shared` bounded max memory) (`AXS-WASM-003`) |
| `AX_TARGET_FEATURE_MISMATCH` | `TARGET` | `E` | `T476`/`T674` | Calling a `@target_feature("simd128")` / `@target_feature("atomics")` function or WASM intrinsic from a caller lacking that feature without `unsafe` (`AXS-WASM-003`) |
| `AX_TARGET_UNSUPPORTED_OP` | `TARGET` | `E` | `T655`/`T674` | `LIR` operation cannot be legally lowered on the active WASM target/feature set (`extern "interrupt"`, hardware `@naked` asm, or multi-thread atomic wait under `-atomics`) (`AXS-WASM-003`, `AXS-WASM-008`) |
| `AX_DRIVER_UNKNOWN_TARGET` | `DRIVER` | `E` | `T016`/`T654` | Unrecognized `--target <triple>` spelling (`AXS-WASM-001`) |
| `AX_DRIVER_INVALID_PROFILE` | `DRIVER` | `E` | `T512` | Unknown `--profile` value (`AXS-WASM-001`) |
| `AX_DRIVER_PROFILE_FORBIDDEN_CAP` | `DRIVER` | `E` | `T512`/`T674` | Reachable graph on `wasm32-freestanding` requires forbidden hosted capability (`os_io`, `thread`, `unwind`, or `heap_alloc` without `@global_allocator`) (`AXS-WASM-001`, `AXS-WASM-023`) |
| `AX_DRIVER_INVALID_PANIC_STRATEGY` | `DRIVER` | `E` | `T522`/`T674` | `--panic unwind` requested on `wasm32-freestanding` or `wasm32-wasi` without an active WASM unwind runtime (`AXS-WASM-024`) |
| `AX_NAME_FREESTANDING_FORBIDDEN_IMPORT` | `NAME` | `E` | `T512` | Importing hosted OS modules (`std.io`, `std.fs`, `std.net`, `std.process`, `std.thread`, `std.env`, `std.time`) on `wasm32-freestanding` (`AXS-WASM-001`) |
| `AX_TYPE_UNALIGNED_PACKED_REF` | `TYPE` | `E` | `T507` | Taking an aligned `view<T>`, `mut_view<T>`, or `*const T` / `*mut T` reference to an unaligned `@repr(packed)` field (`AXS-WASM-009`) |
| `AX_CTM_NON_CONST_STATIC_INIT` | `CTM` | `E` | `T551`/`T552` | `const`, `static`, or `@thread_local static` initialized with a runtime-only expression (`AXS-WASM-010`) |
| `AX_SEC_CAPABILITY_FORGERY` | `SEC` | `E` | `T517` | Casting/converting an integer WASM linear-memory offset or raw pointer into `view<T>` / `mut_view<T>` or `FsCap` without an explicit `unsafe` capability boundary (`AXS-WASM-006`) |
| `AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN` | `SEC` | `E` | `T517` | Ambient host/WASI I/O invoked under `--safety-profile sandbox` or `comptime` without explicit authority token (`AXS-WASM-023`) |
| `AX_CAP_CONTAINER_RELOC` | `CAP` | `E` | `T125`/`T501` | Mutating/growing `Vec<T>`, `String`, or `HashMap<K, V>` (`memory.grow` / heap realloc) while an element `view`/`mut_view` is live (`AXS-WASM-006`) |
| `AX_CONC_NOT_SEND` / `AX_CONC_NOT_SHARE` | `CONC` | `E` | `T089`/`T401` | Transferring or sharing `!Send` / `!Share` values or `externref`/`funcref` host handles across WASM worker threads (`AXS-WASM-008`, `AXS-WASM-022`) |
| `AX_UNSAFE_REQUIRED` | `UNSAFE` | `E` | `T061a`/`T501` | Calling an `@wasm_import` / `extern "C"` function, dereferencing raw pointers, or constructing views from raw pointers outside `unsafe` (`AXS-WASM-006`, `AXS-WASM-023`) |
| `AX_FFI_GENERIC_EXPORT` | `FFI` | `E` | `T503`/`T674` | `@wasm_export` or `@export` attached to a generic function with type/comptime parameters (`AXS-WASM-023`) |
| `AX_FFI_VARIADIC_NOT_EXTERN_C` | `FFI` | `E` | `T503` | Variadic `...` used outside an `extern "C"` import declaration (`AXS-WASM-019`) |
| `AX_LINK_BAD_OBJECT` / `AX_LINK_BAD_ARCHIVE` | `LINK` | `E` | `T027`/`T675` | Malformed `.wasm` object (`\0asm` header, W3C section order, LEB128, `linking` v2, post-`linking` `reloc.CODE`/`reloc.DATA` headers/entries) or malformed GNU `ar` `.a` archive (`AXS-WASM-027`, `AXS-WASM-028`) |
| `AX_LINK_ARTIFACT_TARGET_MISMATCH` | `LINK` | `E` | `T765`/`T675` | Input object/archive `.axmeta` `TargetFingerprint` conflicts with active `wasm32` target, memory sharing mode, or ABI (`AXS-WASM-001`, `AXS-WASM-028`) |
| `AX_LINK_ABI_MISMATCH` | `LINK` | `E` | `T067`/`T675` | Cross-object WASM `FuncType` signature, `SYMTAB_*` symbol kind, or import `(module, name)` signature mismatch (`AXS-WASM-028`) |
| `AX_LINK_UNDEFINED_SYMBOL` / `AX_LINK_DUPLICATE_SYMBOL` | `LINK` | `E` | `T027`/`T675` | Unresolved non-import WASM symbol or duplicate strong symbol definition across `.wasm` objects (`AXS-WASM-028`) |
| `AX_LINK_DUPLICATE_EXPORT` | `LINK` | `E` | `T751`/`T675` | Two `@wasm_export` / `@export` items resolve to the identical WASM `Export` name (`AXS-WASM-023`, `AXS-WASM-028`) |
| `AX_LINK_RELOC_OUT_OF_RANGE` | `LINK` | `E` | `T027`/`T675` | Patched `R_WASM_*` memory address or index overflows 32-bit unsigned `wasm32` range (`AXS-WASM-028`) |
| `AX_ICE_INTERNAL` | `ICE` | `E` | `T009`/`T675` | Compiler-lowered WASM module failed internal `verify_wasm` (`data.stage = "wasm_verify"`, exit code `3`; `AXS-WASM-026`) |

**AXS-WASM-032 — Canonical Positive Examples (`=` and `.` Syntax).**

```axiom
// Example 1: Hosted WASI UTF-8 greeting ("Xin chào thế giới\n" = 23 UTF-8 bytes)
// compiled with: axiomc build --target wasm32-wasi greeting.ax -o greeting.wasm
module demo.wasi_greeting

use std.io.print

@repr(C)
pub struct Ciovec {
    pub buf: *const u8,
    pub buf_len: usize,
}

extern "C" {
    @wasm_import(module = "wasi_snapshot_preview1", name = "fd_write")
    fn wasi_fd_write(fd: i32, iovs: *const Ciovec, iovs_len: usize, nwritten: *mut usize) -> i32
}

pub fn write_stdout_raw(msg: Str) -> Result<usize, i32> {
    let iov = Ciovec {
        buf: msg.as_ptr(),
        buf_len: len(msg),
    }
    let mut nwritten: usize = 0
    // `iov` and `nwritten` have their addresses taken -> allocated in the 16B-aligned
    // LinearMemory shadow-stack frame ($__stack_pointer), never in WASM locals:
    let errno = unsafe {
        wasi_fd_write(1i32, address_of(iov), 1usize, address_of_mut(nwritten))
    }
    if errno == 0i32 {
        return Result.Ok(nwritten)
    }
    return Result.Err(errno)
}

pub fn main() -> i32 {
    let greeting = "Xin chào thế giới\n"
    match write_stdout_raw(greeting) {
        Result.Ok(bytes) => {
            if bytes != 23usize {
                return 2i32
            }
            // High-level std.io routes through std.sys.wasi (fd_write on fd = 1):
            print("Xin chào thế giới\n")
            return 0i32
        }
        Result.Err(code) => return code,
    }
}
```

```axiom
// Example 2: Zero-OS-import wasm32-freestanding module with @wasm_import, @wasm_export,
// FnPtr call_indirect (table 0 slot >= 1), and structured loop + br_table dispatch.
// Compiled with: axiomc build --target wasm32-freestanding --kind dll dsp.ax -o dsp.wasm
module demo.wasm_freestanding_dsp

extern "C" {
    @wasm_import(module = "host_env", name = "on_tick")
    fn host_on_tick(step: u32)
}

fn op_add(acc: i32, x: i32) -> i32 { acc + x }
fn op_xor(acc: i32, x: i32) -> i32 { acc ^ x }

@wasm_export("run_steps")
pub extern "C" fn run_steps(op_kind: u32, limit: i32) -> i32 {
    let reducer: fn(i32, i32) -> i32 = match op_kind {
        0u32 => op_add,
        1u32 => op_xor,
        _ => op_add,
    }
    let mut acc: i32 = 0
    let mut i: i32 = 0
    loop {
        if i >= limit {
            break
        }
        acc = match i & 3i32 {
            0i32 => reducer(acc, i + 1i32),
            1i32 => reducer(acc, i * 2i32),
            2i32 => wrapping_sub(acc, i),
            _ => acc + 7i32,
        }
        unsafe { host_on_tick(i as u32) }
        i += 1i32
    }
    return acc
}

@panic_handler
fn freestanding_abort() -> never {
    loop {}
}
```

**AXS-WASM-033 — Canonical Negative Examples (`=` and `.` Syntax).**

```axiom
// Example 1: Forging a safe view<u32> from a WASM linear-memory integer offset
// (AWASM-24..25) and growing a Vec<i32> while an element view is live (AWASM-30).
module demo.wasm_bad_provenance_and_grow

use std.alloc.vec.Vec

pub fn bad_offset_forgery(raw_wasm_offset: usize) -> u32 {
    let forged: view<u32> = raw_wasm_offset as view<u32> //~ ERROR AX_SEC_CAPABILITY_FORGERY
    return *forged
}

pub fn bad_grow_while_borrowed() -> i32 {
    let mut xs = Vec<i32>.new()
    xs.push(42i32)
    let elem: view<i32> = view(xs[0usize])
    xs.push(99i32) //~ ERROR AX_CAP_CONTAINER_RELOC
    return *elem
}
```

```axiom
// Example 2: Generic @wasm_export and malformed @wasm_import with a function body.
module demo.wasm_bad_ffi_attrs

@wasm_export("id")
pub fn bad_generic_export<T>(x: T) -> T { //~ ERROR AX_FFI_GENERIC_EXPORT
    return x
}

@wasm_import(module = "env", name = "bad_body")
pub fn bad_import_with_body() -> i32 { //~ ERROR AX_FFI_INVALID_WASM_ATTR
    return 1i32
}
```

```axiom
// Example 3: Calling a +simd128 function from baseline wasm32 safe code without unsafe,
// and importing hosted std.fs under --target wasm32-freestanding.
module demo.wasm_bad_feature_and_profile

use std.fs //~ ERROR AX_NAME_FREESTANDING_FORBIDDEN_IMPORT

@target_feature("simd128")
fn dot4_simd(a: i32, b: i32) -> i32 {
    return a * b
}

pub fn caller_baseline(x: i32) -> i32 {
    return dot4_simd(x, 2i32) //~ ERROR AX_TARGET_FEATURE_MISMATCH
}
```

**AXS-WASM-034 — E16.6 Task, Invariant & Requirement Traceability (`T673`–`T676`, `INV-WASM-001`..`003`, `REQ-TGT-079`, `REQ-TGT-207`..`284`, `REQ-TGT-304`).**

| Task | Scope (`paths:` / `locks:`) | Invariant | Covered `CATALOG.md` Requirements | Governing Rules |
|---|---|---|---|---|
| `T673` | `paths`: `spec/SPEC-86-wasm32-backend.md`; `locks`: `spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md` | — (defines `INV-WASM-001`..`003`) | `REQ-TGT-079`, `REQ-TGT-207`, `REQ-TGT-208`, `REQ-TGT-209`, `REQ-TGT-210`, `REQ-TGT-211`, `REQ-TGT-212`, `REQ-TGT-213`, `REQ-TGT-214`, `REQ-TGT-215`, `REQ-TGT-216`, `REQ-TGT-217`, `REQ-TGT-218`, `REQ-TGT-219`, `REQ-TGT-220`, `REQ-TGT-221`, `REQ-TGT-222`, `REQ-TGT-223`, `REQ-TGT-224`, `REQ-TGT-225` | `AXS-WASM-001`..`034` |
| `T674` | `paths`: `compiler/target/wasm32/isel`, `compiler/abi/wasm32`, `tests/mc/wasm32_stackify`, `tests/selfhost/abi`, `tests/selfhost/isel` | `INV-WASM-001` | `REQ-TGT-231`, `REQ-TGT-232`, `REQ-TGT-233`, `REQ-TGT-234`, `REQ-TGT-235`, `REQ-TGT-236`, `REQ-TGT-237`, `REQ-TGT-238`, `REQ-TGT-239`, `REQ-TGT-240`, `REQ-TGT-241`, `REQ-TGT-242`, `REQ-TGT-243`, `REQ-TGT-244`, `REQ-TGT-254`, `REQ-TGT-255`, `REQ-TGT-256`, `REQ-TGT-257`, `REQ-TGT-258`, `REQ-TGT-259`, `REQ-TGT-304` | `AXS-WASM-001`..`004`, `AXS-WASM-009`..`024` |
| `T675` | `paths`: `compiler/target/wasm32/encode`, `compiler/obj/wasm`, `compiler/link/wasm`, `std/sys/wasi`, `tests/obj/wasm`, `tests/selfhost/encode`, `tests/selfhost/obj`, `tests/selfhost/link` | `INV-WASM-002` | `REQ-TGT-226`, `REQ-TGT-227`, `REQ-TGT-228`, `REQ-TGT-229`, `REQ-TGT-245` (with `T687`), `REQ-TGT-246` (with `T687`), `REQ-TGT-247` (with `T686`), `REQ-TGT-248`, `REQ-TGT-249`, `REQ-TGT-250`, `REQ-TGT-251`, `REQ-TGT-252`, `REQ-TGT-253`, `REQ-TGT-260`, `REQ-TGT-261`, `REQ-TGT-262`, `REQ-TGT-263`, `REQ-TGT-266`, `REQ-TGT-267`, `REQ-TGT-268`, `REQ-TGT-269`, `REQ-TGT-271` | `AXS-WASM-001`..`010`, `AXS-WASM-022`..`029` |
| `T676` | `paths`: `tests/conformance/p16/e16_6_wasm32` | `INV-WASM-003` | `REQ-TGT-264`, `REQ-TGT-265`, `REQ-TGT-274`, `REQ-TGT-275`, `REQ-TGT-276`, `REQ-TGT-277`, `REQ-TGT-278`, `REQ-TGT-279`, `REQ-TGT-280`, `REQ-TGT-281`, `REQ-TGT-283`, `REQ-TGT-284` | `AXS-WASM-001`..`034` |
| Cross-epic (`T671`/`T672`) | `std/ffi/jni`, `tests/conformance/p16/e16_5_android_aarch64_jni` (`SPEC-85`) | `INV-JNI-001`, `INV-JNI-002` | `REQ-TGT-230` (`AWASM-41`), `REQ-TGT-270` (`AWASM-81`), `REQ-TGT-272` (`AWASM-83`), `REQ-TGT-273` (`AWASM-84`), `REQ-TGT-282` (`AWASM-93`) — WASM `funcref`/`externref`/callback/WIT/FFI-safety counterparts enforced identically here | `AXS-WASM-022`, `AXS-WASM-023`, `AXS-WASM-030`, `SPEC-85` `AXS-JNI-001..017` |

| Corpus Rule Range (`0523 §155`, `0518 §151`, `0522`, `0524 §112`) | `CATALOG.md` IDs | `SPEC-86` Rule(s) |
|---|---|---|
| `0518 §151 AMACHINE-90`; `0522` header; `0523 §1` | `REQ-TGT-079`, `REQ-TGT-207`, `REQ-TGT-208` | `AXS-WASM-001`, `AXS-WASM-002`, `AXS-WASM-004`, `AXS-WASM-009`, `AXS-WASM-010`, `AXS-WASM-011`, `AXS-WASM-025`, `AXS-WASM-027` |
| `AWASM-20..27` (VM target family, LIR independence, post-opt stackify, locals, linear-memory offsets/provenance/domain, `wasm32` vs `wasm64`) | `REQ-TGT-209`..`216` | `AXS-WASM-001`, `AXS-WASM-002`, `AXS-WASM-004`, `AXS-WASM-006`, `AXS-WASM-009`, `AXS-WASM-010`, `AXS-WASM-011`, `AXS-WASM-016` |
| `AWASM-28..36` (ownership, `view`/`mut_view` capabilities, `memory.grow`, address observability, `BCE` proof, traps vs verification, atomics, `Share`, `Send`) | `REQ-TGT-217`..`225` | `AXS-WASM-004`, `AXS-WASM-006`, `AXS-WASM-007`, `AXS-WASM-008`, `AXS-WASM-010`, `AXS-WASM-017` |
| `AWASM-37..41` (WASI platform contract, browser FFI, host effect contracts, imported memory, imported resource lifetimes) | `REQ-TGT-226`..`230` | `AXS-WASM-022`, `AXS-WASM-023`, `AXS-WASM-029` |
| `AWASM-42..50` (fn refs, `call_indirect` vs `call`, closures, `async` `Future`, no WASM GC, `funcref`/`externref`, `simd128` & vector isolation) | `REQ-TGT-231`..`239` | `AXS-WASM-018`, `AXS-WASM-021`, `AXS-WASM-022` |
| `AWASM-51..55` (`CallConv.Wasm` aggregate ABI, hidden `sret`, variadics, no WASM-exception leakage, profile-governed panic lowering) | `REQ-TGT-240`..`244` | `AXS-WASM-019`, `AXS-WASM-020`, `AXS-WASM-024` |
| `AWASM-56..64` (exports as roots, explicit imports, runtime GC, removable custom sections, determinism, feature DAG, internal `verify_wasm`, no external validator) | `REQ-TGT-245`..`253` | `AXS-WASM-003`, `AXS-WASM-023`, `AXS-WASM-025`, `AXS-WASM-026`, `AXS-WASM-027`, `AXS-WASM-028` |
| `AWASM-65..70` + `0524 §112 ABACKEND-79` (backend-only structured CFG, MIR arbitrary CFG, reducible + `$irr_state` irreducible CFG structuring, SSA stackification, typed local liveness) | `REQ-TGT-254`..`259`, `REQ-TGT-304` | `AXS-WASM-011`, `AXS-WASM-012`, `AXS-WASM-013`, `AXS-WASM-014`, `AXS-WASM-015`, `AXS-WASM-016` |
| `AWASM-71..84` (host sync, non-implicit WASI caps, FFI safety, debug provenance, `--interp` semantic equivalence, target-opt invariance, `TargetFingerprint`, stripping, Component Model/WIT, callbacks, exposed addresses, foreign handles) | `REQ-TGT-260`..`273` | `AXS-WASM-001`, `AXS-WASM-004`, `AXS-WASM-008`, `AXS-WASM-016`, `AXS-WASM-022`, `AXS-WASM-023`, `AXS-WASM-028`, `AXS-WASM-029`, `AXS-WASM-030` |
| `AWASM-85..95` (`TargetBackend` conformance, native-vs-WASM agreement, physical-repr vs semantic equivalence, zero Core WASM syntax, ownership/trait/async/numeric/FFI semantic non-contamination, frontend-independent backend replaceability, `Axiom LIR` portability) | `REQ-TGT-274`..`284` | `AXS-WASM-022`, `AXS-WASM-030` |

## Sources
`0220` (`OS-ABI-001`: §1–4, §10 WASM/WASI, §16, §18, §28–39 `AOS-20..40`); `tasks/0453` (`BOOTSTRAP-194`: §194.1–44 `ATARGET-20..50`, esp. §194.36); `tasks/0518` (`BOOTSTRAP-259`: §151 `AMACHINE-90`); `tasks/0522` (`BOOTSTRAP-263`: register-vs-stack LIR independence); `tasks/0523` (`BOOTSTRAP-264`: §1–156 `AWASM-20..95`); `tasks/0524` (`BOOTSTRAP-265`: §112 `ABACKEND-79, ABACKEND-89..92`); `tasks/0784` (`BOOTSTRAP-562`: §562.5, §562.29–34, §562.77–99, §562.141–145, §562.153, §562.165, §562.174–186, §562.191–193, §562.200 `#71..86, #98, #129..130, #155..163, #174, #177`); `spec/SPEC-03-core-semantics.md`; `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-050..074, 091, 100..110`); `spec/SPEC-10-ownership-move-copy.md`; `spec/SPEC-11-capability.md`; `spec/SPEC-12-drop-raii.md`; `spec/SPEC-24-artifact-format-module-interfaces.md`; `spec/SPEC-25-pass-contracts-proof-carrying-ir.md`; `spec/SPEC-27-separate-compilation-linker-v2.md`; `spec/SPEC-30-concurrency.md`; `spec/SPEC-31-atomics.md`; `spec/SPEC-32-threads-sync.md`; `spec/SPEC-33-async.md`; `spec/SPEC-40-integers.md`; `spec/SPEC-41-floating-point.md`; `spec/SPEC-42-simd.md`; `spec/SPEC-43-simd-backend.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-51-raw-memory-volatile-mmio-layout.md`; `spec/SPEC-52-freestanding-runtime-composition.md`; `spec/SPEC-53-safety-profiles-capability-security.md`; `spec/SPEC-54-panic-unwinding.md`; `spec/SPEC-60-comptime-2-0.md`; `spec/SPEC-63-dyn-trait-vtables.md`; `spec/SPEC-71-alias-escape-promotion.md`; `spec/SPEC-72-loops-scev-bce.md`; `spec/SPEC-73-inlining-specialization-devirt.md`; `spec/SPEC-80-linux-x86-64-elf-static.md`; `spec/SPEC-81-target-desc-isa-conformance.md`; `spec/SPEC-85-android-aarch64-jni.md`; `spec/diagnostics.md`; `spec/invariants.md`.
