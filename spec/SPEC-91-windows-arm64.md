# SPEC-91 — Canonical Windows ARM64 (`aarch64-pc-windows-msvc`) ABI, `__chkstk` Probing, COFF `0xAA64`, `.pdata`/`.xdata` Unwind & PE32+ Linking Specification

- **Status:** draft (T693, 2026-11-04)
- **Owner:** `axiom-architect`
- **Consolidates:** `ADR-0003`, `ADR-0011`, `ADR-0034 §4`, `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-052`, `AXS-EXT-060..062`, `AXS-EXT-070..074`, `AXS-EXT-091`, `AXS-EXT-110`), `spec/SPEC-24-artifact-format-module-interfaces.md`, `spec/SPEC-26-windows-artifact-kinds.md`, `spec/SPEC-27-separate-compilation-linker-v2.md`, `spec/SPEC-32-threads-sync.md`, `spec/SPEC-34-executors-fibers.md`, `spec/SPEC-44-cpu-target-features-multiversioning.md`, `spec/SPEC-50-unsafe-ub-ffi.md`, `spec/SPEC-52-freestanding-runtime-composition.md`, `spec/SPEC-54-panic-unwinding.md`, `spec/SPEC-75-lto-wpo-section-gc-pgo.md`, `spec/SPEC-81-target-desc-isa-conformance.md`, `spec/SPEC-83-aarch64-linux.md`, `spec/SPEC-88-cross-compilation-platform-layer.md`, `spec/SPEC-89-artifact-library-matrix.md`, `0097 §27`, `0107 §64`, `0181`, `0185`, `0186`, `0187`, `0188`, `0193`, `tasks/0453`, `tasks/0518 §151`, `tasks/0521 §156`, `tasks/0522 §159`, `tasks/0524 §112`, `tasks/0563`
- **Covers:** `REQ-TGT-114`, `REQ-TGT-124`, `REQ-TGT-127`, `REQ-TGT-129` (and specifies the E16.12 contract for `T694`, `T695`, `T696`: `REQ-FFI-004`, `REQ-TGT-104`, `REQ-TGT-105`, `REQ-TGT-106`, `REQ-TGT-125`, `REQ-TGT-130`, `REQ-TGT-131`, `REQ-TGT-149`, `REQ-TGT-151`, `REQ-TGT-152`, `REQ-TGT-157`, `REQ-TGT-162`, `REQ-TGT-197`, `REQ-TGT-307`, `REQ-TGT-308`, `REQ-TGT-318`, `REQ-TGT-320`, `REQ-TOOL-001`)
- **Consumers:** `compiler/abi/win_arm64`, `compiler/target/aarch64/win_frame`, `compiler/obj/coff_arm64`, `compiler/link/pe_arm64`, `std/sys/windows/arm64`, `tests/obj/coff_arm64`, `tests/link/pe_arm64`, `tests/selfhost/abi`, `tests/selfhost/obj`, `tests/selfhost/link`, `tests/conformance/p16/e16_12_windows_arm64`, `T694`, `T695`, `T696`

## Tóm tắt

Tài liệu `SPEC-91` chốt đặc tả chuẩn cho đích `aarch64-windows` (`aarch64-pc-windows-msvc`) của Axiom trên nền Windows 11 ARM64, tái sử dụng tầng ISA 64 bit `Arch.AArch64` của `SPEC-83` và hạ tầng PE32+/COFF của `SPEC-26` / `SPEC-89` (Epic `E16.12`):
1. **Quy ước gọi hàm `CallConv.WinArm64` và khóa cứng thanh ghi `X18` (`TEB`) (`AXS-WA64-001`..`010`):** Giữ quy ước truyền tham số không biến thiên theo AAPCS64 (`X0..X7`, `V0..V7` cho số thực và `HFA`/`HVA`, căn chẵn cặp thanh ghi 16 byte `i128`/`u128`, ô ngăn xếp tối thiểu 8 byte, không vùng đỏ `red_zone = 0`, không `shadow_space = 0`), nhưng áp dụng bốn khác biệt đặc thù của Windows ARM64: khóa cứng `X18` làm con trỏ `TEB` (`NtCurrentTeb()`), hàm biến thiên (`...`) vô hiệu hóa hoàn toàn `V0..V7`/`HFA` để truyền mọi tham số cố định lẫn biến thiên qua `X0..X7` và ngăn xếp với `VaList = *mut u8`, phân biệt quy tắc trả về `sret` giữa kiểu C/`@repr(C)` POD (`> 16`B qua `X8`) với hàm C++ non-POD (`X0`) và phương thức thực thể C++ (`X1`), và giao thức thăm dò ngăn xếp `__chkstk` truyền `alloc_bytes >> 4` trong `X15` mà không tự trừ `SP` (bên gọi thực thi `SUB SP, SP, X15, LSL #4` sau `BL __chkstk`).
2. **Tệp đối tượng COFF `IMAGE_FILE_MACHINE_ARM64` (`0xAA64`) và định vị lại `IMAGE_REL_ARM64_*` (`AXS-WA64-011`..`017`):** Chuẩn hóa `compiler/obj/coff_arm64` sinh trực tiếp tệp `.obj` tất định (`TimeDateStamp = 0`), ánh xạ tiết đoạn (`.text`, `.rdata`, `.data`, `.bss`, `.pdata`, `.xdata`, `.tls$`, COMDAT liên kết), toàn bộ bảng 18 mã định vị lại `IMAGE_REL_ARM64_*` (`0x0000`–`0x0011` gồm `ADDR32`, `ADDR32NB`, `BRANCH26`, `PAGEBASE_REL21`, `REL21`, `PAGEOFFSET_12A`/`12L`, `SECREL`, `SECREL_LOW12A`/`HIGH12A`/`LOW12L`, `SECTION`, `ADDR64`, `BRANCH19`, `BRANCH14`, `REL32`) và thư viện tĩnh/nhập `CoffAr` (`IMPORT_OBJECT_HEADER` `Machine = 0xAA64`).
3. **Siêu dữ liệu tháo chồng SEH `.pdata` nén và `.xdata` giải nén (`AXS-WA64-018`..`024`):** Sinh tất định bản ghi hàm chạy 8 byte `IMAGE_ARM64_RUNTIME_FUNCTION_ENTRY` hỗ trợ định dạng nén trực tiếp trong `UnwindData` (`Flag = 1` hoặc `2`) cho khung chuẩn và bảng `.xdata` (`Flag = 0`) với đầy đủ tập mã tháo chồng ARM64 (`alloc_s`, `alloc_m`, `alloc_l`, `save_r19r20_x`, `save_fplr`, `save_fplr_x`, `save_regp`, `save_regp_x`, `save_reg`, `save_reg_x`, `save_lrpair`, `save_fregp`, `save_fregp_x`, `save_freg`, `save_freg_x`, `set_fp`, `add_fp`, `nop`, `end`, `end_c`, `save_next`), tương thích cả `--panic abort` lẫn `--panic unwind` (`__axiom_seh_personality`).
4. **Trình liên kết PE32+ ARM64 (`compiler/link/pe_arm64`) và tầng nền tảng `std.sys.windows.arm64` (`AXS-WA64-025`..`036`):** Liên kết trực tiếp ảnh `.exe` (`ImageBase = 0x140000000`) và `.dll` (`0x180000000`) với cờ an toàn `HIGH_ENTROPY_VA | DYNAMIC_BASE | NX_COMPAT`, sinh cầu nối nhập 12 byte dùng `X16` (`ADRP` + `LDR` + `BR`), đảo mở rộng tầm nhảy `±128 MiB`, bảng `.reloc` (`IMAGE_REL_BASED_DIR64`), sắp xếp `.pdata` tăng dần theo RVA, truy cập TLS ngầm qua `[X18, #0x58]` + `_tls_index`, hàm `__chkstk` tích hợp sẵn không cần MSVC CRT, cùng bảng ánh xạ chẩn đoán `E9100–E9119` và bất biến `INV-WARM-001`..`005`.

---

## 1. `aarch64-windows` Target Identity, `X18` TEB Reservation & `CallConv.WinArm64` ABI (`AXS-WA64-001`..`010`)

**AXS-WA64-001 — `TargetId.AArch64Windows` `TargetDesc` Record, Triple Aliases, `@cfg` Valuation & ISA Reuse (`REQ-TGT-114`, `REQ-TGT-124`).**
`compiler/target/desc` registers `aarch64-windows` (accepting `--target aarch64-windows` and vendor/ABI aliases `aarch64-pc-windows-msvc`, `arm64-pc-windows-msvc`, and `aarch64-windows-msvc`; rejecting unknown or unsupported GNU/32-bit triples such as `arm64-win32` or `aarch64-pc-windows-gnu` with `AX_DRIVER_UNKNOWN_TARGET`, exit code `2`) as an immutable `TargetDesc` record (`SPEC-81 AXS-TGTD-002..017`, `SPEC-88 AXS-XCMP-002`):
- `target_id = TargetId.AArch64Windows`, `arch = Arch.AArch64`, `os = Os.Windows`, `env = Env.Msvc`, `pointer_width_bits = 64`, `endian = Endian.Little`;
- `default_call_conv = CallConv.WinArm64` (`REQ-TGT-105`), `object_format = ObjectFormat.Coff` (`IMAGE_FILE_MACHINE_ARM64 = 0xAA64`, `--kind obj` -> `<stem>.obj`), `archive_format = ArchiveFormat.CoffAr` (`--kind lib`/`staticlib` -> `<stem>.lib`, `--kind axlib`/`rlib` -> `<stem>.axlib`), `image_format = ImageFormat.Pe32Plus` (`--kind exe` and its accepted synonym `--kind bin` -> `<stem>.exe`; `Pe32PlusDll` for `--kind dll`/`cdylib` -> `<stem>.dll` + `<stem>.lib`; `SPEC-89 AXS-ARTM-002..003`);
- `DataLayout`: `i128`/`u128` size `16` and natural alignment `16`, `stack_align = 16`, `red_zone = 0`, `shadow_space = 0`, `page_size = 4096` (`0x1000`), `CACHE_LINE_BYTES = 64`, `MIN_PAGE_SIZE_BYTES = 4096`;
- `@cfg` valuation (`SPEC-88 AXS-XCMP-014`): `target_arch = "aarch64"`, `target_os = "windows"`, `target_env = "msvc"`, `target_abi = "win_arm64"`, `target_vendor = "pc"`, `target_family = {"windows"}`, `target_pointer_width = "64"`, `target_endian = "little"`.
On `aarch64-windows`, both `extern "C"` and `extern "system"` map to `CallConv.WinArm64`; x86-specific foreign ABI strings (`extern "win64"`, `extern "sysv64"`, `extern "stdcall"`, `extern "fastcall"`, `extern "vectorcall"`) are rejected at compile time with `AX_FFI_UNKNOWN_ABI`, and x86-only hardware interrupt lowering (`extern "interrupt"` `IRETQ`, `SPEC-52 AXS-FRE-015`) or `LIR` operations lacking a legal `Arch.AArch64` / `Os.Windows` expansion fail with `AX_TARGET_UNSUPPORTED_OP` (`0181 §19`, `tasks/0521 §60, §63, §156 AARM-20, 30`). The 64-bit `Arch.AArch64` legalizer, instruction selector, `LinearScan`/`Hybrid` register allocators, `verify_mc` core checks, and 32-bit little-endian A64 instruction encoder from `SPEC-83` are shared unchanged (`REQ-TGT-114`). [0181 §19; 0193 §1–2; tasks/0453 §194.2–10; tasks/0521 §60, §63, AARM-20, 30; SPEC-52 AXS-FRE-015; SPEC-81 AXS-TGTD-002..017, 029, 032; SPEC-83 AXS-A64-001; SPEC-88 AXS-XCMP-002, 014; SPEC-89 AXS-ARTM-002..003]

**AXS-WA64-002 — Windows 11 ARM64 Baseline `TargetFeatureSet` & System Security Feature Boundary.**
On `TargetId.AArch64Windows`, the default CPU baseline (`--cpu generic`, matching Windows 11 ARM64 hardware requirements: Armv8.0-A + mandatory AdvSIMD, CRC32, and Armv8.0 Crypto extensions) enables `{ fp, neon, crc, aes, sha2 }` in `TargetFeatureSet` (`SPEC-81 AXS-TGTD-007..010`, `SPEC-83 AXS-A64-003`). Selecting `--cpu armv8.1-a` / `--cpu neoverse-n1` / `--cpu oryon-1` or `+lse` enables single-instruction LSE atomics (`CAS*`, `LDADD*`, `SWP*`; `SPEC-83 AXS-A64-035`); under the default Armv8.0-A baseline without `+lse`, atomic read-modify-write and CAS operations lower to forward-progress-preserving `LDXR`/`LDAXR` + `STXR`/`STLXR` loops with `DMB ISH` fences as required (`SPEC-83 AXS-A64-034`). Disabling mandatory hosted ABI baseline `-fp` or `-neon` is rejected with `AX_TARGET_UNKNOWN_FEATURE`; mutually contradictory flags emit `AX_TARGET_FEATURE_CONFLICT`; and calling a `@target_feature` function without an enclosing `unsafe` block or dominating runtime feature check (`IsProcessorFeaturePresent` / `std.arch.is_aarch64_feature_detected`) emits `AX_TARGET_FEATURE_MISMATCH`. Pointer Authentication (`+pauth`, `PACIBSP`/`AUTIBSP`) and Branch Target Identification (`+bti`) remain strictly target frame/codegen policies and never leak into Core pointer, `view<T>`, or `mut_view<T>` semantics (`SPEC-83 AXS-A64-003`). [tasks/0521 §64, §81–92, §149, AARM-53; SPEC-44 AXS-CPU-010..012; SPEC-81 AXS-TGTD-007..010; SPEC-83 AXS-A64-003, 034..035]

**AXS-WA64-003 — Register File Partitioning & Strict Reservation of `X18` (`TEB` Pointer) (`REQ-TGT-124`, `REQ-TGT-127`).**
`compiler/abi/win_arm64` partitions the A64 register file as follows (`0193 §3–6`, `tasks/0521 §18–22, §60, AARM-30, 33`, `SPEC-81 AXS-TGTD-017`):
- **Caller-saved (volatile):** `X0..X7` (`W0..W7`, integer argument/return), `X8` (`XR`, indirect POD return buffer pointer / volatile scratch), `X9..X15` (volatile temporaries; `X15` also carries the `__chkstk` 16-byte unit count in prologues), `X16` (`IP0`) and `X17` (`IP1`, intra-procedure-call scratch registers clobbered by import thunks, veneers, and `__chkstk`), `X30` (`LR`), `V0..V7` (`Q0..Q7`, non-variadic FP/SIMD argument/return), upper 64 bits `[127:64]` of `V8..V15`, full 128-bit `V16..V31`, and `NZCV`.
- **Callee-saved (non-volatile):** `X19..X28`, `X29` (`FP`, frame pointer), `SP` (stack pointer), and the low 64 bits **`D8..D15`** of `V8..V15` (functions using `Q8..Q15` 128-bit SIMD values need only save/restore `D8..D15`, while callers cannot assume bits `[127:64]` of `V8..V15` survive calls).
- **Strictly reserved platform register `X18` (`TEB`):** Windows ARM64 user mode dedicates `X18` permanently to the current OS thread's `NT_TIB64` / Thread Environment Block (`TEB`, `NtCurrentTeb()`). `X18` is marked `RegRole.Reserved` and excluded from `allocatable_mask`, `caller_saved_mask`, `callee_saved_mask`, and scratch sets. User code, register allocation, stack spilling, import thunks, veneers, and fiber switches **must never** write, modify, spill, or allocate `X18`/`W18`. Controlled read-only `LDR Xd, [X18, #imm]` instructions are permitted **solely** in compiler-lowered implicit TLS (`LDR Xn, [X18, #0x58]`, `AXS-WA64-030`), hosted `__chkstk` `StackLimit` inspection (`LDR X17, [X18, #0x10]`, `AXS-WA64-031`), and `std.sys.windows.arm64` TEB intrinsics (`AXS-WA64-032`). Any other Machine IR write or allocation of `X18`/`W18` is rejected by `verify_mc` (`AX_VERIFY_MC_ILLEGAL` on verifier inputs; `AX_ICE_INTERNAL` if compiler-generated). [0193 §5–6; tasks/0521 §60, AARM-30, 33; SPEC-81 AXS-TGTD-017]

**AXS-WA64-004 — Non-Variadic Parameter Classification (`CallConv.WinArm64`) (`REQ-TGT-124`, `REQ-TGT-125`, `REQ-TGT-131`).**
For **non-variadic** functions, `compiler/abi/win_arm64` classifies parameters left-to-right using state `(NGRN = 0, NSRN = 0, NSAA = 0)` matching AAPCS64 (`SPEC-83 AXS-A64-013..017`) rather than Apple Darwin packing (`SPEC-84 AXS-MACHO-006`):
1. **Integer, pointer, and capability scalars (`<= 64` bits):** `bool`, `i8..i64`, `u8..u64`, `isize`, `usize`, `char`, raw pointers, single-word `view<T>`/`mut_view<T>`, and `fn` pointers consume `X[NGRN]` while `NGRN < 8`, else an **8-byte stack slot** at `[SP + NSAA]` (`NSAA += 8`). Axiom callers zero-extend `bool`/`u8`/`u16` and sign-extend `i8`/`i16` to 32 bits in `W0..W7`, while Axiom callees on `extern "C"` / `extern "system"` boundaries explicitly mask/extend narrow incoming registers (`UXTB`/`SXTB`/`UXTH`/`SXTH`) because foreign MSVC callers leave upper bits `[width..32)` unspecified.
2. **128-bit integers (`i128`, `u128`) & 16-byte-aligned `<= 16`-byte composites:** Natural alignment is `16` bytes (`SPEC-81 AXS-TGTD-005`). If `NGRN` is odd, `NGRN` rounds up to the next **even** register (`NGRN = (NGRN + 1) & ~1`, so `(u64, u128)` occupies `X0` and `X2:X3`, skipping `X1`); if `NGRN <= 6`, the value passes in `(X[NGRN], X[NGRN + 1])` (low 64 bits in `X[NGRN]`) and `NGRN += 2`; otherwise `NGRN = 8`, `NSAA = align_up(NSAA, 16)`, and the value occupies `[SP + NSAA .. SP + NSAA + 16)`. No parameter is ever split half in `X7` and half on the stack.
3. **Floating-point, SIMD, and `HFA`/`HVA` aggregates:** `f32` (`Sn`), `f64` (`Dn`), 64/128-bit vectors (`Dn`/`Qn`), and 1-to-4-element Homogeneous Floating-point or Short-Vector Aggregates (`HFA` of uniform `f32` or `f64`; `HVA` of uniform 8B or 16B vectors; empty ZST fields ignored) consume `k` consecutive registers `V[NSRN .. NSRN + k - 1]` if `NSRN + k <= 8`; otherwise `NSRN = 8` and the entire argument spills to `[SP + align_up(NSAA, max(8, align_of(T)))]` (`NSAA += align_up(size_of(T), 8)`).
4. **Non-`HFA`/`HVA` composites & 2-word fat views:** Zero-sized types (`()`, `[0]T`) consume zero registers and zero stack bytes. Non-`HFA`/`HVA` composites of size `1..=8` bytes pass in 1 GPR (`X[NGRN]`) or an 8-byte stack slot; size `9..=16` bytes (including 2-word `Str`, `view<[T]>`, `mut_view<[T]>`, `view<dyn Trait>`) pass in 2 consecutive GPRs `(X[NGRN], X[NGRN + 1])` when `NGRN <= 6` (even-aligned only when `align_of(T) == 16`), else `NGRN = 8` and pass on the stack (`8`-byte aligned, `16`-byte aligned when `align_of(T) == 16`). Non-`HFA`/`HVA` composites with `size > 16` bytes are copied by the caller into 16-byte-aligned caller temporary memory and passed **by 8-byte pointer** in `X[NGRN]` (if `NGRN < 8`) or an 8-byte stack slot (`[SP + NSAA]`), isolating caller places from callee mutations (`SPEC-83 AXS-A64-015`). Non-FFI-safe parameter types on `extern "C"` / `extern "system"` signatures are rejected with `AX_FFI_BAD_TYPE` (`SPEC-50 AXS-UNS-033`). [0193 §5; tasks/0521 §43–48, §60, AARM-30..31, 37; SPEC-50 AXS-UNS-033; SPEC-83 AXS-A64-013..017]

**AXS-WA64-005 — Return-Value Rules: POD / `@repr(C)` Aggregates (`X8`) vs MSVC C++ Non-POD (`X0`) & Instance-Method (`X1`) Interop (`REQ-TGT-124`, `REQ-TGT-125`).**
Windows ARM64 distinguishes three ABI return conventions across C/Axiom POD types and foreign MSVC C++ signatures:
1. **Standard C, `extern "system"`, `@repr(C)` POD, and Axiom `CallConv.WinArm64` functions:**
   - Unit `()` / ZSTs return nothing; `never` functions do not return.
   - Integer/pointer scalars `<= 64` bits return in `X0`/`W0`; `i128`/`u128` return in `X0:X1` (low 64 bits in `X0`).
   - `f32`/`f64`/vectors return in `V0` (`S0`/`D0`/`Q0`), and 1-to-4-element `HFA`/`HVA` structs return in `V0..V[k-1]`.
   - Non-`HFA`/`HVA` POD composites of `1..=8` bytes return in `X0`; `9..=16` bytes (including 2-word `Str`/slice views) return in `X0:X1`.
   - Non-`HFA`/`HVA` POD composites with `size > 16` bytes return indirectly via a caller-allocated 16-byte-aligned buffer pointer passed in **`X8` (`XR`)**: `X8` does **not** consume `X0..X7` parameter registers, `X8` is volatile across subcalls, and the callee is not required to copy `X8` into `X0` before `RET`.
2. **Foreign MSVC C++ non-POD / non-C++14-aggregate free & static functions:** In the Microsoft ARM64 C++ ABI, any free or `static` function returning a C++ type that is *not* a C++14 aggregate with trivial copy/move/destructor (e.g., has a user-declared constructor, destructor, non-trivial copy/move constructor, private/protected non-static data member, base class, or `virtual` method) — regardless of byte size (`<= 16` bytes included) — passes the hidden return buffer pointer in **`X0`** (shifting explicit integer parameters right starting at `X1`) and returns that buffer pointer in **`X0`**.
3. **Foreign MSVC C++ non-static instance member functions returning any user-defined struct/class:** Any C++ instance method returning a user-defined aggregate/struct/class by value — **even a trivial `<= 16`-byte POD or `HFA` struct** — passes `this` in **`X0`**, passes the hidden return buffer pointer in **`X1`** (shifting explicit integer parameters to `X2..X7`), and returns the buffer pointer in **`X0`**. Because Axiom's FFI boundary targets C ABI (`extern "C"` / `extern "system"`, `SPEC-50 AXS-UNS-031..033`, rejecting non-FFI-safe return types with `AX_FFI_BAD_TYPE`), foreign C++ non-POD functions and instance methods are bound either via C POD wrapper shims or explicit raw-pointer signatures (`fn(this_ptr: *mut Holder, sret_out: *mut Ret, ...) -> *mut Ret`). [tasks/0521 §44–47, §60, §144–145, AARM-30..31; SPEC-50 AXS-UNS-031..033; SPEC-83 AXS-A64-018]

**AXS-WA64-006 — Windows ARM64 Variadic Calling Convention (`extern "C" fn(..., ...)` & `std.ffi.VaList`) (`REQ-TGT-124`, `T694`, `T696`).**
Windows ARM64 variadic functions (`extern "C" fn(fixed..., ...)`; declaring `...` outside an `extern "C"` signature emits `AX_FFI_VARIADIC_NOT_EXTERN_C`, and non-FFI-safe variadic argument types emit `AX_FFI_BAD_TYPE` per `SPEC-50 AXS-UNS-032..033`) diverge fundamentally from both Linux AAPCS64 (`SPEC-83 AXS-A64-022`) and Apple Darwin ARM64 (`SPEC-84 AXS-MACHO-007`):
1. **Floating-point/SIMD argument registers `V0..V7` are NEVER used in a variadic call (`NSRN` disabled for the entire call):** Every argument — **both named fixed parameters before `...` and anonymous variadic arguments after `...`** — is assigned exclusively to GPRs `X0..X7` (`NGRN = 0..7`) and 8-byte-aligned stack slots (`[SP + NSAA]`). A named `f64` parameter passes bit-copied in `X[NGRN]` (`FMOV Xn, Dm`); a named `f32` parameter passes bit-copied in `W[NGRN]` (`FMOV Wn, Sm`); anonymous `f32` arguments undergo C default variadic promotion to `f64` (`FCVT Dm, Sm`) and pass in `X[NGRN]` or an 8-byte stack slot; narrow integers (`bool`, `i8`, `u8`, `i16`, `u16`) promote to 32-bit `i32`/`u32` in `W[NGRN]` or an 8-byte stack slot.
2. **`HFA` / `HVA` classification is completely disabled on variadic signatures:** On any variadic call, `HFA` and `HVA` structs are treated as ordinary non-homogeneous composites: composites of `1..=8` bytes (e.g., `struct { a: f32, b: f32 }`) pack into 1 GPR `X[NGRN]` or 8-byte stack slot; composites of `9..=16` bytes pack into 2 GPRs or stack; and composites `> 16` bytes (including a 4-`f64` 32-byte `HFA`!) are copied into caller temporary stack space and passed **by 8-byte pointer** in `X[NGRN]` or an 8-byte stack slot.
3. **Single-pointer `std.ffi.VaList` & contiguous GPR homing:** On `aarch64-windows`, `std.ffi.VaList` (`va_list`) is `@repr(transparent) pub struct VaList { ptr: *mut u8 }` (`size = 8`, `align = 8`). When an Axiom or C variadic callee takes `VaList`, its prologue allocates `(8 - k) * 8` bytes at the **top** of its stack frame immediately below `[caller_SP + 0]` (where `k` is the number of `X0..X7` slots consumed by fixed parameters), stores `X[k]..X7` contiguously via `STP`/`STR`, and sets `va_list.ptr` to the address of homed `X[k]` (or `[caller_SP + 0]` when `k == 8`) so `va_arg` steps linearly across homed GPRs and caller stack slots. [tasks/0453 §194.18; tasks/0521 §60, §151, AARM-30; SPEC-50 AXS-UNS-032]

**AXS-WA64-007 — Zero Red Zone (`red_zone = 0`), Zero Shadow Space (`shadow_space = 0`) & Hardware 16-Byte `SP` Alignment (`REQ-TGT-129`, `REQ-TGT-130`, `REQ-TGT-131`).**
1. **No red zone (`red_zone = 0`):** Windows ARM64 asynchronous APC delivery, SEH unwinding, and kernel/debugger context captures may write immediately below `SP` at any instruction boundary. Neither hosted nor freestanding functions may ever read or write `[SP - offset]` before decrementing `SP` (`REQ-TGT-130`).
2. **No caller shadow/home space (`shadow_space = 0`):** Unlike `x86_64-windows` (`0181 §3`, `32` bytes), `CallConv.WinArm64` callers reserve **zero** shadow space for `X0..X7`; the first spilled stack argument always starts at `[SP + 0]`.
3. **Mandatory 16-byte `SP` alignment (`stack_align = 16`):** `SP % 16 == 0` holds upon function entry (no return address is pushed by `BL`), at every outgoing `BL`/`BLR`, and at every instruction using `SP` as a base register (avoiding `PSTATE` `SP` alignment faults; `REQ-TGT-131`). [0181 §3–4; 0193 §7–8; tasks/0521 §54, §59, AARM-35..37; SPEC-81 AXS-TGTD-005, 011]

**AXS-WA64-008 — Canonical Windows ARM64 Stack Frame Layout & `X29`/`X30` Frame Chaining (`REQ-TGT-127`, `REQ-TGT-129`, `T694`).**
`compiler/target/aarch64/win_frame` lays out each stack-allocating function frame (16-byte aligned total `frame_size`) from high to low memory so that prologues and epilogues map 1-to-1 onto Windows ARM64 packed `.pdata` or `.xdata` unwind records (`0188 §2, §27–31`, `0193 §8, §18`, `tasks/0521 §54–58`):
```text
High Address: [caller_SP + NSAA]   Incoming spilled arguments (8B-aligned slots, 16B for align-16)
              [caller_SP - H_sz]   Optional variadic X[k]..X7 homed save area (contiguous with caller_SP)
              [saved Int / FP]     Callee-saved X19..X28 (8B each) and D8..D15 (8B each, 8B-aligned)
              [X29, X30]           16B frame record (X29 points directly here: [X29]=prev_FP, [X29+8]=LR)
              [Locals & Spills]    MirLocal slots, RA spills, and >16B outgoing composite copies
Low Address:  [SP + 0]             Outgoing call stack arguments (SP % 16 == 0)
```
Pure leaf functions that require zero stack slots and modify neither `X30` nor `X19..X28`/`D8..D15` allocate zero stack (`frame_size = 0`) and omit `.pdata`/`.xdata` entries (`PC` unwinds directly via `X30`). Non-leaf functions establish the `[X29, X30]` frame record (`STP X29, X30, ...` + `MOV X29, SP` or `ADD X29, SP, #fp_off`); functions with dynamic stack sizes restore `SP` from `X29` (`MOV SP, X29` / `SUB SP, X29, #fp_off`, `.xdata` `set_fp` / `add_fp`) in the epilogue. [0188 §2, §27–31; 0193 §8, §18; tasks/0521 §54–58, AARM-33, 35]

**AXS-WA64-009 — `__chkstk` Stack Probing Protocol (`X15` 16-Byte Units & Caller `SP` Subtraction) (`ADR-0003`, `REQ-TGT-129`, `T694`, `T695`, `T696`).**
Windows ARM64 protects thread stacks with a 4 KiB (`0x1000`) `PAGE_GUARD` page at `NT_TIB64.StackLimit` (`[X18, #0x10]`). Whenever a function's stack allocation `alloc_bytes >= 4096` bytes (after any small initial register-save pre-decrement `<= 512`B), `compiler/target/aarch64/win_frame` MUST emit the Windows ARM64 `__chkstk` protocol (`ADR-0003`, `0188 §11–12, §35`, `T694`):
1. **Caller loads `X15 = alloc_bytes >> 4`:** `alloc_bytes` is a multiple of `16`; the prologue materializes `units = alloc_bytes / 16` into `X15` via `MOVZ X15, #(units & 0xFFFF)` (+ `MOVK X15, #(units >> 16), LSL #16` when `alloc_bytes >= 1 MiB`).
2. **Caller invokes `BL __chkstk` (`IMAGE_REL_ARM64_BRANCH26`):** `__chkstk` probes every 4 KiB page between current `SP` and `SP - (X15 << 4)` downward in order **without modifying `SP`**, preserving `X0..X8`, `X15`, `X18`, `X19..X29`, `V0..V7`, and `D8..D15`, and clobbering **only `X16`, `X17`, `X30` (`LR`), and `NZCV`** (`X30` must therefore be saved *before* `BL __chkstk`, e.g., in an initial `<= 512`B register-save area!).
3. **Caller decrements `SP` after `BL __chkstk`:** Immediately after `BL __chkstk` returns, the caller executes the extended-register subtraction **`SUB SP, SP, X15, LSL #4`** (exact 32-bit A64 encoding `0xCB2F73FF`, `SUB SP, SP, X15, UXTX #4`).
4. **SEH `.xdata` correspondence:** In `.xdata`, `MOVZ`/`MOVK X15` and `BL __chkstk` each emit `nop` (`0xE3`) because they do not alter `SP` or non-volatile registers, while `SUB SP, SP, X15, LSL #4` emits `alloc_m` (`alloc_bytes <= 32752`) or `alloc_l` (`alloc_bytes >= 32768`). [ADR-0003; 0188 §11–12, §35, AUNW-27]

**AXS-WA64-010 — Undecorated COFF Symbol Naming & Backend Semantic Transparency (`REQ-TGT-114`, `REQ-TGT-124`).**
Unlike Darwin Mach-O (`_foo`, `SPEC-84 AXS-MACHO-010`) or 32-bit x86 `stdcall` (`_foo@N`), 64-bit Windows ARM64 COFF uses **zero leading-underscore decoration**: C/Win32 symbols (`mainCRTStartup`, `ExitProcess`, `WriteFile`, `__chkstk`, `_tls_index`, `_tls_used`, `__imp_ExitProcess`) and mangled Axiom `_AX...` symbols serialize verbatim into COFF symbol/string tables, `.idata`, and `.edata` (`0185 §10`, `0186 §4`; linkage modes unsupported by PE/COFF emit `AX_TARGET_UNSUPPORTED_OP`). `CallConv.WinArm64`, `X18` reservation, and `__chkstk` frame lowering are purely backend responsibilities (`REQ-TGT-114`): they preserve Core ownership, `view<T>`/`mut_view<T>` aliasing, deterministic `Drop`, and panic containment identically to `x86_64-windows` and `--interp` (`SPEC-81 AXS-TGTD-019..021`). [0185 §10; 0186 §4; tasks/0521 §112–115, §156 AARM-20, 30, 63; SPEC-81 AXS-TGTD-019..021, 029]

---

## 2. COFF `IMAGE_FILE_MACHINE_ARM64` (`0xAA64`) Object Writer, Relocations & `CoffAr` (`AXS-WA64-011`..`017`)

**AXS-WA64-011 — `compiler/obj/coff_arm64` Layering, 20-Byte `IMAGE_FILE_HEADER` (`0xAA64`) & Determinism (`REQ-TOOL-001`, `REQ-TGT-106`, `REQ-TGT-151`, `T694`).**
`compiler/obj/coff_arm64` serializes the target-neutral `ObjectArtifact` (`SPEC-24 AXS-ART-020..023`, `0097 §27`, `0185 §1–2, §20–21`, `tasks/0521 §102–103, AARM-57`) directly into Microsoft COFF `.obj` bytes without invoking an external assembler (`llvm-mc` / `armasm64.exe`; `REQ-TOOL-001`) and without raw host-memory struct dumps (`write_u16_le`, `write_u32_le`). Every ARM64 `.obj` begins at offset `0` with a 20-byte little-endian `IMAGE_FILE_HEADER`:
- `+0` `Machine: u16 = IMAGE_FILE_MACHINE_ARM64 (0xAA64)` (ingesting a COFF `.obj` with `Machine != 0xAA64` fails with `AX_LINK_ARTIFACT_TARGET_MISMATCH`; truncated headers or out-of-bounds section/symbol/string tables fail with `AX_LINK_BAD_OBJECT`);
- `+2` `NumberOfSections: u16` (1-based section table immediately following at `+20`);
- `+4` `TimeDateStamp: u32 = 0` (always zero for reproducible builds; `INV-DET-001`, `REQ-TGT-106`);
- `+8` `PointerToSymbolTable: u32` (`0` only when `NumberOfSymbols == 0`);
- `+12` `NumberOfSymbols: u32` (total 18-byte symbol + auxiliary slots);
- `+16` `SizeOfOptionalHeader: u16 = 0`; `+18` `Characteristics: u16 = 0`.
Every emitted `.obj` defines the standard COFF absolute feature symbol `@feat.00` (`SectionNumber = IMAGE_SYM_ABSOLUTE (-1)`, `StorageClass = IMAGE_SYM_CLASS_STATIC (3)`, `Value = 0`) for full `link.exe` / `lld-link` interoperability. [0097 §27; 0185 §1–2, §20–21; tasks/0521 §102–103, AARM-57; SPEC-24 AXS-ART-020..023]

**AXS-WA64-012 — COFF `0xAA64` Section Table, `IMAGE_SCN_*` Characteristics & Associative COMDAT (`0185 §3–9, §19`, `T694`).**
Each 40-byte `IMAGE_SECTION_HEADER` maps semantic sections to canonical COFF names and `Characteristics` (section names `> 8` UTF-8 bytes encode `"/<decimal_strtab_offset>"`):

| Section | Purpose | `Characteristics` (`IMAGE_SCN_*`) | Default Alignment |
|---|---|---|---|
| `.text` (`$mn`) | 32-bit A64 machine code | `CNT_CODE (0x20) \| MEM_EXECUTE (0x20000000) \| MEM_READ (0x40000000)` | `ALIGN_16BYTES (0x00500000)` (min 4B) |
| `.rdata` | Read-only constants, UTF-8/UTF-16 literals, vtables | `CNT_INITIALIZED_DATA (0x40) \| MEM_READ (0x40000000)` | `max(4, align_of(T))` (`ALIGN_*`) |
| `.data` | Mutable initialized `static` storage | `CNT_INITIALIZED_DATA (0x40) \| MEM_READ (0x40000000) \| MEM_WRITE (0x80000000)` | `max(4, align_of(T))` |
| `.bss` | Zero-initialized mutable `static` storage (`PointerToRawData = 0`) | `CNT_UNINITIALIZED_DATA (0x80) \| MEM_READ (0x40000000) \| MEM_WRITE (0x80000000)` | `max(4, align_of(T))` |
| `.pdata` | 8-byte `IMAGE_ARM64_RUNTIME_FUNCTION_ENTRY` records | `CNT_INITIALIZED_DATA (0x40) \| MEM_READ (0x40000000)` | `ALIGN_4BYTES (0x00300000)` |
| `.xdata` | Unpacked ARM64 unwind headers, epilog scopes & opcodes | `CNT_INITIALIZED_DATA (0x40) \| MEM_READ (0x40000000)` | `ALIGN_4BYTES (0x00300000)` |
| `.tls$` | `@thread_local static` initializers (`SPEC-32 AXS-SYNC-022`) | `CNT_INITIALIZED_DATA (0x40) \| MEM_READ (0x40000000) \| MEM_WRITE (0x80000000)` | `max(4, align_of(T))` |
| `.axmeta` / `.axmir` / `.axlto` | Embedded Axiom interface, `Verified MIR` & LTO payloads (`"AXMETA01"`, `"AXMIR001"`, `"AXLTO001"`; `VirtualSize = 0`, stripped from final `.exe`/`.dll`) | `LNK_INFO (0x00000200) \| MEM_DISCARDABLE (0x02000000) \| MEM_READ (0x40000000)` (`0x42000200`) | None (`0`; pointer-free container) |

Embedded non-allocatable `.axmeta`, `.axmir`, and `.axlto` sections use `Characteristics = IMAGE_SCN_LNK_INFO | IMAGE_SCN_MEM_DISCARDABLE | IMAGE_SCN_MEM_READ` (`0x42000200`, `VirtualSize = 0`) per `SPEC-24 AXS-ART-021` and `SPEC-89 AXS-ARTM-028`, remain preserved inside `.obj` and static `.lib`/`.axlib` archives for LTO and cross-module verification, and are stripped `100%` from final `.exe` and `.dll` images per `SPEC-24 AXS-ART-022` and `SPEC-89 AXS-ARTM-029`. When per-function section splitting / COMDAT (`IMAGE_SCN_LNK_COMDAT = 0x00001000`) is emitted for generic monomorphizations or `--gc-sections` (`SPEC-27`, `SPEC-75 AXS-LTO-020`), each function's `.pdata` and `.xdata` contributions use `Selection = IMAGE_COMDAT_SELECT_ASSOCIATIVE (5)` pointing to that function's `.text` section number so dead-stripping a function automatically discards its unwind entries without leaving dangling `.pdata` RVAs (`AX_LINK_BAD_OBJECT` on invalid associative COMDAT section indices). If a single section requires `>= 65535` relocations, `NumberOfRelocations` is set to `0xFFFF`, `IMAGE_SCN_LNK_NRELOC_OVFL (0x01000000)` is set, and the first 10-byte relocation record stores the true 32-bit count in `VirtualAddress`. [0185 §3–9, §19; SPEC-24 AXS-ART-021..022; SPEC-32 AXS-SYNC-022..023; SPEC-75 AXS-LTO-002..003, 020; SPEC-89 AXS-ARTM-028..029]

**AXS-WA64-013 — Complete `IMAGE_REL_ARM64_*` (`0x0000`–`0x0011`) Relocation Table & Patching Formulas (`REQ-TGT-149`, `T694`, `T695`).**
Each COFF relocation entry is a packed 10-byte little-endian record `IMAGE_RELOCATION { VirtualAddress: u32, SymbolTableIndex: u32, Type: u16 }` (`VirtualAddress` = byte offset within the section; inline addend `A` is read from the target field/instruction prior to patching). `compiler/obj/coff_arm64` and `compiler/link/pe_arm64` implement the Microsoft ARM64 COFF relocation set (`P` = target slot/instruction VA, `S` = resolved symbol VA, `ImageBase` = PE32+ image base, `SecBase(S)` = start VA of `S`'s merged output section):

| Code | Name | Target Slot / Instruction | Formula & Signed/Unsigned Range (`AX_LINK_RELOC_OUT_OF_RANGE` on overflow) |
|---|---|---|---|
| `0x0000` | `IMAGE_REL_ARM64_ABSOLUTE` | Ignored / alignment pad | No-op |
| `0x0001` | `IMAGE_REL_ARM64_ADDR32` | 32-bit word (`u32`) | `(S + A)` in `[0, 2^32 - 1]` (forbidden in `.text` under ASLR: `AX_LINK_TEXTREL_FORBIDDEN`) |
| `0x0002` | `IMAGE_REL_ARM64_ADDR32NB` | 32-bit RVA word (`.pdata`, `.xdata`, `.edata`) | `(S + A) - ImageBase` in `[0, 2^31 - 1]` |
| `0x0003` | `IMAGE_REL_ARM64_BRANCH26` | `B` / `BL` (`imm26` `[25:0]`) | `((S + A) - P) >> 2`, 4B-aligned, `[-128 MiB, +128 MiB - 4]`; linker emits veneer if out of range (`AXS-WA64-027`) |
| `0x0004` | `IMAGE_REL_ARM64_PAGEBASE_REL21` | `ADRP` (`immhi` `[23:5]`, `immlo` `[30:29]`) | `(((S + A) & ~0xFFF) - (P & ~0xFFF)) >> 12`, signed 21-bit (`±4 GiB`) |
| `0x0005` | `IMAGE_REL_ARM64_REL21` | `ADR` (`immhi` `[23:5]`, `immlo` `[30:29]`) | `(S + A) - P`, signed 21-bit (`±1 MiB`) |
| `0x0006` | `IMAGE_REL_ARM64_PAGEOFFSET_12A` | `ADD` imm (`imm12` `[21:10]`, `sh = 0`) | `(S + A) & 0xFFF`, unsigned 12-bit (`0..4095`) |
| `0x0007` | `IMAGE_REL_ARM64_PAGEOFFSET_12L` | `LDR`/`STR` unsigned imm (`imm12` `[21:10]`) | `((S + A) & 0xFFF) >> scale` (`scale` $\in \{0,1,2,3,4\}$ for 1/2/4/8/16B access; `((S + A) & ((1 << scale) - 1)) == 0`) |
| `0x0008` | `IMAGE_REL_ARM64_SECREL` | 32-bit section offset (`.tls`, debug) | `(S + A) - SecBase(S)` in `[0, 2^32 - 1]` |
| `0x0009` | `IMAGE_REL_ARM64_SECREL_LOW12A` | `ADD` imm (`imm12` `[21:10]`, `sh = 0`) | `((S + A) - SecBase(S)) & 0xFFF` (`0..4095`) |
| `0x000A` | `IMAGE_REL_ARM64_SECREL_HIGH12A` | `ADD` imm (`imm12` `[21:10]`, `sh = 1` bit 22) | `(((S + A) - SecBase(S)) >> 12) & 0xFFF`; verifies `((S + A) - SecBase(S)) < 0x100_0000` (`16 MiB`) |
| `0x000B` | `IMAGE_REL_ARM64_SECREL_LOW12L` | `LDR`/`STR` unsigned imm (`imm12` `[21:10]`) | `(((S + A) - SecBase(S)) & 0xFFF) >> scale` (aligned to `1 << scale`) |
| `0x000C` | `IMAGE_REL_ARM64_TOKEN` | Managed CLR token | Rejected in native Axiom COFF inputs (`AX_LINK_BAD_OBJECT`) |
| `0x000D` | `IMAGE_REL_ARM64_SECTION` | 16-bit section index (`u16`) | 1-based PE output section index of `S` |
| `0x000E` | `IMAGE_REL_ARM64_ADDR64` | 64-bit pointer (`u64` in `.rdata`/`.data`) | `S + A`; records `IMAGE_REL_BASED_DIR64 (10)` in `.reloc` (`AXS-WA64-029`; forbidden in `.text`) |
| `0x000F` | `IMAGE_REL_ARM64_BRANCH19` | `B.cond` / `CBZ` / `CBNZ` (`imm19` `[23:5]`) | `((S + A) - P) >> 2`, 4B-aligned, `[-1 MiB, +1 MiB - 4]` |
| `0x0010` | `IMAGE_REL_ARM64_BRANCH14` | `TBZ` / `TBNZ` (`imm14` `[18:5]`) | `((S + A) - P) >> 2`, 4B-aligned, `[-32 KiB, +32 KiB - 4]` |
| `0x0011` | `IMAGE_REL_ARM64_REL32` | 32-bit PC-relative word (`i32` jump/lookup table) | `(S + A) - P` in `[-2^31, 2^31 - 1]` |

Any unknown relocation code `> 0x0011` or `VirtualAddress` extending past `SizeOfRawData` is rejected with `AX_LINK_BAD_OBJECT` (`REQ-TGT-149`). [0185 §15–18, §48; 0193 §23–24; tasks/0521 §99, AARM-55]

**AXS-WA64-014 — Canonical A64 Code-Generation Relocation Sequences (`0193 §24`, `tasks/0521 §78–80`, `T694`).**
`compiler/target/aarch64` lowers symbolic references on `aarch64-windows` to pure PC-relative instruction sequences with zero text relocations:
1. **Local/external `static` or function address:** `ADRP Xd, sym` (`PAGEBASE_REL21`) + `ADD Xd, Xd, #:lo12:sym` (`PAGEOFFSET_12A`); single-load folding emits `ADRP Xd, sym` + `LDR Wt/Xt/Dt/Qt, [Xd, #:lo12:sym]` (`PAGEOFFSET_12L`) whenever `(offset & ((1 << scale) - 1)) == 0`.
2. **Direct call / tail-call:** `BL callee` / `B callee` (`BRANCH26`, seamlessly targeting either a local/cross-object COFF definition or a linker-synthesized 12-byte DLL import thunk per `AXS-WA64-026`).
3. **Explicit `__imp_<sym>` DLL import indirection:** `ADRP X16, __imp_sym` (`PAGEBASE_REL21`) + `LDR X16, [X16, #:lo12:__imp_sym]` (`PAGEOFFSET_12L`) + `BLR X16` (for `@dllimport` calls) or subsequent `LDR`/`STR` through `X16` (for imported DLL data variables).
4. **Implicit `@thread_local` address:** `LDR X9, [X18, #0x58]` + `ADRP X8, _tls_index` + `LDR W8, [X8, #:lo12:_tls_index]` + `LDR X8, [X9, X8, LSL #3]` + `ADD X8, X8, #:secrel_hi12:sym` (`SECREL_HIGH12A`) + `ADD Xd, X8, #:secrel_lo12:sym` (`SECREL_LOW12A`, or `SECREL_LOW12L` for direct load/store; `AXS-WA64-030`). [0187 §18–23; 0193 §24; tasks/0521 §78–80]

**AXS-WA64-015 — 18-Byte COFF Symbol Table, Storage Classes & String Table (`0185 §10–14`, `T694`).**
Each COFF symbol slot is 18 bytes (`Name: [8]u8` inline or `{ Zeroes = 0u32, Offset: u32 }` into the 4-byte-prefixed UTF-8 string table immediately following the symbol table; `Value: u32`; `SectionNumber: i16`; `Type: u16` — `0x0020` `IMAGE_SYM_DTYPE_FUNCTION << 4` for functions, `0x0000` for data/labels; `StorageClass: u8`; `NumberOfAuxSymbols: u8`):
- Section headers emit a static section symbol (`StorageClass = IMAGE_SYM_CLASS_STATIC (3)`, `NumberOfAuxSymbols = 1`) followed by one 18-byte `IMAGE_AUX_SYMBOL_SECTION` (`Length`, `NumberOfRelocations`, `NumberOfLinenumbers`, `CheckSum`, `Number`, `Selection`).
- Module-private items use `IMAGE_SYM_CLASS_STATIC (3)`; `pub`, `@export`, `@no_mangle`, and undefined `extern` symbols use `IMAGE_SYM_CLASS_EXTERNAL (2)` (`SectionNumber = IMAGE_SYM_UNDEFINED (0)` for imports); weak externals use `IMAGE_SYM_CLASS_WEAK_EXTERNAL (105)` + 1 aux record. Symbols are emitted in deterministic declaration order (`0185 §10–14`). [0185 §10–14; SPEC-27 AXS-LNK-010]

**AXS-WA64-016 — `CoffAr` Static Libraries (`.lib`) & `0xAA64` Short-Import Libraries (`REQ-TOOL-001`, `SPEC-26`, `SPEC-89`, `T694`, `T695`).**
- **Static libraries (`--kind lib`/`staticlib` -> `<stem>.lib`):** `compiler/obj/archive_matrix` (`0097 §27`, `SPEC-26 AXS-WLIB-010..012`, `SPEC-89 AXS-ARTM-008`) packages `0xAA64` `.obj` members directly into a deterministic `CoffAr` `"!<arch>\n"` archive with zeroed timestamps/UIDs/GIDs, 1st/2nd `/` COFF symbol directories, and `//` longnames without `lib.exe` / `llvm-lib` (`REQ-TOOL-001`).
- **DLL import libraries (`--kind dll`/`cdylib` -> `<stem>.dll` + `<stem>.lib`):** Emits compact Microsoft short-import members (`IMPORT_OBJECT_HEADER`: `Sig1 = 0x0000`, `Sig2 = 0xFFFF`, `Version = 0`, **`Machine = IMAGE_FILE_MACHINE_ARM64 (0xAA64)`**, `TimeDateStamp = 0`, `Type = IMPORT_CODE (0)` or `IMPORT_DATA (1)`, `NameType = IMPORT_OBJECT_NAME (1)` or `ORDINAL (0)`). Note that `NameType = IMPORT_OBJECT_NOPREFIX (2)` / `UNDECORATE (3)` are x86-specific; on ARM64, `IMPORT_OBJECT_NAME (1)` matches undecorated COFF symbol names directly (`SPEC-26 AXS-WLIB-030..031`, `SPEC-89 AXS-ARTM-017`). Malformed `CoffAr` `"!<arch>\n"` headers, corrupt `/` linker symbol directories, or truncated `IMPORT_OBJECT_HEADER` members fail with `AX_LINK_BAD_ARCHIVE`; linking a `.lib` or `.obj` whose `Machine != 0xAA64` (such as `0x8664` AMD64 or `0xA641` ARM64EC) is rejected with `AX_LINK_ARTIFACT_TARGET_MISMATCH`. [0097 §27; SPEC-26 AXS-WLIB-010..012, 030..031; SPEC-89 AXS-ARTM-008, 017]

**AXS-WA64-017 — Pre-Encoding `verify_mc` (`REQ-TGT-162`) & Post-Encoding COFF Object/Archive Verification (`REQ-TGT-307`) (`0185 §24`, `tasks/0521 §152–154`, `tasks/0524 §112`, `T694`).**
1. **Pre-encoding Machine IR verification (`REQ-TGT-162`, `tasks/0521 §152–154, §156 AARM-68`, `tasks/0524 §112 ABACKEND-81`):** Before `compiler/obj/coff_arm64` encodes machine instructions, `verify_mc` enforces all `SPEC-83 AXS-A64-037` checks plus four Windows ARM64 invariants: (a) zero writes or general allocations of `X18`/`W18`; (b) `SP % 16 == 0` at every `SP`-relative memory operand and `BL`/`BLR`; (c) frames with `alloc_bytes >= 4096` execute `MOV* X15` -> `BL __chkstk` -> `SUB SP, SP, X15, LSL #4` *after* saving `X30`; and (d) every instruction inside a marked prologue/epilogue region has a valid 1-to-1 ARM64 SEH unwind representation (`0188 §32–34`). Failures on hand-written verifier inputs emit `AX_VERIFY_MC_ILLEGAL`; failures on compiler-produced IR emit `AX_ICE_INTERNAL` (`data.stage = "verify_mc"`, exit code `3`).
2. **Post-encoding COFF `.obj` & `CoffAr` verification + crash-safe output (`REQ-TGT-307`, `SPEC-89 AXS-ARTM-030`, `tasks/0524 §65–66, §112 ABACKEND-82`):** Immediately after COFF `.obj` or `CoffAr` `.lib`/`.axlib` serialization, `verify_coff_obj` / `verify_archive` validates `Machine == 0xAA64`, `TimeDateStamp == 0`, monotonic non-overlapping section raw-data and relocation bounds, valid 1-based symbol and `IMAGE_COMDAT_SELECT_ASSOCIATIVE` section indices, valid `IMAGE_REL_ARM64_*` codes (`0x0000..0x0011`, excluding `0x000C`), valid `.pdata`/`.xdata` alignment and `0xE4`/`0xE5` terminators, and intact `.axmeta`/`.axmir`/`.axlto` `0x42000200` headers (`AX_ICE_INTERNAL` with `data.stage = "obj_verify"` on any compiler-generated violation), writing to `<out>.tmp.<pid>` and atomically renaming to `<out>` only after verification succeeds (`tasks/0563 §304.45 AIMG-50`). [0185 §24; 0188 §32–34; tasks/0521 §152–154, §156 AARM-68; tasks/0524 §65–66, §112 ABACKEND-81..82; tasks/0563 §304.45 AIMG-50; SPEC-83 AXS-A64-037; SPEC-89 AXS-ARTM-030]

---

## 3. Windows ARM64 Exception & Unwind Metadata (`.pdata` Packed & `.xdata` Unpacked SEH) (`AXS-WA64-018`..`024`)

**AXS-WA64-018 — Semantic `FramePlan` $\rightarrow$ `Arm64UnwindPlan` Derivation (`REQ-TGT-129`, `REQ-TGT-152`, `T694`).**
`compiler/target/aarch64/win_frame` derives Windows ARM64 unwind metadata directly from the typed `FramePlan`, `ProloguePlan`, and `EpiloguePlan` — **never** by disassembling raw `.text` bytes (`0188 §2–3, §25–33, AUNW-20..31`, `tasks/0521 §104, AARM-35, 58`, `SPEC-54 AXS-PAN-013`). Pure zero-frame leaf functions (`frame_size == 0`, zero saved registers, `LR` unmodified) require **no** `.pdata` entry because `RtlVirtualUnwind` restores caller `PC = X30` directly when `ControlPc` misses `.pdata`. Every non-leaf function and every leaf function that allocates stack space or saves any register emits one 8-byte `.pdata` entry (or multiple contiguous `.pdata` fragments if `function_bytes > 1_048_572`). Return-value registers (`X0`/`X1`, `V0..V3`) are materialized strictly before `EpilogueStart` (`0188 §31, AEPI-20..23`), and machine peephole/scheduling passes are forbidden from reordering or inserting arbitrary instructions inside `[PrologueStart, PrologueEnd)` or `[EpilogueStart, EpilogueEnd)`. [0188 §2–5, §25–33, AUNW-20..31, AEPI-20..23; tasks/0521 §104, AARM-35, 58; SPEC-54 AXS-PAN-013]

**AXS-WA64-019 — 8-Byte `.pdata` (`IMAGE_ARM64_RUNTIME_FUNCTION_ENTRY`) & Packed Unwind Format (`T694`, `T695`).**
Unlike Windows x64's 12-byte `RUNTIME_FUNCTION` (`BeginAddress`, `EndAddress`, `UnwindInfoAddress`), every Windows ARM64 `.pdata` entry is **8 bytes** (`align = 4`):
- `+0` `BeginAddress: u32` — 32-bit RVA of the function start (`BeginAddress % 4 == 0`, emitted in COFF `.obj` as `0` + `IMAGE_REL_ARM64_ADDR32NB` targeting the function/section symbol).
- `+4` `UnwindData: u32` — discriminated by `Flag = UnwindData & 0x3`:
  - **`Flag == 0` (`0b00`, unpacked `.xdata` reference):** `UnwindData` is the 4-byte-aligned 32-bit RVA of the function's `.xdata` record (`IMAGE_REL_ARM64_ADDR32NB`).
  - **`Flag == 1` (`0b01`, packed canonical prologue + epilogue) or `Flag == 2` (`0b10`, packed body without prologue/epilogue):** Zero `.xdata` bytes are emitted; `UnwindData` encodes all unwind facts inline:

| Bits | Width | Field | Meaning & Constraints for Packed Emission (`Flag == 1` or `2`) |
|---|---|---|---|
| `[1:0]` | `2` | `Flag` | `01` = canonical prologue at start & epilogue at end; `10` = shrink-wrapped body segment; `11` = reserved (`AX_LINK_BAD_UNWIND_INFO`) |
| `[12:2]` | `11` | `FunctionLength` | Total function byte length divided by `4` (`1..=2047`, i.e., `<= 8188` bytes) |
| `[15:13]` | `3` | `RegF` | Saved FP count: `0` = **0** FP regs; `1..=7` = **`RegF + 1`** contiguous regs `D8..D[8 + RegF]` (`2..=8` regs; saving **1** FP reg `D8` alone **must** use `Flag = 0` `.xdata`) |
| `[19:16]` | `4` | `RegI` | Saved GPR count `0..=10` for contiguous `X19..X[18 + RegI]` (`> 10` is illegal: `AX_LINK_BAD_UNWIND_INFO`) |
| `[20]` | `1` | `H` | `1` if prologue homes `X0..X7` (`STP X0, X1`..`STP X6, X7`) into a 64-byte top save area; `0` otherwise |
| `[22:21]` | `2` | `CR` | `00` = unchained (`LR` unsaved); `01` = unchained (`X30` saved at top of save area, or paired `STP X[last], X30` when `RegI` is odd); `10` = `PACIBSP` + chained `FP`; `11` = chained `STP X29, X30` + `MOV X29, SP` |
| `[31:23]` | `9` | `FrameSize` | Total stack frame bytes divided by `16` (`0..=511`, i.e., `<= 8176` bytes; frames `>= 4096`B requiring `__chkstk` always use `Flag = 0` `.xdata`) |

`compiler/target/aarch64/win_frame` emits `Flag = 1` packed `.pdata` whenever the function has **no** exception handler (`X == 0`, e.g., `--panic abort` or cleanup-free frame), `frame_size < 4096`, `function_bytes <= 8188`, `RegF != 1_fp_reg`, and prologue/epilogue strictly follow Microsoft's canonical register-save layout; otherwise it emits `Flag = 0` pointing to `.xdata`. [winnt.h `IMAGE_ARM64_RUNTIME_FUNCTION_ENTRY`; 0188 §19–22, §54–55]

**AXS-WA64-020 — Unpacked `.xdata` Header, Extended Header & `EpilogScope` Records (`T694`).**
Every unpacked `.xdata` record (`4`-byte aligned) has the sequential layout `[HeaderWord (4B)] [ExtendedHeaderWord? (4B)] [EpilogScope* (4B each)] [UnwindCodes (4B * CodeWords)] [ExceptionHandlerRva + HandlerData? (when X == 1)]`:
1. **Primary 32-bit `HeaderWord`:**
   - `bits [17:0]` `FunctionLength`: total function byte size divided by `4` (`<= 262_143` words = `1_048_572` bytes);
   - `bits [19:18]` `Vers`: unwind version, **must be `0`** (`Vers != 0` rejected with `AX_LINK_BAD_UNWIND_INFO`);
   - `bit [20]` `X`: `1` when `ExceptionHandlerRva` (`u32`, `IMAGE_REL_ARM64_ADDR32NB`) + handler data follow the unwind code words, else `0`;
   - `bit [21]` `E`: `1` (single-epilogue inline mode) when the function has **at most one** epilogue situated at the exact end of the function and its start byte index fits in `5` bits (`0..31`), in which case **zero** `EpilogScope` words are emitted and `bits [26:22]` directly store that 5-bit unwind-code byte offset; `0` when `0`, `>= 2`, or mid-function epilogues exist, in which case `bits [26:22]` (`EpilogCount`) store the count of 32-bit `EpilogScope` words;
   - `bits [31:27]` `CodeWords`: number of 32-bit words of unwind opcode bytes (`1..=31`).
2. **Optional `ExtendedHeaderWord` (`4`B):** Emitted immediately after `HeaderWord` **if and only if** `(E == 0 && EpilogCount == 0 && CodeWords == 0)` (used whenever true `epilog_count > 31` or `code_words > 31`): `bits [15:0] = ExtendedEpilogCount`, `bits [23:16] = ExtendedCodeWords`, `bits [31:24] = 0`.
3. **32-bit `EpilogScope` word (emitted `actual_epilog_count` times when `E == 0`):**
   - `bits [17:0]` `EpilogStartOffset`: byte offset of the first epilogue instruction from `BeginAddress`, divided by `4` (sorted ascending across scopes);
   - `bits [21:18]` `Res`: reserved `0`;
   - `bits [31:22]` `EpilogStartIndex`: 10-bit byte index (`0..1023`) into the `UnwindCodes` byte array where this epilogue's opcodes begin (identical epilogues share the same `EpilogStartIndex`). [winnt.h `IMAGE_ARM64_RUNTIME_FUNCTION_ENTRY_XDATA`; 0188 §15–17, §22–26]

**AXS-WA64-021 — Complete `.xdata` ARM64 Unwind Opcode Byte Encoding Table (`T693`, `T694`).**
Unwind opcodes are stored as a contiguous **byte stream** (big-endian multi-byte opcodes within the byte array, padded at the end with `0xE3` `nop` bytes to a 4-byte `CodeWords` multiple):

| Opcode | Len | Exact Byte Bit Pattern | Prologue / Epilogue Instruction Semantics & Parameter Range |
|---|---|---|---|
| `alloc_s` | `1`B | `000xxxxx` | Allocate/deallocate `16 * x` bytes (`x` $\in 1..31$: `16..496`B; `SUB`/`ADD SP, SP, #16*x`) |
| `save_r19r20_x` | `1`B | `001zzzzz` | Pre/post-indexed `STP`/`LDP X19, X20, [SP, #-8*z]!` (`z = off / 8` $\in 1..31$: `8..248`B) |
| `save_fplr` | `1`B | `01zzzzzz` | Signed-offset `STP`/`LDP X29, X30, [SP, #8*z]` (`z = off / 8` $\in 0..63$: `0..504`B) |
| `save_fplr_x` | `1`B | `10zzzzzz` | Pre/post-indexed `STP`/`LDP X29, X30, [SP, #-8*(z+1)]!` (`z = off/8 - 1` $\in 0..63$: `8..512`B) |
| `alloc_m` | `2`B | `11000xxx` `xxxxxxxx` | Allocate/deallocate `16 * x` bytes (`11`-bit `x`: `16..32_752`B, incl. `__chkstk` `SUB SP`) |
| `save_regp` | `2`B | `110010xx` `xxzzzzzz` | Signed-offset `STP`/`LDP X(19+x), X(20+x), [SP, #8*z]` (`x` $\in 0..9$, `z = off/8` $\in 0..63$: `0..504`B) |
| `save_regp_x` | `2`B | `110011xx` `xxzzzzzz` | Pre/post-indexed `STP`/`LDP X(19+x), X(20+x), [SP, #-8*(z+1)]!` (`z = off/8 - 1`: `8..512`B) |
| `save_reg` | `2`B | `110100xx` `xxzzzzzz` | Signed-offset `STR`/`LDR X(19+x), [SP, #8*z]` (`x` $\in 0..11` incl. `X29`/`X30`, `z = off/8`: `0..504`B) |
| `save_reg_x` | `2`B | `1101010x` `xxxzzzzz` | Pre/post-indexed `STR`/`LDR X(19+x), [SP, #-8*(z+1)]!` (`4`-bit `x` $\in 0..11$, **`5`-bit `z`** $= \text{off}/8 - 1$: `8..256`B) |
| `save_lrpair` | `2`B | `1101011x` `xxzzzzzz` | Signed-offset `STP`/`LDP X(19+2*x), X30, [SP, #8*z]` (`x` $\in 0..4$ $\Rightarrow$ `X19,X21,X23,X25,X27`; `0..504`B) |
| `save_fregp` | `2`B | `1101100x` `xxzzzzzz` | Signed-offset `STP`/`LDP D(8+x), D(9+x), [SP, #8*z]` (`x` $\in 0..6$, `z = off/8`: `0..504`B) |
| `save_fregp_x` | `2`B | `1101101x` `xxzzzzzz` | Pre/post-indexed `STP`/`LDP D(8+x), D(9+x), [SP, #-8*(z+1)]!` (`x` $\in 0..6$, `z = off/8 - 1`: `8..512`B) |
| `save_freg` | `2`B | `1101110x` `xxzzzzzz` | Signed-offset `STR`/`LDR D(8+x), [SP, #8*z]` (`x` $\in 0..7$, `z = off/8`: `0..504`B) |
| `save_freg_x` | `2`B | `11011110` `xxxzzzzz` | Pre/post-indexed `STR`/`LDR D(8+x), [SP, #-8*(z+1)]!` (`3`-bit `x` $\in 0..7$, **`5`-bit `z`** $= \text{off}/8 - 1$: `8..256`B) |
| `alloc_l` | `4`B | `11100000` `x[23:16]` `x[15:8]` `x[7:0]` | Allocate/deallocate `16 * x` bytes (`24`-bit `x`: up to `256 MiB - 16`B) |
| `set_fp` | `1`B | `11100001` (`0xE1`) | `MOV X29, SP` in prologue / `MOV SP, X29` in epilogue |
| `add_fp` | `2`B | `11100010` `xxxxxxxx` (`0xE2 xx`) | `ADD X29, SP, #8*x` in prologue / `SUB SP, X29, #8*x` in epilogue (`0..2040`B) |
| `nop` | `1`B | `11100011` (`0xE3`) | Non-unwinding 4B instruction in prologue/epilogue (`MOV X15`, `BL __chkstk`) or trailing word pad |
| `end` | `1`B | `11100100` (`0xE4`) | Terminates prologue or epilogue unwind sequence (represents trailing `RET` in epilogues) |
| `end_c` | `1`B | `11100101` (`0xE5`) | Terminates chained prologue fragment (continues unwinding in parent fragment) |
| `save_next` | `1`B | `11100110` (`0xE6`) | Next consecutive register pair `[X(p+2), X(p+3)]` or `[D(p+2), D(p+3)]` at `prev_off + 16` |
| `pac_sign_lr` | `1`B | `11111100` (`0xFC`) | `PACIBSP` / `AUTIBSP` link-register pointer authentication (`+pauth` frames) |

**AXS-WA64-022 — Reverse-Order Prologue vs Forward-Order Epilogue Encoding Invariant (`T694`).**
Windows ARM64 `RtlVirtualUnwind` steps through unwind codes at **1 A64 instruction (4 bytes) per unwind opcode** (`alloc_*`, `save_*`, `set_fp`, `add_fp`, `nop`, `save_next`, `pac_sign_lr` each advance 1 instruction; `end`/`end_c` consume 0 prologue instructions and represent the final `RET` in epilogues):
- **Prologue codes** begin at byte index `0` of `UnwindCodes` in **exact reverse execution order** (last prologue instruction at index `0`, first prologue instruction last, followed by `0xE4` `end`) so if an interrupt/exception occurs `k` instructions into an `M`-instruction prologue, the unwinder skips the first `M - k` opcodes and undoes only the executed prefix (`0188 §27`).
- **Epilogue codes** begin at `EpilogStartIndex` (or `HeaderWord[26:22]` when `E == 1`) in **exact forward execution order** (first epilogue instruction first, followed by `0xE4` `end` corresponding to the `RET`); when an epilogue is the exact mirror of the prologue, `EpilogStartIndex` may point directly to byte `0` of the prologue codes! [0188 §24–30, AUNW-28..30]

**AXS-WA64-023 — `--panic abort` vs `--panic unwind` SEH Handler Data & FFI No-Unwind Barrier (`REQ-FFI-004`, `0107 §64`, `SPEC-54`, `T694`, `T695`).**
- Under `--panic abort` (`SPEC-54 AXS-PAN-003`), `X = 0` on all `.xdata` entries and canonical frames pack into 8-byte `.pdata` records with zero `.xdata` overhead (`0188 §18, §51`). Requesting `--panic unwind` under `--profile freestanding` or `--profile kernel` is rejected at compile time with `AX_DRIVER_PROFILE_FORBIDDEN_CAP` (`SPEC-52 AXS-FRE-022`, `SPEC-54 AXS-PAN-002`).
- Under `--panic unwind` (`SPEC-54 AXS-PAN-004, 013, 020`), any function with MIR cleanup landing pads (`Drop` destructors), `std.panic.catch_unwind`, or a mandatory `extern "C"` / `extern "system"` FFI no-unwind abort barrier emits unpacked `.xdata` (`Flag = 0`) with `X = 1`, appending `ExceptionHandlerRva: u32` (`IMAGE_REL_ARM64_ADDR32NB` -> `__axiom_seh_personality`) and the RVA-indexed cleanup/barrier scope table (`[try_begin_rva, try_end_rva, landing_pad_rva, action_kind]`). Uncaught panics reaching an `extern "C"` / `extern "system"` frame run local Axiom `Drop`s and abort immediately with exit code `101` (`REQ-FFI-004`, `0107 §64`, `SPEC-54 AXS-PAN-020`). [0107 §64; 0188 §51–53; SPEC-52 AXS-FRE-022; SPEC-54 AXS-PAN-002..004, 013, 020]

**AXS-WA64-024 — Link-Time `.pdata` RVA Sorting, Non-Overlap Validation & `DataDirectory[3]` (`0188 §38–43`, `T695`).**
`compiler/link/pe_arm64` collects all live `.pdata` contributions (after discarding dead COMDAT sections), resolves `BeginAddress` and unpacked `.xdata` `UnwindData` (`Flag == 0`) to final image RVAs, **sorts all 8-byte `.pdata` entries strictly ascending by `BeginAddress`** (`AUNW-32`), verifies that every entry satisfies `BeginAddress % 4 == 0`, `FunctionLength > 0`, and `entry[i].BeginAddress + entry[i].byte_len <= entry[i + 1].BeginAddress` (`AX_LINK_BAD_UNWIND_INFO` on malformed records or overlapping ranges), and writes `OptionalHeader.DataDirectory[3]` (`IMAGE_DIRECTORY_ENTRY_EXCEPTION`) = `{ VirtualAddress = pdata_rva, Size = entry_count * 8 }`. [0188 §38–43, AUNW-32..35]

---

## 4. PE32+ ARM64 (`0xAA64`) Executable & DLL Linker (`compiler/link/pe_arm64`), Import Thunks, `.reloc` & TLS (`AXS-WA64-025`..`031`)

**AXS-WA64-025 — PE32+ ARM64 Image Headers, Security Flags, W^X Section Layout & Post-Encoding Image Verification (`REQ-TOOL-001`, `REQ-TGT-104`, `REQ-TGT-307`, `REQ-TGT-308`, `T695`).**
`compiler/link/pe_arm64` produces native PE32+ `.exe` (`--kind exe` / `--kind bin`) and `.dll` (`--kind dll` / `--kind cdylib`) images directly from `LinkIR`, `0xAA64` `.obj` files, and `CoffAr` `.lib` archives without invoking `link.exe` or `lld-link` (`0097 §27`, `0185 §32–55`, `0186 §17–22`, `tasks/0563 §304.14–20`, `SPEC-26 AXS-WLIB-001..005, 020`, `SPEC-89 AXS-ARTM-002..003, 015`). Input `.obj`/`.lib`/`.axlib` artifacts with `Machine != 0xAA64` fail with `AX_LINK_ARTIFACT_TARGET_MISMATCH`; unresolved strong symbol references fail with `AX_LINK_UNDEFINED_SYMBOL`; duplicate strong definitions fail with `AX_LINK_DUPLICATE_SYMBOL`; and cross-object calling-convention (including variadic vs non-variadic `CallConv.WinArm64`), symbol-kind (`Function` vs `Data` vs `Tls`), or `.axmeta` `AbiFingerprint` mismatches for the same external symbol fail with `AX_LINK_ABI_MISMATCH` (`SPEC-27 AXS-LNK-005, 014`, `SPEC-89 AXS-ARTM-027`):
- **DOS stub & PE signature:** 64-byte `IMAGE_DOS_HEADER` (`e_magic = 0x5A4D`, `e_lfanew = 0x80`) + deterministic DOS stub + `"PE\0\0"` (`0x00004550`).
- **COFF File Header (`20`B):** `Machine = IMAGE_FILE_MACHINE_ARM64 (0xAA64)`, `TimeDateStamp = 0`, `SizeOfOptionalHeader = 240`, `Characteristics = EXECUTABLE_IMAGE (0x0002) | LARGE_ADDRESS_AWARE (0x0020)` (`| DLL (0x2000)` for `--kind dll`/`cdylib`).
- **PE32+ Optional Header (`240`B, `Magic = 0x020B`):**
  - Preferred `ImageBase`: `0x0000_0001_4000_0000` (`.exe`) or `0x0000_0001_8000_0000` (`.dll`);
  - `SectionAlignment = 0x1000` (`4096`B), `FileAlignment = 0x0200` (`512`B);
  - `MajorOperatingSystemVersion = 10`, `MinorOperatingSystemVersion = 0`, `MajorSubsystemVersion = 10`, `MinorSubsystemVersion = 0` (Windows 10/11 ARM64 minimum);
  - `Subsystem`: `IMAGE_SUBSYSTEM_WINDOWS_CUI (3)` by default (`WINDOWS_GUI = 2` with `--subsystem windows`, `NATIVE = 1` under `--profile kernel`);
  - `DllCharacteristics = HIGH_ENTROPY_VA (0x0020) | DYNAMIC_BASE (0x0040) | NX_COMPAT (0x0100)` (`0x0160`, plus `TERMINAL_SERVER_AWARE = 0x8000` on `.exe`);
  - `SizeOfStackReserve = 0x100000` (`1 MiB`, or `--stack-size`), `SizeOfStackCommit = 0x1000` (`4 KiB`), `SizeOfHeapReserve = 0x100000`, `SizeOfHeapCommit = 0x1000`, `CheckSum = 0` (or PE checksum when `--pe-checksum` is requested).
- **Canonical W^X section order, metadata stripping & `verify_coff_pe` (`REQ-TGT-307`):** `.text` (`R|X`), `.rdata` (`R`, merging `.xdata`, read-only constants, `.idata` descriptors/ILT/strings/IAT, and `.edata`), `.data` (`R|W`, followed by virtual `.bss` tail), `.pdata` (`R`), optional `.tls` (`R|W`), and `.reloc` (`R | MEM_DISCARDABLE`). No section may combine `IMAGE_SCN_MEM_WRITE` and `IMAGE_SCN_MEM_EXECUTE`, and `100%` of `.axmeta`/`.axmir`/`.axlto` sections are stripped from final `.exe` and `.dll` images (`SPEC-24 AXS-ART-022`, `SPEC-89 AXS-ARTM-029`). Images whose `SizeOfImage` exceeds `2 GiB` fail with `AX_LINK_IMAGE_TOO_LARGE`. Immediately after PE32+ serialization, `verify_coff_pe` (`SPEC-89 AXS-ARTM-030`, `REQ-TGT-307`, `tasks/0524 §67, §112 ABACKEND-82`, `tasks/0563 §304.33–36, §304.45 AIMG-48..50`) validates PE32+ magic/machine headers, monotonic non-overlapping RVA and file-offset bounds, W^X permissions, sorted `.pdata`/`.edata`/`.reloc` directories, and zero `.axmeta`/`.axmir`/`.axlto` residue (`AX_ICE_INTERNAL` with `data.stage = "link_verify"` on internal violation) before atomically renaming `<out>.tmp.<pid>` to `<out>`. [0097 §27; 0185 §38–54; 0186 §17–22, APE-20..37; tasks/0524 §67, §112 ABACKEND-82..83; tasks/0563 §304.14–20, §304.33–45, AIMG-20..60; SPEC-24 AXS-ART-022; SPEC-26 AXS-WLIB-001..005, 020; SPEC-27 AXS-LNK-005, 014; SPEC-89 AXS-ARTM-002..003, 015, 027, 029..030]

**AXS-WA64-026 — `.idata` Import Directory, IAT (`__imp_<sym>`) & 12-Byte ARM64 Import Thunks (`0187`, `T693`, `T695`).**
DLL imports resolve deterministically (`0187 §8–25, §40, AIMPORT-20..34`, `tasks/0563 §304.17`, `SPEC-26 AXS-WLIB-030..032`):
1. **`.idata` & IAT layout:** Imported DLLs are canonicalized to lowercase ASCII (`kernel32.dll`, `ntdll.dll`, `ws2_32.dll`, `bcrypt.dll`, …) and sorted lexicographically; within each DLL, imported symbols are deduplicated and sorted lexicographically (`Ordinal` imports before named `Hint/Name` entries). `DataDirectory[1]` (`IMPORT`) points to the NUL-terminated array of 20-byte `IMAGE_IMPORT_DESCRIPTOR`s, while `DataDirectory[12]` (`IAT`) spans the contiguous 8-byte-aligned Import Address Table slots (`__imp_<sym>`).
2. **12-byte ARM64 import thunk (`__thunk_<sym>`):** Whenever machine code references an imported function `<sym>` directly via `BL <sym>` or `B <sym>` (`IMAGE_REL_ARM64_BRANCH26`) rather than indirect `__imp_<sym>`, `compiler/link/pe_arm64` synthesizes a 12-byte (3-instruction, 4-byte-aligned) import thunk in `.text`:
   ```text
   __thunk_<sym>:
       adrp x16, __imp_<sym>               ; 0x90000010 + PAGEBASE_REL21(__imp_<sym>)
       ldr  x16, [x16, #:lo12:__imp_<sym>] ; 0xF9400210 + PAGEOFFSET_12L(__imp_<sym>)
       br   x16                            ; 0xD61F0200
   ```
   The thunk clobbers **only `X16` (`IP0`)**, preserving `X0..X8`, `X15`, `X18`, `X19..X30`, and `V0..V31`, requires zero `.pdata` entry (tail-jump stub), and emits zero `.reloc` entries because `ADRP` + `LDR` is purely PC-relative. Direct references to `__imp_<sym>` (including imported data globals) bind directly to the 8-byte IAT slot without generating a thunk. [0187 §8–25, §40, AIMPORT-20..34; tasks/0563 §304.17; SPEC-26 AXS-WLIB-030..032]

**AXS-WA64-027 — `±128 MiB` Range-Extension Veneer Islands for `IMAGE_REL_ARM64_BRANCH26` (`REQ-TGT-308`, `T695`).**
A64 unconditional `B` and `BL` instructions (`IMAGE_REL_ARM64_BRANCH26`) encode a signed 26-bit word displacement (`[-134_217_728, +134_217_724]` bytes = `±128 MiB`). During section layout, if any `BRANCH26` call/jump target `T` lies outside `±128 MiB` of instruction `P`, `compiler/link/pe_arm64` deterministically inserts a 12-byte range-extension veneer island within `±128 MiB` of `P` (`tasks/0521 §100–101`, `SPEC-83 AXS-A64-042`):
```text
__veneer_<T>:
    adrp x16, <T>               ; 0x90000010 + PAGEBASE_REL21(<T>)
    add  x16, x16, #:lo12:<T>   ; 0x91000210 + PAGEOFFSET_12A(<T>)
    br   x16                    ; 0xD61F0200
```
and redirects `P`'s `BRANCH26` field to `__veneer_<T>` before computing `.pdata` RVAs and function lengths. Conditional short branches (`BRANCH19` `±1 MiB`, `BRANCH14` `±32 KiB`) are relaxed intra-function by the compiler; cross-section out-of-range `BRANCH19`/`BRANCH14` relocations fail cleanly with `AX_LINK_RELOC_OUT_OF_RANGE`. [tasks/0521 §100–101; SPEC-83 AXS-A64-042]

**AXS-WA64-028 — PE32+ Export Directory (`.edata` / `DataDirectory[0]`), `--def` & Companion `.lib` (`SPEC-26`, `SPEC-89`, `T695`).**
For `--kind dll`/`cdylib` (and `.exe` images with explicit `@export` or `--def`), `compiler/link/pe_arm64` emits the 40-byte `IMAGE_EXPORT_DIRECTORY` (`TimeDateStamp = 0`), `AddressOfFunctions` (`Export RVA` or forwarder string RVA inside `DataDirectory[0]`), lexicographically sorted `AddressOfNames`, and `AddressOfNameOrdinals` (`SPEC-26 AXS-WLIB-004, 021`, `SPEC-89 AXS-ARTM-015..017`). Non-`@export` `pub` items remain strictly internal to the PE image and never leak into `.edata` (`INV-ARTM-003`). Duplicate exported names/ordinals emit `AX_LINK_DUPLICATE_EXPORT`; invalid `.def` syntax emits `AX_LINK_INVALID_DEF_FILE`. Alongside `<stem>.dll`, the linker writes the companion `<stem>.lib` short-import archive (`Machine = 0xAA64`, `SPEC-26 AXS-WLIB-030`, `AXS-WA64-016`). [tasks/0563 §304.18; SPEC-26 AXS-WLIB-004, 020..021, 030; SPEC-89 AXS-ARTM-006, 015..017]

**AXS-WA64-029 — Base Relocation Table (`.reloc` / `DataDirectory[5]`) & Text-Relocation Ban (`0185 §49–50`, `T695`).**
Every linked PE32+ ARM64 `.exe` and `.dll` sets `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE` and emits `.reloc` (`DataDirectory[5]`):
- Every resolved `IMAGE_REL_ARM64_ADDR64` (`0x000E`) slot in `.rdata`/`.data` (vtables, static function/data pointers, and the four VA fields of `_tls_used`) records one 16-bit entry `(IMAGE_REL_BASED_DIR64 (10) << 12) | (slot_rva & 0xFFF)` inside the ascending-sorted 4 KiB (`PageRVA = slot_rva & ~0xFFF`) `IMAGE_BASE_RELOCATION` block (`8`-byte header `{ VirtualAddress: u32, SizeOfBlock: u32 }`, padded if odd with one trailing `IMAGE_REL_BASED_ABSOLUTE (0)` entry so `SizeOfBlock % 4 == 0`).
- Even when zero `ADDR64` fixups exist in a small binary, `compiler/link/pe_arm64` emits a minimal valid 12-byte dummy `.reloc` block (`PageRVA = 0x1000`, `SizeOfBlock = 12`, two `ABSOLUTE (0)` entries) so the Windows 11 ARM64 ASLR loader never rejects a `DYNAMIC_BASE` image with an empty relocation directory.
- Any `IMAGE_REL_ARM64_ADDR64` or `IMAGE_REL_ARM64_ADDR32` targeting an executable section (`IMAGE_SCN_MEM_EXECUTE`) is rejected at link time with `AX_LINK_TEXTREL_FORBIDDEN`. [0185 §49–50; tasks/0563 §304.19; SPEC-26 AXS-WLIB-005, 023]

**AXS-WA64-030 — Implicit Thread-Local Storage (`@thread_local`, `X18` `TEB + 0x58`, `_tls_index` & `_tls_used`) (`SPEC-32`, `T693`, `T695`, `T696`).**
On `aarch64-windows`, `@thread_local static` variables (`SPEC-32 AXS-SYNC-020..023`) use the Windows ARM64 implicit TLS mechanism via `X18`:
1. **Runtime TEB lookup (`[X18, #0x58]`):** At offset `+0x58` (`88` decimal) of the `TEB` pointed to by `X18` sits `ThreadLocalStoragePointer: *const *mut u8`. Given module `_tls_index: u32`, the current thread's module TLS block base is `tls_base = (*((X18 + 0x58) as *const *mut u8))[_tls_index]`, materialized in 6 instructions:
   ```text
   ldr  x9, [x18, #0x58]                 ; 0xF9402E49 (TEB.ThreadLocalStoragePointer)
   adrp x8, _tls_index                   ; IMAGE_REL_ARM64_PAGEBASE_REL21(_tls_index)
   ldr  w8, [x8, #:lo12:_tls_index]      ; IMAGE_REL_ARM64_PAGEOFFSET_12L(_tls_index)
   ldr  x8, [x9, x8, lsl #3]             ; module TLS block base for current thread
   add  x8, x8, #:secrel_hi12:<tls_sym>  ; IMAGE_REL_ARM64_SECREL_HIGH12A(<tls_sym>)
   add  x0, x8, #:secrel_lo12:<tls_sym>  ; IMAGE_REL_ARM64_SECREL_LOW12A(<tls_sym>)
   ```
2. **Linker `.tls` synthesis (`DataDirectory[9]`):** When any input `.obj` contributes `.tls` / `.tls$` data, `compiler/link/pe_arm64` merges all `.tls$` sections in deterministic order into `.tls` (`tls_rva`, `tls_size < 16 MiB`, else `AX_LINK_RELOC_OUT_OF_RANGE`), resolves `SECREL`/`SECREL_HIGH12A`/`SECREL_LOW12A`/`SECREL_LOW12L` against `tls_rva`, synthesizes 4-byte `_tls_index` (`0u32` in `.data`) and 8-byte `_tls_callbacks` (`0u64` in `.rdata`), emits the 40-byte `IMAGE_TLS_DIRECTORY64` (`_tls_used` in `.rdata` with 4 `IMAGE_REL_BASED_DIR64` base relocations for `StartAddressOfRawData`, `EndAddressOfRawData`, `AddressOfIndex`, `AddressOfCallBacks`), and populates `DataDirectory[9] = { tls_used_rva, 40 }`. [SPEC-32 AXS-SYNC-020..023]

**AXS-WA64-031 — Built-in CRT-Free `__chkstk` Synthesis in `compiler/link/pe_arm64` (`0186 §2`, `0188 §12`, `T695`).**
Because Axiom binaries never depend on `vcruntime140.dll` or `libcmt.lib` (`0181 §16`, `0186 §2`), whenever any linked `.obj` references `__chkstk` and no user/freestanding object defines it, `compiler/link/pe_arm64` synthesizes `__chkstk` directly into `.text`:
- **Hosted Windows (`--profile hosted` / `system`):** Computes `X16 = X15 << 4` (`LSL X16, X15, #4`), computes target low address `X16 = SP - X16` (`SUB X16, SP, X16`, clamped to `0` on underflow), loads current `NT_TIB64.StackLimit` via `LDR X17, [X18, #0x10]` (`0xF9400A51`), and while `X16 < X17`, steps `X17` downward by `4096` (`SUB X17, X17, #1, LSL #12`) and executes a dummy probe read `LDR XZR, [X17]` to trigger the OS `PAGE_GUARD` handler page-by-page before returning via `RET` (`0xD65F03C0`).
- **Freestanding (`--profile freestanding` / `kernel`, where `X18` is not a Win32 TEB):** Steps `X17` downward from `SP` by `4096` bytes (`X16` remaining bytes) probing `LDR XZR, [X17]` on every 4 KiB boundary without reading `X18`.
In both modes, `__chkstk` is a pure zero-stack leaf (`SP` and `X15` untouched, only `X16`, `X17`, and `NZCV` modified). [ADR-0003; 0186 §2; 0188 §11–12]

---

## 5. `std.sys.windows.arm64` Platform Layer, Diagnostics (`E9100–E9119`), Examples, Invariants & Traceability (`AXS-WA64-032`..`036`)

**AXS-WA64-032 — `std.sys.windows.arm64` Startup, `X18` TEB Intrinsics, Fibers & Hermetic Import Stubs (`0186`, `SPEC-88`, `T695`).**
`std/sys/windows/arm64` specializes Level-3 OS support (`SPEC-88 AXS-PLAT-020`) while sharing architecture-neutral Win32 Unicode `*W` I/O, filesystem, networking, heap, synchronization (`WaitOnAddress`), and time modules in `std/sys/windows/`:
1. **CRT-free PE32+ entry points (`0186 §1–16`):**
   - `--kind exe` (`hosted`): `mainCRTStartup` (or `wWinMainCRTStartup` under `--subsystem windows`) establishes a 16-byte-aligned root frame (`X29 = 0`, `X30 = 0` sentinel), initializes CLI UTF-16 `GetCommandLineW` / environment state on demand, invokes Axiom `main()`, and calls `ExitProcess(exit_code as u32)` via `kernel32.dll` import thunk (`never` return; `0186 §7–12`).
   - `--kind dll`/`cdylib`: `DllMainCRTStartup(hinst_dll: usize, fdw_reason: u32, lpv_reserved: *mut u8) -> i32` runs optional module hooks and returns `1i32` (`TRUE`), or `AddressOfEntryPoint = 0` when zero startup hooks exist (`SPEC-26 AXS-WLIB-022`).
   - `--profile freestanding` / `--profile kernel`: binds directly to the single `@entry` symbol (`SPEC-52 AXS-FRE-010`) with zero `kernel32.dll` imports (requesting hosted `kernel32.dll` I/O, TEB-backed `@thread_local` TLS, or `--panic unwind` in `freestanding`/`kernel` fails with `AX_DRIVER_PROFILE_FORBIDDEN_CAP`, `SPEC-52 AXS-FRE-022`).
2. **ARM64 `X18` TEB & fiber intrinsics (`SPEC-34 AXS-EXEC-055`):**
   - `std.sys.windows.arm64.nt_current_teb() -> *mut Teb64` reads `X18` directly (`MOV X0, X18`), providing zero-syscall access to `StackBase` (`+0x08`), `StackLimit` (`+0x10`), `FiberData` (`+0x20`), `ClientId.UniqueThread` (`+0x48`), and `ThreadLocalStoragePointer` (`+0x58`).
   - `host.fiber_*` (`std/sys/windows/fiber.ax`) reuses Win32 `ConvertThreadToFiberEx` / `CreateFiberEx` / `SwitchToFiber` / `DeleteFiber` (`kernel32.dll`), which context-switch all Windows ARM64 non-volatile registers (`X19..X28`, `X29`, `X30`, `D8..D15`, `SP`, `PC`) and `NT_TIB64` stack bounds while preserving `X18` on the owning OS thread.
3. **Hermetic `0xAA64` import stubs (`SPEC-88 AXS-XCMP-023`):** `compiler/link/sysroot` ships built-in deterministic short-import tables (`Machine = 0xAA64`) for `kernel32.dll`, `ntdll.dll`, `ws2_32.dll`, `bcrypt.dll`, `advapi32.dll`, `userenv.dll`, and `api-ms-win-core-synch-l1-2-0.dll` so `axiomc build --target aarch64-pc-windows-msvc` cross-links `.exe` and `.dll` binaries hermetically from any Windows, Linux, or macOS host without a Windows ARM64 SDK (missing `-l<name>` or `@link("<name>")` libraries fail with `AX_LINK_LIBRARY_NOT_FOUND`). [0186 §1–32; tasks/0453 §194.20–25; SPEC-26 AXS-WLIB-003, 022, 030..032; SPEC-34 AXS-EXEC-055; SPEC-52 AXS-FRE-010, 022; SPEC-88 AXS-XCMP-022..023, AXS-PLAT-020]

**AXS-WA64-033 — Canonical Diagnostic Taxonomy & `E9100–E9119` Task-Card Mapping (`spec/diagnostics.md` §3, §11).**
Per `ADR-0011` and `AXD-010..021`, task-card shorthand codes `E9100–E9119` (`T693`–`T696`) map 1-to-1 onto canonical `AX_<AREA>_<NAME>` codes (`<= 48` chars) in `DRIVER`, `TARGET`, `FFI`, `VERIFY`, `LINK`, and `ICE`:

| Card Ref | Canonical `AX_*` Code | Area | Sev | Task | Condition & Structured `data.*` Payload |
|---|---|---|---|---|---|
| `E9100` | `AX_DRIVER_UNKNOWN_TARGET` | `DRIVER` | E | `T694` | Unknown/unsupported Windows ARM64 triple (`--target arm64-win32`, `aarch64-pc-windows-gnu`; `data.target`, exit code `2`; `AXS-WA64-001`) |
| `E9101` | `AX_TARGET_UNKNOWN_FEATURE` | `TARGET` | E | `T694` | Unknown ARM64 feature or disallowed hosted `-fp`/`-neon` removal (`AXS-WA64-002`) |
| `E9102` | `AX_TARGET_FEATURE_CONFLICT` | `TARGET` | E | `T694` | Mutually contradictory ARM64 target features in `--target-feature` or `@target_feature` (`AXS-WA64-002`) |
| `E9103` | `AX_TARGET_FEATURE_MISMATCH` | `TARGET` | E | `T694` | Unguarded safe call to a `@target_feature("+lse")` function on baseline `aarch64-windows` (`AXS-WA64-002`) |
| `E9104` | `AX_FFI_UNKNOWN_ABI` | `FFI` | E | `T694` | x86-only ABI (`"win64"`, `"sysv64"`, `"stdcall"`, `"fastcall"`, `"vectorcall"`) used on `aarch64-windows` (`AXS-WA64-001`) |
| `E9105` | `AX_FFI_BAD_TYPE` | `FFI` | E | `T694` | Non-FFI-safe parameter or return type in `extern "C"` / `extern "system"` `CallConv.WinArm64` (`AXS-WA64-004`..`006`) |
| `E9106` | `AX_FFI_VARIADIC_NOT_EXTERN_C` | `FFI` | E | `T694` | Variadic `...` parameter list declared outside an `extern "C"` import signature (`AXS-WA64-006`) |
| `E9107` | `AX_VERIFY_MC_ILLEGAL` | `VERIFY` | E | `T694` | `verify_mc` failure: unauthorized `X18` write/allocation, unaligned `SP`, invalid `__chkstk` sequence, or non-unwindable prologue/epilogue instruction (`data.rule`, `data.opcode`; `AXS-WA64-003`, `AXS-WA64-017`) |
| `E9108` | `AX_TARGET_UNSUPPORTED_OP` | `TARGET` | E | `T694` | `LIR` operation or target linkage mode illegal on `aarch64-windows` (`AXS-WA64-001`, `AXS-WA64-010`) |
| `E9109` | `AX_DRIVER_PROFILE_FORBIDDEN_CAP` | `DRIVER` | E | `T694`/`T695` | `--panic unwind`, TEB TLS, or hosted `kernel32.dll` I/O requested in `--profile freestanding`\|`kernel` (`AXS-WA64-023`, `AXS-WA64-032`) |
| `E9110` | `AX_LINK_ARTIFACT_TARGET_MISMATCH` | `LINK` | E | `T694`/`T695` | Input `.obj`, `.lib` (`IMPORT_OBJECT_HEADER.Machine`), `.axlib`, or `.axmi` has `Machine != 0xAA64` (e.g. `0x8664` or `0xA641`; `data.expected_target`, `data.found_target`; `AXS-WA64-011`, `AXS-WA64-016`, `AXS-WA64-025`) |
| `E9111` | `AX_LINK_BAD_OBJECT` | `LINK` | E | `T694`/`T695` | Corrupt COFF `0xAA64` header/section/symbol/string table, unknown `IMAGE_REL_ARM64_*` (`> 0x0011` or `0x000C`), or bad associative COMDAT (`AXS-WA64-011`..`015`) |
| `E9112` | `AX_LINK_BAD_ARCHIVE` | `LINK` | E | `T695` | Malformed `CoffAr` `"!<arch>\n"` archive, corrupt `/` symbol directory, or truncated `IMPORT_OBJECT_HEADER` (`AXS-WA64-016`) |
| `E9113` | `AX_LINK_BAD_UNWIND_INFO` | `LINK` | E | `T694`/`T695` | Malformed or overlapping Windows `.pdata`/`.xdata` unwind records (`BeginAddress % 4 != 0`, `Flag == 3`, `RegI > 10`, `.xdata` `Vers != 0`, missing `0xE4`/`0xE5` terminator, or overlapping function RVA intervals; `data.symbol`, `data.rva`, `data.detail`; `AXS-WA64-019`..`020`, `AXS-WA64-024`) |
| `E9114` | `AX_LINK_RELOC_OUT_OF_RANGE` | `LINK` | E | `T695` | `PAGEBASE_REL21` (`±4 GiB`), `REL21`/`BRANCH19` (`±1 MiB`), `BRANCH14` (`±32 KiB`), `SECREL_HIGH12A` (`16 MiB`), or `ADDR32NB` exceeds field range or alignment (`AXS-WA64-013`, `AXS-WA64-027`, `AXS-WA64-030`) |
| `E9115` | `AX_LINK_TEXTREL_FORBIDDEN` | `LINK` | E | `T695` | Absolute `ADDR64` or `ADDR32` relocation targets executable `.text` in a `DYNAMIC_BASE` PE32+ image (`data.section`, `data.symbol`; `AXS-WA64-029`) |
| `E9116` | `AX_LINK_UNDEFINED_SYMBOL` / `AX_LINK_DUPLICATE_SYMBOL` / `AX_LINK_ABI_MISMATCH` | `LINK` | E | `T695` | Unresolved symbol (or missing `__imp_<sym>`), duplicate strong definition, or cross-object `CallConv.WinArm64` (variadic vs non-variadic) / symbol-kind / `.axmeta` `AbiFingerprint` mismatch across `0xAA64` COFF inputs (`data.symbol`, `data.demangled`; `AXS-WA64-025`..`026`) |
| `E9117` | `AX_LINK_LIBRARY_NOT_FOUND` | `LINK` | E | `T695` | Requested `-l<name>` or `@link("<name>")` `.lib` missing from `-L`, `--sysroot`, and built-in `0xAA64` stubs (`data.library`; `AXS-WA64-032`) |
| `E9118` | `AX_LINK_DUPLICATE_EXPORT` / `AX_LINK_INVALID_DEF_FILE` | `LINK` | E | `T695` | Duplicate `@export`/`.def` symbol or syntax/ordinal error in `--def <path>` (`data.symbol`, `data.file`; `AXS-WA64-028`) |
| `E9119` | `AX_LINK_IMAGE_TOO_LARGE` / `AX_ICE_INTERNAL` | `LINK` / `ICE` | E | `T694`/`T695` | PE32+ `SizeOfImage > 2 GiB` (`AX_LINK_IMAGE_TOO_LARGE`), or compiler-generated output fails `verify_mc` / post-encoding `verify_coff_obj` / `verify_coff_pe` (`AX_ICE_INTERNAL`, `data.stage` $\in$ `{"verify_mc", "obj_verify", "link_verify"}`, exit `3`; `AXS-WA64-017`, `AXS-WA64-025`) |

**AXS-WA64-034 — Canonical Positive & Negative Examples (`=` and `.` Syntax).**

#### Positive Example — Hosted `aarch64-pc-windows-msvc` Console `.exe` with `HFA`, Variadic FFI, `[X18, #0x58]` TLS & `8 KiB` `__chkstk` Frame
```axiom
// Cross-compiled or built natively with zero MSVC/LLVM external tools:
//   axiomc build --target aarch64-pc-windows-msvc app/win_arm64_demo.ax -o target/win_arm64_demo.exe
module demo.win_arm64

use std.io.println

@repr(C)
@derive(Copy, Clone)
pub struct Vec2f {
    pub x: f32,
    pub y: f32,
}

@thread_local
static TLS_ACCUM: i64 = 10

@link("kernel32")
extern "system" {
    fn GetCurrentProcessId() -> u32
}

// Non-variadic HFA: `a` and `b` pass in `S0, S1` and `S2, S3`; return in `S0, S1` (`AXS-WA64-004`..`005`).
@export
@no_mangle
pub extern "C" fn add_vec2f(a: Vec2f, b: Vec2f) -> Vec2f {
    Vec2f { x: a.x + b.x, y: a.y + b.y }
}

// Frame >= 4 KiB triggers `MOV X15, #512; BL __chkstk; SUB SP, SP, X15, LSL #4` (`AXS-WA64-009`).
fn touch_large_frame(seed: u8) -> i32 {
    let mut scratch: [8192]u8 = [0u8; 8192]
    scratch[0] = seed
    scratch[8191] = seed + 1u8
    (scratch[0] as i32) + (scratch[8191] as i32)
}

pub fn main() -> i32 {
    println("Xin chào thế giới")
    let pid = unsafe { GetCurrentProcessId() }
    let sum = add_vec2f(Vec2f { x: 1.5f32, y: 2.5f32 }, Vec2f { x: 0.5f32, y: 1.5f32 })
    let tls_v = TLS_ACCUM
    let probe_v = touch_large_frame(4u8)
    if pid > 0u32 && sum.x == 2.0f32 && sum.y == 4.0f32 && tls_v == 10i64 && probe_v == 9i32 {
        return 0
    }
    return 1
}
```

#### Negative Examples — Foreign ABI Rejection & Target Architecture Mismatch
```axiom
// Checked with: axiomc check --target aarch64-pc-windows-msvc bad_abi.ax
module demo.bad_win_arm64_abi

// ERROR [AX_FFI_UNKNOWN_ABI] (E9104): `"stdcall"` is x86-specific; use `extern "system"` or `extern "C"` on `aarch64-windows` (`AXS-WA64-001`)
extern "stdcall" {
    fn LegacyWin32Call(code: u32) -> u32
}

// ERROR [AX_TARGET_FEATURE_MISMATCH] (E9103): `@target_feature("+lse")` callee requires `unsafe` or runtime feature guard on baseline `aarch64-windows` (`AXS-WA64-002`)
@target_feature("+lse")
fn atomic_lse_helper(p: mut_view<i64>) -> i64 {
    *p
}

pub fn caller(p: mut_view<i64>) -> i64 {
    atomic_lse_helper(p)
}
```
```text
# Linking an x86_64 COFF object (`Machine = 0x8664`) into an `aarch64-pc-windows-msvc` image:
$ axiomc build --target aarch64-pc-windows-msvc main.ax x64_helper.obj -o app.exe
error[AX_LINK_ARTIFACT_TARGET_MISMATCH]: object `x64_helper.obj` has COFF machine `0x8664` (`x86_64-windows`), expected `0xAA64` (`aarch64-windows`) (E9110)
```

**AXS-WA64-035 — Windows ARM64 Architectural Invariants (`INV-WARM-001`..`INV-WARM-005`, Card Shorthand `INV-WIN-ARM64-01`..`05`).**
Per `spec/invariants.md` (`IG-1` group `[A-Z]+`), task-card references `INV-WIN-ARM64-01..05` register canonically as `INV-WARM-001`..`INV-WARM-005`:
1. **`INV-WARM-001` (`INV-WIN-ARM64-01`):** `CallConv.WinArm64` (`compiler/abi/win_arm64`) enforces strict `X18` TEB reservation, non-variadic `HFA`/`HVA` + even-aligned `i128` rules, variadic `X0..X7`-only (`V0..V7`/`HFA` disabled, `VaList = *mut u8`) lowering, and `X8` POD vs C++ `sret` boundaries (`T694`).
2. **`INV-WARM-002` (`INV-WIN-ARM64-02`):** `compiler/target/aarch64/win_frame` enforces `X15 = alloc_bytes >> 4` + `BL __chkstk` + `SUB SP, SP, X15, LSL #4` (`0xCB2F73FF`) for frames `>= 4 KiB` and emits exact 8-byte packed `.pdata` (`Flag` $\in \{1, 2\}$) and unpacked `.xdata` SEH unwind opcodes (`T694`).
3. **`INV-WARM-003` (`INV-WIN-ARM64-03`):** `compiler/obj/coff_arm64` enforces pre-encoding `verify_mc` (`REQ-TGT-162`) and post-encoding `verify_coff_obj` / `verify_archive` + atomic output (`REQ-TGT-307`), deterministically emitting `IMAGE_FILE_MACHINE_ARM64 (0xAA64)` COFF `.obj` files (`TimeDateStamp = 0`, `.axmeta`/`.axmir`/`.axlto` `0x42000200`), `IMAGE_REL_ARM64_*` (`0x0000`–`0x0011`) relocations, associative `.pdata`/`.xdata` COMDATs, and `0xAA64` `CoffAr` / short-import `.lib` archives without external assemblers (`REQ-TOOL-001`, `T694`).
4. **`INV-WARM-004` (`INV-WIN-ARM64-04`):** `compiler/link/pe_arm64` and `std/sys/windows/arm64` directly link W^X ASLR PE32+ `.exe`/`.dll` images (stripping `.axmeta`/`.axmir`/`.axlto` and running post-encoding `verify_coff_pe`, `REQ-TGT-307`) with 12-byte `X16` import thunks, `±128 MiB` `BRANCH26` veneers, RVA-sorted non-overlapping `.pdata`, `IMAGE_REL_BASED_DIR64` `.reloc`, `[X18, #0x58]` implicit TLS, and CRT-free `__chkstk` / `mainCRTStartup` (`REQ-TOOL-001`, `T695`).
5. **`INV-WARM-005` (`INV-WIN-ARM64-05`):** End-to-end `E16.12` conformance (`tests/conformance/p16/e16_12_windows_arm64`) passes common target conformance suites (`REQ-TGT-197`, `tasks/0522 §159 ABACKEND-51`) and certifies invariant Core semantics (`REQ-TGT-318`), equivalent observable behavior across `aarch64-windows`, `x86_64-windows`, `aarch64-linux`, and `--interp` (`REQ-TGT-157`, `tasks/0521 §156 AARM-63`), `"Xin chào thế giới"` console I/O, variadic/HFA/`X18`/`__chkstk` torture tests, `.dll`+`.lib`+`.exe` round-trips, TLS, `.pdata`/`.xdata` SEH unwinding + `extern "C"` FFI no-unwind abort barriers (`REQ-FFI-004`), and cross-host bit-for-bit determinism (`REQ-TGT-106, 320`, `T696`).

**AXS-WA64-036 — Epic `E16.12` (`T693`–`T696`) End-to-End Traceability Matrix.**

| Task | Owned Paths | Covered `CATALOG.md` Requirements | Governing `SPEC-91` Rules & Invariants |
|---|---|---|---|
| `T693` | `spec/SPEC-91-windows-arm64.md` (+ `INDEX.md`, `diagnostics.md`, `invariants.md`) | `REQ-TGT-114`, `REQ-TGT-124`, `REQ-TGT-127`, `REQ-TGT-129` | `AXS-WA64-001`..`036`; registers `E9100–E9119` & `INV-WARM-001`..`005` |
| `T694` | `compiler/abi/win_arm64`, `compiler/target/aarch64/win_frame`, `compiler/obj/coff_arm64`, `tests/obj/coff_arm64`, `tests/selfhost/{abi,obj}` | `REQ-TGT-124`, `REQ-TGT-125`, `REQ-TGT-130`, `REQ-TGT-131`, `REQ-TGT-149` (+ `REQ-TGT-105, 106, 162, 307`, `REQ-TOOL-001`) | `AXS-WA64-001`..`023`, `AXS-WA64-033`; `INV-WARM-001`..`003` |
| `T695` | `compiler/link/pe_arm64`, `std/sys/windows/arm64`, `tests/link/pe_arm64`, `tests/selfhost/link` | `REQ-TGT-104`, `REQ-TGT-124`, `REQ-TGT-151`, `REQ-TGT-152`, `REQ-TGT-308` (+ `REQ-FFI-004`, `REQ-TGT-106, 307`, `REQ-TOOL-001`) | `AXS-WA64-024`..`033`; `INV-WARM-004` |
| `T696` | `tests/conformance/p16/e16_12_windows_arm64` | `REQ-TGT-124`, `REQ-TGT-157`, `REQ-TGT-197`, `REQ-TGT-318` (+ `REQ-FFI-004`, `REQ-TGT-106, 307, 320`, `REQ-TOOL-001`) | `AXS-WA64-001`..`036`; `INV-WARM-005` |
