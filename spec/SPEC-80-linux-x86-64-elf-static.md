# SPEC-80 — Canonical Linux x86-64 SysV ABI, ELF64 Object & Static ELF Executable Specification

- **Status:** draft (T650, 2026-11-03)
- **Owner:** `axiom-architect`
- **Consolidates:** `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-052`, `AXS-EXT-060..062`, `AXS-EXT-070..074`, `AXS-EXT-110`), `spec/SPEC-52-freestanding-runtime-composition.md`, `0053`, `0163`, `0164`, `0192`, `0217`, `0255`, `0256`, `tasks/0369`, `tasks/0563`
- **Covers:** `REQ-TGT-002`, `REQ-TGT-003`, `REQ-TGT-037`, `REQ-TGT-038`, `REQ-TGT-039`, `REQ-TGT-040` (and specifies the E16.9 contract for `T066`, `T651`, `T652`: `REQ-TGT-041`, `REQ-TGT-042`, `REQ-TGT-043`, `REQ-TGT-059`, `REQ-TGT-060`, `REQ-TGT-096`, `REQ-TGT-097`, `REQ-TGT-098`, `REQ-TGT-099`, `REQ-TGT-100`, `REQ-TGT-101`, `REQ-TGT-102`, `REQ-TGT-103`, `REQ-TGT-104`, `REQ-TGT-105`, `REQ-TGT-106`, `REQ-TGT-111`, `REQ-TGT-112`)
- **Consumers:** `compiler/driver/target_linux`, `compiler/abi/sysv64`, `compiler/obj/elf`, `compiler/link/elf`, `std/sys/linux`, `tools/axtest.py`, `T066`, `T651`, `T652`

## Tóm tắt

Tài liệu `SPEC-80` chốt đặc tả chuẩn cho đích biên dịch bản địa thứ hai của Axiom (`x86_64-linux`, Epic `E16.9`), chứng minh kiến trúc backend x86-64 tách biệt hoàn toàn giữa CPU ISA và nền tảng hệ điều hành (`0192 §1–2, §27`):
1. **Mô tả đích `x86_64-linux` (`TargetDesc`) và tái sử dụng chuỗi hạ tầng x86-64 (`AXS-ELFS-001`..`009`):** Dùng lại toàn bộ `LIR → x86-64 ISel → Machine IR → RegAlloc → Encoder`; chỉ thay thế tầng dữ liệu đích (`CallConv.SysV64`, `ObjectFormat.Elf`, `ArchiveFormat.GnuAr`, `ImageFormat.ElfExec`), căn chỉnh ngăn xếp 16 byte trước `call`, và vùng đỏ (red zone) 128 byte cho hàm lá (tắt khi có `-mno-red-zone` hoặc trong hồ sơ `freestanding`/`kernel`).
2. **Quy ước gọi hàm System V AMD64 ABI (`CallConv.SysV64`, `AXS-ELFS-010`..`020`):** Tham số nguyên/con trỏ qua `RDI, RSI, RDX, RCX, R8, R9`, tham số dấu phẩy động/vector qua `XMM0..XMM7`, phân loại cấu trúc theo từng eightbyte (`INTEGER`, `SSE`, `MEMORY`), con trỏ trả về ẩn `sret` trong `RDI` (trả lại trong `RAX`), trả về 16 byte qua cặp thanh ghi `RAX:RDX` / `XMM0:XMM1`, và tập thanh ghi bảo toàn bởi hàm được gọi `RBX, RBP, R12..R15`.
3. **Đối tượng khả định vị lại ELF64 (`ET_REL`) và thư viện tĩnh GNU `ar` (`AXS-ELFS-021`..`029`):** Phát sinh trực tiếp tệp `.o` (`ET_REL`, `.text`, `.rodata`, `.data`, `.bss`, `.symtab`, `.strtab`, `.shstrtab`, `.rela.text`, `.rela.rodata`, `.rela.data`) với các bản ghi định vị lại `R_X86_64_64`, `R_X86_64_PC32`, `R_X86_64_PLT32`, `R_X86_64_32`, `R_X86_64_32S`, ký hiệu `SHN_ABS` cho `@at`, và kho lưu trữ tĩnh `.a` (`!<arch>\n`) tất định.
4. **Trình liên kết tệp thực thi tĩnh ELF64 (`ET_EXEC`) và giao diện syscall `std.sys.linux` (`AXS-ELFS-030`..`049`):** Ghép các phân đoạn thành 3 segment `PT_LOAD` (`RX`, `R`, `RW`) căn trang 4 KiB tại địa chỉ cơ sở `0x400000`, tổng hợp điểm vào `_start` đọc `argc`/`argv`/`envp` từ ngăn xếp khởi tạo của nhân Linux, gọi `main`, thoát qua `SYS_exit_group = 231` / `SYS_exit = 60` không cần `libc`/`ld`, và ánh xạ đầy đủ bảng host intrinsic (`SPEC-04 AXS-EXT-110`) sang syscall nhân Linux x86-64.

---

## 1. `x86_64-linux` Target Description, Profiles, Frame Policy & Shared x86-64 Boundary (`AXS-ELFS-001`..`009`)

**AXS-ELFS-001 — `x86_64-linux` `TargetDesc` Record.** The compiler registers `x86_64-linux` (accepting CLI `--target x86_64-linux` and canonical aliases `x86_64-unknown-linux-gnu` / `x86_64-unknown-linux-musl` for static builds) as a pure data record (`SPEC-04 AXS-EXT-060..061`, `REQ-TGT-105`):
- `arch = Arch.X86_64`, `os = Os.Linux`, `pointer_width = 64`, `endian = Endian.Little`;
- `default_call_conv = CallConv.SysV64` (`SPEC-04 AXS-EXT-052`);
- `object_format = ObjectFormat.Elf`, `archive_format = ArchiveFormat.GnuAr`, `image_format = ImageFormat.ElfExec` (`SPEC-04 AXS-EXT-070`);
- `default_cpu_features = { sse, sse2 }` (`SPEC-44 AXS-CPU-001`), `stack_align = 16`, `shadow_space = 0`, `red_zone = 128`, `page_size = 4096`. [0163 §1–7; 0192 §3; SPEC-04 AXS-EXT-060..061; REQ-TGT-105]

**AXS-ELFS-002 — Shared x86-64 ISA Backend vs Platform Target Layer.** `LIR` is target-independent (`REQ-TGT-111`), and the x86-64 instruction selector, virtual/physical register model, register allocator (`LinearScan` for `-O0`/`-O1` and graph/hybrid allocation for `-O2`, `REQ-TGT-112`), instruction verifier, and machine encoder are shared unchanged between `x86_64-windows` and `x86_64-linux` (`0192 §1–2, §27–28, AELF-28`). Platform differences live exclusively in `TargetDesc`, `compiler/abi/sysv64`, `compiler/obj/elf`, `compiler/link/elf`, and `std/sys/linux`. [0192 §1–2, §27–29 AELF-28; REQ-TGT-111, REQ-TGT-112]

**AXS-ELFS-003 — Compilation Profiles & Invariant Core Semantics Across Targets.** All four compilation profiles (`--profile hosted|freestanding|kernel|system`, `SPEC-04 AXS-EXT-062`, `SPEC-52 AXS-FRE-001..003`) are supported on `x86_64-linux`. Core language semantics (ownership, `view<T>`/`mut_view<T>`, deterministic `Drop`, checked arithmetic) are identical across `hosted` and `freestanding` profiles (`REQ-TGT-002`) and across Windows and Linux (`0192 AELF-37..38`). Freestanding and kernel targets require no hosted runtime machinery (`REQ-TGT-096`), no garbage collection (`REQ-TGT-097`), no mandatory reference counting (`REQ-TGT-098`), no mandatory object headers (`REQ-TGT-099`), and no programmer-visible pointer syntax for safe values (`REQ-TGT-100`). [0192 AELF-36..38; SPEC-52 AXS-FRE-001..003; REQ-TGT-002, REQ-TGT-096..100]

**AXS-ELFS-004 — Freestanding Entry Points & Zero Implicit Global Initialization.** In `--profile freestanding` and `--profile kernel`, the user program defines `@entry fn _start(...)` (`SPEC-52 AXS-FRE-010`, `REQ-TGT-003`), which `compiler/link/elf` binds directly as ELF `e_entry` without synthesizing a hosted startup wrapper (`0192 §20–21`). Module-level `static` items are initialized exclusively from compile-time constants (`SPEC-52 AXS-FRE-004`); compilation never emits implicit global constructors (`.init_array` / `.ctors`) from module imports (`REQ-TGT-003`). [0192 §20–21; SPEC-52 AXS-FRE-004, AXS-FRE-010; REQ-TGT-003]

**AXS-ELFS-005 — 16-Byte Stack Alignment Contract Before `call`.** Under `CallConv.SysV64`, `FrameLayout` enforces 16-byte stack frame alignment (`0192 §8, AELF-30`, `REQ-TGT-040`): upon entry to any function (immediately after the `call` instruction pushes the 8-byte return address), `RSP % 16 == 8` (`(RSP + 8) % 16 == 0`), and immediately before executing any outgoing `call` instruction, `RSP % 16 == 0` (widened to 32- or 64-byte alignment when 256-bit `AVX` or 512-bit `AVX-512` stack arguments or locals require it). [0192 §8, AELF-30; REQ-TGT-040]

**AXS-ELFS-006 — 128-Byte Leaf Red Zone Policy & `-mno-red-zone` Control.** The System V AMD64 ABI defines a 128-byte red zone at `[RSP - 128, RSP)` that signal and user-space interrupt handlers do not clobber (`0192 §9, AELF-31`). In `hosted` and `system` profiles, `FrameLayout` may place up to 128 bytes of locals/spills at negative offsets from `RSP` without emitting `sub rsp, N` **only** in true leaf functions (zero outgoing `call` instructions, zero inline `syscall` instructions, and zero dynamic stack allocations). The red zone (`red_zone = 0`) is strictly disabled when `--no-red-zone` / `-mno-red-zone` is passed, in `--profile freestanding` and `--profile kernel`, and in `extern "interrupt"` handlers (`SPEC-52 AXS-FRE-015`). [0163 §5; 0192 §9, AELF-31]

**AXS-ELFS-007 — Zero Shadow Space & Outgoing Stack Argument Layout.** Unlike `CallConv.Win64`, `CallConv.SysV64` allocates zero bytes of register shadow/home space (`shadow_space = 0`). Arguments classified as `MEMORY` (or spilling past the 6 GPR / 8 XMM registers) are placed on the stack starting at `[RSP + 0]` in left-to-right parameter order, with each stack argument size rounded up to an 8-byte multiple and aligned to `max(8, align_of(T))`. [0192 §4, §8]

**AXS-ELFS-008 — Direct Native Object Emission & Optional Assembly Dumps.** `compiler/obj/elf` emits ELF64 `.o` files directly from encoded Machine IR bytes without invoking any external assembler (`REQ-TGT-059`, `REQ-TGT-101`, `REQ-TGT-103`, `REQ-TGT-104`). Textual assembly emission (`inspect --emit=asm` / `--emit=mc`) is an optional diagnostic view (`REQ-TGT-102`), never an intermediate compilation stage. [0255 §1–2; REQ-TGT-059, REQ-TGT-101..104]

**AXS-ELFS-009 — Byte-Exact Deterministic ELF Generation.** Every ELF64 object (`.o`), GNU archive (`.a`), and static executable emitted for `x86_64-linux` is a pure deterministic function of source inputs and compiler flags (`0192 AELF-39`, `SPEC-04 AXS-EXT-006`, `REQ-TGT-059`, `REQ-TGT-106`), containing zero timestamps, zero host paths, and zero pointer-ordered hash iterations. [0192 AELF-39; SPEC-04 AXS-EXT-006; REQ-TGT-059, REQ-TGT-106]

---

## 2. System V AMD64 Calling Convention (`CallConv.SysV64`, `AXS-ELFS-010`..`020`)

**AXS-ELFS-010 — Integer & Pointer Argument Registers (`RDI, RSI, RDX, RCX, R8, R9`).** Scalar `INTEGER`-class arguments (`i8..i64`, `u8..u64`, `isize`, `usize`, `bool`, `char`, raw pointers `*const T`/`*mut T`, single-pointer `view<T>`/`mut_view<T>` to sized `T`, and `fn` pointers) are assigned left-to-right to the 6 general-purpose registers `RDI`, `RSI`, `RDX`, `RCX`, `R8`, `R9` (`0192 §4, §26`). Integer types narrower than 32 bits (`i8`, `u8`, `i16`, `u16`, `bool`) are sign- or zero-extended to 32 bits by the caller; arguments after the 6th `INTEGER` eightbyte are passed in `MEMORY` on the stack (`AXS-ELFS-007`). [0192 §4, §26; SPEC-04 AXS-EXT-052]

**AXS-ELFS-011 — Floating-Point & Vector Argument Registers (`XMM0..XMM7`).** Scalar floating-point (`f32`, `f64`) and 128-bit SIMD vector (`v128` / `Vector<T, N>`) arguments are classified as `SSE` and assigned left-to-right to `XMM0` through `XMM7` (`0192 §5`, `SPEC-41 AXS-FLT-040`). The `SSE` register counter (`0..8`) is independent of the `INTEGER` register counter (`0..6`). When 256-bit `AVX` or 512-bit `AVX-512` features are enabled on the function signature (`SPEC-44 AXS-CPU-010`), `v256`/`v512` arguments use `YMM0..YMM7` / `ZMM0..ZMM7`. [0192 §5; SPEC-41 AXS-FLT-040; SPEC-43 AXS-SBE-020]

**AXS-ELFS-012 — 128-Bit Integer (`i128`/`u128`) & Fat-Pointer (`Str`, `view<[T]>`, `dyn Trait`) Passing.** A 16-byte integer (`i128` or `u128`, passed as low 64 bits then high 64 bits) or a 16-byte two-word fat pointer (`Str` / `view<[T]>` `(ptr, len)` or `view<dyn Trait>` `(data_ptr, vtable_ptr)`) consists of two `INTEGER` eightbytes (`SPEC-40 AXS-INT-011`, `SPEC-63 AXS-DYN-021`). If at least 2 GPRs remain free in `RDI, RSI, RDX, RCX, R8, R9`, the two eightbytes occupy the next two consecutive available GPRs (no even/odd alignment pair is required). If only 0 or 1 GPR remains free, the entire 16-byte value is passed on the stack (Aligned to 16 bytes for `i128`/`u128` and 8 bytes for fat pointers) and the remaining single GPR stays available for a subsequent 1-eightbyte `INTEGER` parameter. [0192 §4, §6; SPEC-40 AXS-INT-011; SPEC-63 AXS-DYN-021]

**AXS-ELFS-013 — Eightbyte Aggregate Classification (`NO_CLASS`, `INTEGER`, `SSE`, `MEMORY`).** Structs, tuples, enums, and fixed arrays passed or returned by value are classified per eightbyte (`0192 §6, AELF-29`, `SPEC-50 AXS-UNS-034`, `REQ-TGT-042`):
1. **Size / alignment filter:** If `size == 0` (ZST, e.g. `()`), the type is `NO_CLASS` and consumes 0 registers and 0 stack bytes. If `size > 16` bytes (more than two 8-byte chunks, excluding native SIMD vector types) or the type contains unaligned fields (`@repr(packed)`), the entire aggregate is classified as `MEMORY`.
2. **Eightbyte field merge ($k \in \{0, 1\}$):** Partition the aggregate (`1 <= size <= 16`) into up to two 8-byte ranges $[0, 8)$ and $[8, 16)$. Initialize each eightbyte class to `NO_CLASS`. For every scalar leaf field overlapping eightbyte $k$, merge its class (`INTEGER` for integers/pointers/discriminants, `SSE` for `f32`/`f64`/`v128`) into eightbyte $k$'s class using the associative SysV merge rule:
   $$\text{merge}(a, b) = \begin{cases} b & \text{if } a = \text{NO\_CLASS} \\ a & \text{if } b = \text{NO\_CLASS} \text{ or } a = b \\ \text{MEMORY} & \text{if } a = \text{MEMORY} \text{ or } b = \text{MEMORY} \\ \text{INTEGER} & \text{if } \{a, b\} = \{\text{INTEGER}, \text{SSE}\} \end{cases}$$
3. **Post-merger & register availability rule:** If either eightbyte is `MEMORY`, both become `MEMORY`. For call arguments, if the remaining free GPRs (`< needed_int_eightbytes`) or remaining free XMMs (`< needed_sse_eightbytes`) cannot hold **all** eightbytes of the aggregate simultaneously, the entire aggregate is reclassified as `MEMORY` and passed by copy on the stack without consuming any registers. [0192 §6, AELF-29; SPEC-50 AXS-UNS-034; REQ-TGT-042]

**AXS-ELFS-014 — Scalar & Dual-Register 16-Byte Return Values (`RAX:RDX`, `XMM0:XMM1`, Mixed).** Return values with `1 <= size <= 16` classified into one or two register eightbytes are returned directly in registers (`0192 §6`, `REQ-TGT-042`):
- `(INTEGER)`: returned in `RAX`.
- `(SSE)`: returned in `XMM0`.
- `(INTEGER, INTEGER)` (including `i128`/`u128`, `Str`, `view<[T]>`, `dyn Trait`, and 2-word integer structs/enums): eightbyte 0 in `RAX`, eightbyte 1 in `RDX`.
- `(SSE, SSE)` (e.g. `struct Vec2f64 { x: f64, y: f64 }`): eightbyte 0 in `XMM0`, eightbyte 1 in `XMM1`.
- `(INTEGER, SSE)`: eightbyte 0 in `RAX`, eightbyte 1 in `XMM0`.
- `(SSE, INTEGER)`: eightbyte 0 in `XMM0`, eightbyte 1 in `RAX`. [0192 §6; REQ-TGT-042]

**AXS-ELFS-015 — Hidden `sret` Return Pointer in `RDI` Returned in `RAX`.** When a function's return type is classified as `MEMORY` (`size > 16` bytes), the caller allocates a disjoint stack slot aligned to `max(16, align_of(Ret))` and passes its address as an implicit first argument in `RDI` (`0192 §6`, `REQ-TGT-042`, `REQ-TGT-043`). Explicit `INTEGER` parameters therefore start at `RSI, RDX, RCX, R8, R9` (5 remaining GPRs). Upon return, the callee writes the returned aggregate to `[sret]` and places the `sret` pointer value into `RAX`, preserving ownership and deterministic `Drop` semantics without extra copies (`REQ-TGT-043`). [0192 §6; REQ-TGT-042, REQ-TGT-043]

**AXS-ELFS-016 — Caller-Saved Registers & Explicit Call Clobbers.** Under `CallConv.SysV64`, `RAX`, `RCX`, `RDX`, `RSI`, `RDI`, `R8`, `R9`, `R10`, `R11`, all vector registers `XMM0..XMM15` (`YMM0..YMM15`, `ZMM0..ZMM31`), and `RFLAGS` (with direction flag `DF = 0` on entry and return) are caller-saved (`0192 §7`, `REQ-TGT-037`, `REQ-TGT-039`). Every Machine IR `CALL` instruction explicitly lists these registers in its ABI clobber set (`REQ-TGT-037`), and register allocation never assumes a caller-saved register survives across a call boundary (`REQ-TGT-039`). [0192 §7; REQ-TGT-037, REQ-TGT-039]

**AXS-ELFS-017 — Callee-Saved Registers (`RBX, RBP, R12..R15`).** Under `CallConv.SysV64`, `RBX`, `RBP`, `R12`, `R13`, `R14`, and `R15` (along with the stack pointer `RSP`) are callee-saved (`0192 §7`, `REQ-TGT-038`). Unlike `Win64`, `RDI`, `RSI`, and `XMM6..XMM15` are **not** callee-saved on `SysV64`. `FrameLayout` records and saves/restores in the prologue/epilogue every callee-saved register modified by the function body (`REQ-TGT-038`). [0192 §7; REQ-TGT-038]

**AXS-ELFS-018 — Parallel Argument & Return Copy Resolution.** Argument setup before `call`, parameter entry moves at function start, and multi-register return moves (`RAX:RDX`, `XMM0:XMM1`) are modeled as simultaneous parallel copies (`REQ-TGT-041`). `compiler/abi/sysv64` topologically orders non-conflicting moves and breaks register permutation cycles (such as swapping `RDI` and `RSI`) using dedicated caller-saved scratch registers `R10`/`R11` (or `XMM15` for `SSE`) so no source value is overwritten before use (`REQ-TGT-041`). [0162 §19–21; REQ-TGT-041]

**AXS-ELFS-019 — Variadic `extern "C"` Calls & `AL` Vector Register Count.** For calls to variadic `extern "C" fn(fixed..., ...)` declarations (`SPEC-50 AXS-UNS-032`), `compiler/abi/sysv64` promotes variadic `f32` arguments to `f64` and sets `AL` (`mov al, K`, where $0 \le K \le 8$) immediately before `call` to the exact number of `XMM` registers holding floating-point/vector arguments. [SPEC-50 AXS-UNS-032]

**AXS-ELFS-020 — Calling Convention Mapping for `Axiom`, `"C"`, `"system"`, and `"win64"`.** On `x86_64-linux`, default `fn`, `extern "C" fn`, and `extern "system" fn` all lower to `CallConv.SysV64`; `extern "win64" fn` explicitly selects `CallConv.Win64`, and `extern "interrupt" fn` selects `CallConv.Interrupt` (`SPEC-52 AXS-FRE-015`). [0163 §6; 0192 §4, §23]

---

## 3. ELF64 Relocatable Objects (`ET_REL`) & Deterministic GNU `ar` Archives (`AXS-ELFS-021`..`029`)

**AXS-ELFS-021 — ELF64 Relocatable File Header (`Elf64_Ehdr`, 64 Bytes).** `compiler/obj/elf` emits relocatable `.o` objects beginning with a 64-byte little-endian `Elf64_Ehdr` (`0192 §10–11`, `0255 §1–3`):
- `e_ident[0..4] = "\x7FELF"` (`0x7F, 0x45, 0x4C, 0x46`), `EI_CLASS = ELFCLASS64 (2)`, `EI_DATA = ELFDATA2LSB (1)`, `EI_VERSION = EV_CURRENT (1)`, `EI_OSABI = ELFOSABI_NONE (0)`, `EI_ABIVERSION = 0`, `e_ident[9..16] = 0`;
- `e_type = ET_REL (1)`, `e_machine = EM_X86_64 (62 / 0x3E)`, `e_version = 1`, `e_entry = 0`, `e_phoff = 0`, `e_flags = 0`, `e_ehsize = 64`, `e_phentsize = 0`, `e_phnum = 0`, `e_shentsize = 64`, and `e_shstrndx` set to the section index of `.shstrtab`. [0192 §10–11, AELF-20..21; 0255 §1–3]

**AXS-ELFS-022 — Canonical ELF64 Section Table (`Elf64_Shdr`, 64 Bytes Each).** `compiler/obj/elf` maps format-neutral `SectionKind`s (`SPEC-04 AXS-EXT-071`) to canonical ELF64 sections (`0192 §11–12, AELF-24`, `0255 §4–7`):

| Section | `sh_type` | `sh_flags` | `sh_addralign` | `sh_entsize` | Purpose |
|---|---|---|---|---|---|
| `""` (index `0`) | `SHT_NULL (0)` | `0` | `0` | `0` | Mandatory null section header |
| `.text` (`.text.<sym>`) | `SHT_PROGBITS (1)` | `SHF_ALLOC \| SHF_EXECINSTR (0x6)` | `16` | `0` | Machine code bytes |
| `.rodata` (`.rodata.<sym>`) | `SHT_PROGBITS (1)` | `SHF_ALLOC (0x2)` | `max(8, align)` | `0` | Read-only constants, `Str` literals, vtables |
| `.data` (`.data.<sym>`) | `SHT_PROGBITS (1)` | `SHF_ALLOC \| SHF_WRITE (0x3)` | `max(8, align)` | `0` | Initialized mutable `static` storage |
| `.bss` (`.bss.<sym>`) | `SHT_NOBITS (8)` | `SHF_ALLOC \| SHF_WRITE (0x3)` | `max(8, align)` | `0` | Zero-initialized mutable `static` (`0` file bytes) |
| `.rela.text`, `.rela.rodata`, `.rela.data` | `SHT_RELA (4)` | `SHF_INFO_LINK (0x40)` | `8` | `24` | Explicit-addend relocations (`sh_link = .symtab`, `sh_info = target_sec`) |
| `.symtab` | `SHT_SYMTAB (2)` | `0` | `8` | `24` | Symbol table (`sh_link = .strtab`, `sh_info = first_non_local`) |
| `.strtab`, `.shstrtab` | `SHT_STRTAB (3)` | `0` | `1` | `0` | NUL-terminated symbol and section name tables (byte `0` = `\0`) |

When per-item section subdivision or generic deduplication is active (`SPEC-27 AXS-LNK-020`), each item is emitted into `.text.<sym>` / `.rodata.<sym>` / `.data.<sym>` / `.bss.<sym>` with `SHT_GROUP (17)` COMDAT groups (`GRP_COMDAT = 0x1`). [0192 §11–12; 0255 §4–7; SPEC-04 AXS-EXT-071; SPEC-27 AXS-LNK-020]

**AXS-ELFS-023 — Embedded Non-Alloc `.axmeta` / `.axlto` Sections in ELF64.** Compiler metadata sections (`.axmeta`, `.axmir`, `.axlto`, `SPEC-24 AXS-ART-020`) are emitted in ELF64 `.o` files with `sh_type = SHT_PROGBITS (1)` and `sh_flags = 0` (non-`SHF_ALLOC`), validated for BLAKE3 integrity and `TargetFingerprint` on read, and stripped by `compiler/link/elf` when writing final `ET_EXEC` images. [SPEC-04 AXS-EXT-071; SPEC-24 AXS-ART-020..024]

**AXS-ELFS-024 — ELF64 Symbol Table (`Elf64_Sym`, 24 Bytes) & Local-Before-Global Invariant.** Every `.symtab` begins with the null entry at index `0` (`STN_UNDEF`), followed by all `STB_LOCAL (0)` symbols (section symbols `STT_SECTION = 3` and private items) sorted deterministically by name, followed by all `STB_GLOBAL (1)` and `STB_WEAK (2)` symbols sorted deterministically by name (`0192 §13`, `SPEC-04 AXS-EXT-072`). `.symtab.sh_info` is set to the exact index of the first non-`STB_LOCAL` symbol. Defined functions use `STT_FUNC (2)` (`st_size` = encoded byte length), defined data items use `STT_OBJECT (1)`, and unresolved external references use `STB_GLOBAL`, `STT_NOTYPE (0)`, and `st_shndx = SHN_UNDEF (0)`. [0192 §13; SPEC-04 AXS-EXT-072]

**AXS-ELFS-025 — Fixed-Address `@at` / `@addr` Symbols via `SHN_ABS`.** Fixed-address overlay declarations (`@at(0xFEE0_0000) extern static LAPIC: ...`, `SPEC-55 AXS-ADR-021`, `SPEC-04 AXS-EXT-072`) are emitted into `.symtab` with special section index `st_shndx = SHN_ABS (0xFFF1)` and `st_value = 0xFEE0_0000`. Linker relocations against a `SHN_ABS` symbol use $S = \text{st\_value}$ directly without section base adjustment. Pinned placement definitions (`@at(A) static X = ...`) carry `pinned_vma = Some(A)` (`AX_LINK_AT_OVERLAP` on VMA collision). [SPEC-04 AXS-EXT-071..072; SPEC-55 AXS-ADR-021..023]

**AXS-ELFS-026 — Explicit-Addend Relocations (`Elf64_Rela`, 24 Bytes) & Relocation Kinds.** The x86-64 machine encoder never resolves ELF symbols directly (`0192 §14–15, AELF-22..23`, `REQ-TGT-060`); it zeroes the 4- or 8-byte target field in `.text`/`.data` and records a format-neutral relocation mapped by `compiler/obj/elf` to a 24-byte `Elf64_Rela { r_offset: u64, r_info: (sym_idx << 32) | r_type, r_addend: i64 }` entry ($S$ = symbol virtual address, $A$ = signed `r_addend`, $P$ = relocated field virtual address):

| Target-Neutral Kind | ELF64 `r_type` | Value | Width | Computation | Signed/Unsigned Range |
|---|---|---|---|---|---|
| `Addr64` | `R_X86_64_64` | `1` | 64-bit | $S + A$ | Full 64-bit `u64` / `i64` |
| `Rel32` (RIP-rel data/const) | `R_X86_64_PC32` | `2` | 32-bit | $S + A - P$ | Signed `i32` $[-2^{31}, 2^{31}-1]$ |
| `Plt32` / `Rel32` (`call`/`jmp`) | `R_X86_64_PLT32` | `4` | 32-bit | $S + A - P$ (static link resolves directly to target $S$) | Signed `i32` $[-2^{31}, 2^{31}-1]$ |
| `Abs32` (zero-extended 32-bit) | `R_X86_64_32` | `10` | 32-bit | $S + A$ | Unsigned `u32` $[0, 2^{32}-1]$ |
| `Abs32S` (sign-extended `imm32`/`disp32`) | `R_X86_64_32S` | `11` | 32-bit | $S + A$ | Signed `i32` $[-2^{31}, 2^{31}-1]$ |

For x86-64 RIP-relative instructions where the CPU adds `disp32` to `RIP_next = P + k` ($k = 4$ when `disp32` is at the end of the instruction), `r_addend` is `extra_offset - k` (`-4` for a direct target reference). [0192 §14–15, AELF-22..23; SPEC-04 AXS-EXT-073; REQ-TGT-060]

**AXS-ELFS-027 — Relocation Overflow Verification (`AX_LINK_RELOC_OUT_OF_RANGE`).** During static linking, if $S + A - P$ for `R_X86_64_PC32`/`R_X86_64_PLT32` or $S + A$ for `R_X86_64_32S` lies outside $[-2^{31}, 2^{31}-1]$, or $S + A$ for `R_X86_64_32` lies outside $[0, 2^{32}-1]$, `compiler/link/elf` rejects the link with `AX_LINK_RELOC_OUT_OF_RANGE` (`spec/diagnostics.md` §10.8). [0256 §9; SPEC-27 AXS-LNK-024]

**AXS-ELFS-028 — ELF64 Reader/Writer Round-Trip & Corrupt Object Rejection (`AX_LINK_BAD_OBJECT`).** `compiler/obj/elf` implements both `ElfObjectWriter` and `ElfObjectReader` such that serializing an `ObjectFile` and parsing it back preserves all sections, symbols, alignments, and `Elf64_Rela` records (`0192 AELF-40`). Any input `.o` lacking `\x7FELF` magic, having `EI_CLASS != ELFCLASS64`, `EI_DATA != ELFDATA2LSB`, `e_type != ET_REL`, or truncated/out-of-bounds section/symbol/string tables is rejected with `AX_LINK_BAD_OBJECT` (or `AX_LINK_ARTIFACT_TARGET_MISMATCH` if `e_machine != EM_X86_64`). [0192 §30 ELF-BOOT-011..012, AELF-40; 0256 §4]

**AXS-ELFS-029 — Deterministic GNU `ar` (`ArchiveFormat.GnuAr`) Static Archives (`.a`).** On `x86_64-linux`, `--kind lib` produces a deterministic GNU `ar` archive (`lib<name>.a` or `-o <path>`, `SPEC-04 AXS-EXT-070`, `SPEC-26 AXS-WLIB-010..012`):
- 8-byte signature `!<arch>\n`, followed by 60-byte ASCII headers with `ar_date = "0           "`, `ar_uid = "0     "`, `ar_gid = "0     "`, `ar_mode = "0       "`, and `\x60\n` trailer (even-byte padded with `\n`).
- First member `"/               "` (GNU symbol table): 4-byte **big-endian** symbol count $N$, $N \times 4$-byte **big-endian** member file offsets, and $N$ NUL-terminated symbol names in deterministic member/lexicographical order.
- Optional `"//              "` extended filename table for member names $> 15$ bytes (`"/<dec_offset>"`).
- `compiler/link/elf` extracts `.a` archive members via the demand-driven fixed-point loop (`SPEC-26 AXS-WLIB-012`) and reports `AX_LINK_BAD_ARCHIVE` on corrupt archives. [SPEC-04 AXS-EXT-070; SPEC-26 AXS-WLIB-010..012; tasks/0369]

---

## 4. Static ELF64 Executable Linker (`ET_EXEC`), `PT_LOAD` Layout & `_start` Contract (`AXS-ELFS-030`..`039`)

**AXS-ELFS-030 — Static ELF64 Executable Header (`Elf64_Ehdr`, `ET_EXEC`).** `compiler/link/elf` emits static Linux x86-64 executables (`ImageFormat.ElfExec`) with `e_type = ET_EXEC (2)`, `e_machine = EM_X86_64 (62)`, `e_version = 1`, `e_phoff = 64`, `e_phentsize = 56`, `e_shentsize = 64`, and `e_entry` set to the virtual address of `_start` (or the user's `@entry` function in `freestanding`/`kernel` profiles). [0192 §16–20, §24, AELF-27, AELF-34; 0256]

**AXS-ELFS-031 — Section-to-Segment Mapping, `0x400000` Base & W^X `PT_LOAD` Layout.** Sections and segments are distinct (`0192 §17–18, AELF-25..26`). `compiler/link/elf` merges input sections by permission class at default image base `0x0040_0000` (`4 MiB`) and builds up to three 4 KiB page-aligned (`p_align = 0x1000`) `PT_LOAD (1)` program headers plus `PT_GNU_STACK (0x6474e551)`:
1. **Segment 0 (`RX`, `p_flags = PF_R | PF_X = 0x5`)**: Maps `Elf64_Ehdr` + `Elf64_Phdr[]` + `.text` starting at `p_vaddr = 0x400000`, `p_paddr = 0x400000`, `p_offset = 0`, `p_filesz = p_memsz`.
2. **Segment 1 (`R`, `p_flags = PF_R = 0x4`)**: Maps `.rodata` at `p_vaddr = align_up(seg0_end, 0x1000)` (omitted when `.rodata` is empty).
3. **Segment 2 (`RW`, `p_flags = PF_R | PF_W = 0x6`)**: Maps `.data` followed by `.bss` at `p_vaddr = align_up(prev_end, 0x1000)` with `p_filesz = sizeof(.data)` and `p_memsz = sizeof(.data) + sizeof(.bss)` (omitted when both `.data` and `.bss` are empty).
4. **`PT_GNU_STACK`**: Emitted with `p_flags = PF_R | PF_W (0x6)` (never `PF_X`) to enforce a non-executable process stack. No `PT_LOAD` segment ever sets both `PF_W` and `PF_X` (strict W^X). [0192 §17–18, AELF-25..26; tasks/0563]

**AXS-ELFS-032 — Page Congruence & Non-Overlapping Virtual Address Layout.** Every `PT_LOAD` segment satisfies `p_vaddr % 0x1000 == p_offset % 0x1000` and `p_memsz >= p_filesz`. All section and symbol virtual addresses are finalized before patching any `Elf64_Rela` entry. If an image exceeds the 2 GiB small-code-model range or pinned `@at` sections overlap, the linker reports `AX_LINK_IMAGE_TOO_LARGE` or `AX_LINK_AT_OVERLAP`. [0192 §18; 0256 §6–9]

**AXS-ELFS-033 — Hosted `_start` Entry Stub, Initial Linux Stack (`argc`/`argv`/`envp`) & `SYS_exit_group`.** On Linux x86-64 process creation, the kernel transfers control to `e_entry` (`_start`) with `RSP` 16-byte aligned pointing directly to `[argc, argv[0], ..., argv[argc-1], 0, envp[0], ..., 0, auxv...]` (`0192 §20–22, AELF-32`). In `--profile hosted`, the linker synthesizes `_start`:
1. `xor ebp, ebp` (marks outermost frame per SysV AMD64 ABI);
2. Reads `rdi = [rsp]` (`argc`), `rsi = rsp + 8` (`argv`), `rdx = rsp + 8 * (argc + 2)` (`envp`), storing them into `std.sys.linux` globals (`__ax_linux_argc`, `__ax_linux_argv`, `__ax_linux_envp`) when `std` process/env support is linked;
3. `and rsp, -16` and `call main` (or `__ax_main_wrapper`);
4. `mov edi, eax` (exit code), `mov eax, 231` (`SYS_exit_group`), `syscall`, followed by fallback `mov eax, 60` (`SYS_exit`), `syscall`, and `ud2`. [0192 §20–22, AELF-32]

**AXS-ELFS-034 — Zero `libc`, `crt1.o`, or External Linker Dependency.** Static executables built with `--target x86_64-linux` contain zero `PT_INTERP`, zero `DT_NEEDED`, zero `glibc`/`musl` startup objects (`crt1.o`, `crti.o`, `crtn.o`), and are linked entirely in-process by `compiler/link/elf` without invoking `ld`, `lld`, or `gcc` (`0192 §21, AELF-27, AELF-35`, `INV-BOOT-003`, `INV-SEM-005`). [0192 §21, AELF-27, AELF-35; INV-BOOT-003; INV-SEM-005]

**AXS-ELFS-035 — Default Artifact Extensions & Executable Permissions on `x86_64-linux`.** When `-o <path>` is omitted under `--target x86_64-linux`: `--kind exe` writes `<stem>` (no extension, `chmod 0755` on POSIX/WSL filesystems), `--kind obj` / `--emit=obj` writes `<stem>.o`, and `--kind lib` writes `lib<stem>.a`. `-L<dir>` and `-l<name>` probe `<dir>/lib<name>.a` and `<dir>/<name>.a` in deterministic CLI order (`AX_LINK_LIBRARY_NOT_FOUND` if missing). [SPEC-04 AXS-EXT-070; SPEC-26 AXS-WLIB-002..003]

**AXS-ELFS-036 — Cross-Object Symbol Resolution (`Strong`, `Weak`, `COMDAT`) in `compiler/link/elf`.** Across input `.o` files and extracted `.a` archive members, `compiler/link/elf` resolves `STB_GLOBAL` (`Strong`), `STB_WEAK` (`Weak`), and `SHT_GROUP` (`GRP_COMDAT`) definitions (`0256 §5`, `SPEC-27 AXS-LNK-010..014`): two strong definitions emit `AX_LINK_DUPLICATE_SYMBOL`, a strong definition overrides a weak definition, multiple weak/COMDAT definitions deterministically select the first in canonical link order, an unresolved strong reference emits `AX_LINK_UNDEFINED_SYMBOL`, and an unresolved `STB_WEAK` reference resolves to virtual address `0`. [0256 §5; SPEC-27 AXS-LNK-010..014]

**AXS-ELFS-037 — Reachability-Based Section Garbage Collection (`--gc-sections`).** `compiler/link/elf` performs mark-sweep reachability analysis from `_start` / `@entry`, `@export`, `@used`, and `@at` fixed-address roots over the section relocation graph (`0192 §16`, `0256 §3`, `SPEC-27 AXS-LNK-020..022`), discarding unreferenced `.text.<sym>`, `.rodata.<sym>`, `.data.<sym>`, and `.bss.<sym>` sections before assigning virtual addresses. [0192 §16; 0256 §3; SPEC-27 AXS-LNK-020..022]

**AXS-ELFS-038 — Freestanding & Kernel ELF64 Image Layout & Pinned VMA Support.** In `--profile freestanding` and `--profile kernel`, `compiler/link/elf` sets `e_entry` directly to the `@entry` function (`AXS-ELFS-004`), places `@section("...")` and `@at(A)` pinned sections at their exact requested virtual addresses (`AX_LINK_AT_OVERLAP` on overlap), and supports `--format bin` raw flat binary output (`SPEC-55 AXS-ADR-022..024`). [SPEC-52 AXS-FRE-023; SPEC-55 AXS-ADR-022..024; REQ-TGT-002, REQ-TGT-003]

**AXS-ELFS-039 — Standard ELF64 Tooling & Cross-Linker Interoperability.** ELF64 `.o`, `.a`, and `ET_EXEC` files emitted by `axiomc` strictly obey the System V gABI and x86-64 psABI so `readelf -a`, `objdump -dr`, `nm`, and system linkers (`ld`/`lld`) inspect and cross-link `--emit=obj` output cleanly without warnings or malformed headers (`0192 §30`, `ADR-0034 §4`). [0192 §30; ADR-0034 §4]

---

## 5. `std.sys.linux` Raw Syscall ABI & `SPEC-04 AXS-EXT-110` Host Mapping (`AXS-ELFS-040`..`049`)

**AXS-ELFS-040 — Linux x86-64 Raw `syscall` ABI Convention.** `std/sys/linux` invokes the Linux kernel directly via the `syscall` (`0F 05`) instruction without `libc` wrappers (`0192 §23, AELF-33, AELF-35`):
- Syscall number in `RAX`; up to 6 arguments in `RDI`, `RSI`, `RDX`, `R10` (4th argument in `R10`, **not** `RCX`), `R8`, `R9`.
- `syscall` clobbers `RCX` (return `RIP`) and `R11` (saved `RFLAGS`) and returns a signed 64-bit result in `RAX` where values in `[-4095, -1]` represent `-errno`. [0192 §23, AELF-33]

**AXS-ELFS-041 — Deterministic Linux `-errno` to `AXS-EXT-110` Host Error Mapping.** Every fallible `__ax_host_*` implementation in `std/sys/linux` maps kernel `-errno` values in `[-4095, -1]` to the canonical negated host error codes of `SPEC-04 AXS-EXT-110` (never exposing raw OS `errno` numbers, `SPEC-03 AXS-SEM-003`):
- `-ENOENT (-2)` $\rightarrow$ `-1` (`NotFound`);
- `-EPERM (-1)`, `-EACCES (-13)`, `-EROFS (-30)` $\rightarrow$ `-2` (`PermissionDenied`);
- `-EEXIST (-17)` $\rightarrow$ `-3` (`AlreadyExists`);
- `-EBADF (-9)`, `-ENOTDIR (-20)`, `-EISDIR (-21)`, `-EINVAL (-22)`, `-ENAMETOOLONG (-36)` $\rightarrow$ `-4` (`InvalidInput`);
- `-ETIMEDOUT (-110)` (and `-EAGAIN (-11)` on timed waits) $\rightarrow$ `-5` (`TimedOut`);
- `-EINTR (-4)` is retried transparently on blocking/I/O syscalls; all other `-errno` values map to `-9` (`Other`). [SPEC-04 AXS-EXT-110; SPEC-03 AXS-SEM-003]

**AXS-ELFS-042 — Heap Allocation Mapping (`heap_alloc`, `heap_realloc`, `heap_free`).** `std/sys/linux/heap.ax` implements `host.heap_alloc(size, align)`, `host.heap_realloc(p, old_size, new_size, align)`, and `host.heap_free(p, size, align)` (`SPEC-04 AXS-EXT-110`) using `SYS_mmap = 9` (`PROT_READ | PROT_WRITE = 0x3`, `MAP_PRIVATE | MAP_ANONYMOUS = 0x22`, `fd = -1`, `offset = 0`), `SYS_mremap = 25` (`MREMAP_MAYMOVE = 0x1`), and `SYS_munmap = 11` (with an internal lock-free size-class slab for sub-page allocations and page-aligned `mmap` for larger blocks up to `align <= 4096`), returning `null` (`0 as *mut u8`) on allocation failure. [SPEC-04 AXS-EXT-110; T651]

**AXS-ELFS-043 — Console & File I/O Mapping (`stdio`, `open`, `read`, `write`, `close`, `file_size`).** `std/sys/linux/io.ax` maps the `SPEC-04 AXS-EXT-110` I/O intrinsics directly to Linux file descriptors:
- `stdio(0|1|2)` returns `0` (`STDIN`), `1` (`STDOUT`), or `2` (`STDERR`) (`-4` if `which > 2`).
- `open(path, path_len, mode)` copies `path` into a NUL-terminated buffer (returning `-4` on interior `\0` or invalid UTF-8) and invokes `SYS_openat = 257` with `dfd = AT_FDCWD (-100)`, `mode = 0666`, and flags `O_RDONLY | O_CLOEXEC (0x80000)` for `0`, `O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC (0x80241)` for `1`, or `O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC (0x80441)` for `2`.
- `read` $\rightarrow$ `SYS_read = 0`; `write` $\rightarrow$ `SYS_write = 1` (writing UTF-8 bytes directly to console/files); `close` $\rightarrow$ `SYS_close = 3`; `file_size(h)` $\rightarrow$ `SYS_fstat = 5` reading `stat.st_size` (`offset 48` in `x86_64` `struct stat`). [SPEC-04 AXS-EXT-110; T651]

**AXS-ELFS-044 — Process, CLI Arguments, Environment & `exe_path` Mapping (`args_count`, `arg`, `env_get`, `exe_path`, `exit`).** `std/sys/linux/process.ax` reads `__ax_linux_argc`, `__ax_linux_argv`, and `__ax_linux_envp` saved by `_start` (`AXS-ELFS-033`):
- `args_count()` returns `__ax_linux_argc`; `arg(i, buf, cap)` returns `-4` when `i >= __ax_linux_argc` and otherwise copies `min(n, cap)` bytes of `argv[i]` and returns `n`.
- `env_get(name, name_len, buf, cap)` scans `envp` for `<name>=<val>` (returning `-4` if `name` is empty or contains `'='`/`'\0'`, `-1` if unset) and writes `min(val_len, cap)` bytes returning `val_len`.
- `exe_path(buf, cap)` invokes `SYS_readlinkat = 267` (`AT_FDCWD = -100`, `"/proc/self/exe"`, or `SYS_readlink = 89`) into a stack/scratch buffer, copies `min(n, cap)` bytes to `buf`, and returns `n`.
- `exit(code)` invokes `SYS_exit_group = 231` (`EDI = code`) followed by `SYS_exit = 60`. [SPEC-04 AXS-EXT-110; ADR-0013 §1; T651]

**AXS-ELFS-045 — Filesystem & Directory Mapping (`remove`, `mkdir`, `metadata`, `dir_open`, `dir_next`, `dir_close`).** `std/sys/linux/fs.ax` maps filesystem intrinsics (`SPEC-04 AXS-EXT-110`):
- `remove(path, path_len)` $\rightarrow$ `SYS_unlinkat = 263` (`AT_FDCWD = -100`, `flags = 0`); `mkdir(path, path_len)` $\rightarrow$ `SYS_mkdirat = 258` (`AT_FDCWD = -100`, `mode = 0777`, `-3` on `EEXIST`).
- `metadata(path, path_len, out)` $\rightarrow$ `SYS_newfstatat = 262` (`AT_FDCWD = -100`, `flags = 0`), setting `out[0]` to `1` (`S_IFREG`), `2` (`S_IFDIR`), or `3` (other) from `st_mode & 0o170000` (`offset 24`) and `out[1] = st_size as u64` (`offset 48`).
- `dir_open` opens with `SYS_openat = 257` (`O_RDONLY | O_DIRECTORY | O_CLOEXEC = 0x90000`); `dir_next` buffers `linux_dirent64` records via `SYS_getdents64 = 217`, skips `"."` and `".."`, and does not advance the cursor when `entry_len > cap`; `dir_close` closes the descriptor via `SYS_close = 3`. [SPEC-04 AXS-EXT-110; T651]

**AXS-ELFS-046 — Monotonic Clock Mapping (`monotonic_ns`).** `std/sys/linux/time.ax` implements `host.monotonic_ns() -> u64` via `SYS_clock_gettime = 228` with `CLOCK_MONOTONIC = 1`, computing `(tv_sec as u64) * 1_000_000_000u64 + (tv_nsec as u64)`. [SPEC-04 AXS-EXT-110; T651]

**AXS-ELFS-047 — Threads & Futex Mapping (`thread_*`, `futex_wait`, `futex_wake`).** `std/sys/linux/thread.ax` maps `SPEC-32 AXS-SYNC-002` / `SPEC-04 AXS-EXT-110` concurrency intrinsics:
- `thread_spawn`: maps stack via `SYS_mmap = 9` + guard page via `SYS_mprotect = 10` (`PROT_NONE = 0`) and spawns an OS thread via `SYS_clone = 56` (`CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND | CLONE_THREAD | CLONE_SYSVSEM | CLONE_PARENT_SETTID | CLONE_CHILD_CLEARTID`); child exit invokes `SYS_exit = 60` (thread-only exit).
- `thread_join` / `thread_detach`: synchronize on the `CLONE_CHILD_CLEARTID` futex word (`SYS_futex = 202`) and reclaim the thread stack.
- `thread_current_id` $\rightarrow$ `SYS_gettid = 186`; `thread_yield` $\rightarrow$ `SYS_sched_yield = 24`; `thread_sleep_ns` $\rightarrow$ `SYS_nanosleep = 35` / `SYS_clock_nanosleep = 230`.
- `futex_wait` / `futex_wake` $\rightarrow$ `SYS_futex = 202` with `FUTEX_WAIT_PRIVATE = 128` (`0` on wake or `-EAGAIN`, `-5` on `-ETIMEDOUT`, `-4` if `addr` is null or not 4-byte aligned) and `FUTEX_WAKE_PRIVATE = 129`. [SPEC-04 AXS-EXT-110; SPEC-32 AXS-SYNC-002; T651]

**AXS-ELFS-048 — Stackful Fibers (`fiber_*`) Under `CallConv.SysV64`.** `std/sys/linux/fiber.ax` implements `fiber_create`, `fiber_resume`, `fiber_yield`, and `fiber_destroy` (`SPEC-34 AXS-EXEC-054`, `SPEC-04 AXS-EXT-110`) using `SYS_mmap = 9` + `SYS_mprotect = 10` stack allocation and a `SysV64` context switch saving/restoring only `RBX, RBP, R12..R15, RSP, RIP` (64 bytes, no `XMM` or TEB state). [SPEC-04 AXS-EXT-110; SPEC-34 AXS-EXEC-054]

**AXS-ELFS-049 — Asynchronous I/O (`aio_*`) & WSL Test Runner Integration (`tools/axtest.py`).** `std/sys/linux/aio.ax` maps the `SPEC-35 AXS-AIO-050` / `SPEC-04 AXS-EXT-110` `aio_*` intrinsics using `io_uring` (`SYS_io_uring_setup = 425`, `SYS_io_uring_enter = 426`) with automatic fallback to `epoll` (`SYS_epoll_create1 = 291`, `SYS_epoll_ctl = 233`, `SYS_epoll_pwait = 281`, `SYS_eventfd2 = 290`, positional file `SYS_pread64 = 17` / `SYS_pwrite64 = 18` / `SYS_fsync = 74`, and non-blocking sockets `SYS_socket = 41`, `SYS_bind = 49`, `SYS_listen = 50`, `SYS_accept4 = 288`, `SYS_connect = 42`, `SYS_sendto = 44`, `SYS_recvfrom = 45`, `SYS_shutdown = 48`, `SYS_getsockname = 51`). In `tools/axtest.py` (`T651`), `--target x86_64-linux` tests execute directly on Linux hosts and via `wsl` on Windows hosts when available (or validate ELF64 binary structure and cleanly skip execution when `wsl` is unavailable). [SPEC-04 AXS-EXT-110; SPEC-35 AXS-AIO-050; T651]

---

## 6. Diagnostics, Canonical Examples & Traceability (`AXS-ELFS-050`..`053`)

**AXS-ELFS-050 — Diagnostics Referenced by `SPEC-80`.** `x86_64-linux` reuses the canonical `DRIVER`, `FFI`, `UNSAFE`, and `LINK` diagnostic codes (`spec/diagnostics.md` §10–11):

| Code | Area | Sev | Condition on `x86_64-linux` |
|---|---|---|---|
| `AX_DRIVER_UNKNOWN_TARGET` | `DRIVER` | `error` | Unrecognized `--target <triple>` (note: in frozen `axiom0`, `--target x86_64-linux` reported `epic = "E16.9"`; in `axiomc`, `x86_64-linux` is an active supported target, `AXS-ELFS-001`) |
| `AX_LINK_BAD_OBJECT` | `LINK` | `error` | Input `.o` lacks `\x7FELF` magic, is not 64-bit little-endian `ET_REL`, or has corrupt section/symbol/relocation tables (`AXS-ELFS-028`) |
| `AX_LINK_BAD_ARCHIVE` | `LINK` | `error` | Input `.a` archive lacks `!<arch>\n` magic or has corrupt 60-byte headers / symbol index (`AXS-ELFS-029`) |
| `AX_LINK_ARTIFACT_TARGET_MISMATCH` | `LINK` | `error` | Input `.o` / `.a` / `.axmi` has `e_machine != EM_X86_64` or mismatched `TargetFingerprint` (`AXS-ELFS-023`, `AXS-ELFS-028`) |
| `AX_LINK_UNDEFINED_SYMBOL` | `LINK` | `error` | Referenced global symbol remains undefined after archive extraction (`AXS-ELFS-036`) |
| `AX_LINK_DUPLICATE_SYMBOL` | `LINK` | `error` | Two `.o` files or extracted `.a` members define the same strong `STB_GLOBAL` symbol (`AXS-ELFS-036`) |
| `AX_LINK_RELOC_OUT_OF_RANGE` | `LINK` | `error` | `R_X86_64_PC32`, `R_X86_64_PLT32`, `R_X86_64_32`, or `R_X86_64_32S` target overflows 32-bit field (`AXS-ELFS-027`) |
| `AX_LINK_AT_OVERLAP` | `LINK` | `error` | Two pinned `@at` / `@addr` sections overlap in virtual address space (`AXS-ELFS-025`, `AXS-ELFS-038`) |

**AXS-ELFS-051 — Canonical Positive Examples (`=` and `.` Syntax).**

```axiom
// Example 1: SysV AMD64 ABI 6-GPR + XMM + 16-byte dual-register return & UTF-8 stdout on x86_64-linux
// Compiled with: axiomc build --target x86_64-linux sysv_demo.ax -o sysv_demo
module demo.linux_sysv

use std.io.println

@repr(C)
pub struct Pair16 {
    pub lo: i64,
    pub hi: i64,
}

// Passed in RDI..R9 (first 6 ints), 7th int on stack [RSP+0], floats in XMM0..XMM1;
// Returned in RAX:RDX (two INTEGER eightbytes, AXS-ELFS-013..014).
pub fn combine_sysv(
    a: i64, b: i64, c: i64, d: i64, e: i64, f: i64, g: i64,
    x: f64, y: f64,
) -> Pair16 {
    let sum_int = a + b + c + d + e + f + g
    let sum_flt = (x + y) as i64
    return Pair16 { lo = sum_int, hi = sum_flt }
}

pub fn inspect_pair(p: view<Pair16>) -> i64 {
    return p.lo + p.hi
}

pub fn main() -> i32 {
    println("Xin chào thế giới")
    let res = combine_sysv(1, 2, 3, 4, 5, 6, 10, 5.5, 5.5)
    let total = inspect_pair(view(res))
    if total == 42 {
        return 0
    }
    return 1
}
```

```axiom
// Example 2: Freestanding Linux x86-64 binary with @entry _start and @at SHN_ABS symbol (AXS-ELFS-004, AXS-ELFS-025)
// Compiled with: axiomc build --target x86_64-linux --profile freestanding bare_linux.ax -o bare_linux
module demo.linux_freestanding

@entry
@no_mangle
pub fn _start() -> i32 {
    let mut acc: i32 = 20
    acc = acc + 22
    return acc
}
```

**AXS-ELFS-052 — Canonical Negative Examples (`=` and `.` Syntax).**

```axiom
// Example 1: Pinned @at VMA overlap rejected by compiler/link/elf (AX_LINK_AT_OVERLAP, AXS-ELFS-025)
module demo.linux_overlap_err

@at(0x0040_2000)
pub static BLOCK_A: [64]u8 = [0u8; 64]

@at(0x0040_2020) //~ ERROR AX_UNSAFE_AT_OVERLAP
pub static BLOCK_B: [64]u8 = [1u8; 64]
```

```axiom
// Example 2: Freestanding Linux build importing hosted std.fs rejected (AX_NAME_FREESTANDING_FORBIDDEN_IMPORT, AXS-ELFS-003)
// Compiled with: axiomc check --target x86_64-linux --profile freestanding bad_fs.ax
module demo.linux_bad_freestanding

use std.fs.File //~ ERROR AX_NAME_FREESTANDING_FORBIDDEN_IMPORT

@entry
pub fn _start() -> i32 {
    return 0
}
```

**AXS-ELFS-053 — Requirement, Invariant & Task Traceability Matrix (`E16.9`).**

| Task | Scope | Invariant | Covered Requirements | Primary Test Suites |
|---|---|---|---|---|
| `T650` | `SPEC-80`: `x86_64-linux` `TargetDesc`, `CallConv.SysV64`, ELF64 `ET_REL`/`.a`/`ET_EXEC`, `_start`, and `std.sys.linux` syscall specification | `INV-ELFS-001`..`003` | `REQ-TGT-002`, `REQ-TGT-003`, `REQ-TGT-037`, `REQ-TGT-038`, `REQ-TGT-039`, `REQ-TGT-040` | `spec/SPEC-80-linux-x86-64-elf-static.md` |
| `T066` | `compiler/abi/sysv64`, `compiler/obj/elf` (`ET_REL` + `.a`), and `compiler/link/elf` (`ET_EXEC` at `0x400000` + `_start`) | `INV-ELFS-001` | `REQ-TGT-041`, `REQ-TGT-042`, `REQ-TGT-043`, `REQ-TGT-059`, `REQ-TGT-060`, `REQ-TGT-101`, `REQ-TGT-103`, `REQ-TGT-104` | `tests/run/linux`, `tests/selfhost/abi`, `tests/selfhost/obj`, `tests/selfhost/link` |
| `T651` | `std/sys/linux` raw syscall host interface (`AXS-EXT-110`), `compiler/driver/target_linux`, and `tools/axtest.py` WSL runner | `INV-ELFS-002` | `REQ-TGT-096`, `REQ-TGT-097`, `REQ-TGT-098`, `REQ-TGT-099`, `REQ-TGT-100` | `tests/run/linux_std`, `tests/selfhost/driver` |
| `T652` | End-to-end E16.9 `x86_64-linux` SysV ABI, static ELF64 & WSL differential conformance suite | `INV-ELFS-003` | `REQ-TGT-102`, `REQ-TGT-105`, `REQ-TGT-106`, `REQ-TGT-111`, `REQ-TGT-112` | `tests/conformance/p16/e16_9_linux_x64_static` |

## Sources

0053 §1–25; 0163 §1–7; 0164 §1–41; 0192 §1–32 (`AELF-20..40`, `ELF-BOOT-001..012`); 0217; 0220; 0255 §1–20; 0256 §1–42; `tasks/0369`; `tasks/0471` (`AKERNEL-20..27`); `tasks/0518` (`AMACHINE-48..54`, `AMACHINE-70..71`, `AMACHINE-107..117`); `tasks/0520` §13; `tasks/0563`; `spec/SPEC-03-core-semantics.md`; `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-052`, `AXS-EXT-060..062`, `AXS-EXT-070..074`, `AXS-EXT-110`); `spec/SPEC-24-artifact-format-module-interfaces.md`; `spec/SPEC-26-windows-artifact-kinds.md`; `spec/SPEC-27-separate-compilation-linker-v2.md`; `spec/SPEC-32-threads-sync.md`; `spec/SPEC-34-executors-fibers.md`; `spec/SPEC-35-async-io.md`; `spec/SPEC-40-integers.md`; `spec/SPEC-41-floating-point.md`; `spec/SPEC-43-simd-backend.md`; `spec/SPEC-44-cpu-features-multiversioning.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-52-freestanding-runtime-composition.md`; `spec/SPEC-55-fixed-address-declarations.md`; `spec/SPEC-63-dyn-trait-vtables.md`; `ADR-0001`; `ADR-0002`; `ADR-0003`; `ADR-0013`; `ADR-0034` §4.
