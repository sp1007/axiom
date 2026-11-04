# SPEC-90 — Canonical Universal / Multi-Architecture Artifacts, Mach-O Universal 2 Fat Binaries & `x86_64-macos` Slice Specification

- **Status:** draft (T689, 2026-11-04)
- **Owner:** `axiom-architect`
- **Consolidates:** `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-052`, `AXS-EXT-060..062`, `AXS-EXT-070..074`), `spec/SPEC-24-artifact-format-module-interfaces.md` (`AXS-ART-002`, `AXS-ART-010..014`, `AXS-ART-020..024`), `spec/SPEC-80-linux-x86-64-elf-static.md` (`AXS-ELFS-002`, `AXS-ELFS-005..020`, `AXS-ELFS-026..027`, `AXS-ELFS-048`), `spec/SPEC-81-target-desc-isa-conformance.md` (`AXS-TGTD-001..012`), `spec/SPEC-84-macos-aarch64-macho.md` (`AXS-MACHO-001..036`), `spec/SPEC-88-cross-compilation-platform-layer.md` (`AXS-XCMP-001..028`, `AXS-PLAT-001..024`), `spec/SPEC-89-artifact-library-matrix.md` (`AXS-ARTM-001..040`), `0097`, `0163`, `0196`, `0217`, `0220`, `tasks/0453`, `tasks/0518`, `tasks/0521`, `tasks/0522`, `tasks/0524`, `tasks/0563`, `tasks/0587`
- **Covers:** `REQ-TGT-001`, `REQ-TGT-104`, `REQ-TGT-105`, `REQ-TGT-200` (and specifies the normative `E16.11` contract for `T690`, `T691`, `T692`: `REQ-TGT-106`, `REQ-TGT-153`, `REQ-TGT-154`, `REQ-TGT-199`, `REQ-TGT-307`, `REQ-TGT-318`, `REQ-TGT-319`, `REQ-TGT-320`, `REQ-TOOL-001`)
- **Consumers:** `compiler/target/x64/macos`, `compiler/obj/macho_universal`, `compiler/link/macho`, `compiler/link/archive_resolve`, `compiler/driver/universal`, `compiler/driver/emit_universal`, `std/sys/macos`, `tests/obj/macho_universal`, `tests/driver/universal`, `tests/selfhost/obj`, `tests/selfhost/driver`, `tests/conformance/p16/e16_11_universal_artifacts`, `T690`, `T691`, `T692`

## Tóm tắt

Tài liệu `SPEC-90` chốt đặc tả chuẩn cho hiện vật nhị phân đa kiến trúc / Universal của Axiom (Epic `E16.11`), đóng khép kín mảnh ghép `ArtifactKind.Universal` đã dành chỗ từ `SPEC-04 AXS-EXT-070` và `SPEC-89 AXS-ARTM-039`:
1. **Mô hình ghép hiện vật đa đích tường minh và lát cắt `x86_64-macos` (`AXS-UNIV-001`..`009`):** Hiện vật Universal luôn được tạo bằng bước ghép hậu liên kết tường minh (`--universal-targets`), tuyệt đối không sinh ngầm định, giữ nguyên ngữ nghĩa lõi và hành vi quan sát được tương đương giữa các đích (`REQ-TGT-001`, `REQ-TGT-199`, `REQ-TGT-318`). Việc chọn hậu phương máy được quyết định hoàn toàn bởi `TargetSpec` / `TargetDesc` (`REQ-TGT-105`), chốt đầy đủ phần chênh lệch của đích `TargetId.X86_64Macos` (`x86_64-macos` / `x86_64-apple-darwin`) so với `SPEC-84`: quy ước gọi hàm `CallConv.SysV64` trên Darwin kèm tiền tố ký hiệu `_`, căn chỉnh trang/segment 4 KiB (`0x1000`), bảng định vị lại `X86_64_RELOC_*` (`0..9`), TLS `tlv_descriptor`, Compact Unwind `UNWIND_X86_64_*`, và các ký hiệu `$INODE64` của `libSystem.B.dylib` (`REQ-TGT-104`).
2. **Định dạng nhị phân Mach-O Fat / Universal 2 tất định (`AXS-UNIV-010`..`018`):** Đặc tả từng byte theo thứ tự big-endian cho `fat_header` (8 byte: `FAT_MAGIC = 0xCAFEBABE` / `FAT_MAGIC_64 = 0xCAFEBABF`, `nfat_arch`), bảng mô tả `fat_arch` (20 byte) và `fat_arch_64` (32 byte), căn chỉnh lát cắt bắt buộc `2^12` (4 KiB) cho `CPU_TYPE_X86_64` và `2^14` (16 KiB) cho `CPU_TYPE_ARM64`, sắp xếp lát cắt tăng dần tất định theo `(cputype, cpusubtype)`, đệm `0x00`, tự động nâng cấp lên `FAT_MAGIC_64` khi `offset` hoặc `size >= 4 GiB`, và cổng kiểm chứng `verify_universal_artifact` (`REQ-TGT-106`, `REQ-TGT-153`, `REQ-TGT-307`, `REQ-TGT-320`).
3. **Tệp thực thi, `.dylib`, kho lưu trữ tĩnh `BsdAr` đa kiến trúc và chữ ký mã theo từng lát cắt (`AXS-UNIV-019`..`025`):** Mọi lát cắt `MH_EXECUTE` và `MH_DYLIB` nhúng sẵn `LC_UUID` (`BLAKE3("axiom-macho-uuid-v1" || ...)`) và `LC_CODE_SIGNATURE` SHA-256 ad-hoc (`CS_ADHOC | CS_LINKER_SIGNED = 0x0002_0002`) độc lập **trước** khi đóng gói Fat; kho tĩnh `.a` / `.axlib` đa kiến trúc bọc từng kho `BsdAr` (`!<arch>\n` + `__.SYMDEF SORTED` dùng offset cục bộ theo lát cắt) bên trong vỏ Fat; gói đa hệ điều hành phi-Mach-O dùng `.axpkg` (`"AXPKG001"`, `SPEC-24`).
4. **Đường ống driver đa kiến trúc, công cụ kiểm tra/trích xuất lát cắt thay thế `lipo` và bảng mã chẩn đoán (`AXS-UNIV-026`..`036`):** Chuẩn hóa cờ `--universal-targets`, chia sẻ truy vấn tầng A (`TargetIndependent`) và cô lập tuyệt đối bộ nhớ đệm tầng B/C theo `(TargetId, TargetFeatureSet, CallConv, CodegenFingerprint)` (`TargetFingerprint`, `REQ-TGT-154`, `REQ-TGT-200`, `REQ-TGT-319`), cung cấp lệnh nội sinh `--inspect-slices` / `--extract-slice` / `--verify-arch` không cần Xcode `lipo` (`REQ-TOOL-001`), ánh xạ `E9000–E9014` sang mã `AX_<AREA>_<NAME>` chuẩn và đăng ký `INV-UNIV-001`..`004`.

---

## 1. Multi-Target Composition Model & `x86_64-macos` (`x86_64-apple-darwin`) Mach-O Slice Delta (`AXS-UNIV-001`..`009`)

**AXS-UNIV-001 — Explicit Multi-Target Composition Model, Cross-Slice Behavioral Equivalence & Bootstrap Freeze Boundary (`REQ-TGT-001`, `REQ-TGT-199`, `REQ-TGT-318`).**
1. **Explicit-only multi-target composition (`ATARGET-43`, `REQ-TGT-001`):** Universal and multi-architecture binary artifacts are **never** produced implicitly. An ordinary build (`axiomc build` or `axiomc build --target <triple>`) always emits a thin single-target artifact (`SPEC-88 AXS-XCMP-009`, `SPEC-89 AXS-ARTM-003`). Multi-architecture outputs are produced **exclusively** when the user or manifest explicitly opts into multi-target artifact composition (`--universal-targets <t1>,<t2>[,...]`, `[build] universal_targets = [...]` in `axiom.toml`, `--compose-universal`, or multi-target `axiomc package` for `.axpkg`; `tasks/0453 §194.29, §194.44 ATARGET-43`, `tasks/0587 §30–31`).
2. **Post-link artifact composition, semantic invariance & cross-target observable equivalence (`tasks/0453 §194.29`, `tasks/0522 §159 ABACKEND-53`, `tasks/0524 §112 ABACKEND-93`, `REQ-TGT-199`, `REQ-TGT-318`):** Universal packaging is strictly a post-compile / post-link container composition pass (`ArtifactKind.Universal`, `SPEC-04 AXS-EXT-070`). Core language syntax, ownership, capability checking (`view<T>` / `mut_view<T>`), deterministic `Drop`, concurrency safety, and panic semantics are 100% invariant across thin and universal builds (`REQ-TGT-318`), and equivalent target-independent Axiom programs MUST exhibit equivalent observable behavior across `x86_64-macos`, `aarch64-macos`, and `--interp` (`ABACKEND-53`, `AARM-63`, `REQ-TGT-199`).
3. **Orthogonal multi-target vs. multi-CPU mechanisms (`tasks/0587 §30–32, §39 ATARGET-22`):**
   - **Mach-O Universal 2 Fat Binaries (`ArtifactKind.Universal`, `FAT_MAGIC` / `FAT_MAGIC_64`):** Single-file, OS-loader-native multi-ISA containers combining distinct Darwin Mach-O target slices (`x86_64-macos` + `aarch64-macos`) for executables (`MH_EXECUTE`), dynamic libraries (`MH_DYLIB`), static archives (`BsdAr` `.a`), and Axiom package archives (`BsdAr` `.axlib`).
   - **Multi-Target Package Bundles (`.axpkg`, `magic = "AXPKG001"`, `SPEC-24 AXS-ART-024`, `AXS-UNIV-023`):** Explicit distribution archives indexing per-target subdirectories (`x86_64-windows/`, `aarch64-windows/`, `x86_64-linux/`, `aarch64-linux/`, `riscv64-linux/`, `aarch64-macos/`, `x86_64-macos/`, `wasm32-wasi/`) because PE/COFF, ELF64, and W3C WASM OS loaders do not natively dispatch Mach-O `FAT_MAGIC` headers (Windows ARM64X / ARM64EC hybrid PE images remain outside v1 `P16`).
   - **Intra-Target CPU Multiversioning (`@multiversion`, `SPEC-44`):** Dispatches multiple microarchitectural implementations (`sse2` vs `avx2`, `neon` vs `sve`) *inside a single thin ISA slice* (`MultiCPUArtifact`), orthogonal to `MultiTargetArtifact` (`tasks/0587 §30`).
4. **Self-hosted implementation boundary (`INV-BOOT-004`):** Because `bootstrap/axiom0/` is frozen post-`T087` (`INV-BOOT-004`), all `E16.11` production modules (`compiler/target/x64/macos`, `compiler/obj/macho_universal`, `compiler/driver/universal`, and `compiler/driver/emit_universal`) are implemented exclusively in the self-hosted `compiler/` tree (`axiomc`). [tasks/0453 §194.29, §194.44 ATARGET-43; tasks/0521 §156 AARM-63; tasks/0522 §159 ABACKEND-53; tasks/0524 §112 ABACKEND-93; tasks/0587 §30–32, §39 ATARGET-22; SPEC-04 AXS-EXT-070; SPEC-24 AXS-ART-024; SPEC-44; SPEC-88 AXS-XCMP-009; SPEC-89 AXS-ARTM-003, AXS-ARTM-039; INV-BOOT-004; REQ-TGT-001, REQ-TGT-199, REQ-TGT-318]

**AXS-UNIV-002 — `TargetSpec`-Driven Backend Selection & `TargetId.X86_64Macos` (`x86_64-macos` / `x86_64-apple-darwin`) `TargetDesc`, CPU Baseline & `@cfg` Valuation (`REQ-TGT-105`, `T690`).**
Machine backend target selection is determined solely by explicit `TargetSpec` / `TargetDesc` data (`tasks/0518 §151 AMACHINE-116`, `REQ-TGT-105`), never host OS/ISA ambient state; `compiler/target/x64/macos` (`T690`) registers the 64-bit Intel/Rosetta-2 macOS target in `compiler/target/desc` (`SPEC-81 AXS-TGTD-001..012`, `SPEC-88 AXS-XCMP-002`):
1. **Triple normalization:** Canonical triple `"x86_64-macos"` (`TargetId.X86_64Macos`), accepting CLI and `axiom.toml` aliases `"x86_64-apple-darwin"` and version-suffixed `"x86_64-apple-macosx<X>.<Y>[.<Z>]"` (matching `SPEC-84 AXS-MACHO-001` for `"aarch64-macos"` / `"aarch64-apple-darwin"` / `"arm64-apple-darwin"`).
2. **`TargetDesc` orthogonal fields (`SPEC-81 AXS-TGTD-004..006`):**
   - `arch = Arch.X86_64`, `os = Os.Macos`, `env = Env.Darwin`, `pointer_width_bits = 64`, `endian = Endian.Little`;
   - `default_call_conv = CallConv.SysV64`, `object_format = ObjectFormat.MachO`, `archive_format = ArchiveFormat.BsdAr`, `image_format = ImageFormat.MachO`;
   - `stack_align = 16`, `shadow_space = 0`, `red_zone = 128` (`0` under `--no-red-zone`, `--profile freestanding|kernel`, or `extern "interrupt"`), `page_size = 4096` (`0x1000`).
3. **Baseline `TargetFeatureSet` & Rosetta 2 safety (`SPEC-81 AXS-TGTD-007`):** Default CPU model `"x86-64-v2"` (`core2` / macOS 11.0+ baseline) enables `{ sse, sse2, sse3, ssse3, sse4.1, sse4.2, popcnt, cx16 }`. Higher extensions (`avx`, `avx2`, `fma`, `bmi1`, `bmi2`, `aes`) are **off** by default unless explicitly requested via `--cpu`, `--target-feature`, or `@target_feature` / `@multiversion` (`SPEC-44`), guaranteeing that default `x86_64-macos` slices execute both on native Intel Macs and under Apple Silicon Rosetta 2 without illegal-instruction traps.
4. **Canonical `@cfg` & `std.target` valuation (`SPEC-88 AXS-XCMP-007, AXS-XCMP-014`):**
   - `target_arch = "x86_64"`, `target_os = "macos"`, `target_family = {"unix"}`, `target_env = "darwin"`, `target_abi = "sysv64"`, `target_vendor = "apple"`, `target_endian = "little"`, `target_pointer_width = "64"`, `target_has_atomic = {"8", "16", "32", "64", "ptr", "128"}`;
   - `std.target.MIN_PAGE_SIZE_BYTES = 4096`, `std.target.CACHE_LINE_BYTES = 64` (contrasting with `16384` and `128` on `aarch64-macos`!). [0163 §1–7; 0196 §1, §34; tasks/0518 §151 AMACHINE-116; SPEC-44; SPEC-81 AXS-TGTD-001..012; SPEC-84 AXS-MACHO-001..002; SPEC-88 AXS-XCMP-002, AXS-XCMP-007, AXS-XCMP-014; REQ-TGT-105]

**AXS-UNIV-003 — `x86_64-macos` Calling Convention (`CallConv.SysV64` on Darwin), Frame Pointer, Variadic ABI & `_` Symbol Prefix (`SPEC-80` vs. `SPEC-84`, `T690`).**
`compiler/target/x64/macos` reuses the shared x86-64 instruction selector, `RegisterFile`, `LinearScan`/`Hybrid` register allocators, `verify_mc`, and x86-64 machine encoder (`SPEC-80 AXS-ELFS-002`) together with `compiler/abi/sysv64` (`SPEC-80 AXS-ELFS-005..020`: integer/pointer arguments in `RDI, RSI, RDX, RCX, R8, R9`; FP/vector arguments in `XMM0..XMM7`; 16-byte eightbyte classification & `RAX:RDX` / `XMM0:XMM1` returns; hidden `sret` in `RDI` echoed in `RAX`; callee-saved `RBX, RBP, R12..R15`; 16-byte `RSP` alignment immediately before `CALL`), subject to four Darwin-specific ABI rules:
1. **Leading `_` Mach-O symbol decoration (`SPEC-84 AXS-MACHO-010`):** Identical to `aarch64-macos`, every C-linkage (`main` -> `_main`, `@export("foo")` / `extern "C" fn foo` -> `_foo`) and Axiom-mangled (`_AX...` -> `__AX...`) external or private-external symbol carries a single leading underscore `_` in Mach-O symbol tables, archive indices, and export tries, whereas section-local temporary labels (`L...`) carry no extra underscore (and explicit `\x01<literal>` symbol names such as `\x01_stat$INODE64` emit `<literal>` verbatim without doubling `_`).
2. **Frame pointer (`RBP`) chain preservation:** Matching Apple's Darwin frame-pointer chain contract (`SPEC-84 AXS-MACHO-009`), all non-leaf functions (and all functions at `-O0`/`-O1` unless `--omit-frame-pointer` is explicitly passed) establish a 16-byte-aligned `push rbp; mov rbp, rsp` frame-pointer chain so XNU `stackshot`, Instruments, DTrace, and Compact Unwind (`UNWIND_X86_64_MODE_RBP_FRAME`) walk call stacks without DWARF `.eh_frame`.
3. **Variadic `extern "C"` ABI contrast (`x86_64-macos` vs. `aarch64-macos`):** Unlike `CallConv.Aapcs64Darwin` (which forces all anonymous variadic arguments onto the stack and represents `va_list` as `*mut u8`, `SPEC-84 AXS-MACHO-007`), `x86_64-macos` follows standard System V AMD64 variadics (`SPEC-80 AXS-ELFS-019`): anonymous arguments continue filling remaining `RDI..R9` and `XMM0..XMM7` slots, `AL` is set to the count of `XMM` vector arguments ($0 \le \text{AL} \le 8$), and C `va_list` has the 24-byte `[1]VaListTag` layout (`{ gp_offset: u32, fp_offset: u32, overflow_arg_area: *mut u8, reg_save_area: *mut u8 }`).
4. **128-byte leaf red zone (`SPEC-80 AXS-ELFS-006`):** True leaf functions in `hosted` and `system` profiles may address `[RSP - 128 .. RSP)` without adjusting `RSP`; `--no-red-zone`, `freestanding`, `kernel`, and `extern "interrupt"` set `red_zone = 0`. [0196 §11–12; SPEC-50 AXS-UNS-032; SPEC-80 AXS-ELFS-002, AXS-ELFS-005..020; SPEC-84 AXS-MACHO-007, AXS-MACHO-009, AXS-MACHO-010]

**AXS-UNIV-004 — `x86_64-macos` Mach-O 64 Header (`CPU_TYPE_X86_64`) & Deterministic Section Mapping (`REQ-TGT-104`, `REQ-TGT-106`, `REQ-TGT-153`, `T690`).**
1. **32-byte little-endian `mach_header_64` (`<mach-o/loader.h>`):**
   - `+0..4`: `magic = MH_MAGIC_64 (0xFEED_FACF)` (wire bytes `[0xCF, 0xFA, 0xED, 0xFE]`);
   - `+4..8`: `cputype = CPU_TYPE_X86_64 (0x0100_0007)` (`CPU_ARCH_ABI64 | CPU_TYPE_I386`);
   - `+8..12`: `cpusubtype = CPU_SUBTYPE_X86_64_ALL (0x0000_0003)` on emitted `MH_OBJECT (0x1)`, `MH_EXECUTE (0x2)`, and `MH_DYLIB (0x6)` (when `--cpu haswell` or higher subtype mode is explicitly requested as an `x86_64h` slice, `CPU_SUBTYPE_X86_64_H = 0x0000_0008`; when reading external Darwin `.o`/`.dylib`/`.a` inputs, the Mach-O reader masks capability bits `cpusubtype & ~CPU_SUBTYPE_MASK` where `CPU_SUBTYPE_MASK = 0xFF00_0000` so legacy `CPU_SUBTYPE_LIB64 = 0x8000_0000` headers `0x8000_0003` are accepted seamlessly).
2. **Deterministic build version & sections (`SPEC-84 AXS-MACHO-013..016`, `SPEC-89 AXS-ARTM-028`):**
   - Emits `LC_BUILD_VERSION (0x32)` (`cmdsize = 24`, `platform = PLATFORM_MACOS = 1`, `minos = 0x000B_0000` macOS 11.0 default overridable via `--macos-version-min <X.Y>`, `sdk = minos`, `ntools = 0` in `MH_OBJECT` / `1` in linked images).
   - Maps `SectionKind`s in deterministic reproducible order (`AMACHINE-117`, `AARM-59`) to `__TEXT,__text` (`align = 4` -> 16-byte function alignment, `S_ATTR_PURE_INSTRUCTIONS | S_ATTR_SOME_INSTRUCTIONS`), `__TEXT,__const`, `__TEXT,__cstring` (`S_CSTRING_LITERALS`), `__DATA_CONST,__const`, `__DATA,__data`, `__DATA,__bss` (`S_ZEROFILL`), and non-allocatable `__AXIOM,__axmeta` / `__axmir` / `__axlto` (`S_ATTR_DEBUG`, stripped from `MH_EXECUTE` and `MH_DYLIB` per `SPEC-89 AXS-ARTM-029`). [0196 §4–8; tasks/0518 §151 AMACHINE-115, 117; tasks/0521 §156 AARM-59; SPEC-84 AXS-MACHO-013..016; SPEC-89 AXS-ARTM-028..029; REQ-TGT-104, REQ-TGT-106, REQ-TGT-153]

**AXS-UNIV-005 — `x86_64-macos` Mach-O Relocation Records (`X86_64_RELOC_*`, `0..9`, `REQ-TGT-104`, `REQ-TGT-106`, `REQ-TGT-153`, `T690`).**
`compiler/target/x64/macos` and `compiler/link/macho` deterministically encode and resolve 8-byte little-endian `relocation_info` entries (`r_address: i32`, packed `u32` word `r_symbolnum:24 | r_pcrel:1 | r_length:2 | r_extern:1 | r_type:4` per `<mach-o/x86_64/reloc.h>`, sorted in descending `r_address` order when paired):

| `r_type` Name | Code | `r_pcrel` | `r_length` | Instruction / Data Context & Linker Formula ($S$ = target VMA, $P$ = field VMA, $A$ = inline addend) |
|---|---|---|---|---|
| `X86_64_RELOC_UNSIGNED` | `0` | `0` | `3` (8B) / `2` (4B) | Absolute 64-bit pointer (`quad`) or 32-bit value in `__DATA` / `__DATA_CONST` / DWARF: writes $S + A$ (`A` read from inline target bytes; emits `DYLD_CHAINED_PTR_64_OFFSET` rebase/bind in `MH_EXECUTE`/`MH_DYLIB`; rejected in `__TEXT` with `AX_LINK_TEXTREL_FORBIDDEN`) |
| `X86_64_RELOC_SIGNED` | `1` | `1` | `2` (4B) | Signed 32-bit RIP-relative `disp32` at instruction end (`leaq sym(%rip), %reg`, `movl sym(%rip), %eax`): writes $S + A - (P + 4)$ (`A` read as signed `i32` from inline `disp32`) |
| `X86_64_RELOC_BRANCH` | `2` | `1` | `2` (4B) | Signed 32-bit RIP-relative `callq` (`E8`) / `jmpq` (`E9`) `rel32`: resolves directly to $S + A - (P + 4)$ for local symbols or to synthesized `__TEXT,__stubs` trampoline VMA for dylib imports |
| `X86_64_RELOC_GOT_LOAD` | `3` | `1` | `2` (4B) | `movq sym@GOTPCREL(%rip), %reg` (`REX.W 8B /r disp32`, `r_extern = 1`): patches `disp32` to `GOT_slot(sym) - (P + 4)`; when `sym` is defined in the current linkage unit and $A = 0$, the linker MAY relax `8B` (`MOV`) -> `8D` (`LEA`) pointing directly to $S - (P + 4)$ |
| `X86_64_RELOC_GOT` | `4` | `1` | `2` (4B) | Non-relaxable RIP-relative GOT slot reference (`pushq sym@GOTPCREL(%rip)` or ALU memory operand, `r_extern = 1`): patches `disp32` to `GOT_slot(sym) + A - (P + 4)` |
| `X86_64_RELOC_SUBTRACTOR` | `5` | `0` | `3` (8B) / `2` (4B) | Immediately precedes `X86_64_RELOC_UNSIGNED` at identical `r_address`: computes $(S_{\text{unsigned}} - S_{\text{subtractor}}) + A$ for PIC jump tables, compact unwind, and `.eh_frame` |
| `X86_64_RELOC_SIGNED_1` | `6` | `1` | `2` (4B) | RIP-relative memory + 1-byte trailing immediate (`movb $imm8, sym(%rip)`, `RIP_next = P + 5`): inline `i32` encodes $A - 1$; linker writes $S + A - (P + 5)$ |
| `X86_64_RELOC_SIGNED_2` | `7` | `1` | `2` (4B) | RIP-relative memory + 2-byte trailing immediate (`movw $imm16, sym(%rip)`, `RIP_next = P + 6`): inline `i32` encodes $A - 2$; linker writes $S + A - (P + 6)$ |
| `X86_64_RELOC_SIGNED_4` | `8` | `1` | `2` (4B) | RIP-relative memory + 4-byte trailing immediate (`movl $imm32, sym(%rip)`, `RIP_next = P + 8`): inline `i32` encodes $A - 4$; linker writes $S + A - (P + 8)$ |
| `X86_64_RELOC_TLV` | `9` | `1` | `2` (4B) | Darwin TLS descriptor access `movq sym@TLVP(%rip), %rdi` (`r_extern = 1`): resolves to local `__DATA,__thread_vars` descriptor VMA $S - (P + 4)$ (relaxing `8B` -> `8D` `leaq` when local) or GOT slot for imported TLV |

Any signed 32-bit displacement outside $[-2^{31}, 2^{31} - 1]$ fails deterministically with `AX_LINK_RELOC_OUT_OF_RANGE` (`E9013`). [0196 §9–10; 0217 §15–17, §46–47; tasks/0518 §151 AMACHINE-115, 117; tasks/0521 §156 AARM-59; SPEC-80 AXS-ELFS-026..027; SPEC-84 AXS-MACHO-017, AXS-MACHO-022; REQ-TGT-104, REQ-TGT-106, REQ-TGT-153]

**AXS-UNIV-006 — `x86_64-macos` 4 KiB Segment Alignment, Virtual Address Layout, 6-Byte `__stubs` & `LC_DYLD_CHAINED_FIXUPS` (`0196 §32–34`, `SPEC-84 AXS-MACHO-020..024`, `T690`).**
1. **4 KiB VM/segment alignment vs. 4 GiB `__PAGEZERO`:** Unlike `aarch64-macos` (`PAGE_SIZE = 0x4000` = 16 KiB), `x86_64-macos` aligns Mach-O segments (`__TEXT`, `__DATA_CONST`, `__DATA`, `__LINKEDIT`) to **`PAGE_SIZE = 0x1000` (4,096 bytes)** (`0196 §34`, `SPEC-88 AXS-XCMP-007`):
   - In `MH_EXECUTE`: `__PAGEZERO` still spans `vmaddr = 0x0`, `vmsize = 0x1_0000_0000` (`4 GiB`, `fileoff = 0`, `filesize = 0`, `maxprot = 0`, `initprot = 0`) to trap 32-bit pointer truncations, and `__TEXT` starts at `vmaddr = 0x1_0000_0000`, `fileoff = 0`.
   - In `MH_DYLIB`: `__PAGEZERO` and `LC_MAIN` are omitted and `__TEXT` starts at `vmaddr = 0x0`, `fileoff = 0` (`SPEC-89 AXS-ARTM-021`).
   - Strict `W^X` holds across all segments: `__TEXT` (`VM_PROT_READ | VM_PROT_EXECUTE = 5`), `__DATA_CONST` (`VM_PROT_READ | VM_PROT_WRITE = 3`, `SG_READ_ONLY = 0x10` post-`dyld`), `__DATA` (`VM_PROT_READ | VM_PROT_WRITE = 3`), and `__LINKEDIT` (`VM_PROT_READ = 1`).
2. **6-byte x86-64 `__TEXT,__stubs` trampolines:** For each imported dynamic function symbol `k`, `compiler/link/macho` emits a 6-byte indirect jump `jmpq *got_slot_k(%rip)` (`[0xFF, 0x25, disp32_le]`) in `__TEXT,__stubs` (`flags = S_SYMBOL_STUBS | S_ATTR_PURE_INSTRUCTIONS | S_ATTR_SOME_INSTRUCTIONS`, `reserved1 = indirect_symtab_start`, `reserved2 = 6`, `align = 1`) targeting the 8-byte pointer slot in `__DATA_CONST,__got`.
3. **4 KiB `LC_DYLD_CHAINED_FIXUPS (0x8000_0034)`:** Encodes `dyld_chained_starts_in_segment.page_size = 0x1000` (4,096 bytes) and `pointer_format = DYLD_CHAINED_PTR_64_OFFSET (6)` (4-byte chain stride, `DYLD_CHAINED_PTR_START_NONE = 0xFFFF`; the Mach-O reader accepts both `DYLD_CHAINED_PTR_64 = 2` and `DYLD_CHAINED_PTR_64_OFFSET = 6`). [0196 §16–22, §32–34; tasks/0563 §304.21–24; SPEC-84 AXS-MACHO-020..024; SPEC-89 AXS-ARTM-021..022]

**AXS-UNIV-007 — `x86_64-macos` Darwin TLS (`tlv_descriptor`), Compact Unwind (`UNWIND_X86_64_*`), Panic Trap (`UD2`) & `std.sys.macos` `$INODE64` ABI (`SPEC-84 AXS-MACHO-018, AXS-MACHO-027..031`).**
1. **Darwin x86-64 TLS (`__thread_vars`):** Uses the identical 24-byte `tlv_descriptor { thunk: extern "C" fn(*mut TlvDesc) -> *mut u8, key: usize, offset: usize }` layout (`__DATA,__thread_vars`, `__DATA,__thread_data`, `__DATA,__thread_bss`, `thunk = __tlv_bootstrap`; function-pointer type syntax per `SPEC-02 AXS-GRM-086`) as `SPEC-84 AXS-MACHO-018`. Accessing `@thread_local static X` executes `movq _X@TLVP(%rip), %rdi; callq *(%rdi)`, where Darwin's `_tlv_bootstrap` ABI preserves all registers except `%rdi` and `%rax` (and flags) and returns the thread's storage pointer in `%rax`.
2. **x86-64 Compact Unwind (`__TEXT,__unwind_info`):** Emits 32-bit compact unwind descriptors (`<mach-o/compact_unwind_encoding.h>`):
   - `UNWIND_X86_64_MODE_RBP_FRAME (0x0100_0000)` for `rbp`-framed functions (bits `[16..24)` = `rbp` frame offset / 8, bits `[0..15)` = up to five 3-bit saved register codes from `{RBX=1, R12=2, R13=3, R14=4, R15=5}`);
   - `UNWIND_X86_64_MODE_STACK_IMMD (0x0200_0000)` / `UNWIND_X86_64_MODE_STACK_IND (0x0300_0000)` for frameless stack-adjusting functions (`0x0000_0000` for zero-frame leaves);
   - `UNWIND_X86_64_MODE_DWARF (0x0400_0000)` indexing `__TEXT,__eh_frame` when frame size or LSDA cleanup requires DWARF CFI (`--panic unwind`).
3. **FFI no-unwind abort instruction:** Uncaught panics at `@export` `extern "C"` boundaries execute `UD2` (`[0x0F, 0x0B]`) after deterministic reverse-order local `Drop` cleanup (`SPEC-54 AXS-PAN-020`), contrasting with `BRK #0x1` on `aarch64-macos`.
4. **`std.sys.macos` & `libSystem.B.dylib` x86-64 `$INODE64` ABI delta (`SPEC-84 AXS-MACHO-027..031`, `SPEC-88 AXS-XCMP-025`):**
   - On `aarch64-macos`, `_stat`, `_fstat`, `_lstat`, and `_readdir` natively use 64-bit `ino_t`. On `x86_64-macos`, unsuffixed `_stat`/`_fstat`/`_lstat`/`_readdir` in `/usr/lib/libSystem.B.dylib` are legacy 32-bit inode entry points! Therefore, on `@cfg(target_arch = "x86_64")`, `std.sys.macos` and the built-in `compiler/link/sysroot` Darwin stub catalog bind the 64-bit inode symbols **`_stat$INODE64`**, **`_fstat$INODE64`**, **`_lstat$INODE64`**, and **`_readdir$INODE64`** (`144`-byte `struct stat64` and `1048`-byte `struct dirent` with `u64 d_ino` + `u64 d_seekoff`).
   - `std.sys.macos` stackful fiber context switching (`SPEC-34 AXS-EXEC-054`) branches cleanly via `@cfg(target_arch = "x86_64")` (saving/restoring only `RBX, RBP, R12..R15, RSP, RIP` in a `64`-byte `FiberContext` with no `XMM` or TEB state, matching `SPEC-80 AXS-ELFS-048`) vs. `@cfg(target_arch = "aarch64")` (saving/restoring `X19..X28, X29, X30, SP, D8..D15` in a `160`-byte `FiberContext` while never reading or writing `X18`, matching `SPEC-84 AXS-MACHO-030`). [0196 §27–29; 0220 §4, §7; SPEC-02 AXS-GRM-086; SPEC-34 AXS-EXEC-054; SPEC-54 AXS-PAN-020; SPEC-80 AXS-ELFS-048; SPEC-84 AXS-MACHO-018, AXS-MACHO-027..031; SPEC-88 AXS-XCMP-025]

**AXS-UNIV-008 — Unified Per-Slice SHA-256 Ad-Hoc `LC_CODE_SIGNATURE` Policy (`SPEC-84 AXS-MACHO-025`, `REQ-TGT-153`, `REQ-TOOL-001`, `T690`).**
By default, `compiler/link/macho` embeds a self-contained deterministic SHA-256 ad-hoc `LC_CODE_SIGNATURE (0x1D)` (`CS_SuperBlob` magic `0xFADE_0CC0` + 88-byte v`0x0002_0400` `CS_CodeDirectory` magic `0xFADE_0C02`, `flags = CS_ADHOC (0x0000_0002) | CS_LINKER_SIGNED (0x0002_0000)` = `0x0002_0002`, `hashSize = 32`, `hashType = CS_HASHTYPE_SHA256 = 2`, `pageSize = 12` -> 4,096-byte SHA-256 page slots over `[0 .. sig_offset)`, big-endian headers) at the end of `__LINKEDIT` in **both** `aarch64-macos` and `x86_64-macos` `MH_EXECUTE` and `MH_DYLIB` thin slices (`execSegFlags = CS_EXECSEG_MAIN_BINARY = 0x1` for `MH_EXECUTE`, `0x0` for `MH_DYLIB`). Signing both architectures uniformly guarantees `codesign --verify --deep --strict` compliance on macOS 11+ and Apple Silicon Rosetta 2 without Xcode tools (`--no-codesign` is honored only for explicit raw/test `x86_64-macos` thin builds and is rejected on `aarch64-macos` `MH_EXECUTE` where XNU kernel policy mandates ad-hoc signatures). [0097 §27; 0196 §23; tasks/0521 §156 AARM-59; tasks/0563 §304.25; SPEC-84 AXS-MACHO-025; SPEC-89 AXS-ARTM-022; REQ-TGT-153, REQ-TOOL-001]

**AXS-UNIV-009 — Mandatory Pre-Composition Thin-Slice Verification Gate (`REQ-TGT-307`, `SPEC-89 AXS-ARTM-030`).**
Every thin `MH_OBJECT`, `MH_EXECUTE`, `MH_DYLIB`, and `BsdAr` `.a`/`.axlib` slice produced for `x86_64-macos` or `aarch64-macos` MUST pass `verify_mc` (pre-encoding) and `verify_macho_image` / `verify_archive` (post-encoding, `SPEC-89 AXS-ARTM-030`) **before** entering `compiler/obj/macho_universal`, asserting valid `cputype`/`cpusubtype`, segment `W^X`, 4 KiB (`x86_64`) or 16 KiB (`arm64`) segment page alignment, zero residual `.axmeta`/`.axmir`/`.axlto` bytes in linked images, and valid SHA-256 `LC_CODE_SIGNATURE` page digests. [tasks/0524 §112 ABACKEND-82; tasks/0563 §304.33; SPEC-89 AXS-ARTM-030; REQ-TGT-307]

---

## 2. Mach-O Fat / Universal 2 Binary Format (`FAT_MAGIC` & `FAT_MAGIC_64`, `AXS-UNIV-010`..`018`)

**AXS-UNIV-010 — Big-Endian Outer `fat_header` (8 Bytes) vs. Little-Endian Inner Slices (`<mach-o/fat.h>`, `T690`).**
A Mach-O Universal 2 container begins at file offset `0` with an 8-byte **big-endian** `fat_header` (`u32be` network byte order), even though every `x86_64-macos` and `aarch64-macos` Mach-O 64 slice inside the container is **little-endian** (`MH_MAGIC_64 = 0xFEED_FACF`, wire bytes `[0xCF, 0xFA, 0xED, 0xFE]`):

| Byte Offset | Field | Wire Type | Allowed Value(s) & Wire Bytes |
|---|---|---|---|
| `+0..4` | `magic` | `u32be` | `FAT_MAGIC = 0xCAFE_BABE` (`[0xCA, 0xFE, 0xBA, 0xBE]`; LE `u32` view `FAT_CIGAM = 0xBEBA_FECA`) for 32-bit `fat_arch` descriptors, or `FAT_MAGIC_64 = 0xCAFE_BABF` (`[0xCA, 0xFE, 0xBA, 0xBF]`; LE `u32` view `FAT_CIGAM_64 = 0xBFBA_FECA`) for 64-bit `fat_arch_64` descriptors |
| `+4..8` | `nfat_arch` | `u32be` | Number of architecture slice descriptors immediately following byte `8` (`1 <= nfat_arch <= MAX_FAT_ARCHS`, where `MAX_FAT_ARCHS = 16`) |

**Java `.class` `0xCAFEBABE` disambiguation & 64-bit inner-slice magic check:** Because JVM `.class` files also start with `[0xCA, 0xFE, 0xBA, 0xBE]` followed by `(minor_version: u16be, major_version: u16be)` with `major_version >= 45` (so when `minor_version == 0`, the big-endian `u32` at `+4..8` is `>= 45`), `compiler/obj/macho_universal` first enforces `1 <= nfat_arch <= 16` and descriptor bounds (rejecting JVM `.class` files and corrupt outer headers deterministically with `AX_LINK_BAD_UNIVERSAL`, `E9008`) and then validates that every declared Universal 2 slice begins with 64-bit `MH_MAGIC_64 (0xFEED_FACF)` or `"!<arch>\n"` (rejecting legacy 32-bit `MH_MAGIC = 0xFEED_FACE` or non-Mach-O/non-`BsdAr` inner slice payloads with `AX_LINK_FAT_SLICE_KIND_MISMATCH`, `E9005`; `AXS-UNIV-018`..`019`). [tasks/0453 §194.29; tasks/0563 §304.31; tasks/0587 §30]

**AXS-UNIV-011 — 32-Bit `fat_arch` Slice Descriptor Table (`20` Bytes per Slice, `FAT_MAGIC = 0xCAFEBABE`).**
When `fat_header.magic == FAT_MAGIC (0xCAFE_BABE)`, bytes `[8 .. 8 + 20 * nfat_arch)` hold `nfat_arch` packed 20-byte **big-endian** `fat_arch` records:

| Relative Offset | Field | Wire Type | Semantics |
|---|---|---|---|
| `+0..4` | `cputype` | `u32be` | Mach `cpu_type_t` (`CPU_TYPE_X86_64 = 0x0100_0007`, `CPU_TYPE_ARM64 = 0x0100_000C`) |
| `+4..8` | `cpusubtype` | `u32be` | Mach `cpu_subtype_t` (`0x0000_0003` for `x86_64`, `0x0000_0000` for `arm64`, `0x8000_0002` for `arm64e`) |
| `+8..12` | `offset` | `u32be` | Unsigned 32-bit byte offset from byte `0` of the Fat container to byte `0` of this slice (`offset >= 8 + 20 * nfat_arch`) |
| `+12..16` | `size` | `u32be` | Exact unsigned 32-bit byte length of this slice (`size > 0`) |
| `+16..20` | `align` | `u32be` | Base-2 logarithm $a$ of slice alignment ($2^a$ bytes; `0 <= align <= 30`, `(offset & ((1u64 << align) - 1)) == 0`) |

[tasks/0453 §194.29; tasks/0587 §30, ATARGET-22]

**AXS-UNIV-012 — 64-Bit `fat_arch_64` Slice Descriptor Table (`32` Bytes per Slice, `FAT_MAGIC_64 = 0xCAFEBABF`).**
When `fat_header.magic == FAT_MAGIC_64 (0xCAFE_BABF)`, bytes `[8 .. 8 + 32 * nfat_arch)` hold `nfat_arch` packed 32-byte **big-endian** `fat_arch_64` records:

| Relative Offset | Field | Wire Type | Semantics |
|---|---|---|---|
| `+0..4` | `cputype` | `u32be` | Mach `cpu_type_t` |
| `+4..8` | `cpusubtype` | `u32be` | Mach `cpu_subtype_t` |
| `+8..16` | `offset` | `u64be` | Unsigned 64-bit byte offset from byte `0` of the Fat container to byte `0` of this slice (`offset >= 8 + 32 * nfat_arch`) |
| `+16..24` | `size` | `u64be` | Exact unsigned 64-bit byte length of this slice (`size > 0`) |
| `+24..28` | `align` | `u32be` | Base-2 logarithm $a$ of slice alignment (`0 <= align <= 30`, `(offset & ((1u64 << align) - 1)) == 0`) |
| `+28..32` | `reserved` | `u32be` | Reserved padding field; MUST be emitted as `0x0000_0000` and MUST equal `0` when validated (`AX_LINK_BAD_UNIVERSAL` if non-zero) |

[tasks/0453 §194.29; tasks/0587 §30, ATARGET-22]

**AXS-UNIV-013 — Mandatory Per-Architecture Slice Alignment (`2^12` = 4 KiB vs. `2^14` = 16 KiB, `REQ-TGT-104`, `T690`).**
Because XNU's Mach-O image loader `mmap`s each segment directly from file offset `slice.offset + segment.fileoff`, `slice.offset` MUST be aligned to at least the hardware/kernel virtual memory page size of that slice's architecture:
1. **Emission rules (`compiler/obj/macho_universal` writer):**
   - `CPU_TYPE_X86_64 (0x0100_0007)` slices (`x86_64-macos`): **`align = 12`** ($2^{12} = 4,096\text{ B} = \text{0x1000}$).
   - `CPU_TYPE_ARM64 (0x0100_000C)` slices (`aarch64-macos`): **`align = 14`** ($2^{14} = 16,384\text{ B} = \text{0x4000}$).
   `macho_universal` applies these exact alignment exponents (`12` for `x86_64`, `14` for `arm64`) uniformly across Universal executables (`MH_EXECUTE`), dynamic libraries (`MH_DYLIB`), and static/package archives (`BsdAr` `.a` / `.axlib`).
2. **Consumption & validation rules (`compiler/obj/macho_universal` reader / verifier):**
   - Every slice descriptor MUST satisfy `align <= 30` and `(offset & ((1u64 << align) - 1)) == 0`.
   - For `MH_EXECUTE` and `MH_DYLIB` slices, `align` MUST ALSO satisfy `align >= 12` (`offset % 4096 == 0`) on `CPU_TYPE_X86_64` and `align >= 14` (`offset % 16384 == 0`) on `CPU_TYPE_ARM64`.
   - For external `BsdAr` `.a` static archives created by third-party Apple `libtool -static` / `lipo` (which historically emit `align = 3` -> 8-byte alignment for non-`mmap`-executed archives), the reader accepts any `3 <= align <= 30` provided `(offset & ((1u64 << align) - 1)) == 0`.
   - Any violation of these alignment constraints fails deterministically with `AX_LINK_UNALIGNED_FAT_SLICE` (`E9007`). [0196 §34; tasks/0453 §194.29; tasks/0518 §151 AMACHINE-115; SPEC-84 AXS-MACHO-020; REQ-TGT-104]

**AXS-UNIV-014 — Deterministic Slice Ordering (`cputype`, `cpusubtype`) & Disjoint Architecture Invariant (`REQ-TGT-106`, `REQ-TGT-153`, `REQ-TGT-320`, `T690`).**
1. **Canonical ascending `(cputype, cpusubtype_masked)` sort:** Regardless of the order in which targets or thin slice files are supplied on the command line (e.g., `--universal-targets aarch64-apple-darwin,x86_64-apple-darwin` vs. `--universal-targets x86_64-macos,aarch64-macos`), `compiler/obj/macho_universal` sorts all slices in **strictly ascending unsigned `(cputype, cpusubtype & 0x00FF_FFFF)` order** prior to offset assignment:
   - Since `CPU_TYPE_X86_64 = 0x0100_0007 < CPU_TYPE_ARM64 = 0x0100_000C`, in every macOS Universal 2 artifact emitted by `axiomc`:
     - **Slice `0`** is `x86_64-macos` (`cputype = 0x0100_0007`, `cpusubtype = 0x0000_0003`, `align = 12`, placed at `offset = 0x1000 = 4,096`);
     - **Slice `1`** is `aarch64-macos` (`cputype = 0x0100_000C`, `cpusubtype = 0x0000_0000`, `align = 14`, placed at `offset = align_up(0x1000 + size_0, 0x4000)`).
2. **Disjoint architecture slice invariant:** Two slices in the same Universal container MUST NOT share identical `(cputype, cpusubtype & 0x00FF_FFFF)`. Duplicate architecture slices (including passing alias pairs such as `x86_64-macos,x86_64-apple-darwin` or two `arm64` thin inputs) are rejected deterministically with `AX_LINK_DUPLICATE_FAT_ARCH` (`E9003`), whereas distinct subtypes of one `cputype` (such as `CPU_SUBTYPE_ARM64_ALL = 0` alongside `CPU_SUBTYPE_ARM64E = 2`) are permitted and ordered deterministically (`0` before `2`). [tasks/0453 §194.29, §194.42; tasks/0518 §151 AMACHINE-117; tasks/0521 §156 AARM-59; tasks/0524 §112 ABACKEND-95; tasks/0587 §30, ATARGET-22, ATARGET-30; REQ-TGT-106, REQ-TGT-153, REQ-TGT-320]

**AXS-UNIV-015 — Monotonic Non-Overlapping Slice Placement & Deterministic Zero-Byte Gap Padding (`REQ-TGT-106`, `REQ-TGT-153`, `REQ-TGT-320`, `T690`).**
Given $N = \text{nfat\_arch}$ sorted slices $[s_0, \dots, s_{N-1}]$ and descriptor byte size $E \in \{20, 32\}$ (`hdr_end = 8 + N * E`):
1. Set `cursor: u64 = hdr_end`.
2. For $i = 0 \dots N - 1$:
   - Compute $A_i = 1\text{u64} \ll s_i.\text{align}$ and $s_i.\text{offset} = ((\text{cursor} + A_i - 1) \mathbin{\&} \sim(A_i - 1))$.
   - Emit exact $(s_i.\text{offset} - \text{cursor})$ zero bytes (`0x00`) in the inter-slice / post-header gap $[\text{cursor} \dots s_i.\text{offset})$ — never uninitialized heap or arena bytes!
   - Emit the exact $s_i.\text{size}$ bytes of $s_i$ verbatim at $[s_i.\text{offset} \dots s_i.\text{offset} + s_i.\text{size})$.
   - Advance `cursor = s_i.offset + s_i.size`.
3. The final Universal file length equals exact $s_{N-1}.\text{offset} + s_{N-1}.\text{size}$ with zero trailing unreferenced bytes. When reading external Fat containers created by third-party tools, slices are validated to satisfy `offset >= hdr_end`, non-overlapping byte intervals, and `offset + size <= file_len` without `u64` overflow (`AX_LINK_BAD_UNIVERSAL`). [tasks/0518 §151 AMACHINE-117; tasks/0521 §156 AARM-59; tasks/0524 §112 ABACKEND-95; tasks/0563 §304.5, §304.37; REQ-TGT-106, REQ-TGT-153, REQ-TGT-320]

**AXS-UNIV-016 — Automatic Deterministic Promotion from `FAT_MAGIC` to `FAT_MAGIC_64` at $\ge 4\text{ GiB}$ (`REQ-TGT-106`, `REQ-TGT-153`, `T690`).**
1. **Default 32-bit `FAT_MAGIC` first:** Unless `--fat64` is explicitly requested, `compiler/obj/macho_universal` computes the candidate layout of `AXS-UNIV-015` with $E = 20$ (`FAT_MAGIC = 0xCAFE_BABE`). If every slice $i \in [0, N)$ satisfies **both** `offset_i <= 0xFFFF_FFFF` and `size_i <= 0xFFFF_FFFF`, `macho_universal` emits `FAT_MAGIC` (`0xCAFE_BABE`) with 20-byte `fat_arch` descriptors.
2. **Automatic `FAT_MAGIC_64` promotion:** If **any** slice has `offset_i > 0xFFFF_FFFF` ($\ge 2^{32}$) **or** `size_i > 0xFFFF_FFFF` ($\ge 2^{32}$), or if `--fat64` is passed, `macho_universal` promotes the container to `FAT_MAGIC_64 (0xCAFE_BABF)`, **recomputes `hdr_end = 8 + 32 * N` and all slice offsets $s_i.\text{offset}$** from scratch under $E = 32$, and emits 32-byte `fat_arch_64` descriptors (`reserved = 0`).
3. **Explicit `--fat32` overflow check:** If `--fat32` is explicitly passed while any slice requires `offset_i > 0xFFFF_FFFF` or `size_i > 0xFFFF_FFFF`, composition never truncates 64-bit values into `u32be`; it fails deterministically with `AX_LINK_IMAGE_TOO_LARGE` (`E9009`). [tasks/0518 §151 AMACHINE-117; tasks/0521 §156 AARM-59; tasks/0563 §304.30–33; REQ-TGT-106, REQ-TGT-153]

**AXS-UNIV-017 — Endian-Explicit Wire Encoding & Zero Host Struct Casting (`REQ-TGT-106`, `REQ-TGT-153`, `tasks/0563 §304.31–32`).**
`compiler/obj/macho_universal` reads and writes every `fat_header`, `fat_arch`, and `fat_arch_64` field through explicit big-endian byte primitives (`read_u32_be`, `read_u64_be`, `write_u32_be`, `write_u64_be`) while reading inner Mach-O 64 headers via explicit little-endian primitives (`read_u32_le`, `read_u64_le`). Host pointer-cast struct serialization is strictly forbidden (`tasks/0563 §304.32 AIMG-32..34`). [tasks/0518 §151 AMACHINE-117; tasks/0521 §156 AARM-59; tasks/0563 §304.31–32 AIMG-32..34; REQ-TGT-106, REQ-TGT-153]

**AXS-UNIV-018 — Universal Container Structural Verifier (`verify_universal_artifact`, `REQ-TGT-307`, `T690`).**
`compiler/obj/macho_universal` runs `verify_universal_artifact` both immediately after composing any Universal 2 output (internal failure -> `AX_ICE_INTERNAL` with `data.stage = "universal_verify"`) and when opening any external Fat input (external failure -> `AX_LINK_BAD_UNIVERSAL`, `AX_LINK_UNALIGNED_FAT_SLICE`, `AX_LINK_DUPLICATE_FAT_ARCH`, `AX_LINK_FAT_SLICE_KIND_MISMATCH`, or `AX_LINK_BAD_CODESIGN`):
1. `magic` is `0xCAFE_BABE` or `0xCAFE_BABF`, `1 <= nfat_arch <= 16`, and `8 + nfat_arch * E <= file_len`.
2. Every descriptor has `size > 0`, `align <= 30`, `(offset & ((1u64 << align) - 1)) == 0`, `offset >= hdr_end`, checked `offset + size <= file_len` with zero `u64` overflow, and (for `FAT_MAGIC_64`) `reserved == 0`.
3. Descriptor byte ranges `[offset_i .. offset_i + size_i)` are pairwise disjoint (and for compiler-emitted Universal binaries, strictly sorted by ascending `(cputype, cpusubtype & 0x00FF_FFFF)` with all gap bytes equal to `0x00`).
4. `(cputype, cpusubtype & 0x00FF_FFFF)` pairs are pairwise distinct (`AXS-UNIV-014`).
5. Each slice's inner payload magic (`MH_MAGIC_64` or `"!<arch>\n"`), inner `cputype`/`cpusubtype` (including every `MH_OBJECT` member inside a `BsdAr` slice), slice alignment floor (`AXS-UNIV-013`), homogeneous payload kind (`AXS-UNIV-019`), and embedded `LC_CODE_SIGNATURE` SHA-256 page hashes (`AXS-UNIV-020`) are structurally valid. [tasks/0524 §112 ABACKEND-82; tasks/0563 §304.33–34; SPEC-89 AXS-ARTM-030; REQ-TGT-307]

---

## 3. Universal Executables, `.dylib`s, Static Archives (`BsdAr`), Code Signing & Linker Consumption (`AXS-UNIV-019`..`025`)

**AXS-UNIV-019 — Homogeneous Slice Kind & `.dylib` Install-Name / Version Coherence (`REQ-TGT-104`, `REQ-TGT-200`, `T690`, `T692`).**
1. **Homogeneous payload kind invariant:** Every slice inside a Mach-O Universal 2 container MUST belong to the **identical artifact category**:
   - **Universal Executable (`--kind exe|bin`):** Every slice is a 64-bit Mach-O `MH_EXECUTE (0x2)` image.
   - **Universal Dynamic Library (`--kind dll|cdylib`):** Every slice is a 64-bit Mach-O `MH_DYLIB (0x6)` image. Furthermore, all slices in a Universal `.dylib` MUST record identical `LC_ID_DYLIB` `install_name`, `current_version`, and `compatibility_version` values (`SPEC-89 AXS-ARTM-021`; disagreement across composed `.dylib` slices fails with `AX_LINK_INVALID_DYLIB_VERSION`, `E9006`).
   - **Universal Static Archive (`--kind lib|staticlib`):** Every slice is a self-contained deterministic `BsdAr` (`"!<arch>\n"`) archive containing `MH_OBJECT (0x1)` members matching that slice's `cputype` (zero `lib.axrmeta` member).
   - **Universal Axiom Package Library (`--kind axlib`):** Every slice is a self-contained deterministic `BsdAr` (`"!<arch>\n"`) archive whose first regular member after `__.SYMDEF SORTED` is that slice's target-parameterized `lib.axrmeta` (`magic = "AXMI0001"`, embedding `TargetFingerprint` `(TargetId, TargetFeatureSet, CallConv, CodegenFingerprint)` for `t_i`; `SPEC-24 AXS-ART-023`, `SPEC-89 AXS-ARTM-013`, `REQ-TGT-200`) followed by `t_i`'s `MH_OBJECT` CGU members.
2. **Forbidden heterogeneous, 32-bit, or non-Darwin payloads:** Mixing `MH_EXECUTE` with `MH_DYLIB`, mixing Mach-O images with `BsdAr` archives, mixing `staticlib` with `axlib`, or placing legacy 32-bit `MH_MAGIC (0xFEED_FACE)`, raw `MH_OBJECT` (unless explicitly invoking `--compose-universal` on homogeneous `.o` inputs), ELF, COFF, or WASM bytes inside a Universal container is rejected deterministically with `AX_LINK_FAT_SLICE_KIND_MISMATCH` (`E9005`). Standalone `--kind obj` (`--emit=obj`) and standalone `.axmi` outputs remain single-target (`AXS-UNIV-026`). [tasks/0518 §151 AMACHINE-115; tasks/0522 §159 ABACKEND-54; tasks/0587 §30–32, ATARGET-22; SPEC-24 AXS-ART-022..023; SPEC-89 AXS-ARTM-003..005, AXS-ARTM-013, AXS-ARTM-021; REQ-TGT-104, REQ-TGT-200]

**AXS-UNIV-020 — Per-Slice `LC_UUID` & `LC_CODE_SIGNATURE` Embedding Before Fat Composition (`0196 §23–24`, `SPEC-84 AXS-MACHO-021, AXS-MACHO-025..026`, `REQ-TGT-106`, `REQ-TGT-153`, `T690`, `T692`).**
Apple's Universal 2 security model signs **each thin Mach-O slice independently**, never the outer `fat_header` or inter-slice zero padding:
1. **Distinct deterministic per-slice `LC_UUID`:** Each thin `MH_EXECUTE` / `MH_DYLIB` slice computes its 24-byte `LC_UUID (0x1B)` payload as the exact first 16 bytes of `BLAKE3("axiom-macho-uuid-v1" || image_bytes_with_zeroed_uuid_and_codesig)` (with no RFC 4122 v5 bit clamping and never wall-clock or random; `SPEC-84 AXS-MACHO-021`), ensuring thin Mach-O builds and extracted Universal slices produce identical `LC_UUID` bytes while `x86_64-macos` and `aarch64-macos` slices carry distinct, reproducible UUIDs (since `mach_header_64.cputype`/`cpusubtype` and target machine code reside inside `image_bytes_with_zeroed_uuid_and_codesig`) for `lldb` / crash-report symbolication.
2. **Slice-local `LC_CODE_SIGNATURE` hashing:** Each thin `MH_EXECUTE` / `MH_DYLIB` slice computes and appends its `CS_SuperBlob` + SHA-256 `CS_CodeDirectory` over slice-relative byte offsets `[0 .. slice_sig_offset)` (`SPEC-84 AXS-MACHO-025`, `AXS-UNIV-008`) **prior** to Universal composition.
3. **Byte-verbatim slice embedding & round-trip extraction identity:** `compiler/obj/macho_universal` copies each signed thin slice into `[slice.offset .. slice.offset + slice.size)` without mutating a single byte inside the slice. Consequently, extracting slice $A$ via `--extract-slice <arch>` (`AXS-UNIV-028`) yields a standalone thin Mach-O binary **byte-for-byte identical** to building `--target <triple_A>` directly, with its `LC_CODE_SIGNATURE` immediately valid without re-signing. Any corrupted SHA-256 page hash inside a slice fails `verify_universal_artifact` / `--verify-arch` with `AX_LINK_BAD_CODESIGN` (`E9010`). [0196 §23–24; tasks/0518 §151 AMACHINE-117; tasks/0521 §156 AARM-59; tasks/0563 §304.25, §304.37–38; SPEC-84 AXS-MACHO-021, AXS-MACHO-025..026; REQ-TGT-106, REQ-TGT-153]

**AXS-UNIV-021 — Universal Static Archive (`lib<stem>.a` & `lib<stem>.axlib`) Wire Layout (`SPEC-89 AXS-ARTM-009, 012..013`, `REQ-TGT-104`, `REQ-TGT-106`, `REQ-TGT-153`, `T690`).**
A macOS universal static library is **never** a single `!<arch>\n` archive mixing `x86_64` and `arm64` `.o` members (because BSD `__.SYMDEF SORTED` indexes symbol names without `cputype` keys). Instead, `compiler/obj/macho_universal` emits an outer `FAT_MAGIC` / `FAT_MAGIC_64` container whose slices are complete per-architecture deterministic `BsdAr` (`"!<arch>\n"`) archives (`SPEC-89 AXS-ARTM-008..013`):
```text
+0x0000 .. +0x0008  fat_header  { magic = 0xCAFEBABE, nfat_arch = 2 }                     (u32be)
+0x0008 .. +0x001C  fat_arch[0] { X86_64, sub=3, offset=0x1000, size=S0, align=12 }       (u32be)
+0x001C .. +0x0030  fat_arch[1] { ARM64,  sub=0, offset=off1,   size=S1, align=14 }       (u32be)
+0x0030 .. +0x1000  0x00 zero-byte padding (4,048 bytes)
+0x1000 .. +0x1000+S0  Thin x86_64 BsdAr:
                       "!<arch>\n"
                       + 60B hdr "#1/20           " + "__.SYMDEF SORTED\0\0\0\0" + ranlib[] (slice-local ran_off!)
                       [+ optional lib.axrmeta for --kind axlib]
                       + #1/<len> 8B-aligned x86_64 MH_OBJECT members
+0x1000+S0 .. +off1    0x00 zero-byte padding to 16 KiB boundary (off1 = align_up(0x1000 + S0, 0x4000))
+off1   .. +off1+S1    Thin arm64 BsdAr:
                       "!<arch>\n"
                       + 60B hdr "#1/20           " + "__.SYMDEF SORTED\0\0\0\0" + ranlib[] (slice-local ran_off!)
                       [+ optional lib.axrmeta for --kind axlib]
                       + #1/<len> 8B-aligned arm64 MH_OBJECT members
```
Every `ran_off` inside each slice's `__.SYMDEF SORTED` (or `__.SYMDEF_64` when $S_i \ge 4\text{ GiB}$, `SPEC-89 AXS-ARTM-012`) is strictly **slice-relative** (measured from byte `0` of that slice's `"!<arch>\n"` magic, never from byte `0` of the outer Fat file), so extracting any slice yields a directly linkable thin BSD `.a` / `.axlib` archive. [0196; 0217 §19, §44; tasks/0518 §151 AMACHINE-115, 117; tasks/0521 §156 AARM-59; SPEC-84 AXS-MACHO-019; SPEC-89 AXS-ARTM-008..013; REQ-TGT-104, REQ-TGT-106, REQ-TGT-153]

**AXS-UNIV-022 — Linker & Frontend Consumption of Universal `.a`, `.axlib`, `.dylib` & `.tbd` Dependencies (`compiler/link/macho`, `compiler/link/archive_resolve`, `REQ-TGT-154`, `REQ-TGT-200`, `REQ-TGT-319`).**
When compiling or linking an active Darwin target slice $T \in \{\text{`x86\_64-macos`}, \text{`aarch64-macos`}\}$ (whether in a thin `--target` build or inside one leg of `--universal-targets`):
1. **Universal `.a` & `.axlib` resolution:** `compiler/link/archive_resolve` (`SPEC-89 AXS-ARTM-025`) and `compiler/artifact/axmi` detect `FAT_MAGIC` / `FAT_MAGIC_64`, validate the Fat header (`AXS-UNIV-018`), select the slice matching $T$'s `cputype` (preferring exact `cpusubtype` match and falling back to `CPU_SUBTYPE_X86_64_ALL = 3` / `CPU_SUBTYPE_ARM64_ALL = 0`), project a bounded byte view `[slice.offset .. slice.offset + slice.size)`, verify that slice's `lib.axrmeta` `TargetFingerprint` (`TargetId`, `TargetFeatureSet`, `AbiFingerprint`, `CodegenFingerprint`), and run standard `BsdAr` demand-driven `__.SYMDEF SORTED` member extraction (`--whole-archive` / `-force_load` honored per `SPEC-89 AXS-ARTM-026`) within that slice view.
2. **Universal `.dylib` & multi-arch `.tbd` resolution:** `compiler/link/macho` / `dynlib_matrix` selects the matching `MH_DYLIB` slice from any Fat `.dylib` (or filters the `targets:` / `archs:` list of Apple `.tbd` v3/v4 text stubs to active target $T$, `SPEC-84 AXS-MACHO-028`) to read `LC_ID_DYLIB` and exported symbols.
3. **Missing architecture slice diagnostic (`E9012`):** If a consumed Fat `.a`, `.axlib`, or `.dylib` (or `.tbd` stub) is structurally valid but lacks a slice matching active target $T$ (for example, linking an `aarch64-macos`-only `libfoo.a` into `--universal-targets x86_64-macos,aarch64-macos`), compilation fails deterministically on leg $T$ with `AX_LINK_ARTIFACT_TARGET_MISMATCH` (`data.expected_target = "x86_64-macos"`, `data.available_slices = ["aarch64-macos"]`; `tasks/0587 §36`). [tasks/0521 §156 AARM-60; tasks/0522 §159 ABACKEND-54; tasks/0524 §112 ABACKEND-94; tasks/0587 §32, §36; SPEC-84 AXS-MACHO-019, AXS-MACHO-028; SPEC-88 AXS-XCMP-009; SPEC-89 AXS-ARTM-022, AXS-ARTM-025..026; REQ-TGT-154, REQ-TGT-200, REQ-TGT-319]

**AXS-UNIV-023 — Multi-Target Package Bundles (`.axpkg`, `"AXPKG001"`) for Cross-OS Distribution (`REQ-TGT-001`, `SPEC-24 AXS-ART-024`, `tasks/0587 §31`).**
For distributing prebuilt multi-target packages across incompatible OS or object ecosystems (such as `x86_64-windows`, `aarch64-windows`, `x86_64-linux`, `aarch64-linux`, `riscv64-linux`, `aarch64-macos`, `x86_64-macos`, and `wasm32-wasi`), Axiom uses the `.axpkg` package container (`magic = "AXPKG001"`, `format_family = 6`, 64-byte `ArtifactHeader` with `target_fingerprint = 0` at outer bundle level; `SPEC-24 AXS-ART-002, AXS-ART-024`):
- Its manifest section maps canonical target triples (e.g., `"x86_64-windows"`, `"x86_64-linux"`, `"aarch64-linux"`, `"wasm32-wasi"`, plus `"universal-macos"` or thin `"aarch64-macos"` / `"x86_64-macos"`) to embedded per-target `.axlib`, static/dynamic library, or executable payloads, each carrying its own 128-bit `TargetFingerprint` and BLAKE3-128 `content_hash` (`ATARGET-22`).
- Attempting to pass non-Mach-O or cross-OS targets (`x86_64-linux,aarch64-linux` or `x86_64-windows,aarch64-macos`) to `--universal-targets` (which constructs a single OS-loader Mach-O Universal 2 file) fails deterministically with `AX_DRIVER_UNIVERSAL_TARGET_INCOMPATIBLE` (`E9002`) with a help note directing the user to per-target `--target` builds or `.axpkg` packaging. [tasks/0587 §31–32, ATARGET-22; SPEC-24 AXS-ART-002, AXS-ART-024; REQ-TGT-001]

**AXS-UNIV-024 — Architectural Layering & Crash-Safe Atomic Universal Output (`INV-LAYER-002`, `SPEC-89 AXS-ARTM-030`).**
1. **Strict `objmodel` layering (`INV-LAYER-002`):** `compiler/obj/macho_universal` resides strictly in the `objmodel` architectural layer (`SPEC-04 AXS-EXT-074`) and depends **only** on `kernel`, `diag`, `source`, `artifact/container`, and `objmodel`. It MUST NOT import `syntax`, `hir`, `sema`, `mir`, `opt`, or `driver`.
2. **Crash-safe atomic write (`AIMG-50`):** Every Universal 2 artifact is serialized to `<out>.tmp.<pid>`, verified via `verify_universal_artifact` (`AXS-UNIV-018`), and atomically renamed to `<out>`; failed builds never leave partial or stale output files on disk. [tasks/0563 §304.36, §304.45 AIMG-50; SPEC-04 AXS-EXT-074; SPEC-89 AXS-ARTM-030, AXS-ARTM-039; INV-LAYER-002]

**AXS-UNIV-025 — Cross-Host Byte-for-Byte Universal Determinism & Cross-Slice Behavioral Equivalence (`REQ-TGT-106`, `REQ-TGT-153`, `REQ-TGT-199`, `REQ-TGT-318`, `REQ-TGT-320`, `T690`, `T692`).**
1. **Cross-host bit-for-bit binary determinism (`AMACHINE-117`, `AARM-59`, `ABACKEND-95`, `REQ-TGT-106`, `REQ-TGT-153`, `REQ-TGT-320`):** Building a Universal 2 executable, `.dylib`, `.a`, or `.axlib` in reproducible mode from identical `.ax` sources, `axiom.toml`, CLI flags, and hermetic sysroot on a `Windows` host, a `Linux` host, or a `macOS` host — and regardless of whether `--universal-targets` lists `x86_64-macos,aarch64-macos` or `aarch64-apple-darwin,x86_64-apple-darwin` or runs with `--jobs 1` vs. `--jobs N` — MUST produce **100% bit-for-bit identical** output bytes.
2. **Cross-slice observable behavioral equivalence (`ABACKEND-53`, `AARM-63`, `ABACKEND-93`, `REQ-TGT-199`, `REQ-TGT-318`):** For any target-independent Axiom program, executing the `x86_64-macos` slice, executing the `aarch64-macos` slice, and evaluating under `--interp` MUST produce equivalent observable behavior (stdout/stderr output, exit status, file/memory side effects, and deterministic `Drop`/panic behavior). [tasks/0453 §194.42; tasks/0518 §151 AMACHINE-117; tasks/0521 §156 AARM-59, AARM-63; tasks/0522 §159 ABACKEND-53, ABACKEND-55; tasks/0524 §112 ABACKEND-93, ABACKEND-95; tasks/0563 §304.37; SPEC-23; SPEC-88 AXS-XCMP-008; REQ-TGT-106, REQ-TGT-153, REQ-TGT-199, REQ-TGT-318, REQ-TGT-320]

---

## 4. Driver Multi-Arch Pipeline & Native `lipo`-Free Slice Inspection/Extraction Tooling (`T691`, `AXS-UNIV-026`..`031`)

**AXS-UNIV-026 — `--universal-targets` CLI Flag, `axiom.toml` Schema & Option Validation (`REQ-TGT-001`, `REQ-TGT-105`, `T691`).**
`compiler/driver/universal` (`T691`) extends `axiomc build` with explicit multi-architecture Universal composition:
1. **CLI & manifest syntax:**
   - CLI: `axiomc build --universal-targets <t1>,<t2>[,...]` (also accepting `--universal-targets=<t1>,<t2>[,...]`).
   - Manifest (`axiom.toml`): optional `universal_targets = ["x86_64-macos", "aarch64-macos"]` under `[build]` (overridden by CLI `--universal-targets` or single-target `--target`).
2. **Validation rules (exit code `2` on CLI usage/flag errors):**
   - **Target normalization & `TargetSpec` resolution (`AMACHINE-116`, `REQ-TGT-105`):** Each comma-separated token `<t_k>` is resolved through `SPEC-88 AXS-XCMP-002` into an explicit `TargetSpec` / `TargetDesc` (`"x86_64-apple-darwin"` -> `TargetId.X86_64Macos`, `"aarch64-apple-darwin"` / `"arm64-apple-darwin"` -> `TargetId.AArch64Macos`); any unknown triple emits `AX_DRIVER_UNKNOWN_TARGET` (`E9000`).
   - **Arity & mutual exclusion:** An empty `--universal-targets` string, an empty comma element (`"x86_64-macos,"`), fewer than `2` targets (`--universal-targets x86_64-macos`; hint: use `--target x86_64-macos`), or passing both `--target` and `--universal-targets` on the same CLI invocation fails with `AX_DRIVER_INVALID_UNIVERSAL_TARGETS` (`E9001`).
   - **Darwin Mach-O homogeneity:** Passing any non-Mach-O target (`x86_64-windows`, `x86_64-linux`, `aarch64-linux`, `aarch64-android`, `riscv64-linux`, `wasm32-*`, `<arch>-uefi`, `<arch>-none`) in `--universal-targets` fails with `AX_DRIVER_UNIVERSAL_TARGET_INCOMPATIBLE` (`E9002`).
   - **Disjoint normalized slices:** Two tokens normalizing to the identical `(cputype, cpusubtype & 0x00FF_FFFF)` (such as `--universal-targets x86_64-macos,x86_64-apple-darwin`) fail immediately before compilation with `AX_LINK_DUPLICATE_FAT_ARCH` (`E9003`).
   - **Supported `--kind` set:** `--universal-targets` supports `--kind exe|bin` (default), `--kind dll|cdylib`, `--kind lib|staticlib`, and `--kind axlib`. Combining `--universal-targets` with `--kind obj` (`--emit=obj`) or `wasm-module`/`wasm-reactor` fails with `AX_DRIVER_INVALID_ARTIFACT_KIND` (`E9004`), and passing `--universal-targets` to `axiomc run` fails with `AX_DRIVER_USAGE` (`AXS-UNIV-031`). [tasks/0453 §194.29–30; tasks/0518 §151 AMACHINE-116; tasks/0587 §30, §38; SPEC-88 AXS-XCMP-002; SPEC-89 AXS-ARTM-002, AXS-ARTM-031; REQ-TGT-001, REQ-TGT-105]

**AXS-UNIV-027 — Multi-Slice Build Orchestration & Three-Tier `CompilerDB` Cache Isolation (`compiler/driver/universal`, `REQ-TGT-154`, `REQ-TGT-200`, `REQ-TGT-319`, `T691`).**
For normalized target slice list $S = [t_0, \dots, t_{k-1}]$ (canonically ordered `[TargetId.X86_64Macos, TargetId.AArch64Macos]` per `AXS-UNIV-014`), `compiler/driver/universal` executes a four-stage pipeline:
1. **Stage 1 — Shared Tier-A Frontend Ingestion (once per invocation):** Source file reading, UTF-8 & CRLF-to-LF normalization (`SPEC-01`), lexing, full S0/S1 AST parsing across all `@cfg` branches (`SPEC-88 AXS-XCMP-011`), and `axiom.toml` resolution run **once** and populate `CompilerDB` Tier A (`TargetIndependent`, `SPEC-88 AXS-XCMP-005`).
2. **Stage 2 — Per-Slice Isolated Tier-B & Tier-C Compilation (`REQ-TGT-154`, `REQ-TGT-200`, `REQ-TGT-319`):**
   For each target $t_i \in S$ (scheduled concurrently across `DatabaseSnapshot` workers under `--jobs N` or sequentially under `--jobs 1`, `SPEC-23`):
   - Evaluates `@cfg(...)` predicates strictly against $t_i$ (`target_arch = "x86_64"` + `target_abi = "sysv64"` on leg `0` vs. `target_arch = "aarch64"` + `target_abi = "apple_arm64"` on leg `1`), runs name resolution, typechecking, ownership/capability/concurrency verification, $t_i$-parameterized `const`/`comptime` (`MIN_PAGE_SIZE_BYTES = 4096` vs. `16384`), `Verified MIR`, `OptIR`, LTO (when `--lto=thin|full` is enabled, scoped strictly within leg $t_i$), `Axiom LIR` ABI lowering, $t_i$ instruction selection, register allocation, `verify_mc`, Mach-O `MH_OBJECT` emission, Mach-O linking (`MH_EXECUTE` / `MH_DYLIB`) or `BsdAr` packaging (`.a` / `.axlib`), per-slice SHA-256 ad-hoc `LC_CODE_SIGNATURE` signing (`AXS-UNIV-008`), and `verify_macho_image` / `verify_archive` (`AXS-UNIV-009`).
   - All Tier-B (`CfgEnvFingerprint` + `DataLayoutFingerprint`) and Tier-C (`TargetFingerprint` = `BLAKE3(TargetId, TargetFeatureSet, CallConv / AbiFingerprint, OptProfile, CodegenFingerprint)` + `SysrootFingerprint`; `AARM-60`, `ABACKEND-54`, `ABACKEND-94`) cache entries and intermediate thin staging files are partitioned under `target/<canonical-triple>/<profile>/` (`target/x86_64-macos/<profile>/` and `target/aarch64-macos/<profile>/`), guaranteeing **zero** cross-slice semantic or machine-code cache pollution (`ATARGET-06..09, 39..40`, `REQ-TGT-154`, `REQ-TGT-200`, `REQ-TGT-319`).
3. **Stage 3 — Deterministic Diagnostic Join & Failure Barrier:** Diagnostics emitted during leg $t_i$ attach `data.target = "<canonical-triple>"` and merge in canonical `(slice_index, AXD-060)` order (`SPEC-23 AXS-PAR-023`). If any leg emits an error, Stage 4 is skipped and `axiomc` exits `1`.
4. **Stage 4 — Universal 2 Composition & Output Placement:** `compiler/driver/universal` invokes `compiler/obj/macho_universal` (`AXS-UNIV-010`..`021`) over the verified thin slices and writes `-o <path>` or default `target/universal-macos/<profile>/<artifact_name>` (`<pkg>` for `exe`, `lib<pkg>.dylib` for `cdylib`/`dll`, `lib<pkg>.a` for `staticlib`/`lib`, `lib<pkg>.axlib` for `axlib`). [tasks/0453 §194.29–32, ATARGET-39..40; tasks/0521 §156 AARM-60; tasks/0522 §159 ABACKEND-54; tasks/0524 §112 ABACKEND-94; tasks/0587 §5–8, §33, §35, ATARGET-06..09, ATARGET-26; SPEC-21; SPEC-22; SPEC-23; SPEC-88 AXS-XCMP-005, AXS-XCMP-009; REQ-TGT-154, REQ-TGT-200, REQ-TGT-319]

**AXS-UNIV-028 — Native `lipo`-Free Slice Inspection, Extraction & Verification CLI (`compiler/driver/emit_universal`, `REQ-TOOL-001`, `T689`, `T691`).**
To enable CI, release verification, and developer debugging on Windows, Linux, and macOS hosts with **zero** dependency on Xcode Command Line Tools (`lipo`, `otool`, `codesign`, `file`; `REQ-TOOL-001`), `compiler/driver/emit_universal` (`T691`) implements three native binary slice operations exposed through `axiomc inspect` (with top-level `axiomc obj inspect` / driver flag aliases):

| Operation | Canonical CLI Invocations & Accepted Aliases | Behavior |
|---|---|---|
| **Inspect Slices** | `axiomc inspect --inspect-slices [--json] <file>`<br>`axiomc inspect --emit=slices [--json] <file>`<br>`axiomc inspect --slices [--json] <file>`<br>`axiomc obj inspect --slices [--json] <file>` | Parses `<file>` (accepting Universal 2 `FAT_MAGIC`/`FAT_MAGIC_64` containers as well as thin Mach-O `MH_EXECUTE`/`MH_DYLIB`/`MH_OBJECT` and thin `BsdAr` `.a`/`.axlib` files), runs structural validation (`AXS-UNIV-018`), and prints the deterministic slice table (`AXS-UNIV-029`). |
| **Extract Slice** | `axiomc inspect --extract-slice <arch> <fat_file> -o <out_file>`<br>`axiomc obj --extract-slice <arch> <fat_file> -o <out_file>` | Validates `<fat_file>` as a Universal 2 container, resolves `<arch>` (`"x86_64"` / `"x86_64-macos"` / `"x86_64-apple-darwin"`, `"arm64"` / `"aarch64"` / `"aarch64-macos"` / `"aarch64-apple-darwin"`, or `"arm64e"`), verifies the target slice, and atomically writes exact raw bytes `[offset .. offset + size)` to `<out_file>` preserving embedded `LC_CODE_SIGNATURE` (`AXS-UNIV-020`). Missing `-o` emits `AX_DRIVER_USAGE`; missing `<arch>` slice emits `AX_LINK_FAT_ARCH_NOT_FOUND` (`E9011`). |
| **Verify Arch** | `axiomc inspect --verify-arch <arch1>[,<arch2>...] [--json] <file>`<br>`axiomc obj --verify-arch <arch1>[,<arch2>...] [--json] <file>` | Validates `<file>` (Universal or thin), verifies per-slice SHA-256 `LC_CODE_SIGNATURE` page digests when present (`AX_LINK_BAD_CODESIGN` on mismatch), and checks that **every** requested `<arch_k>` exists in `<file>` (exiting `0` on full match; emitting `AX_LINK_FAT_ARCH_NOT_FOUND`, `E9011`, and exiting `1` if any `<arch_k>` is absent). |

Passing an unrecognized `<arch>` string (outside `{x86_64, x86_64h, arm64, aarch64, arm64e}` and their canonical Darwin triples) emits `AX_DRIVER_UNKNOWN_TARGET` (`E9000`, exit code `2`). [0097 §27; tasks/0453 §194.43; tasks/0563 §304.34; REQ-TOOL-001]

**AXS-UNIV-029 — Deterministic Text & `--json` Output Schema for `--inspect-slices` (`compiler/driver/emit_universal`, `T691`).**
1. **Human-readable text output (default without `--json`, LF-only):**
   ```text
   container: fat32 (magic=0xcafebabe, slices=2)
   slice[0]: arch=x86_64 triple=x86_64-macos cputype=0x01000007 cpusubtype=0x00000003 kind=exe offset=4096 size=68432 align=2^12 (4096) uuid=0123456789abcdef0123456789abcdef codesign=adhoc-sha256
   slice[1]: arch=arm64 triple=aarch64-macos cputype=0x0100000c cpusubtype=0x00000000 kind=exe offset=81920 size=70112 align=2^14 (16384) uuid=fedcba9876543210fedcba9876543210 codesign=adhoc-sha256
   ```
   Where `container` is `"fat32"` (`0xcafebabe`), `"fat64"` (`0xcafebabf`), or `"thin"` (`offset=0`, `size=<file_len>`, `slices=1`); `kind` is `"exe"`, `"dylib"`, `"obj"`, `"archive"`, or `"axlib"`; `uuid` is 32 lowercase hex digits or `"none"`; and `codesign` is `"adhoc-sha256"`, `"signed"`, or `"none"`.
2. **Machine-readable `--json` schema:**
   ```json
   {
     "container": "fat32",
     "magic": "0xcafebabe",
     "slice_count": 2,
     "slices": [
       {
         "index": 0,
         "arch": "x86_64",
         "triple": "x86_64-macos",
         "cputype": 16777223,
         "cpusubtype": 3,
         "kind": "exe",
         "offset": 4096,
         "size": 68432,
         "align_pow2": 12,
         "align_bytes": 4096,
         "uuid": "0123456789abcdef0123456789abcdef",
         "codesigned": true
       }
     ]
   }
   ```
   Field order and formatting are 100% deterministic. [0097 §27; tasks/0563 §304.34; SPEC-89 AXS-ARTM-031; REQ-TOOL-001]

**AXS-UNIV-030 — Standalone Pre-Built Thin Slice Composition (`--compose-universal`, `REQ-TGT-001`, `REQ-TOOL-001`, `T691`).**
To support staged or distributed build pipelines (`tasks/0587 §34`) where thin slices are compiled on separate workers or cached from earlier `--target` invocations, `compiler/driver/universal` supports `axiomc build --compose-universal <slice_file_1> <slice_file_2> [...] -o <universal_out>` (alias `axiomc obj --compose-universal <slice_file_1> <slice_file_2> [...] -o <universal_out>`):
- Reads each input thin file (if an input is itself a valid Fat container, flattens its constituent thin slices), verifies disjoint `(cputype, cpusubtype & 0x00FF_FFFF)` (`E9003`), homogeneous payload kind and `.dylib` version agreement (`E9005`, `E9006`), and thin slice structural / code-signature integrity (`E9010`, `E9014`), sorts slices per `AXS-UNIV-014`, composes the `FAT_MAGIC` / `FAT_MAGIC_64` container (`AXS-UNIV-015`..`016`), runs `verify_universal_artifact` (`AXS-UNIV-018`), and writes `<universal_out>` atomically. [0097 §27; tasks/0453 §194.29; tasks/0587 §34, §38; REQ-TGT-001, REQ-TOOL-001]

**AXS-UNIV-031 — `axiomc run` Isolation Policy for Multi-Arch Universal Builds (`ATARGET-13`).**
Passing `--universal-targets` or `--compose-universal` to `axiomc run` is rejected deterministically with `AX_DRIVER_USAGE` (exit code `2`: `'run' does not support '--universal-targets'; use 'axiomc build --universal-targets ...' or 'axiomc run --target <triple>'`), preserving `SPEC-88`'s strict separation between cross/multi-target artifact production and host execution (`tasks/0587 §39 ATARGET-13`). [tasks/0587 §39 ATARGET-13; SPEC-89 AXS-ARTM-002]

---

## 5. Diagnostics (`E9000–E9014`), Canonical Examples & Traceability Matrix (`AXS-UNIV-032`..`036`)

**AXS-UNIV-032 — Canonical Diagnostic Taxonomy & `E9000–E9014` Task-Card Mapping (`spec/diagnostics.md` §3, §11).**
Per `ADR-0011` and `AXD-010..021`, `axiomc` never exposes numeric serial codes in diagnostic output; task-card shorthand references `E9000–E9014` (`T689`–`T692`) map 1-to-1 onto canonical `AX_<AREA>_<NAME>` identifiers in the existing `DRIVER` and `LINK` areas:

| Card Ref | Canonical `AX_*` Code | Area | Sev | Task | Condition & Structured `data.*` Payload |
|---|---|---|---|---|---|
| `E9000` | `AX_DRIVER_UNKNOWN_TARGET` | `DRIVER` | E | `T691` | Unknown target triple in `--universal-targets` / `universal_targets` or unknown architecture token in `--extract-slice` / `--verify-arch` (`data.target`, exit code `2`; `AXS-UNIV-026`, `AXS-UNIV-028`) |
| `E9001` | `AX_DRIVER_INVALID_UNIVERSAL_TARGETS` | `DRIVER` | E | `T691` | Empty `--universal-targets`, empty comma item, fewer than `2` target slices, or mutually exclusive `--target` combined with `--universal-targets` (`data.flag`, `data.value`, exit code `2`; `AXS-UNIV-026`) |
| `E9002` | `AX_DRIVER_UNIVERSAL_TARGET_INCOMPATIBLE` | `DRIVER` | E | `T691` | Non-Mach-O target (`x86_64-windows`, `x86_64-linux`, `wasm32-wasi`, `<arch>-none`, …) or cross-OS mix passed to Mach-O `--universal-targets` instead of `.axpkg` (`data.target`, exit code `2`; `AXS-UNIV-023`, `AXS-UNIV-026`) |
| `E9003` | `AX_LINK_DUPLICATE_FAT_ARCH` | `LINK` | E | `T690`/`T691` | Two slices in `--universal-targets`, `--compose-universal`, or a Fat container resolve to the identical `(cputype, cpusubtype & 0x00FF_FFFF)` (`data.arch`, `data.cputype`, `data.cpusubtype`; `AXS-UNIV-014`, `AXS-UNIV-026`) |
| `E9004` | `AX_DRIVER_INVALID_ARTIFACT_KIND` | `DRIVER` | E | `T691` | `--universal-targets` combined with unsupported `--kind obj` (`--emit=obj`) or `wasm-module`/`wasm-reactor` (passing `--universal-targets` to `axiomc run` emits `AX_DRIVER_USAGE`; `data.kind`, exit code `2`; `AXS-UNIV-026`, `AXS-UNIV-031`) |
| `E9005` | `AX_LINK_FAT_SLICE_KIND_MISMATCH` | `LINK` | E | `T690`/`T692` | Heterogeneous payload kinds across slices in a Fat container (e.g., `MH_EXECUTE` mixed with `MH_DYLIB` or `BsdAr`), legacy 32-bit `MH_MAGIC (0xFEED_FACE)` or non-Mach-O/non-`BsdAr` slice magic, or inner `mach_header_64.cputype` disagreeing with outer `fat_arch.cputype` (`data.slice_index`, `data.expected_kind`, `data.found_kind`; `AXS-UNIV-010`, `AXS-UNIV-018`..`019`) |
| `E9006` | `AX_LINK_INVALID_DYLIB_VERSION` | `LINK` | E | `T690`/`T691` | Composed Universal `MH_DYLIB` slices disagree on `LC_ID_DYLIB` `install_name`, `current_version`, or `compatibility_version`, or specify malformed `X.Y.Z` dylib versions (`data.flag`, `data.value`; `AXS-UNIV-019`, `SPEC-89 AXS-ARTM-021`) |
| `E9007` | `AX_LINK_UNALIGNED_FAT_SLICE` | `LINK` | E | `T690`/`T692` | Fat slice descriptor violates alignment rules: `align > 30`, `(offset & ((1u64 << align) - 1)) != 0`, or `MH_EXECUTE`/`MH_DYLIB` slice `align` below target page shift (`< 12` for `CPU_TYPE_X86_64`, `< 14` for `CPU_TYPE_ARM64`; `data.arch`, `data.offset`, `data.align`; `AXS-UNIV-013`) |
| `E9008` | `AX_LINK_BAD_UNIVERSAL` | `LINK` | E | `T690`–`T692` | Corrupt or malformed Fat container: invalid magic (including JVM `.class` `0xCAFEBABE`), `nfat_arch == 0` or `> 16`, truncated descriptor table, `size == 0`, `offset < hdr_end`, `offset + size` overflow or `> file_len`, overlapping slices, or non-zero `fat_arch_64.reserved` (`data.file`, `data.detail`; `AXS-UNIV-010`..`018`) |
| `E9009` | `AX_LINK_IMAGE_TOO_LARGE` | `LINK` | E | `T690` | Slice `offset` or `size >= 2^32` when 32-bit `--fat32` (`FAT_MAGIC`) is explicitly forced (`data.file`, `data.size`; `AXS-UNIV-016`) |
| `E9010` | `AX_LINK_BAD_CODESIGN` | `LINK` | E | `T690`–`T692` | Corrupt or mismatched per-slice `LC_CODE_SIGNATURE` (`CS_SuperBlob` / `CS_CodeDirectory` magic, bounds, `pageSize`, or SHA-256 page hash mismatch over `[0 .. slice_sig_off)`) during composition or `--verify-arch` (`data.file`, `data.arch`, `data.detail`; `AXS-UNIV-020`, `AXS-UNIV-028`) |
| `E9011` | `AX_LINK_FAT_ARCH_NOT_FOUND` | `LINK` | E | `T691`/`T692` | Architecture requested by `--extract-slice <arch>` or `--verify-arch <arch>` does not exist in `<file>`, or `--extract-slice` is invoked on a non-Fat thin file (`data.file`, `data.requested_arch`, `data.available_archs`; `AXS-UNIV-028`) |
| `E9012` | `AX_LINK_ARTIFACT_TARGET_MISMATCH` | `LINK` | E | `T690`/`T691` | Linked `.a`, `.axlib`, `.dylib`, `.tbd`, `.o`, or `.axmi` dependency lacks a slice matching active target leg $T$, or an inner `BsdAr` member's `cputype` mismatches its enclosing slice (`data.expected_target`, `data.available_slices`; `AXS-UNIV-018`, `AXS-UNIV-022`) |
| `E9013` | `AX_LINK_RELOC_OUT_OF_RANGE` / `AX_LINK_TEXTREL_FORBIDDEN` | `LINK` | E | `T690` | `x86_64-macos` slice 32-bit RIP-relative relocation overflows `i32` (`AX_LINK_RELOC_OUT_OF_RANGE`) or non-PIC `X86_64_RELOC_UNSIGNED` targets `__TEXT` (`AX_LINK_TEXTREL_FORBIDDEN`; `AXS-UNIV-005`) |
| `E9014` | `AX_LINK_BAD_OBJECT` / `AX_LINK_BAD_ARCHIVE` | `LINK` | E | `T690` | Malformed thin Mach-O slice header/load-commands (`AX_LINK_BAD_OBJECT`) or malformed thin `BsdAr` `"!<arch>\n"` / `__.SYMDEF SORTED` / `#1/<len>` header inside a Universal archive (`AX_LINK_BAD_ARCHIVE`; `AXS-UNIV-004`, `AXS-UNIV-021`) |

[ADR-0011; spec/diagnostics.md AXD-010..021, §10–11]

**AXS-UNIV-033 — Canonical Positive Example 1: Universal 2 Executable (`MH_EXECUTE`) with Per-Slice `@cfg` Specialization & Target Page-Size Introspection.**
```axiom
// Built from any Windows, Linux, or macOS host without Xcode / clang / lipo:
//   axiomc build --universal-targets x86_64-apple-darwin,aarch64-apple-darwin app/main.ax -o dist/hello_univ
// Inspect & extract slices natively:
//   axiomc inspect --inspect-slices dist/hello_univ
//   axiomc inspect --verify-arch x86_64,arm64 dist/hello_univ
//   axiomc inspect --extract-slice x86_64 dist/hello_univ -o dist/hello_x64
//   axiomc inspect --extract-slice arm64  dist/hello_univ -o dist/hello_arm64
module app

use std.io.println
use std.target.{CACHE_LINE_BYTES, MIN_PAGE_SIZE_BYTES}

@cfg(target_arch = "x86_64")
fn slice_tag() -> Str {
    "x86_64-macos (4 KiB page, SysV64)"
}

@cfg(target_arch = "aarch64")
fn slice_tag() -> Str {
    "aarch64-macos (16 KiB page, Aapcs64Darwin)"
}

@cfg(target_arch = "x86_64")
const EXPECTED_PAGE: usize = 4096

@cfg(target_arch = "aarch64")
const EXPECTED_PAGE: usize = 16384

pub fn main() -> i32 {
    println("Xin chào thế giới")
    println(slice_tag())
    if MIN_PAGE_SIZE_BYTES == EXPECTED_PAGE && CACHE_LINE_BYTES >= 64 {
        return 0
    }
    return 1
}
```

**AXS-UNIV-034 — Canonical Positive Example 2: Universal Static Library (`.a`), Universal Dynamic Library (`.dylib`) & Universal Package Library (`.axlib`).**
```axiom
// --- math_univ/lib.ax ---
// 1) Universal C static archive (Fat container wrapping x86_64 + arm64 BsdAr archives):
//    axiomc build --universal-targets x86_64-macos,aarch64-macos --kind staticlib math_univ/lib.ax -o dist/libmath_univ.a
//
// 2) Universal macOS dynamic library (Fat container wrapping two ad-hoc signed MH_DYLIB slices
//    sharing LC_ID_DYLIB "@rpath/libmath_univ.1.dylib" and compatibility_version 1.0.0):
//    axiomc build --universal-targets x86_64-macos,aarch64-macos --kind cdylib math_univ/lib.ax \
//        --install-name @rpath/libmath_univ.1.dylib --current-version 1.2.0 --compatibility-version 1.0.0 \
//        -o dist/libmath_univ.1.dylib
//
// 3) Universal Axiom native library (Fat container wrapping two BsdAr slices each carrying its own
//    slice-local lib.axrmeta + MH_OBJECT CGUs):
//    axiomc build --universal-targets x86_64-macos,aarch64-macos --kind axlib math_univ/lib.ax -o dist/libmath_univ.axlib
module math_univ

pub const BANNER: Str = "Xin chào thế giới"

// Hidden internal helper: N_PEXT in Mach-O; never exported in LC_DYLD_EXPORTS_TRIE
pub fn clamp_u32(v: u32, hi: u32) -> u32 {
    if v > hi { hi } else { v }
}

@export("ax_weighted_sum")
pub extern "C" fn weighted_sum(a: u32, b: u32) -> u32 {
    clamp_u32(a, 10000u32) * 3u32 + clamp_u32(b, 10000u32)
}
```

**AXS-UNIV-035 — Canonical Negative Examples (`E9001`–`E9012`).**
```axiom
// 1) Duplicate normalized Darwin architecture slice (E9003 -> AX_LINK_DUPLICATE_FAT_ARCH):
//    axiomc build --universal-targets x86_64-macos,x86_64-apple-darwin main.ax -o app
//    -> ERROR AX_LINK_DUPLICATE_FAT_ARCH (data.arch = "x86_64", data.cputype = 0x01000007)
//
// 2) Non-Mach-O target passed to --universal-targets (E9002 -> AX_DRIVER_UNIVERSAL_TARGET_INCOMPATIBLE):
//    axiomc build --universal-targets x86_64-linux,aarch64-linux main.ax -o app
//    -> ERROR AX_DRIVER_UNIVERSAL_TARGET_INCOMPATIBLE (exit code 2; data.target = "x86_64-linux";
//       help: ELF targets do not use Mach-O Fat headers; build per-target binaries or a '.axpkg' bundle)
//
// 3) Mutually exclusive --target and --universal-targets (E9001 -> AX_DRIVER_INVALID_UNIVERSAL_TARGETS):
//    axiomc build --target aarch64-macos --universal-targets x86_64-macos,aarch64-macos main.ax
//    -> ERROR AX_DRIVER_INVALID_UNIVERSAL_TARGETS (exit code 2)
//
// 4) Composing heterogeneous thin slices (MH_EXECUTE + MH_DYLIB) (E9005 -> AX_LINK_FAT_SLICE_KIND_MISMATCH):
//    axiomc build --compose-universal app_x64 libfoo_arm64.dylib -o bad_fat
//    -> ERROR AX_LINK_FAT_SLICE_KIND_MISMATCH (data.expected_kind = "exe", data.found_kind = "dylib")
//
// 5) Malformed Fat binary with ARM64 MH_EXECUTE slice at 4 KiB offset 0x1000 instead of 16 KiB (align < 14)
//    (E9007 -> AX_LINK_UNALIGNED_FAT_SLICE):
//    axiomc inspect --verify-arch arm64 bad_arm64_4k_aligned.fat
//    -> ERROR AX_LINK_UNALIGNED_FAT_SLICE (data.arch = "arm64", data.offset = 4096, data.align = 12)
//
// 6) Extracting a slice absent from the Universal container (E9011 -> AX_LINK_FAT_ARCH_NOT_FOUND):
//    axiomc inspect --extract-slice arm64e dist/hello_univ -o hello_arm64e
//    -> ERROR AX_LINK_FAT_ARCH_NOT_FOUND (data.requested_arch = "arm64e", data.available_archs = ["x86_64", "arm64"])
//
// 7) Linking an arm64-only static archive into a Universal x86_64+arm64 build
//    (E9012 -> AX_LINK_ARTIFACT_TARGET_MISMATCH):
//    axiomc build --universal-targets x86_64-macos,aarch64-macos main.ax deps/libonly_arm64.a -o app
//    -> ERROR AX_LINK_ARTIFACT_TARGET_MISMATCH (data.expected_target = "x86_64-macos",
//       data.available_slices = ["aarch64-macos"])
module bad_universal_cli_examples
```

**AXS-UNIV-036 — `E16.11` Implementation, Invariant (`INV-UNIV-001`..`004`) & Requirement Traceability Matrix.**
Per `spec/invariants.md` rule `IG-1` (`^### (INV-[A-Z]+-[0-9]{3}) — `), the `T689` task-card shorthand `INV-UNIV-01..04` is registered canonically as 3-digit `INV-UNIV-001`..`INV-UNIV-004`:

| Task | Owned Paths | Rules & Invariants Verified | Covered Requirements |
|---|---|---|---|
| `T689` | `spec/SPEC-90-universal-multiarch-artifacts.md` (`locks`: `INDEX.md`, `diagnostics.md`, `invariants.md`) | `AXS-UNIV-001`..`036`; registers `INV-UNIV-001`..`004` & `E9000–E9014` (`AX_DRIVER_*` / `AX_LINK_*`) | `REQ-TGT-001`, `REQ-TGT-104`, `REQ-TGT-105`, `REQ-TGT-200` |
| `T690` | `compiler/target/x64/macos`, `compiler/obj/macho_universal`, `tests/obj/macho_universal`, `tests/selfhost/obj` | `AXS-UNIV-002`..`025`, `032`; `INV-UNIV-001`, `INV-UNIV-002` | `REQ-TGT-001`, `REQ-TGT-104`, `REQ-TGT-106`, `REQ-TGT-153` |
| `T691` | `compiler/driver/universal`, `compiler/driver/emit_universal`, `tests/driver/universal`, `tests/selfhost/driver` | `AXS-UNIV-001`, `026`..`032`; `INV-UNIV-003` | `REQ-TGT-001`, `REQ-TGT-154`, `REQ-TGT-200`, `REQ-TGT-319` |
| `T692` | `tests/conformance/p16/e16_11_universal_artifacts` | End-to-end conformance across `AXS-UNIV-001`..`036`; `INV-UNIV-004` | `REQ-TGT-001`, `REQ-TGT-199`, `REQ-TGT-318`, `REQ-TGT-320` |

Detailed requirement & corpus-anchor mapping:

| Requirement / Corpus Anchor | Canonical `SPEC-90` Rule(s) | Board Task(s) |
|---|---|---|
| `REQ-TGT-001` (`tasks/0453 §194.29, §194.44 ATARGET-41..43`: universal binaries created by explicit composition of multi-target native artifacts, never implicit) | `AXS-UNIV-001`, `AXS-UNIV-023`, `AXS-UNIV-026`, `AXS-UNIV-030` | `T689`, `T690`, `T691`, `T692` |
| `REQ-TGT-104` (`tasks/0518 §151 AMACHINE-115`: direct native PE, ELF, Mach-O & WASM output emission through the object backend) | `AXS-UNIV-004`..`006`, `AXS-UNIV-010`..`021` | `T689`, `T690` |
| `REQ-TGT-105` (`tasks/0518 §151 AMACHINE-116`: machine backend target selection is determined by `TargetSpec`; `0163 §1–7` `TargetId.X86_64Macos` / `x86_64-apple-darwin`) | `AXS-UNIV-002`..`003`, `AXS-UNIV-026` | `T689` |
| `REQ-TGT-106` (`tasks/0518 §151 AMACHINE-117`), `REQ-TGT-153` (`tasks/0521 §156 AARM-59`), `REQ-TGT-320` (`tasks/0524 §112 ABACKEND-95`: deterministic machine backend codegen & reproducible cross-host Universal compilation; `tasks/0453 §194.42`) | `AXS-UNIV-004`..`005`, `AXS-UNIV-008`, `AXS-UNIV-014`..`017`, `AXS-UNIV-020`..`021`, `AXS-UNIV-025` | `T690`, `T692` |
| `REQ-TGT-154` (`tasks/0521 §156 AARM-60`), `REQ-TGT-200` (`tasks/0522 §159 ABACKEND-54`), `REQ-TGT-319` (`tasks/0524 §112 ABACKEND-94`: backend caches include `TargetId`, `TargetFeatureSet`, ABI/`CallConv` & codegen identity; Tier-A sharing & per-slice cache isolation) | `AXS-UNIV-019`, `AXS-UNIV-022`, `AXS-UNIV-027` | `T689`, `T691` |
| `REQ-TGT-199` (`tasks/0522 §159 ABACKEND-53`; see also `tasks/0521 §156 AARM-63`: equivalent Axiom programs have equivalent observable behavior across targets) | `AXS-UNIV-001`, `AXS-UNIV-025`, `AXS-UNIV-033`..`034` | `T692` |
| `REQ-TGT-307` (`tasks/0524 §112 ABACKEND-82`: post-encoding object, image & Universal container verification) | `AXS-UNIV-009`, `AXS-UNIV-018` | `T690`, `T692` |
| `REQ-TGT-318` (`tasks/0524 §112 ABACKEND-93`: all supported targets pass common semantic conformance tests with invariant Core semantics) | `AXS-UNIV-001`, `AXS-UNIV-025`, `AXS-UNIV-033`..`034` | `T692` |
| `REQ-TOOL-001` (`0097 §27`; `tasks/0453 §194.43`; `tasks/0563 §304.34`: native toolchain produces & inspects/extracts/verifies Universal artifacts without third-party Xcode `lipo`/`codesign`) | `AXS-UNIV-008`, `AXS-UNIV-028`..`030` | `T689`, `T690`, `T691` |
| `0196 §1–40` (`MACHO-001`), `0217 §15–19, §33–34, §44–47` (`ALINK-20..56`), `tasks/0563 §304.21–37` (`AIMG-25..50`), `tasks/0587 §30–39` (`ATARGET-01..30`) | `AXS-UNIV-001`..`032` | `T689`, `T690`, `T691`, `T692` |

---

## Sources

`0097 §27`; `0163 §1–7`; `0196 §1–40`; `0217 §15–19, §33–34, §44–47, §72` (`ALINK-20..56`); `0220 §4, §7`; `tasks/0453 §194.2–6, §194.28–32, §194.41–44` (`ATARGET-20..50`); `tasks/0518 §151` (`AMACHINE-112, 114, 115, 116, 117`); `tasks/0521 §156` (`AARM-59..60, 63`); `tasks/0522 §159` (`ABACKEND-53..55`); `tasks/0524 §112` (`ABACKEND-82..83, 93..95`); `tasks/0563 §304.5, §304.21–25, §304.30–37, §304.45` (`AIMG-25..50`); `tasks/0587 §1–8, §30–39` (`ATARGET-01..30`); `spec/decisions/ADR-0011-diagnostic-code-taxonomy.md`; `spec/SPEC-01-lexical.md`; `spec/SPEC-02-grammar.md` (`AXS-GRM-086`); `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-052`, `AXS-EXT-060..062`, `AXS-EXT-070..074`); `spec/SPEC-21-query-engine-semantic-db.md`; `spec/SPEC-22-incremental-compilation.md`; `spec/SPEC-23-parallel-compilation.md`; `spec/SPEC-24-artifact-format-module-interfaces.md` (`AXS-ART-002`, `AXS-ART-010..014`, `AXS-ART-020..024`); `spec/SPEC-34-executors-fibers.md` (`AXS-EXEC-054`); `spec/SPEC-44-cpu-features-multiversioning.md`; `spec/SPEC-50-unsafe-ub-ffi.md` (`AXS-UNS-032`); `spec/SPEC-54-panic-unwinding.md` (`AXS-PAN-020`); `spec/SPEC-80-linux-x86-64-elf-static.md` (`AXS-ELFS-002`, `AXS-ELFS-005..020`, `AXS-ELFS-026..027`, `AXS-ELFS-048`); `spec/SPEC-81-target-desc-isa-conformance.md` (`AXS-TGTD-001..012`); `spec/SPEC-84-macos-aarch64-macho.md` (`AXS-MACHO-001..036`); `spec/SPEC-88-cross-compilation-platform-layer.md` (`AXS-XCMP-001..028`, `AXS-PLAT-001..024`); `spec/SPEC-89-artifact-library-matrix.md` (`AXS-ARTM-001..040`); `spec/diagnostics.md`; `spec/invariants.md`; `spec/requirements/CATALOG.md`.
