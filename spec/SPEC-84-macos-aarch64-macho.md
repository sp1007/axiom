# SPEC-84 — Canonical macOS AArch64 Darwin ABI, Mach-O 64 Object/Image & Ad-Hoc Codesign Specification

- **Status:** draft (T665, 2026-11-03)
- **Owner:** `axiom-architect`
- **Consolidates:** `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-052`, `AXS-EXT-060..062`, `AXS-EXT-070..074`, `AXS-EXT-110`), `spec/SPEC-24-artifact-format-module-interfaces.md`, `spec/SPEC-27-separate-compilation-linker-v2.md`, `spec/SPEC-50-unsafe-ub-ffi.md`, `spec/SPEC-52-freestanding-runtime-composition.md`, `spec/SPEC-54-panic-unwinding.md`, `spec/SPEC-56-module-relative-bindings.md`, `spec/SPEC-81-target-desc-isa-conformance.md`, `spec/SPEC-83-aarch64-linux.md`, `0193`, `0196`, `0217`, `0220`, `tasks/0369`, `tasks/0453`, `tasks/0521`, `tasks/0524`, `tasks/0563`
- **Covers:** `REQ-TGT-147`, `REQ-TGT-296`, `REQ-TGT-297`, `REQ-TGT-298` (and specifies the E16.4 contract for `T666`, `T667`, `T668`: `REQ-TGT-299`..`REQ-TGT-303`, `REQ-TGT-311`..`REQ-TGT-317`)
- **Consumers:** `compiler/abi/apple_arm64`, `compiler/obj/macho`, `compiler/link/macho`, `std/sys/macos`, `tests/obj/macho`, `tests/link/macho`, `tests/selfhost/abi`, `tests/selfhost/obj`, `tests/selfhost/link`, `tests/conformance/p16/e16_4_macos_aarch64`, `T666`, `T667`, `T668`, `T685`, `T689`, `T690`

## Tóm tắt

Tài liệu `SPEC-84` chốt đặc tả chuẩn cho đích `aarch64-macos` (Apple Silicon Darwin ARM64) của Axiom, bao gồm quy ước gọi hàm `CallConv.Aapcs64Darwin`, mô hình tệp đối tượng/thư viện tĩnh/ảnh thực thi & `.dylib` Mach-O 64 bit, chữ ký mã ad-hoc `LC_CODE_SIGNATURE` tự thân, và tầng hệ điều hành `std.sys.macos` qua `libSystem.B.dylib` (Epic `E16.4`):
1. **Tái sử dụng tầng ISA `Arch.AArch64` và chuyên biệt hóa `CallConv.Aapcs64Darwin` (`AXS-MACHO-001`..`011`):** Giữ nguyên bộ chọn lệnh, cấp phát thanh ghi, `verify_mc` và bộ mã hóa 32 bit của `SPEC-83`, chỉ thay lớp ABI Apple ARM64: khóa cứng thanh ghi nền tảng `X18` (cấm mã người dùng đọc/ghi), bên gọi mở rộng dấu/không dấu cho tham số `< 32` bit trong `W0..W7`, xếp chặt tham số tràn ngăn xếp không biến thiên theo kích thước và căn chỉnh tự nhiên (`1/2/4/8/16` byte), luôn đặt mọi tham số biến thiên (`...`) lên ngăn xếp theo ô `8` byte (`va_list = *mut u8`), vùng đỏ `128` byte cho hàm lá, bắt buộc duy trì chuỗi khung `X29` (`FP`), tiền tố `_` cho ký hiệu C/Mach-O, và tách biệt Pointer Authentication (`pauth`) khỏi ngữ nghĩa lõi (`REQ-TGT-147`, `REQ-TGT-296`..`298`).
2. **Tệp đối tượng Mach-O 64 (`MH_OBJECT`), định vị lại ARM64 và kho lưu trữ BSD `ar` (`AXS-MACHO-012`..`019`):** Chuẩn hóa `mach_header_64` (`MH_MAGIC_64 = 0xFEEDFACF`, `CPU_TYPE_ARM64 = 0x0100000C`, `MH_SUBSECTIONS_VIA_SYMBOLS`), ánh xạ tiết đoạn ngữ nghĩa sang `__TEXT` / `__DATA_CONST` / `__DATA`, bảng ký hiệu `nlist_64`, toàn bộ tập định vị lại `ARM64_RELOC_*` (`UNSIGNED`, `SUBTRACTOR`, `BRANCH26`, `PAGE21`, `PAGEOFF12`, `GOT_LOAD_*`, `TLVP_LOAD_*`, `ADDEND`), và thư viện tĩnh BSD 4.4 `ar` (`__.SYMDEF SORTED`, tên dài `#1/<len>`).
3. **Trình liên kết Mach-O 64 bản địa (`MH_EXECUTE` & `MH_DYLIB`), căn chỉnh trang 16 KiB, `dyld` chained fixups, export trie và `LC_CODE_SIGNATURE` (`AXS-MACHO-020`..`026`):** Căn chỉnh phân đoạn theo trang ảo 16 KiB (`0x4000`) trên Apple Silicon (`__PAGEZERO`, `__TEXT`, `__DATA_CONST`, `__DATA`, `__LINKEDIT`) tuân thủ nghiêm ngặt W^X, sinh cầu nối `__TEXT,__stubs` + `__DATA_CONST,__got`, chuỗi con trỏ `LC_DYLD_CHAINED_FIXUPS` (`DYLD_CHAINED_PTR_64_OFFSET`), cây tiền tố ULEB128 `LC_DYLD_EXPORTS_TRIE`, và khối chữ ký ad-hoc `LC_CODE_SIGNATURE` (`CS_MAGIC_EMBEDDED_SIGNATURE`, `CS_MAGIC_CODEDIRECTORY` băm SHA-256 từng trang 4 KiB với `CS_ADHOC | CS_LINKER_SIGNED`) không cần Xcode hay `ld64`/`codesign` bên ngoài.
4. **Ranh giới nền tảng `libSystem.B.dylib`, danh mục stub `.tbd` tích hợp và `std.sys.macos` (`AXS-MACHO-027`..`036`):** Cấm phát lệnh syscall thô `SVC #0x80` không ổn định của nhân XNU; liên kết động tới `/usr/lib/libSystem.B.dylib` (kèm bộ đọc `.tbd` và danh mục xuất tích hợp sẵn để biên dịch chéo từ Windows/Linux không cần macOS SDK), khởi chạy qua `LC_MAIN` (`__axiom_start`), hỗ trợ Compact Unwind (`__TEXT,__unwind_info`), và xác lập ma trận kiểm thử tương thích `E16.4`.

---

## 1. `aarch64-macos` Target Identity, Layering & Apple ARM64 Darwin ABI (`AXS-MACHO-001`..`011`)

**AXS-MACHO-001 — `aarch64-macos` `TargetDesc` Record & Orthogonal Layer Separation.** `compiler/target/desc` registers `aarch64-macos` (accepting `--target aarch64-macos` and vendor/ABI aliases `aarch64-apple-darwin`, `arm64-apple-darwin`, and version-suffixed `aarch64-apple-macosx*`) as an immutable `TargetDesc` record (`0196 §1–2, §40 AMACHO-20, 23, 38`, `tasks/0521 §61, §63, AARM-20, 22, 30`, `SPEC-81 AXS-TGTD-002..006`):
- `target_id = TargetId.AArch64Macos`, `arch = Arch.AArch64`, `os = Os.Macos`, `env = Env.Darwin`, `pointer_width_bits = 64`, `endian = Endian.Little`;
- `default_call_conv = CallConv.Aapcs64Darwin`, `object_format = ObjectFormat.MachO`, `archive_format = ArchiveFormat.BsdAr`, `image_format = ImageFormat.MachO` (`MH_EXECUTE` for `--kind exe`, `MH_DYLIB` `lib<name>.dylib` for `--kind dll`, `MH_OBJECT` `.o` for `--kind obj` / `--emit=obj`, and BSD `ar` `lib<name>.a` for `--kind lib`);
- `stack_align = 16`, `shadow_space = 0`, `red_zone = 128`, `page_size = 16384` (`0x4000`, 16 KiB Apple Silicon VM page granularity).
The `Arch.AArch64` ISA layer (`RegisterFile` unit topology, `IsaTable`, legalizer, instruction selector, `LinearScan`/`Hybrid` register allocators, `verify_mc`, and 32-bit A64 encoder from `SPEC-83`) is reused unchanged; conversely, `compiler/obj/macho` and `compiler/link/macho` live outside `compiler/target/aarch64` so `x86_64-apple-darwin` slices (`SPEC-90`, `E16.11`) share the identical Mach-O object/image infrastructure (`0196 §1–2, AMACHO-20, 23`). [0196 §1–2, AMACHO-20, 23, 38; tasks/0521 §61, §63; SPEC-81 AXS-TGTD-002..006; SPEC-83 AXS-A64-001]

**AXS-MACHO-002 — Apple Silicon Baseline `TargetFeatureSet` & Pointer Authentication (`pauth`) System Boundary.** On `TargetId.AArch64Macos`, the default CPU baseline (`cpu_model = "apple-m1"`, Armv8.4-A/Armv8.5-A Apple Silicon minimum on macOS 11.0+) enables `{ fp, neon, lse, fp16, dotprod, crc, aes, sha2, sha3, rcpc }` in `TargetFeatureSet` (`SPEC-81 AXS-TGTD-007..010`, `SPEC-83 AXS-A64-003`), so single-instruction LSE atomics (`CAS*`, `LDADD*`, `SWP*`, `AXS-A64-035`) and `LDAPR` (`+rcpc`) are legal by default unless lowered via `--cpu generic` or `-lse`. Disabling mandatory ABI baseline `-neon` or `-fp` on hosted `aarch64-macos` is rejected with `AX_TARGET_UNKNOWN_FEATURE`. Pointer Authentication (`+pauth`, `PACIASP`/`AUTIASP`/`BLRAA`/`RETAB`, `arm64e`) and Branch Target Identification (`+bti`) are strictly target ABI/system capabilities, **never** Core language pointer, `view<T>`, `mut_view<T>`, or provenance semantics (`tasks/0521 §91–92, §156 AARM-53`, `REQ-TGT-147`): standard macOS user-space builds emit `CPU_SUBTYPE_ARM64_ALL (0)` without implicit pointer signing, while explicit `+pauth` functions emit prologue/epilogue return-address signing transparently at the Machine IR frame layer without altering `MIR` or `Axiom LIR`. [tasks/0521 §91–92, §156 AARM-53; SPEC-81 AXS-TGTD-007..010; SPEC-83 AXS-A64-003; REQ-TGT-147]

**AXS-MACHO-003 — Shared AAPCS64 Register & Aggregate Classification Foundation.** Except for the explicit Darwin specializations in `AXS-MACHO-004`..`010`, `CallConv.Aapcs64Darwin` (`compiler/abi/apple_arm64`) shares the `CallConv.Aapcs64` register convention (`SPEC-83 AXS-A64-013..018`, `tasks/0524 §112 ABACKEND-71..72`, `REQ-TGT-296`, `REQ-TGT-297`):
- Up to 8 GPR argument/return registers `X0..X7` (`W0..W7`) for integers, raw pointers, single-word views, `fn` pointers, 2-word fat pointers (`Str`, `view<[T]>`, `mut_view<[T]>`, `view<dyn Trait>`), and non-HFA/HVA composites of size `1..=16` bytes (`1` or `2` 8-byte doublewords).
- Up to 8 FP/SIMD argument/return registers `V0..V7` (`S0..S7`, `D0..D7`, `Q0..Q7`) for `f32`, `f64`, 64/128-bit vectors, and 1-to-4-element Homogeneous Floating-point / Short-Vector Aggregates (`HFA` / `HVA`).
- Non-HFA/HVA composites with `size > 16` bytes pass by caller-allocated 16-byte-aligned temporary copy via a 64-bit pointer in `X[NGRN]` (or an 8-byte pointer slot on the stack when `NGRN == 8`), and return via the Indirect Result Location Register `X8` (`XR` / `sret`) **without** consuming `X0`.
- Callee-saved registers are `X19..X28`, `X29` (`FP`), `SP`, and the low 64 bits `D8..D15` of `V8..V15`; `X0..X17`, `X30` (`LR`), `V0..V7`, upper bits `[64..128)` of `V8..V15`, `V16..V31`, and `NZCV` are caller-saved. [0193 §5–6; 0196 §1–2; tasks/0521 §43–48, §61; tasks/0524 §112 ABACKEND-71..72; SPEC-83 AXS-A64-013..018; REQ-TGT-296, REQ-TGT-297]

**AXS-MACHO-004 — Strict Reservation of Apple Platform Register `X18`.** On `aarch64-macos`, Apple reserves `X18` (`W18`) exclusively for kernel/platform thread and system state (`0196 §1`, `tasks/0521 §60–61, AARM-30`, `SPEC-81 AXS-TGTD-017`). `compiler/abi/apple_arm64` marks `X18` as `RegRole.Reserved` and excludes `X18` from `allocatable_mask`, `caller_saved_mask`, `callee_saved_mask`, and scratch sets. User functions, `std/sys/macos` routines, veneers, and fiber context switches **must never** read, write, spill, reload, or temporarily clobber `X18`/`W18`; `verify_mc` rejects any Machine IR instruction on `aarch64-macos` that references `X18` or `W18` (`AX_VERIFY_MC_ILLEGAL`). [0196 §1; tasks/0521 §60–61, AARM-30; SPEC-81 AXS-TGTD-017]

**AXS-MACHO-005 — Caller & Callee Sign/Zero Extension of Sub-32-Bit Scalars (`< 32` Bits).** Whereas standard AAPCS64 leaves upper bits `[width..32)` of `Wn` unspecified for narrow scalar parameters, `CallConv.Aapcs64Darwin` mandates explicit 32-bit promotion at every register call/return boundary (`T665`, `T666`):
- Before every `BL`/`BLR` (and tail-call `B`/`BR`), the **caller** zero-extends `bool` (`AND Wd, Wn, #1`), `u8` (`UXTB`), and `u16` (`UXTH`) to 32 bits and sign-extends `i8` (`SXTB`) and `i16` (`SXTH`) to 32 bits in `W0..W7` (which architecturally zeroes bits `[32..64)` of `X0..X7`).
- Before `RET`, the **callee** likewise zero- or sign-extends narrow return values (`bool`, `u8`, `u16`, `i8`, `i16`) to 32 bits in `W0`. Callees receiving narrow arguments from foreign C/Objective-C/Swift callers on `aarch64-macos` may rely on incoming `W0..W7` bits `[0..32)` already being properly extended. [0196 §1–2; SPEC-50 AXS-UNS-032]

**AXS-MACHO-006 — Tightly Packed Natural-Alignment Stack Slots & Unrounded Even/Odd 16-Byte GPR Pairs.** `CallConv.Aapcs64Darwin` diverges from standard AAPCS64 (`SPEC-83 AXS-A64-013, 017`) in two layout rules for **non-variadic** parameters (`T665`, `T666`):
1. **Unrounded 16-byte register pairs:** When a fixed 16-byte-aligned parameter (`i128`, `u128`, or a 16-byte-aligned `<= 16`-byte composite) is assigned to GPRs, Apple ARM64 **does not** round `NGRN` up to an even register: if `NGRN <= 6`, the value occupies `(X[NGRN], X[NGRN + 1])` (including odd-even pairs such as `X1:X2`); if `NGRN == 7`, `NGRN` advances to `8` (never splitting a parameter half in `X7` and half on the stack) and the parameter spills to the stack.
2. **Natural-alignment stack packing:** Spilled non-variadic fixed arguments in the outgoing stack area (`NSAA`, starting at `[SP + 0]`) are packed at their **exact natural byte size and natural alignment** (`slot_align = align_of(T)` $\in \{1, 2, 4, 8, 16\}$, `slot_size = size_of(T)`, with `bool` occupying 1 byte at alignment 1) rather than rounding every argument up to an 8-byte slot:
   $$\text{offset}_i = \text{align\_up}(\text{NSAA}, \text{align\_of}(T_i)), \qquad \text{NSAA}' = \text{offset}_i + \text{size\_of}(T_i)$$
   For example, after `X0..X7` are exhausted, four spilled `u8` parameters followed by an `i32` occupy `[SP + 0]`, `[SP + 1]`, `[SP + 2]`, `[SP + 3]`, and `[SP + 4..8)` (`8` bytes total instead of `40` bytes on Linux AAPCS64). Total outgoing stack allocation is rounded up to a multiple of `16` bytes at the call site. [0196 §1–2; tasks/0453 §194.18; tasks/0524 ABACKEND-72; REQ-TGT-297]

**AXS-MACHO-007 — Variadic `extern "C"` Stack-Only Argument Passing & Single-Pointer `va_list`.** Under `CallConv.Aapcs64Darwin`, variadic calls (`extern "C" fn(fixed..., ...)`) follow Apple's stack-only variadic convention rather than standard AAPCS64 (`SPEC-83 AXS-A64-022`):
1. Named fixed parameters preceding `...` are assigned to `X0..X7`, `V0..V7`, and packed natural-alignment stack slots exactly as in `AXS-MACHO-003`..`006`.
2. At the `...` boundary, register assignment terminates (`NGRN = 8`, `NSRN = 8`) and `NSAA` is rounded up to an **8-byte boundary** (`var_base = align_up(fixed_nsaa, 8)`).
3. Every anonymous variadic argument is **always placed on the stack**, promoted per C default variadic promotions (`bool`/`u8`/`u16` zero-extended and `i8`/`i16` sign-extended to 32-bit `i32`/`u32` stored in an 8-byte slot, `f32` widened via `FCVT Dn, Sn` to `f64` stored in an 8-byte slot), with each argument aligned to `max(8, align_of(T))` and sized to `align_up(size_of(T), 8)` (`> 16`-byte composites pass as an 8-byte pointer to a caller-allocated copy).
4. Consequently, Darwin ARM64 `std.ffi.VaList` (`va_list`) is a single 8-byte `@repr(transparent)` pointer `{ ptr: *mut u8 }` advancing through the contiguous 8-byte-aligned variadic stack array. [0196 §1–2; tasks/0453 §194.18; tasks/0521 §151; SPEC-50 AXS-UNS-032]

**AXS-MACHO-008 — 128-Byte Leaf Red Zone & Mandatory 16-Byte `SP` Alignment.** Unlike `aarch64-linux` (`red_zone = 0`, `SPEC-83 AXS-A64-019`), the Darwin XNU kernel guarantees a **128-byte leaf red zone** immediately below `SP` (`[SP - 128 .. SP)`) that asynchronous user-space signal handlers never overwrite (`TargetDesc.red_zone = 128`):
- Pure leaf functions in `--profile hosted` (making zero outgoing calls, modifying neither `X30` nor `X19..X28`/`D8..D15`, and requiring $\le 128$ bytes of local/spill space) may address `[SP - offset]` ($1 \le \text{offset} \le 128$) via `LDUR`/`STUR`/`LDP`/`STP` without decrementing `SP`.
- The red zone is disabled (`red_zone = 0`) when `--no-red-zone` is passed or under `--profile freestanding` / `--profile kernel`.
- Hardware `SP` alignment (`SP % 16 == 0`) is strictly enforced at function entry, at every outgoing `BL`/`BLR`, and at every instruction using `SP` as a base register (`SPEC-83 AXS-A64-019, 037`). [0193 §8; 0196 §1; SPEC-81 AXS-TGTD-005, 011]

**AXS-MACHO-009 — Mandatory `X29` (`FP`) Frame-Pointer Chain & Stack Probing.** Apple platforms mandate an unbroken `X29` (`FP`) frame-record chain for kernel `stackshot` sampling, crash reporting, and Compact Unwind (`0196 §27–28`, `tasks/0524 ABACKEND-75`, `REQ-TGT-300`):
- Every non-leaf function (and any function that allocates a stack frame outside the 128-byte leaf red zone) establishes a 16-byte frame record `[prev_X29, saved_X30]` pointed to **directly** by `X29` (`*(u64*)X29 == caller_X29` and `*(u64*)(X29 + 8) == saved_LR`, with `X29 % 16 == 0` and `caller_X29 > X29` or `caller_X29 == 0` at the root frame).
- Standard prologue layout places callee-saved register pairs below or above the frame record (`STP X29, X30, [SP, #-N]!` + `MOV X29, SP` for $N \le 504$, or `SUB SP, SP, #frame_size` + `STP X29, X30, [SP, #fp_off]` + `ADD X29, SP, #fp_off` so `X29` always points directly to `[prev_X29, saved_X30]`). `X29` is never repurposed as a general allocatable scratch register on `aarch64-macos` at any optimization level.
- Functions whose total frame size $N \ge 4096$ bytes emit the deterministic 4 KiB page-probing loop (`SUB SP, SP, #4096` + `STR XZR, [SP]`) before touching lower frame addresses (`ADR-0003`, `SPEC-83 AXS-A64-021`), ensuring neither 4 KiB nor 16 KiB guard pages can be skipped. [0196 §27–28; ADR-0003; tasks/0524 ABACKEND-75; SPEC-83 AXS-A64-020..021; REQ-TGT-300]

**AXS-MACHO-010 — Leading-Underscore (`_`) Mach-O Symbol Decoration.** Darwin Mach-O prepends a single leading underscore `_` to all C ABI and linkage symbol names (`0196 §11–12, AMACHO-32`):
- Internal compiler representations (`AST`, `HIR`, `THIR`, `Verified MIR`, `OptIR`, `Axiom LIR`, and format-neutral `LinkIR`) store undecorated logical symbol names (`"malloc"`, `"main"`, `"_exit"`, `@export("add")` $\rightarrow$ `"add"`, and canonical `_AX...` mangled Axiom symbols).
- `compiler/obj/macho` and `compiler/link/macho` prepend exactly one `_` at serialization time (`"malloc"` $\rightarrow$ `"_malloc"`, `"_exit"` $\rightarrow$ `"__exit"`, `"add"` $\rightarrow$ `"_add"`, `"_AX..."` $\rightarrow$ `"__AX..."`) in `nlist_64` string tables, `LC_DYLD_CHAINED_FIXUPS` import tables, and `LC_DYLD_EXPORTS_TRIE`.
- Temporary assembler/section-local labels (jump tables, constant pools, unwind anchors) use Mach-O private label prefixes `L` or `l` (`LBB0_1`, `l_anon.0`) **without** a leading `_` so linkers omit them from public symbol tables. Linker diagnostics (`AX_LINK_UNDEFINED_SYMBOL`, `AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_DUPLICATE_EXPORT`) strip the Mach-O `_` prefix and demangle Axiom symbols before reporting (`SPEC-27 AXS-LNK-014`). [0196 §11–12, AMACHO-32; SPEC-27 AXS-LNK-014]

**AXS-MACHO-011 — Semantic Transparency of ABI, Register Allocation, Spilling, Addressing & Optimization.** `compiler/abi/apple_arm64` and the `aarch64-macos` backend pipeline strictly uphold the backend semantic preservation contracts (`tasks/0524 §112 ABACKEND-71..78, 86..88`, `SPEC-81 AXS-TGTD-019..021, 039`, `REQ-TGT-296`..`303`, `REQ-TGT-311`..`313`):
1. `CallConv.Aapcs64Darwin` lowering never alters source-level type, ownership, or capability semantics (`ABACKEND-71`, `REQ-TGT-296`), and aggregate ABI classification (`HFA`/`HVA`, `<= 16`B GPRs, `> 16`B caller copy, `X8` `sret`) remains strictly target-specific (`ABACKEND-72`, `REQ-TGT-297`).
2. Register allocation (`ABACKEND-73`, `REQ-TGT-298`), physical stack-slot spilling/reloading (`ABACKEND-74`, `REQ-TGT-299`), and `X29`-chained frame lowering (`ABACKEND-75`, `REQ-TGT-300`) preserve ownership, `view<T>`/`mut_view<T>` aliasing guarantees, deterministic `Drop`, and unwinding semantics.
3. Mach-O `@PAGE`/`@PAGEOFF`, `@GOTPAGE`/`@GOTPAGEOFF`, and `@TLVPPAGE` address lowerings are target implementation details that preserve pointer provenance and memory access semantics (`ABACKEND-76..77`, `REQ-TGT-301..302`), while branch relaxation, `__stubs`, and `±128 MiB` veneers preserve semantic CFG behavior (`ABACKEND-78`, `REQ-TGT-303`).
4. Target-specific optimizations (`LDP`/`STP` pairing, GOT-to-page relaxation, dead-atom stripping) never weaken safety guarantees (`ABACKEND-86`, `REQ-TGT-311`) or alter observable behavior (`ABACKEND-87`, `REQ-TGT-312`), while permitting distinct physical layouts across targets for the same semantic type (`ABACKEND-88`, `REQ-TGT-313`). [tasks/0524 §112 ABACKEND-71..78, 86..88; SPEC-81 AXS-TGTD-019..021, 039; REQ-TGT-296..303, REQ-TGT-311..313]

---

## 2. Mach-O 64 Object Model (`MH_OBJECT`), Sections, Relocations & BSD `ar` (`AXS-MACHO-012`..`019`)

**AXS-MACHO-012 — Format-Neutral Object IR Boundary & Explicit Field-by-Field Serialization.** `compiler/obj/macho` lowers the format-independent `ObjectArtifact` (`SPEC-24 AXS-ART-020..024`, `0217 §4–17`, `tasks/0369 §2–9, ALINK-20..25`) into Mach-O 64 bytes without exposing Mach-O headers, `nlist_64`, or relocation bitfields to `LIR` or `Arch.AArch64` (`0196 §2–3, §31, AMACHO-20..24`). Every header, load command, section, symbol, and relocation record is serialized field-by-field with explicit endian writers (`write_u32_le`, `write_u64_le`, bounds-checked `ByteWriter`); raw host-memory struct dumping (`fwrite(&hdr, ...)`) is strictly forbidden (`tasks/0563 §304.30–32, AIMG-32..34, 59`). [0196 §2–3, §31, AMACHO-20..24; 0217 §4–17; tasks/0369 §2–9; tasks/0563 §304.30–32, AIMG-32..34, 59; SPEC-24 AXS-ART-020]

**AXS-MACHO-013 — `mach_header_64` Schema, CPU Constants & File-Type Flags.** Every 64-bit Mach-O artifact begins at offset `0` with a 32-byte little-endian `mach_header_64` (`0196 §4–5`, `tasks/0563 §304.21`):
- `magic: u32 = MH_MAGIC_64 (0xFEEDFACF)`, `cputype: i32 = CPU_TYPE_ARM64 (0x0100000C)`, `cpusubtype: i32 = CPU_SUBTYPE_ARM64_ALL (0x00000000)` (`CPU_SUBTYPE_ARM64E = 0x00000002` only when `+pauth` `arm64e` ABI is explicitly targeted), `ncmds: u32`, `sizeofcmds: u32`, `reserved: u32 = 0`.
- `filetype` and canonical `flags`:
  - `MH_OBJECT (0x1)` (`.o`): `flags = MH_SUBSECTIONS_VIA_SYMBOLS (0x00002000)`.
  - `MH_EXECUTE (0x2)` (executable): `flags = MH_NOUNDEFS (0x1) | MH_DYLDLINK (0x4) | MH_TWOLEVEL (0x80) | MH_PIE (0x00200000)` (`| MH_HAS_TLV_DESCRIPTORS (0x00800000)` when TLS sections exist; `0` in `--profile freestanding` static images).
  - `MH_DYLIB (0x6)` (`lib<name>.dylib`, `--kind dll`): `flags = MH_NOUNDEFS (0x1) | MH_DYLDLINK (0x4) | MH_TWOLEVEL (0x80) | MH_NO_REEXPORTED_DYLIBS (0x00100000)` (`| MH_HAS_TLV_DESCRIPTORS` if TLS is present). [0196 §4–5; tasks/0563 §304.21]

**AXS-MACHO-014 — Semantic-to-Mach-O `(segname, sectname)` Mapping & `section_64` Binary Field Order.** Each 80-byte little-endian `section_64` descriptor maps semantic `SectionKind` categories to canonical `(segname: [16]u8, sectname: [16]u8, flags: u32, align_log2: u32)` (`0196 §7–8, §25, §27, §40 AMACHO-24, 33..34`, `0217 §5–10, §51`, `tasks/0563 §304.22`). Although Mach-O assembly notation writes `segname,sectname` (e.g. `__TEXT,__text`), the 80-byte binary `section_64` struct serializes **`sectname: [16]u8` first at `+0..16` and `segname: [16]u8` second at `+16..32`**, followed by `addr: u64` (`+32`), `size: u64` (`+40`), `offset: u32` (`+48`), `align: u32` (`+52`, $\log_2$ alignment), `reloff: u32` (`+56`), `nreloc: u32` (`+60`), `flags: u32` (`+64`), `reserved1: u32` (`+68`), `reserved2: u32` (`+72`), and `reserved3: u32 = 0` (`+76`):

| Semantic Category | `segname,sectname` | `section_64.flags` | Min `align` ($2^k$) | Notes |
|---|---|---|---|---|
| Executable code | `__TEXT,__text` | `S_REGULAR (0x0) \| S_ATTR_PURE_INSTRUCTIONS (0x80000000) \| S_ATTR_SOME_INSTRUCTIONS (0x400)` | $2^2 = 4\text{ B}$ | 32-bit A64 words |
| Dynamic call stubs | `__TEXT,__stubs` | `S_SYMBOL_STUBS (0x8) \| S_ATTR_PURE_INSTRUCTIONS \| S_ATTR_SOME_INSTRUCTIONS` | $2^2 = 4\text{ B}$ | Linker-synthesized (`reserved2 = 12`) |
| NUL-terminated UTF-8 strings | `__TEXT,__cstring` | `S_CSTRING_LITERALS (0x2)` | $2^0 = 1\text{ B}$ | Deduplicated by linker |
| Pure read-only constants | `__TEXT,__const` | `S_REGULAR (0x0)` | $\max(1, \text{align}(T))$ | No pointer fixups |
| Compact unwind / DWARF CFI | `__TEXT,__unwind_info`, `__TEXT,__eh_frame` | `S_REGULAR (0x0)` (`__LD,__compact_unwind` in `.o`) | $2^2$ / $2^3$ | Generated from `UnwindInfo` |
| Non-lazy GOT pointer slots | `__DATA_CONST,__got` | `S_NON_LAZY_SYMBOL_POINTERS (0x6)` | $2^3 = 8\text{ B}$ | Linker-synthesized, `SG_READ_ONLY` |
| Relocated read-only data (vtables) | `__DATA_CONST,__const` | `S_REGULAR (0x0)` | $2^3 = 8\text{ B}$ | Rebased by `dyld`, then read-only |
| Mutable initialized statics | `__DATA,__data` | `S_REGULAR (0x0)` | $\max(1, \text{align}(T))$ | Read-write |
| Zero-initialized statics | `__DATA,__bss` | `S_ZEROFILL (0x1)` | $\max(1, \text{align}(T))$ | `offset = 0`, 0 file bytes (`AIMG-29`) |
| Thread-local descriptors & data | `__DATA,__thread_vars`, `__DATA,__thread_data`, `__DATA,__thread_bss` | `S_THREAD_LOCAL_VARIABLES (0x13)`, `S_THREAD_LOCAL_REGULAR (0x11)`, `S_THREAD_LOCAL_ZEROFILL (0x12)` | $2^3 = 8\text{ B}$ / $\text{align}(T)$ | `@thread_local static` (`AXS-MACHO-018`) |
| DWARF debug / Axiom IR metadata | `__DWARF,__debug_*` / `__AXIOM,__axmeta` | `S_REGULAR \| S_ATTR_DEBUG (0x02000000)` | $2^0 = 1\text{ B}$ | `__AXIOM` stripped from final images |

Custom `@section("__SEG,__sect")` attributes (`SPEC-52 AXS-FRE-014`) validate `segname` and `sectname` lengths ($\le 16$ ASCII bytes each, `AX_TYPE_INVALID_SECTION`). [0196 §7–8, §25, §27, §40 AMACHO-24, 33..34; 0217 §5–10, §51; tasks/0563 §304.22, §304.45 AIMG-29; SPEC-24 AXS-ART-024; SPEC-52 AXS-FRE-014]

**AXS-MACHO-015 — `MH_OBJECT` Relocatable Object Load Commands.** `compiler/obj/macho` emits four deterministic load commands in every `MH_OBJECT` file (`0196 §6, §31, AMACHO-21`, `T666`):
1. `LC_SEGMENT_64 (0x19)` with an empty 16-byte `segname` (`""`), `vmaddr = 0`, wrapping all emitted `section_64` headers in canonical section order with contiguous section VMAs starting at `0`.
2. `LC_BUILD_VERSION (0x32)` (`24` bytes): `platform = PLATFORM_MACOS (1)`, `minos = 0x000B0000` (`11.0.0`, configurable via `--macos-version-min`), `sdk = 0x000B0000`, `ntools = 0`.
3. `LC_SYMTAB (0x02)` (`24` bytes): `symoff`, `nsyms`, `stroff`, `strsize` (8-byte padded string pool starting with `"\x00"`).
4. `LC_DYSYMTAB (0x0B)` (`80` bytes): partitions `nlist_64` into three contiguous ranges: `[0 .. nlocalsym)` (locals), `[iextdefsym .. iextdefsym + nextdefsym)` (defined externals sorted ascending by Mach-O name), and `[iundefsym .. iundefsym + nundefsym)` (undefined externals sorted ascending by Mach-O name). [0196 §6, §31, AMACHO-21]

**AXS-MACHO-016 — `nlist_64` Symbol Table, Visibility & `MH_SUBSECTIONS_VIA_SYMBOLS` Atom Model.** Each symbol in `LC_SYMTAB` is a 16-byte little-endian `nlist_64 { n_strx: u32, n_type: u8, n_sect: u8, n_desc: u16, n_value: u64 }` (`0196 §11`, `SPEC-27`, `SPEC-55`):
- **Storage & visibility:** Module-private items emit `n_type = N_SECT (0x0E)` (`n_sect` = 1-based section index, `n_value` = section VMA). Cross-module non-`@export` `pub` items emit private externals `N_SECT | N_EXT (0x01) | N_PEXT (0x10)` (resolved across `.o` files at link time, then internalized and excluded from `LC_DYLD_EXPORTS_TRIE`). `@export` and `@no_mangle` items emit `N_SECT | N_EXT`. Generic/inline ODR items add `n_desc |= N_WEAK_DEF (0x0080)`. Fixed-address `@at(addr)` overlays/symbols emit `n_type = N_ABS (0x02) | N_EXT` (`n_sect = NO_SECT (0)`, `n_value = addr`). External imports emit `n_type = N_UNDF (0x00) | N_EXT` (`n_desc |= N_WEAK_REF (0x0040)` for weak imports).
- **Atom dead-stripping (`MH_SUBSECTIONS_VIA_SYMBOLS`):** Every non-`L*` symbol in a section begins an independent atom `[sym.n_value .. next_sym.n_value)` so `compiler/link/macho` (`--gc-sections`, `SPEC-27 AXS-LNK-020..023`) and Apple `ld64` can garbage-collect unreferenced functions and statics at atom granularity. [0196 §11; SPEC-27 AXS-LNK-010..023; SPEC-55 AXS-ADR-022]

**AXS-MACHO-017 — 8-Byte `relocation_info` Encoding & `ARM64_RELOC_*` Relocation Set.** Each Mach-O relocation record (`section_64.reloff`, count `nreloc`, sorted in descending `r_address` order for `ld64` compatibility or deterministic canonical order) is an 8-byte little-endian pair `(r_address: i32, r_packed: u32)` where `r_packed = (r_symbolnum & 0x00FF_FFFF) | ((r_pcrel as u32) << 24) | ((r_length as u32) << 25) | ((r_extern as u32) << 27) | ((r_type as u32) << 28)` (`0196 §9–10, §40 AMACHO-27`, `T666`). When `r_extern = 1`, `r_symbolnum` is a 0-based `nlist_64` index; when `r_extern = 0`, `r_symbolnum` is a 1-based `section_64` index. `compiler/obj/macho` and `compiler/link/macho` support the complete `ARM64_RELOC_*` set:

| Code | Name | `pcrel` / `len` | Target & Relocation Formula (`P` = instr/slot VMA, `S` = target VMA, `A` = addend) |
|---|---|---|---|
| `0` | `ARM64_RELOC_UNSIGNED` | `0`, `2` (`32`b) or `3` (`64`b) | Data pointer `S + A` (`A` stored inline in little-endian slot; static TLS template offset at `tlv_descriptor +16`; forbidden in `__TEXT`) |
| `1` | `ARM64_RELOC_SUBTRACTOR` | `0`, `2` or `3` | Prefix record before `UNSIGNED` at identical `r_address`: `(S_unsigned - S_sub) + A` |
| `2` | `ARM64_RELOC_BRANCH26` | `1`, `2` | `B`/`BL` `imm26 = (S + A - P) >> 2` (`±128 MiB`, 4-byte aligned) |
| `3` | `ARM64_RELOC_PAGE21` | `1`, `2` | `ADRP` `imm21 = (((S + A) & ~0xFFF) - (P & ~0xFFF)) >> 12` (**4 KiB** hardware page delta, `±4 GiB`) |
| `4` | `ARM64_RELOC_PAGEOFF12` | `0`, `2` | `ADD` `imm12 = (S + A) & 0xFFF`, or scaled `LDR`/`STR` `imm12 = ((S + A) & 0xFFF) >> scale` |
| `5` | `ARM64_RELOC_GOT_LOAD_PAGE21` | `1`, `2` | `ADRP Xd, sym@GOTPAGE`: `((GOT(S) & ~0xFFF) - (P & ~0xFFF)) >> 12` (`r_extern = 1`, `A = 0`) |
| `6` | `ARM64_RELOC_GOT_LOAD_PAGEOFF12` | `0`, `2` | `LDR Xd, [Xn, sym@GOTPAGEOFF]`: `(GOT(S) & 0xFFF) >> 3` (`8`-byte aligned GOT slot) |
| `7` | `ARM64_RELOC_POINTER_TO_GOT` | `1`/`2` or `0`/`3` | `32`-bit PC-relative `GOT(S) - P` (personality/table slot) or `64`-bit `GOT(S)` |
| `8` | `ARM64_RELOC_TLVP_LOAD_PAGE21` | `1`, `2` | `ADRP Xd, sym@TLVPPAGE`: 4 KiB page delta to local `tlv_descriptor` or external GOT slot |
| `9` | `ARM64_RELOC_TLVP_LOAD_PAGEOFF12` | `0`, `2` | `LDR Xd, [Xn, sym@TLVPPAGEOFF]`: relaxed to `ADD` for linkage-unit-local `tlv_descriptor` |
| `10` | `ARM64_RELOC_ADDEND` | `0`, `2` | Prefix record (`r_extern = 0`) supplying signed 24-bit `r_symbolnum` addend `A` to next `PAGE21`/`PAGEOFF12`/`BRANCH26` |

Hardware A64 `ADRP` (`ARM64_RELOC_PAGE21`, `GOT_LOAD_PAGE21`, `TLVP_LOAD_PAGE21`) **always** masks and shifts by **4 KiB (`0x1000`, `12` bits)** even though Apple Silicon Mach-O segments align to **16 KiB (`0x4000`)** VM pages. Prefix records (`ARM64_RELOC_ADDEND`, `ARM64_RELOC_SUBTRACTOR`) must immediately precede their paired relocation at the exact same `r_address`; unpaired or out-of-range relocations emit `AX_LINK_BAD_OBJECT` or `AX_LINK_RELOC_OUT_OF_RANGE`. [0196 §9–10, §40 AMACHO-27; SPEC-83 AXS-A64-041]

**AXS-MACHO-018 — Darwin Thread-Local Storage (`@thread_local`) Descriptor Model.** On `aarch64-macos`, `@thread_local static` variables lower via Darwin Thread-Local Variables (`TLV`) rather than ELF `TPIDR_EL0` offsets (`0217 §10, §51, §72 ALINK-36`, `0220 §16`, `tasks/0369 §17`, `tasks/0521 §80`):
1. Initialized and zero-initialized TLS payloads are placed in `__DATA,__thread_data` (`S_THREAD_LOCAL_REGULAR = 0x11`) and `__DATA,__thread_bss` (`S_THREAD_LOCAL_ZEROFILL = 0x12`), setting `MH_HAS_TLV_DESCRIPTORS (0x00800000)` in `mach_header_64.flags`.
2. Each `@thread_local` symbol emits a 24-byte `tlv_descriptor { thunk: *const fn, key: u64, offset: u64 }` in `__DATA,__thread_vars` (`S_THREAD_LOCAL_VARIABLES = 0x13`):
   - `+0` (`thunk`, `8`B): emits an `ARM64_RELOC_UNSIGNED` (`r_length = 3`, `r_extern = 1`) relocation in `MH_OBJECT` referencing `_tlv_bootstrap` (`"__tlv_bootstrap"` in the Mach-O string table, imported from `libSystem.B.dylib`), which `compiler/link/macho` lowers to a `DYLD_CHAINED_PTR_64_OFFSET` **bind** (`bind = 1`) entry in `MH_EXECUTE` / `MH_DYLIB`.
   - `+8` (`key`, `8`B): initialized to `0` (`pthread_key_t` populated lazily by `dyld` / `libSystem` at runtime; **no** relocation and **no** chained-fixup entry).
   - `+16` (`offset`, `8`B): in `MH_OBJECT` (`T666`), emits an `ARM64_RELOC_UNSIGNED` (`r_length = 3`) relocation targeting the backing TLS symbol in `__DATA,__thread_data` or `__DATA,__thread_bss` (because the merged template offset across `.o` files is unknown until link time). In `MH_EXECUTE` / `MH_DYLIB` (`compiler/link/macho`, `T667`), the static linker resolves that relocation in `S_THREAD_LOCAL_VARIABLES` directly to the static 64-bit byte offset `(S + A) - tls_template_base_vma` from the start of the concatenated `[__thread_data, __thread_bss]` template and **must never** emit a `DYLD_CHAINED_PTR_64_OFFSET` (`bind = 0`) rebase entry at `+16` (`AXS-MACHO-023`).
3. TLS address materialization emits `ADRP X0, sym@TLVPPAGE` (`TLVP_LOAD_PAGE21`) + `LDR X0, [X0, sym@TLVPPAGEOFF]` (`TLVP_LOAD_PAGEOFF12`, relaxed by `compiler/link/macho` to `ADD X0, X0, #off` when `sym` is defined in the same image) followed by `LDR X16, [X0]` + `BLR X16`, returning the thread's `*mut T` instance pointer in `X0`. [0217 §10, §51, §72 ALINK-36; 0220 §16; tasks/0369 §17; tasks/0521 §80; SPEC-52]

**AXS-MACHO-019 — Deterministic BSD 4.4 `ar` Static Archives (`lib<name>.a`).** For `--kind lib` on `aarch64-macos`, `compiler/obj/macho` packages `MH_OBJECT` members into a deterministic BSD 4.4 `ar` archive (`0217 §19, §37, §44, §72 ALINK-28..29, 50`, `tasks/0369 §10, §31`, `T666`, generalized across targets in `SPEC-89` `T685`–`T686`):
- **Header & extended member names:** 8-byte global magic `"!<arch>\n"`, followed by 60-byte ASCII member headers padded to 2-byte alignment with `"\n"`. Filenames exceeding 16 bytes or containing spaces use BSD `#1/<byte_len>` extended naming, writing the NUL-padded member name (rounded to an 8-byte multiple so the embedded `MH_OBJECT` begins on an 8-byte file boundary) immediately before the member payload.
- **Deterministic `__.SYMDEF SORTED` index:** All archive headers write zeroed metadata (`mtime = "0"`, `uid = "0"`, `gid = "0"`, `mode = "100644"`). The first archive member is `__.SYMDEF SORTED`, containing a little-endian `ranlib` array of `(ran_strx: u32, ran_off: u32)` pairs sorted lexicographically by Mach-O symbol name (including defined `N_EXT` symbols and excluding `N_UNDF` imports) followed by the symbol string pool. Malformed archives or non-`CPU_TYPE_ARM64` members emit `AX_LINK_BAD_ARCHIVE` or `AX_LINK_ARTIFACT_TARGET_MISMATCH`. [0217 §19, §37, §44, §72 ALINK-28..29, 50; tasks/0369 §10, §31; SPEC-24 AXS-ART-025]

---

## 3. Mach-O 64 Native Linker (`MH_EXECUTE`, `MH_DYLIB`), `dyld` Fixups & Ad-Hoc Codesign (`AXS-MACHO-020`..`026`)

**AXS-MACHO-020 — Distinct `FileOffset` vs `VirtualAddress` & 16 KiB (`0x4000`) Segment Layout.** `compiler/link/macho` maintains distinct typed `FileOffset` and `VirtualAddress` spaces (`0196 §32–34, §40 AMACHO-25..26`, `tasks/0563 §304.5–6, §304.22, §304.28–29, §304.45 AIMG-25, 27..31`) and aligns every mapped segment's `vmaddr`, `vmsize`, `fileoff`, and `filesize` (except trailing `__LINKEDIT.filesize`) to **16 KiB (`0x4000 = 16384` bytes)** with strict W^X (`PROT_WRITE` and `PROT_EXEC` never co-occur; `AIMG-31`):
1. `__PAGEZERO` (`MH_EXECUTE` only): `vmaddr = 0x0`, `vmsize = 0x1_0000_0000` (`4 GiB`), `fileoff = 0`, `filesize = 0`, `maxprot = 0`, `initprot = 0` (omitted in `MH_DYLIB`).
2. `__TEXT`: `vmaddr = 0x1_0000_0000` (`MH_EXECUTE`) or `0x0` (`MH_DYLIB`), `fileoff = 0` (wrapping `mach_header_64` and all load commands before `__text`, `__stubs`, `__cstring`, `__const`, `__unwind_info`, `__eh_frame`), `maxprot = R|X (0x5)`, `initprot = R|X (0x5)`. If load commands exceed the initial header padding (`AX_LINK_BAD_OBJECT` guard), `__text` shifts up deterministically before relocation resolution.
3. `__DATA_CONST` (emitted when `__got` or relocated `__const` is non-empty): `maxprot = R|W (0x3)`, `initprot = R|W (0x3)`, `flags = SG_READ_ONLY (0x10)` (`dyld` applies chained fixups and then `mprotect`s the segment to `PROT_READ`).
4. `__DATA` (emitted when mutable/TLS/zerofill sections exist): `maxprot = R|W (0x3)`, `initprot = R|W (0x3)`. `S_ZEROFILL` (`__bss`, `__thread_bss`) sections are placed last in `__DATA`, contributing to `vmsize` while occupying **zero file bytes** (`section.offset = 0`, `filesize <= vmsize`, `AIMG-28..29`).
5. `__LINKEDIT` (always last): `fileoff` and `vmaddr` 16 KiB-aligned immediately after the preceding segment, `maxprot = R (0x1)`, `initprot = R (0x1)`, holding chained fixups, export trie, `nlist_64` symbol/indirect/string tables, and trailing `LC_CODE_SIGNATURE` (`vmsize = align_up(filesize, 0x4000)`). [0196 §6–7, §30–34, §40 AMACHO-25..26; tasks/0563 §304.5–6, §304.22, §304.28–29, §304.45 AIMG-25, 27..31]

**AXS-MACHO-021 — Canonical Load-Command Sequence for `MH_EXECUTE` & `MH_DYLIB`.** `compiler/link/macho` emits 8-byte-aligned load commands (`cmdsize % 8 == 0`) in deterministic order (`0196 §6, §13–18, §22–24`, `tasks/0563 §304.21–25`, `T667`):
1. `LC_SEGMENT_64 (0x19)` commands for `__PAGEZERO` (`MH_EXECUTE` only), `__TEXT`, optional `__DATA_CONST`, optional `__DATA`, and `__LINKEDIT`.
2. `LC_DYLD_CHAINED_FIXUPS (0x80000034)` (`16`-byte `linkedit_data_command`) and `LC_DYLD_EXPORTS_TRIE (0x80000033)` (`16` bytes).
3. `LC_SYMTAB (0x02)` and `LC_DYSYMTAB (0x0B)` (including indirect symbol table entries for `__TEXT,__stubs` and `__DATA_CONST,__got`).
4. `MH_EXECUTE` emits `LC_LOAD_DYLINKER (0x0E)` (`"/usr/lib/dyld"`) and `LC_MAIN (0x80000028)` (`entryoff = file_offset(__axiom_start)`, `stacksize = 0` or `--stack-size`); `MH_DYLIB` instead emits `LC_ID_DYLIB (0x0D)` (`install_name` defaulting to `"@rpath/lib<name>.dylib"`, `current_version = 0x00010000`, `compatibility_version = 0x00010000`).
5. `LC_UUID (0x1B)` (`24` bytes): first 16 bytes of `BLAKE3("axiom-macho-uuid-v1" || image_bytes_with_zeroed_uuid_and_codesig)` (never wall-clock or random; `0196 §24, §40 AMACHO-36`, `tasks/0563 §304.37–38, §304.45 AIMG-46..47`).
6. `LC_BUILD_VERSION (0x32)`: `platform = PLATFORM_MACOS (1)`, `minos = 0x000B0000` (`11.0.0`), `sdk = 0x000B0000`, `ntools = 1` (`TOOL_LD = 3`).
7. `LC_LOAD_DYLIB (0x0C)` (`LC_LOAD_WEAK_DYLIB = 0x80000018` when all bindings are weak) in deterministic 1-based `lib_ordinal` order starting with `"/usr/lib/libSystem.B.dylib"` (`ordinal = 1` in `--profile hosted`), optional `LC_RPATH (0x8000001C)` entries, and finally `LC_CODE_SIGNATURE (0x1D)`. [0196 §6, §13–18, §22–24, §40 AMACHO-35..36; tasks/0563 §304.21–25, §304.37–38, §304.45 AIMG-37, 41, 45..47]

**AXS-MACHO-022 — `__TEXT,__stubs` + `__DATA_CONST,__got`, GOT Relaxation & `±128 MiB` Branch Islands.** Dynamic calls, address-taken imports, and long branches resolve without text relocations (`0196 §10, §16–20, §40 AMACHO-28..29, 31`, `tasks/0518 AMACHINE-73, 79`, `SPEC-83 AXS-A64-042`):
- **12-byte dynamic call stubs:** Each imported function referenced by `ARM64_RELOC_BRANCH26` receives an 8-byte pointer slot in `__DATA_CONST,__got` and a 12-byte stub in `__TEXT,__stubs` (`S_SYMBOL_STUBS`, `reserved2 = 12`, `reserved1` = indirect symbol index): `ADRP X16, got_slot@PAGE` (`4`B) + `LDR X16, [X16, got_slot@PAGEOFF]` (`4`B) + `BR X16` (`4`B).
- **Local GOT relaxation & function-pointer equality:** When `ARM64_RELOC_GOT_LOAD_PAGE21` + `GOT_LOAD_PAGEOFF12` resolves to a symbol defined inside the same `MH_EXECUTE` (or non-interposable symbol in `MH_DYLIB`), `compiler/link/macho` relaxes `LDR Xd, [Xn, #off]` to `ADD Xd, Xn, #off` targeting the definition directly and elides the unused GOT slot. Address-taken external functions use their canonical GOT pointer (`dyld` binds every module to the unique exported target address, preserving `fn_ptr_a == fn_ptr_b`, `AMACHINE-79`).
- **Branch islands & textrel ban:** Any internal `ARM64_RELOC_BRANCH26` exceeding `±128 MiB` (`[-0x0800_0000, +0x07FF_FFFC]`) redirects to a deterministic 12-byte veneer (`ADRP X16, target@PAGE` + `ADD X16, X16, target@PAGEOFF` + `BR X16`). Any remaining absolute relocation (`ARM64_RELOC_UNSIGNED`) in `__TEXT` is rejected with `AX_LINK_TEXTREL_FORBIDDEN`. [0196 §10, §16–20, §40 AMACHO-28..29, 31; tasks/0518 AMACHINE-73, 79; SPEC-83 AXS-A64-042]

**AXS-MACHO-023 — `LC_DYLD_CHAINED_FIXUPS` Pointer-Chain Encoding.** Instead of legacy `LC_DYLD_INFO_ONLY` opcodes, `compiler/link/macho` emits macOS 11+/12+ `LC_DYLD_CHAINED_FIXUPS` in `__LINKEDIT` (`0196 §16–21, §40 AMACHO-28..31`, `0217 §30–31, §33, §52–53`, `T667`):
- Header `dyld_chained_fixups_header` (`fixups_version = 0`, `imports_format = DYLD_CHAINED_IMPORT (1)`, `symbols_format = 0` uncompressed) points to `dyld_chained_starts_in_image` containing a `dyld_chained_starts_in_segment` table (`size`, `page_size = 0x4000`, `pointer_format = DYLD_CHAINED_PTR_64_OFFSET (6)`, `segment_offset`, `max_valid_pointer = 0`, `page_count`, `page_start[page_count]` with `DYLD_CHAINED_PTR_START_NONE = 0xFFFF` for fixup-free 16 KiB pages) for `__DATA_CONST` and `__DATA`.
- Within each 16 KiB page, 8-byte pointer slots form a singly linked list (`next` = 12-bit stride in **4-byte** multiples to the next fixup on that page, `0` = end of chain):
  - **Rebase (`bind == 0`, internal `ARM64_RELOC_UNSIGNED` pointer slots):** `target: u36` = byte offset from image base (`vmaddr - image_base`), `high8: u8 = 0`, `reserved: u7 = 0`, `next: u12`, `bind: u1 = 0`. **Exception (`tlv_descriptor.offset`):** an `ARM64_RELOC_UNSIGNED` at `+16` inside `S_THREAD_LOCAL_VARIABLES` (`__DATA,__thread_vars`) resolves statically to `(S + A) - tls_template_base_vma` and **must never** emit a rebase entry (`AXS-MACHO-018`, whereas `tlv_descriptor.thunk` at `+0` emits a `bind == 1` entry for `__tlv_bootstrap` and `tlv_descriptor.key` at `+8` remains `0` with no fixup).
  - **Bind (`bind == 1`, external GOT / data / `_tlv_bootstrap` import):** `ordinal: u24` = index in `dyld_chained_import` table (`lib_ordinal: u8` 1-based `LC_LOAD_DYLIB` index, `weak_import: u1`, `name_offset: u23`), `addend: u8` (`DYLD_CHAINED_IMPORT_ADDEND` used if signed addends exceed `0..255`), `reserved: u19 = 0`, `next: u12`, `bind: u1 = 1`. [0196 §16–21, §40 AMACHO-28..31; 0217 §30–31, §33, §52–53]

**AXS-MACHO-024 — `LC_DYLD_EXPORTS_TRIE` ULEB128 Radix Tree.** `compiler/link/macho` serializes all public exported symbols (`N_SECT | N_EXT` without `N_PEXT`: `_main` in `MH_EXECUTE` and `@export`/`@no_mangle` `pub` items in `MH_DYLIB`) into `LC_DYLD_EXPORTS_TRIE` (`0196 §16, §22, §40 AMACHO-32`, `T667`):
- Each trie node encodes `terminal_size: uleb128` (`0` for non-terminal nodes; otherwise `flags: uleb128` — `EXPORT_SYMBOL_FLAGS_KIND_REGULAR (0x00)` plus `EXPORT_SYMBOL_FLAGS_WEAK_DEFINITION (0x04)` when weak, or `EXPORT_SYMBOL_FLAGS_KIND_THREAD_LOCAL (0x02)` for TLV — followed by `symbol_offset: uleb128` relative to `__TEXT.vmaddr`), `child_count: u8`, and lexicographically sorted `(edge_label_cstr, child_node_offset: uleb128)` edges.
- Node offsets are ULEB128 byte offsets from the start of the trie blob, solved by deterministic fixed-point iteration. Duplicate exported Mach-O names emit `AX_LINK_DUPLICATE_EXPORT`. [0196 §16, §22, §40 AMACHO-32; SPEC-27 AXS-LNK-012]

**AXS-MACHO-025 — Self-Contained Ad-Hoc `LC_CODE_SIGNATURE` (`CS_SuperBlob` & 88-Byte `CS_CodeDirectory`).** Apple Silicon kernels (`macOS 11+`) immediately kill (`SIGKILL` / `EXEC_BAD_ACCESS` code-signing policy) any `CPU_TYPE_ARM64` `MH_EXECUTE` or `MH_DYLIB` lacking a valid signature. `compiler/link/macho` synthesizes a complete ad-hoc signature at the exact end of `__LINKEDIT` (`sig_off % 16 == 0`, `ident_len_with_nul = len(basename) + 1`, `nCodeSlots = ceil(sig_off / 4096)`, `cd_len = 88 + ident_len_with_nul + 32 * nCodeSlots`, `total_sig_bytes = 20 + cd_len = 108 + ident_len_with_nul + 32 * nCodeSlots`, `sig_off + total_sig_bytes == file_len`) with **big-endian (`u32be` / `u64be`)** fields inside the little-endian Mach-O file, requiring zero external `codesign` or Xcode tools (`0196 §15, §23, §40 AMACHO-35, 37`, `0217 §34, §72 ALINK-55`, `tasks/0563 §304.25, §304.45 AIMG-45, 52`, `T667`):
1. `CS_SuperBlob` (`20` bytes at `[sig_off .. sig_off + 20)`): `+0` `magic: u32be = CS_MAGIC_EMBEDDED_SIGNATURE (0xFADE0CC0)`, `+4` `length: u32be = total_sig_bytes`, `+8` `count: u32be = 1`, `+12` `index[0].type: u32be = CSSLOT_CODEDIRECTORY (0)`, `+16` `index[0].offset: u32be = 20` (byte offset **relative to `CS_SuperBlob` start `sig_off`**, placing `CS_CodeDirectory` at `cd_off = sig_off + 20`).
2. `CS_CodeDirectory` (`88`-byte `v0x00020400` header at `[cd_off + 0 .. cd_off + 88)`, all internal offsets relative to `cd_off = sig_off + 20`): `+0` `magic: u32be = CS_MAGIC_CODEDIRECTORY (0xFADE0C02)`, **`+4` `length: u32be = total_sig_bytes - 20` (`= cd_len`)**, `+8` `version: u32be = 0x00020400` (`v2.4.0`), `+12` `flags: u32be = CS_ADHOC (0x00000002) | CS_LINKER_SIGNED (0x00020000)` (`0x00020002`), `+16` `hashOffset: u32be = 88 + ident_len_with_nul` (byte offset **relative to `CS_CodeDirectory` start `sig_off + 20`** to code hash slot `0`), `+20` `identOffset: u32be = 88` (byte offset **relative to `CS_CodeDirectory` start `sig_off + 20`** to the NUL-terminated UTF-8 output basename, e.g. `"hello\0"`), `+24` `nSpecialSlots: u32be = 0`, `+28` `nCodeSlots: u32be = ceil(sig_off / 4096)`, `+32` `codeLimit: u32be = sig_off` (`0` when `sig_off >= 4 GiB`, with `codeLimit64 = sig_off`), `+36` `hashSize: u8 = 32`, `+37` `hashType: u8 = CS_HASHTYPE_SHA256 (2)`, `+38` `platform: u8 = 0`, `+39` `pageSize: u8 = 12` ($2^{12} = 4096\text{ B}$ code-signing hash pages, even on 16 KiB VM Apple Silicon!), `+40` `spare2: u32be = 0`, `+44` `scatterOffset: u32be = 0`, `+48` `teamOffset: u32be = 0`, `+52` `spare3: u32be = 0`, `+56` `codeLimit64: u64be = 0` (`sig_off` only when `sig_off >= 0x1_0000_0000`), `+64` `execSegBase: u64be = __TEXT.fileoff`, `+72` `execSegLimit: u64be = __TEXT.filesize`, `+80` `execSegFlags: u64be = CS_EXECSEG_MAIN_BINARY (0x1)` for `MH_EXECUTE` (`0x0` for `MH_DYLIB`), followed immediately at `cd_off + 88` by `ident` (`ident_len_with_nul` bytes) and at `cd_off + 88 + ident_len_with_nul` by `32 * nCodeSlots` digest bytes.
3. **SHA-256 page digests:** Slot $i \in [0, \text{nCodeSlots})$ stores `SHA256(file_bytes[4096*i .. min(4096*(i+1), sig_off)])` computed **after** all headers, `LC_UUID`, relocations, chained fixups, export trie, and `LC_CODE_SIGNATURE` (`dataoff = sig_off`, `datasize = total_sig_bytes`) have been written to `[0 .. sig_off)`. [0196 §15, §23, §40 AMACHO-35, 37; 0217 §34, §72 ALINK-55; tasks/0563 §304.25, §304.45 AIMG-45, 52]

**AXS-MACHO-026 — Post-Serialization `verify_macho_image` Gate.** Before writing or returning any `MH_OBJECT`, `MH_EXECUTE`, or `MH_DYLIB`, `compiler/link/macho` executes `verify_macho_image` (`0196 §30, §40 AMACHO-40`, `tasks/0563 §304.33–36, §304.45 AIMG-37, 41, 48..50`), asserting: (a) `sizeofcmds` fits before the first section's `offset`, (b) segments are monotonically ordered, non-overlapping in both VMA and file-offset space, 16 KiB-aligned, and strictly W^X, (c) `S_ZEROFILL` sections occupy zero file bytes, (d) `LC_MAIN.entryoff` falls inside `__TEXT,__text`, (e) all chained-fixup pointers lie inside `__DATA_CONST`/`__DATA`, are 8-byte aligned, and exclude `S_THREAD_LOCAL_VARIABLES` `tlv_descriptor.offset` slots, and (f) `LC_CODE_SIGNATURE` sits at EOF with valid big-endian `CS_SuperBlob` (`20`B, `offset = 20`) and `CS_CodeDirectory` (`88`B `v0x00020400`, `length = total_sig_bytes - 20`, `identOffset = 88`, `hashOffset = 88 + ident_len_with_nul`) headers and matching SHA-256 4 KiB page digests. Any internal violation aborts emission with `AX_ICE_INTERNAL` (`stage = "link_verify"`). [0196 §30, §40 AMACHO-40; tasks/0563 §304.33–36, §304.45 AIMG-37, 41, 48..50]

---

## 4. macOS Platform Boundary, `libSystem.B.dylib`, `std.sys.macos` & Unwind/Debug (`AXS-MACHO-027`..`032`)

**AXS-MACHO-027 — Mandatory `libSystem.B.dylib` Dynamic Boundary & Ban on Raw XNU Syscalls.** Unlike `aarch64-linux` (`SVC #0`, `SPEC-83 AXS-A64-044`), Apple's Darwin/XNU kernel explicitly withholds user-space syscall ABI stability (`SVC #0x80` numbers and Mach trap layouts may change across minor macOS updates, and Apple Silicon kernels reject statically linked `MH_EXECUTE` binaries lacking `/usr/lib/dyld`) (`0196 §15–16, §40 AMACHO-39`, `0220 §1–4, §7, §39 AOS-20..23, 36..38`). Consequently, all `--profile hosted` `aarch64-macos` binaries dynamically bind `"/usr/lib/libSystem.B.dylib"` (`LC_LOAD_DYLIB`, `ordinal = 1`) and **never** emit raw `SVC #0x80` instructions. All Darwin C/POSIX imports remain strictly encapsulated inside `std/sys/macos` (`AOS-21..22`). [0196 §15–16, §40 AMACHO-39; 0220 §1–4, §7, §39 AOS-20..23, 36..38]

**AXS-MACHO-028 — Hermetic Built-In `libSystem.B.dylib` Catalog & `.tbd` / `.dylib` Stub Reader.** To guarantee zero-Xcode native builds on macOS and hermetic cross-compilation from Windows/Linux (`0196 §15–17, §40 AMACHO-28, 37`, `tasks/0453 §194.20–22`, `T667`), `compiler/link/macho` resolves dynamic libraries without invoking external Apple tools:
1. **Built-in `libSystem` catalog:** Ships a deterministic built-in export table for `"/usr/lib/libSystem.B.dylib"` (`current_version = 0x05416402`, `compatibility_version = 0x00010000`) covering all `std/sys/macos` bindings (`AXS-MACHO-030`), `_tlv_bootstrap`, `libunwind` entry points, and standard C math/memory symbols, so `axiomc build --target aarch64-macos` succeeds out-of-the-box with zero SDK files installed.
2. **External `.tbd` & `.dylib` reader:** For user `-l<name>` / `@link("<name>")` dependencies (`-L<dir>` and `--sysroot`, generalized across dynamic targets in `SPEC-89` `E16.10` `T685`–`T687`), `compiler/link/macho` parses Apple Text-Based Stub files (`lib<name>.tbd` v3/v4 YAML-subset `install-name`, `current-version`, `compatibility-version`, and `arm64-macos` exported symbol lists), thin `CPU_TYPE_ARM64` `MH_DYLIB` headers (`LC_ID_DYLIB` + `LC_DYLD_EXPORTS_TRIE`), and `FAT_MAGIC` (`0xCAFEBABE`) / `FAT_MAGIC_64` (`0xCAFEBABF`) universal headers containing a `CPU_TYPE_ARM64` slice (`SPEC-90` `E16.11` `T689`–`T690`). Missing libraries emit `AX_LINK_LIBRARY_NOT_FOUND`; `.dylib`/`.tbd` inputs lacking an `arm64-macos` slice emit `AX_LINK_ARTIFACT_TARGET_MISMATCH`. [0196 §15–17, §40 AMACHO-28, 37; tasks/0453 §194.20–22; SPEC-26 AXS-WLIB-003]

**AXS-MACHO-029 — Hosted Process Startup (`LC_MAIN` $\rightarrow$ `__axiom_start`), Module-Relative Bindings & Freestanding Mode.**
- **Hosted startup (`--profile hosted`):** `dyld` maps the image, applies `LC_DYLD_CHAINED_FIXUPS`, initializes `libSystem.B.dylib`, and calls the `LC_MAIN` entry function `__axiom_start(argc: i32, argv: *const *const u8, envp: *const *const u8, apple: *const *const u8) -> i32` (`X0..X3`, `SP % 16 == 0`) (`0196 §13–14, §40 AMACHO-38`, `tasks/0563 §304.23, §304.45 AIMG-41`). `__axiom_start` (`std/sys/macos/start.ax`, delivered by `T667`) establishes a root `X29` frame record, stores `(argc, argv, envp)` for `std.env`, runs Axiom runtime startup and user `main`, and returns the `i32` exit status to `dyld` (or invokes `_exit`).
- **Module-relative bindings (`SPEC-56`):** `@at(image_self() + off)` and `@at(image("foo.dylib") + off)` resolve base addresses via `_dyld_image_count` / `_dyld_get_image_header` / `dlopen` (`RTLD_NOLOAD`).
- **Freestanding separation (`--profile freestanding` / `kernel`):** Zero `std/sys/macos` code, `LC_LOAD_DYLINKER`, or `libSystem.B.dylib` imports are linked, and entry binds directly to user `@entry` (`SPEC-52 AXS-FRE-003..010`). [0196 §13–14, §40 AMACHO-38; 0217 §25–29, §72 ALINK-39..40; 0220 §7, §13–14, §39 AOS-30; tasks/0563 §304.23, §304.45 AIMG-41; SPEC-52 AXS-FRE-003..010; SPEC-56 AXS-MOD-010..014]

**AXS-MACHO-030 — `std.sys.macos` Host Interface (`__ax_host_*`), Darwin ARM64 Layouts & Fiber Context Switch.** `std/sys/macos` (delivered by `T667` and certified end-to-end by `T668`) implements the complete `SPEC-04 AXS-EXT-110` host contract over `libSystem.B.dylib` (`0220 §7, §14–31, §39 AOS-20..40`). On `arm64-apple-darwin`, 64-bit inodes are the native baseline, so `stat`, `fstat`, `lstat`, and `readdir` carry **no** `$INODE64` suffix (`_stat`, `_fstat`, `_lstat`, `_readdir` in Mach-O):
- **Heap & Process/Env:** `malloc`, `posix_memalign` (for alignments $> 16\text{ B}$), `realloc`, `free`; `_NSGetArgc`, `_NSGetArgv`, `getenv`, `_NSGetExecutablePath` + `realpath` (`exe_path`), `getentropy` (CSPRNG), `_exit`, and `*__error()` for thread-local `errno` (`IoError` normalization, `AOS-23`).
- **Console, File & FS (`Darwin ARM64 ABI`):** `open` (using Darwin flag values `O_RDONLY = 0x0000`, `O_WRONLY = 0x0001`, `O_RDWR = 0x0002`, `O_NONBLOCK = 0x0004`, `O_APPEND = 0x0008`, `O_CREAT = 0x0200`, `O_TRUNC = 0x0400`, `O_EXCL = 0x0800`, `O_CLOEXEC = 0x0100_0000`), `read`, `write`, `pread`, `pwrite`, `lseek`, `fsync`, `close`, `unlink`, `mkdir`, `rmdir`, `rename`; `fstat`/`stat` populating the **144-byte** Darwin ARM64 `struct stat` (`st_dev: i32` at `0`, `st_mode: u16` at `4`, `st_nlink: u16` at `6`, `st_ino: u64` at `8`, `st_mtimespec: (i64, i64)` at `48`, `st_size: i64` at `96`); and `opendir`/`readdir`/`closedir` reading Darwin `struct dirent` (`d_ino: u64` at `0`, `d_seekoff: u64` at `8`, `d_reclen: u16` at `16`, `d_namlen: u16` at `18`, `d_type: u8` at `20`, `d_name: [1024]u8` at `21`).
- **Clocks, Threads, Fibers & Async I/O:** `clock_gettime_nsec_np(CLOCK_UPTIME_RAW = 8)` (`monotonic_ns`), `clock_gettime(CLOCK_REALTIME = 0)` (`wall_clock`), `nanosleep`; `pthread_create`/`pthread_join`/`pthread_detach`, `sched_yield`, Darwin `__ulock_wait`/`__ulock_wake` (`UL_COMPARE_AND_WAIT = 1`, with `pthread_mutex_*`/`pthread_cond_*` fallback); `kqueue` + `kevent64` + BSD sockets for `aio_*` (`0220 §22–24, §39 AOS-28..29`); and 160-byte stackful fiber context switching (`std/sys/macos/fiber.ax`, `SPEC-34 AXS-EXEC-054`) saving/restoring `X19..X28`, `X29`, `X30`, `SP`, and `D8..D15` via `STP`/`LDP` while **never reading or writing `X18`** (`AXS-MACHO-004`). [0220 §7, §14–31, §39 AOS-20..40; SPEC-04 AXS-EXT-110; SPEC-34 AXS-EXEC-054]

**AXS-MACHO-031 — Compact Unwind (`__TEXT,__unwind_info`), `__eh_frame`, `__DWARF` & Panic/FFI Barrier.**
- **Compact Unwind & DWARF CFI fallback:** `compiler/obj/macho` emits 32-byte per-function descriptors in `__LD,__compact_unwind` (`0196 §27–28, §40 AMACHO-34`), which `compiler/link/macho` folds into `__TEXT,__unwind_info` (`UNWIND_ARM64_MODE_FRAMELESS = 0x0200_0000` for leaf functions, `UNWIND_ARM64_MODE_FRAME = 0x0400_0000` encoding saved `X19..X28`/`D8..D15` bitmasks for standard `X29`-framed functions, and `UNWIND_ARM64_MODE_DWARF = 0x0300_0000` pointing into `__TEXT,__eh_frame` DWARF CFI FDEs for oversized or non-canonical prologues).
- **DWARF debug & panic barrier:** Debug builds (`-g`) emit `__DWARF,__debug_{info,abbrev,line,str,rnglists}` from `DebugIR` (`0196 §25–26, §40 AMACHO-33`, `SPEC-93` `E17.2` `T704`–`T707`), stripping `__DWARF` under `--strip` without altering code or unwind semantics (`tasks/0563 §304.39–40, §304.45 AIMG-42..43`). `--panic abort` reports to `stderr` and calls `_exit(101)` (`0196 §29`); `--panic unwind` runs reverse-order `Drop` cleanup via `libunwind` (`SPEC-54`); uncaught panics reaching an `extern "C"` boundary execute `BRK #0x1` (`0xD420_0020`, `SPEC-54 AXS-PAN-010`). [0196 §25–29, §40 AMACHO-33..34; tasks/0563 §304.39–40, §304.45 AIMG-42..43; SPEC-54 AXS-PAN-001..010; SPEC-83 AXS-A64-047]

**AXS-MACHO-032 — Deterministic Artifacts, `TargetFingerprint` Cache Isolation & E16.4 Conformance Matrix.** For a fixed source snapshot, `TargetFingerprint`, and optimization profile, `aarch64-macos` ABI lowering, `MH_OBJECT` / BSD `ar` / `MH_EXECUTE` / `MH_DYLIB` bytes, `LC_UUID`, and `LC_CODE_SIGNATURE` SHA-256 page hashes are byte-for-byte deterministic (`0196 §24, §40 AMACHO-36`, `0217 §44–45, §72 ALINK-50..51`, `tasks/0524 §90, §112 ABACKEND-95`, `tasks/0563 §304.37–38, §304.45 AIMG-46..47`). Incremental/artifact cache keys (`SPEC-22`, `SPEC-24`) include `(SemanticFingerprint, TargetId.AArch64Macos, TargetFeatureSet, CallConv.Aapcs64Darwin, OptProfile, CodegenFingerprint)` so `aarch64-linux` and `aarch64-macos` artifacts never collide (`tasks/0453 §194.31`, `tasks/0524 §91, §112 ABACKEND-94`). Under the E16.4 backend conformance contract (`T668`, `tasks/0524 §68–87, §112 ABACKEND-89..92`, `REQ-TGT-314`..`317`, `0196 §35–40 AMACHO-40`): (a) distinct A64/Darwin instruction sequences (e.g. `-O0` vs `-O2`, `+lse` vs LL/SC, unrelaxed GOT `LDR` vs relaxed `ADD`) may validly represent identical `LIR` semantics (`ABACKEND-89`, `REQ-TGT-314`); (b) assembly and binary encoding golden tests inspect implementation/container quality only and are **never** the semantic authority (`ABACKEND-90`, `REQ-TGT-315`); (c) reference `--interp` evaluation and differential execution across `x86_64`, `aarch64-linux`, and `aarch64-macos` (`0 WEAK-NATIVE`) are the authoritative semantic validation mechanisms (`ABACKEND-91`, `REQ-TGT-316`); and (d) backend semantic conformance tests are target-independent at the semantic level (`ABACKEND-92`, `REQ-TGT-317`), while Mach-O binary verification remains independent of frontend semantic verification (`AMACHO-40`):

| Verification Pillar | Gate / Suite | Asserted Contract |
|---|---|---|
| 1. Darwin ABI & `X18`/Frame Verifier | `ABIVerifier` + `verify_mc` (`tests/selfhost/abi`) | `X18` untouched, `< 32`b caller/callee extension, packed natural-alignment stack slots, stack-only variadics, `128`B leaf red zone, unbroken `X29` chain |
| 2. Mach-O 64 Object & BSD `ar` | `tests/obj/macho`, `tests/selfhost/obj` | `MH_OBJECT` headers, `section_64` `(sectname, segname)` order, `_` symbols, `MH_SUBSECTIONS_VIA_SYMBOLS`, all `ARM64_RELOC_*` records (4 KiB `ADRP`), `tlv_descriptor`, deterministic `lib*.a` |
| 3. Native Linker, `std.sys.macos` & Codesign | `verify_macho_image` (`tests/link/macho`, `tests/selfhost/link`) | 16 KiB W^X segments, `__stubs`+`__got`, `LC_DYLD_CHAINED_FIXUPS` (with static non-rebased `tlv_descriptor.offset`), `LC_DYLD_EXPORTS_TRIE`, `.tbd`/built-in `libSystem`, `std/sys/macos` bindings, valid EOF 88-byte-header SHA-256 `LC_CODE_SIGNATURE` |
| 4. Conformance & Differential Execution | `tools/axtest.py` (`tests/conformance/p16/e16_4_macos_aarch64`) | Cross-build structural + SHA-256 codesign determinism on all hosts, target-independent semantic conformance (`REQ-TGT-314..317`), and native Apple Silicon differential execution (`otool -l`, `dyld_info`, `codesign --verify -vvv`, `std.fs`/`net`/`thread`/FFI, UTF-8 `"Xin chào thế giới"`) matching `--interp` and `x86_64`/`aarch64-linux` |

---

## 5. Diagnostics, Canonical Examples & Traceability (`AXS-MACHO-033`..`036`)

**AXS-MACHO-033 — Diagnostics Referenced by `SPEC-84`.** `aarch64-macos` reuses canonical `DRIVER`, `TARGET`, `TYPE`, `FFI`, `VERIFY`, `LINK`, and `ICE` diagnostic codes (`spec/diagnostics.md` §10–11):

| Code | Area | Sev | Delivering Task | Condition on `aarch64-macos` |
|---|---|---|---|---|
| `AX_DRIVER_UNKNOWN_TARGET` | `DRIVER` | `error` | `T016`/`T654` | Unrecognized `--target <triple>` (`AXS-MACHO-001`) |
| `AX_TARGET_UNKNOWN_FEATURE` | `TARGET` | `error` | `T476`/`T654`/`T666` | Unknown feature name (e.g. `"avx2"`) or forbidden removal of hosted `-neon`/`-fp` baseline on `aarch64-macos` (`AXS-MACHO-002`) |
| `AX_TARGET_FEATURE_CONFLICT` | `TARGET` | `error` | `T654`/`T666` | Contradictory feature toggles (e.g. `+sve,-neon`) (`AXS-MACHO-002`) |
| `AX_TARGET_FEATURE_MISMATCH` | `TARGET` | `error` | `T476`/`T666` | Calling a `@target_feature("pauth")` or `@target_feature("sve")` function from baseline code without `unsafe` or runtime guard (`AXS-MACHO-002`) |
| `AX_TARGET_UNSUPPORTED_OP` | `TARGET` | `error` | `T655`/`T666` | `LIR` operation or ABI convention cannot be legally expanded on `aarch64-macos` without altering semantics (`AXS-MACHO-011`) |
| `AX_TYPE_INVALID_SECTION` | `TYPE` | `error` | `T512`/`T666` | `@section("...")` exceeds 16-byte `segname` or `sectname` Mach-O limits (`AXS-MACHO-014`) |
| `AX_FFI_VARIADIC_NOT_EXTERN_C` | `FFI` | `error` | `T503` | Variadic `...` used outside an `extern "C"` declaration (`AXS-MACHO-007`) |
| `AX_VERIFY_MC_ILLEGAL` | `VERIFY` | `error` | `T655`/`T666` | Machine IR touches reserved `X18`/`W18`, breaks `X29` frame-record or 16B `SP` alignment, or violates A64 `verify_mc` (`AXS-MACHO-004`, `AXS-MACHO-009`) |
| `AX_LINK_BAD_OBJECT` | `LINK` | `error` | `T027`/`T666`/`T667` | Malformed `MH_OBJECT` header, unpaired `ADDEND`/`SUBTRACTOR` relocation, or corrupt `.dylib`/`.tbd` (`AXS-MACHO-013`, `AXS-MACHO-017`) |
| `AX_LINK_BAD_ARCHIVE` | `LINK` | `error` | `T750`/`T666`/`T667` | Corrupt BSD `ar` `!<arch>\n` header, `#1/<len>` extended name, or `__.SYMDEF` table (`AXS-MACHO-019`) |
| `AX_LINK_LIBRARY_NOT_FOUND` | `LINK` | `error` | `T750`/`T667` | Requested `-l<name>` / `@link("<name>")` not found in `-L` paths, `.tbd`/`.dylib` search, or built-in `libSystem` catalog (`AXS-MACHO-028`) |
| `AX_LINK_DUPLICATE_EXPORT` | `LINK` | `error` | `T751`/`T667` | Two `@export` / `@no_mangle` items resolve to the identical `_`-prefixed Mach-O export in `LC_DYLD_EXPORTS_TRIE` (`AXS-MACHO-024`) |
| `AX_LINK_ARTIFACT_TARGET_MISMATCH` | `LINK` | `error` | `T766`/`T666`/`T667` | Input `.o`/`.a`/`.dylib`/`.tbd`/`.axmi` lacks `CPU_TYPE_ARM64` or conflicts with `TargetId.AArch64Macos` (`AXS-MACHO-019`, `AXS-MACHO-028`, `AXS-MACHO-032`) |
| `AX_LINK_RELOC_OUT_OF_RANGE` | `LINK` | `error` | `T027`/`T667` | `ARM64_RELOC_PAGE21` (`±4 GiB`) or non-relaxable relocation overflows its A64 field (`AXS-MACHO-017`, `AXS-MACHO-022`) |
| `AX_LINK_TEXTREL_FORBIDDEN` | `LINK` | `error` | `T658`/`T667` | `ARM64_RELOC_UNSIGNED` targets read-only/executable `__TEXT` in `MH_EXECUTE` or `MH_DYLIB` (`AXS-MACHO-022`) |
| `AX_ICE_INTERNAL` (`stage = "link_verify"`) | `ICE` | `error` | `T667` | Synthesized Mach-O image failed `verify_macho_image` structural, W^X, or SHA-256 codesign check (`AXS-MACHO-026`) |

**AXS-MACHO-034 — Canonical Positive Examples (`=` and `.` Syntax).**

```axiom
// Example 1: CallConv.Aapcs64Darwin packed natural-alignment stack spill, <32-bit extension,
// stack-only variadic C FFI (libSystem snprintf), and UTF-8 output on --target aarch64-macos.
// Compiled with: axiomc build --target aarch64-macos darwin_abi_demo.ax -o darwin_abi_demo
module demo.macos_darwin_abi

use std.io.println

extern "C" {
    fn snprintf(buf: *mut u8, cap: usize, fmt: *const u8, ...) -> i32
}

// X0..X7 carry a0..a7; under CallConv.Aapcs64Darwin, spilled b0..b3 (u8) and tail (i32)
// pack tightly at [SP + 0..4) and [SP + 4..8) (8 bytes total) with caller UXTB extension (AXS-MACHO-005..006).
pub fn sum_packed_darwin_spill(
    a0: i64, a1: i64, a2: i64, a3: i64,
    a4: i64, a5: i64, a6: i64, a7: i64,
    b0: u8, b1: u8, b2: u8, b3: u8,
    tail: i32
) -> i64 {
    let head = a0 + a1 + a2 + a3 + a4 + a5 + a6 + a7
    let bytes = (b0 as i64) + (b1 as i64) + (b2 as i64) + (b3 as i64)
    return head + bytes + (tail as i64)
}

pub fn format_tag(out: mut_view<[u8]>, fmt_cstr: view<[u8]>, code: i32) -> i32 {
    // Variadic 'code' is always placed in an 8-byte stack slot on Apple ARM64 (AXS-MACHO-007).
    return unsafe { snprintf(out.as_mut_ptr(), len(out), fmt_cstr.as_ptr(), code) }
}

pub fn main() -> i32 {
    println("Xin chào thế giới")
    let total = sum_packed_darwin_spill(1, 1, 1, 1, 1, 1, 1, 1, 2u8, 3u8, 4u8, 5u8, 20)
    let mut scratch: [16]u8 = [0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8]
    let fmt: [4]u8 = [37u8, 100u8, 33u8, 0u8] // "%d!\0"
    let written = format_tag(mut_view(scratch), view(fmt), total as i32)
    if total == 42 && written == 3 {
        return 0
    }
    return 1
}
```

```axiom
// Example 2: Exporting a Mach-O MH_DYLIB symbol (_ax_mac_dot3 in LC_DYLD_EXPORTS_TRIE) with HFA Vec3f.
// Compiled with: axiomc build --target aarch64-macos --kind dll mac_math.ax -o libmac_math.dylib
module demo.macos_dylib_export

@repr(C)
pub struct Vec3f {
    pub x: f32
    pub y: f32
    pub z: f32
}

@export("ax_mac_dot3")
pub extern "C" fn ax_mac_dot3(a: Vec3f, b: Vec3f) -> f32 {
    return a.x * b.x + a.y * b.y + a.z * b.z
}
```

**AXS-MACHO-035 — Canonical Negative Examples (`=` and `.` Syntax).**

```axiom
// Example 1: Calling a @target_feature("pauth") function from baseline aarch64-macos code
// without unsafe is rejected (AX_TARGET_FEATURE_MISMATCH, AXS-MACHO-002).
module demo.macos_bad_pauth_call

@target_feature("pauth")
pub fn signed_frame_step(x: i64) -> i64 {
    return x + 1
}

pub fn caller_without_pauth(x: i64) -> i64 {
    return signed_frame_step(x) //~ ERROR AX_TARGET_FEATURE_MISMATCH
}
```

```axiom
// Example 2: Requesting an x86-only feature on --target aarch64-macos is rejected (AX_TARGET_UNKNOWN_FEATURE).
module demo.macos_bad_x86_feature

@target_feature("avx2") //~ ERROR AX_TARGET_UNKNOWN_FEATURE
pub fn invalid_feature_on_apple_silicon(x: i32) -> i32 {
    return x
}
```

```axiom
// Example 3: Variadic '...' on a non-extern-"C" Axiom function is rejected (AX_FFI_VARIADIC_NOT_EXTERN_C).
module demo.macos_bad_variadic_fn

pub fn bad_variadic(head: i32, ...) -> i32 { //~ ERROR AX_FFI_VARIADIC_NOT_EXTERN_C
    return head
}
```

**AXS-MACHO-036 — Requirement, Invariant & Task Traceability Matrix (`E16.4`: `REQ-TGT-147`, `REQ-TGT-296`..`303`, `REQ-TGT-311`..`317`).**

| Task | Scope | Invariant | Covered Requirements | Primary Test Suites |
|---|---|---|---|---|
| `T665` | `SPEC-84`: Canonical `CallConv.Aapcs64Darwin`, `MH_OBJECT` / BSD `ar` / `MH_EXECUTE` / `MH_DYLIB`, `LC_DYLD_CHAINED_FIXUPS`, `LC_DYLD_EXPORTS_TRIE`, ad-hoc `LC_CODE_SIGNATURE` & `std.sys.macos` specification | `INV-MACHO-001`..`003` | `REQ-TGT-147`, `REQ-TGT-296`..`REQ-TGT-298` | `spec/SPEC-84-macos-aarch64-macho.md` |
| `T666` | `compiler/abi/apple_arm64` & `compiler/obj/macho`: `CallConv.Aapcs64Darwin` (`X18` reservation, `< 32`b ext, packed stack, stack variadics, `128`B red zone, `X29` FP), `_` symbols, `MH_OBJECT` writer (`section_64`, `tlv_descriptor`), `ARM64_RELOC_*` & BSD `ar` | `INV-MACHO-001` | `REQ-TGT-299`..`REQ-TGT-302` | `tests/obj/macho`, `tests/selfhost/abi`, `tests/selfhost/obj` |
| `T667` | `compiler/link/macho` & `std/sys/macos`: 16 KiB segment layout, `__stubs`+`__got`, `LC_DYLD_CHAINED_FIXUPS`, `LC_DYLD_EXPORTS_TRIE`, `.tbd` / built-in `libSystem.B.dylib`, `MH_EXECUTE` / `MH_DYLIB`, 88-byte-header SHA-256 ad-hoc `LC_CODE_SIGNATURE`, and `std/sys/macos` (`libSystem.B.dylib` `__ax_host_*`, Darwin ARM64 144B `stat`/64-bit-inode `dirent`/`O_*`, `kqueue`, `pthread`/`__ulock_*`, 160B `X18`-preserving fibers, `__axiom_start`) | `INV-MACHO-002` | `REQ-TGT-303`, `REQ-TGT-311`..`REQ-TGT-313` | `tests/link/macho`, `tests/selfhost/link` |
| `T668` | `tests/conformance/p16/e16_4_macos_aarch64`: E16.4 macOS AArch64 ABI, Mach-O 64 container, `dyld` chained fixups / export trie, SHA-256 ad-hoc `LC_CODE_SIGNATURE`, `std.sys.macos`, determinism & differential execution conformance suite — feeding `E16.10` cross-target artifact/library matrix (`T685`–`T688`, `SPEC-89`) and `E16.11` universal/multi-arch Mach-O Fat artifacts (`T689`–`T692`, `SPEC-90`) | `INV-MACHO-003` | `REQ-TGT-314`..`REQ-TGT-317` | `tests/conformance/p16/e16_4_macos_aarch64` |

Detailed requirement mapping across `REQ-TGT-147`, `REQ-TGT-296`..`303`, `REQ-TGT-311`..`317`, and `AMACHO-20..40`:

| Requirement(s) | Corpus Anchor | Canonical `SPEC-84` Rule(s) | Board Task(s) |
|---|---|---|---|
| `REQ-TGT-147` | `0521 §91–92, §156`, `AARM-53` | `AXS-MACHO-002` (`pauth`/PAC is target/system ABI policy, never Core pointer/capability semantics) | `T665` |
| `REQ-TGT-296`, `REQ-TGT-297` | `0524 §112`, `ABACKEND-71..72` | `AXS-MACHO-003`, `AXS-MACHO-005`..`007`, `AXS-MACHO-011` (`CallConv.Aapcs64Darwin` & aggregate ABI preserve Core semantics) | `T665` |
| `REQ-TGT-298` | `0524 §112`, `ABACKEND-73` | `AXS-MACHO-004`, `AXS-MACHO-011` (RA respects `X18` reservation and preserves ownership/aliasing) | `T665` |
| `REQ-TGT-299`, `REQ-TGT-300` | `0524 §112`, `ABACKEND-74..75` | `AXS-MACHO-008`, `AXS-MACHO-009`, `AXS-MACHO-011` (spill slots, `128`B red zone, `X29` frame chain, `Drop`/unwind preservation) | `T666` |
| `REQ-TGT-301`, `REQ-TGT-302` | `0524 §112`, `ABACKEND-76..77` | `AXS-MACHO-011`, `AXS-MACHO-017`..`018` (`@PAGE`/`@GOTPAGE`/`@TLVPPAGE` 4 KiB relocations preserve provenance & memory semantics) | `T666` |
| `REQ-TGT-303` | `0524 §112`, `ABACKEND-78` | `AXS-MACHO-011`, `AXS-MACHO-022` (`__stubs`+`__got` and `±128 MiB` `X16` branch islands preserve CFG semantics) | `T667` |
| `REQ-TGT-311`..`REQ-TGT-313` | `0524 §112`, `ABACKEND-86..88` | `AXS-MACHO-011`, `AXS-MACHO-016`, `AXS-MACHO-022` (GOT relaxation, dead-atom GC & target-distinct layout preserve safety and behavior) | `T667` |
| `REQ-TGT-314`..`REQ-TGT-317` | `0524 §68–87, §112`, `ABACKEND-89..92` | `AXS-MACHO-032` (distinct A64/Darwin instruction sequences for identical `LIR` semantics, assembly goldens non-authoritative for semantics, `--interp` reference + differential execution validation & target-independent semantic backend conformance tests) | `T668` |
| — (`AMACHO-20..40`, `ALINK-20..56`, `AIMG-20..60`, `AOS-20..40`, `ABACKEND-94..95`) | `0196 §1–40`, `0217 §4–55, §72`, `0220 §1–39`, `0524 §90–91, §112`, `0563 §304.21–45` | `AXS-MACHO-001`, `AXS-MACHO-012`..`032` (Mach-O layering, `MH_OBJECT`/BSD `ar`/`MH_EXECUTE`/`MH_DYLIB`, chained fixups, export trie, 88-byte `CS_CodeDirectory` ad-hoc codesign, hermetic `.tbd`/`libSystem`, `std.sys.macos`, `TargetFingerprint` cache isolation & deterministic builds) | `T665`–`T668`, `T685`–`T690` |

## Sources

0193 §1–40 (`AARCH64-20..40`); 0196 §1–41 (`AMACHO-20..40`); 0217 §1–72 (`ALINK-20..56`); 0220 §1–39 (`AOS-20..40`); `tasks/0369` §1–37 (`ALINK-20..50`); `tasks/0453` §194.18–31, §194.44 (`ATARGET-20..50`); `tasks/0518` §1–151 (`AMACHINE-20..120`); `tasks/0521` §60–63, §80, §91–92, §136, §156 (`AARM-20..70`); `tasks/0524` §1–113 (`ABACKEND-71..100`); `tasks/0563` §304.5–6, §304.21–45 (`AIMG-20..60`); `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-052`, `AXS-EXT-060..062`, `AXS-EXT-070..074`, `AXS-EXT-110`); `spec/SPEC-22-incremental-compilation.md`; `spec/SPEC-24-artifact-format-module-interfaces.md`; `spec/SPEC-26-windows-artifact-kinds.md`; `spec/SPEC-27-separate-compilation-linker-v2.md`; `spec/SPEC-34-executors-fibers.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-52-freestanding-runtime-composition.md`; `spec/SPEC-54-panic-unwinding.md`; `spec/SPEC-55-fixed-address-declarations.md`; `spec/SPEC-56-module-relative-bindings.md`; `spec/SPEC-81-target-desc-isa-conformance.md`; `spec/SPEC-83-aarch64-linux.md`; `spec/invariants.md` (`INV-TGTD-001..003`, `INV-AARCH-001..003`, `INV-MACHO-001..003`); `spec/diagnostics.md`; `ADR-0001`; `ADR-0002`; `ADR-0003`; `ADR-0011`.
