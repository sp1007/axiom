# SPEC-89 — Cross-Target Artifact Kinds & Library Matrix (`exe`, `obj`, `lib`/`staticlib`, `dll`/`cdylib`, `axlib`, `wasm` Command/Reactor)

## Tóm tắt
Tài liệu này chuẩn hóa ma trận thành phẩm đầu ra (`ArtifactKind`) và định dạng thư viện tĩnh/động xuyên suốt mọi kiến trúc đích của trình biên dịch `axiomc` (Epic `E16.10`, Phase 16 `P16-targets-platforms`, mở rộng `SPEC-04`, `SPEC-24`, `SPEC-26`, `SPEC-27`, và `SPEC-80`..`SPEC-88`):
- **Phân loại thành phẩm thống nhất và cờ CLI `--kind` (`AXS-ARTM-001..007`)**: Thống nhất 6 loại thành phẩm kiến trúc (`Executable`, `Object`, `StaticLib`, `DynLib`, `AxLib`, `Universal`) dưới cờ chuẩn `--kind <exe|obj|lib|dll|axlib>` kèm các bí danh chuẩn hóa tất định (`bin -> exe`, `staticlib -> lib`, `cdylib -> dll`, `wasm-module`/`wasm-reactor -> dll` trên `wasm32-*`, `--emit=obj -> obj`). Mọi thành phẩm được phát sinh nhị phân trực tiếp từ `ObjectWriter` / `ImageWriter` mà không qua hợp ngữ trung gian hay trình liên kết bên ngoài (`REQ-TOOL-001`, `REQ-TGT-101`, `REQ-TGT-103`, `REQ-TGT-104`, `REQ-TGT-184`), đồng thời cưỡng chế cô lập hiển thị biểu tượng mặc định ẩn (`STV_HIDDEN`, `N_PEXT`, non-`dllexport`) cho mọi biểu tượng không gắn `@export`.
- **Định dạng kho lưu trữ tĩnh tất định (`CoffAr`, `GnuAr`, `BsdAr`) và gói thư viện bản địa `.axlib` (`AXS-ARTM-008..014`)**: Chuẩn hóa phong bì `!<arch>\n` với tiêu đề thành viên 60 byte có `mtime = 0`, `uid = 0`, `gid = 0`, chế độ tệp chuẩn hóa theo từng đích, bảng chỉ mục biểu tượng `CoffAr` (2 thành viên liên kết `/` + `//`), `GnuAr` (`/` big-endian 32-bit, `/SYM64/` 64-bit khi $\ge 4\text{ GiB}$, và `//`), cùng `BsdAr` (`__.SYMDEF SORTED` / `__.SYMDEF_64` little-endian và tên mở rộng `#1/<len>` căn lề 8 byte cho `MH_OBJECT`). Định nghĩa thành phẩm `.axlib` nhúng thành viên giao diện `lib.axrmeta` (`SPEC-24` `.axmi` + mẫu `Verified MIR` tổng quát) bên cạnh các tệp đối tượng `.obj`/`.o`/`.wasm` chứa `.axmeta`/`.axlto`.
- **Ma trận thư viện động đa nền tảng (`PE .dll`, `ELF .so`, `Mach-O .dylib`, `WASM Reactor`) (`AXS-ARTM-015..024`)**: Quy định chi tiết tệp định nghĩa mô-đun `.def` (số thứ tự `@ordinal`, `NONAME`, `DATA`, chuyển tiếp `Foo = OTHER.Bar`) và thư viện nhập khẩu ngắn/chuẩn `.lib` trên Windows; đánh số phiên bản biểu tượng GNU (`SHT_GNU_versym`, `VERDEF`, `VERNEED`, `--version-script`) và `DT_SONAME`/`DT_RUNPATH` trên Linux/Android/RISC-V; không gian tên hai mức (`MH_TWOLEVEL`), `LC_ID_DYLIB` (`@rpath`/`@loader_path`/`@executable_path`), bộ ba phiên bản `X.Y.Z`, `LC_LOAD_WEAK_DYLIB`/`LC_REEXPORT_DYLIB`, stub `.tbd`, và chữ ký ad-hoc `LC_CODE_SIGNATURE` trên macOS; cùng mô hình mô-đun `Reactor` (`_initialize`) so với `Command` (`_start`) trên WebAssembly (`REQ-TGT-245..247`).
- **Trích xuất kho lưu trữ điểm bất động, `--whole-archive`, phân giải biểu tượng kim cương và nhúng phân đoạn IR (`AXS-ARTM-025..040`)**: Chuẩn hóa thuật toán trích xuất theo nhu cầu tới điểm bất động, phạm vi `--whole-archive` / `--no-whole-archive` / `-force_load`, ma trận phân giải `Strong` / `Weak` / `Comdat` xuyên định dạng (`REQ-TGT-308`), ánh xạ phân đoạn không cấp phát `.axmeta`/`.axmir`/`.axlto` trên COFF/ELF/Mach-O/WASM kèm quy tắc bắt buộc tước bỏ khỏi ảnh thực thi/thư viện động cuối, cổng kiểm định hậu mã hóa (`REQ-TGT-307`), và hệ thống mã chẩn đoán chuẩn `AX_*`.

Status: draft (T685, 2026-11-04). Owner: axiom-architect.
Rule IDs `AXS-ARTM-NNN` (`001..040`) and invariants `INV-ARTM-001..005` are stable and never renumbered (distinct from `SPEC-24`'s `AXS-ART-NNN` / `INV-ART-001..003` and `SPEC-26`'s `AXS-WLIB-NNN` / `INV-WLIB-001..003`).
Consolidates: `0097 §27`, `0164 §1–11, §20–35`, `0185`, `0186`, `0187`, `0196`, `0197 §1–5, §17–26`, `0217 §3–4, §11–24, §30–45, §53–57, §68–72` (`ALINK-20..56`), `tasks/0369 §1–22, §25–37` (`ALINK-20..50`), `tasks/0453 §194.10, §194.20–23, §194.28–31, §194.36, §194.42–44` (`ATARGET-20..50`), `tasks/0518 §151` (`AMACHINE-71, 112, 114, 115, 117`), `tasks/0521 §156` (`AARM-52, 57`), `tasks/0522 §159` (`ABACKEND-38`), `tasks/0523 §155` (`AWASM-56..58`), `tasks/0524 §112` (`ABACKEND-82..83, 93, 95`), `tasks/0563 §304.1–304.46` (`AIMG-20..60`), `spec/decisions/ADR-0001-fixed-address-declarations.md`, `spec/decisions/ADR-0034-oracle-independence.md`, `spec/SPEC-04-core-extensibility.md`, `spec/SPEC-24-artifact-format-module-interfaces.md`, `spec/SPEC-26-windows-artifact-kinds.md`, `spec/SPEC-27-separate-compilation-linker-v2.md`, `spec/SPEC-50-unsafe-ub-ffi.md`, `spec/SPEC-52-freestanding-runtime-composition.md`, `spec/SPEC-54-panic-unwinding.md`, `spec/SPEC-56-module-relative-bindings.md`, `spec/SPEC-75-lto-wpo-section-gc-pgo.md`, and `spec/SPEC-80-linux-x86-64-elf-static.md`..`spec/SPEC-88-cross-compilation-platform-layer.md`.
Covers: `REQ-TGT-101`, `REQ-TGT-103`, `REQ-TGT-104`, `REQ-TGT-184`, `REQ-TGT-307`, `REQ-TGT-308` (and governs downstream `E16.10` tasks `T686`, `T687`, `T688` covering `REQ-TOOL-001`, `REQ-TGT-060`, `REQ-TGT-106`, `REQ-TGT-146`, `REQ-TGT-151`, `REQ-TGT-245`, `REQ-TGT-246`, `REQ-TGT-247`, `REQ-TGT-318`, `REQ-TGT-320`, while generalizing `E18.7` `T750`–`T751` `REQ-OWNER-006`).
Consumers: `T686` (`compiler/obj/archive_matrix`, `compiler/link/archive_resolve`, `tests/link/static_matrix`), `T687` (`compiler/obj/def_import`, `compiler/link/dynlib_matrix`, `tests/link/dynlib_matrix`), `T688` (`tests/conformance/p16/e16_10_artifact_matrix`), and `T689`–`T692` (`SPEC-90`, universal multi-arch artifacts).

---

## 1. Cross-Target Artifact Taxonomy, CLI Surface & Target Matrix (`AXS-ARTM-001`..`007`)

**AXS-ARTM-001 — Unified `ArtifactKind` Model & Direct Native Emission Without Intermediate Assembly (`REQ-TGT-101`, `REQ-TGT-103`, `REQ-TGT-104`, `REQ-TGT-151`, `REQ-TGT-184`, `REQ-TOOL-001`).**
1. **Canonical `ArtifactKind` enumeration (`SPEC-04 AXS-EXT-070`, `SPEC-26 AXS-WLIB-001`, `0197 §23`, `tasks/0563 §304.3`):**
   `compiler/obj` defines a single target-independent output classification shared by the driver, incremental cache (`SPEC-22`), object/archive writers, and native linkers:
   ```axiom
   pub enum ArtifactKind {
       Executable   // Standalone executable or WASM command module (--kind exe | bin)
       Object       // Relocatable native/WASM object file (--kind obj, --emit=obj)
       StaticLib    // Foreign/C-ABI static archive of relocatable objects (--kind lib | staticlib)
       DynLib       // Shared/dynamic library or WASM reactor module (--kind dll | cdylib)
       AxLib        // Axiom native package library: lib.axrmeta + object members (--kind axlib)
       Universal    // Multi-architecture Fat container wrapping per-arch slices (SPEC-90, E16.11)
   }
   ```
2. **Direct binary emission without textual assembly (`REQ-TGT-101`, `REQ-TGT-103`, `REQ-TGT-104`, `REQ-TOOL-001`):**
   - Every target backend emits relocatable objects (`COFF`, `ELF64`, `Mach-O 64`, relocatable `.wasm`), static archives (`CoffAr`, `GnuAr`, `BsdAr`), and linked images (`PE32+`, `ELF64`, `Mach-O 64`, linked `.wasm`) **directly in memory and on disk** from verified `Machine IR` / `LinkedImage` (`tasks/0518 §151 AMACHINE-112, 114, 115`, `tasks/0563 §304.2–4 AIMG-20, 52, 60`).
   - Textual assembly (`.s` / `.asm`) and WAT (`.wat`) exist exclusively for `axiomc inspect` human diagnostics and are **never** an intermediate representation in compilation (`REQ-TGT-103`). No external assembler (`as`, `ml64`), archiver (`ar`, `lib.exe`, `libtool`), linker (`ld`, `link.exe`, `ld64`, `wasm-ld`), or code-signing utility (`codesign`) is invoked (`REQ-TOOL-001`, `0097 §27`).
3. **Strict separation between ISA encoding and object/container serialization (`REQ-TGT-151`, `REQ-TGT-184`):**
   - Per `SPEC-24 AXS-ART-020`, `SPEC-27 AXS-LNK-004`, and `SPEC-81 AXS-TGTD-039`, instruction encoders (`compiler/target/<arch>/encode`) produce pure byte slices + abstract `RelocFixup` descriptors without importing `COFF`, `ELF`, `Mach-O`, or `ar` container headers (`tasks/0521 §156 AARM-57`, `tasks/0522 §159 ABACKEND-38`). Object writers (`compiler/obj/*`), archive producers (`compiler/obj/archive_matrix`), and image writers (`compiler/link/*`) serialize container formats field-by-field with explicit endianness and checked offset arithmetic (`tasks/0563 §304.30–32, §304.45 AIMG-32..34, 53, 59`). [0097 §27; 0197 §23; 0217 §3–4, §72 ALINK-20..23; tasks/0518 §151 AMACHINE-112, 114, 115; tasks/0521 §156 AARM-57; tasks/0522 §159 ABACKEND-38; tasks/0563 §304.2–4, §304.30–32, §304.45 AIMG-20, 32..34, 52..53, 59..60; SPEC-04 AXS-EXT-070; SPEC-24 AXS-ART-020; SPEC-27 AXS-LNK-004; SPEC-81 AXS-TGTD-039]

**AXS-ARTM-002 — Canonical `--kind` CLI Flag, Manifest `kind` Mapping & Synonym Normalization.**
1. **Single authoritative CLI flag (`--kind`):**
   `axiomc build` and `axiomc compile` select the output artifact via `--kind <kind>` (default `exe`), overriding `kind = "<kind>"` in `axiom.toml` (`[package]` or `[[target]]`, `SPEC-26 AXS-WLIB-002`). Rust-specific `--crate-type` is **not** an Axiom flag (`0197 §23`) and is rejected by the CLI parser with `AX_DRIVER_UNKNOWN_OPTION` accompanied by a help attachment suggesting `--kind <exe|obj|lib|dll|axlib>`.
2. **Normalized `--kind` spelling table:**
   To preserve 100% compatibility with `SPEC-26` and `SPEC-80`..`SPEC-88` (`exe`, `obj`, `lib`, `dll`) while supporting explicit C-ABI vs Axiom-ABI library distinctions (`staticlib`, `cdylib`, `axlib`, `wasm-module`), the driver normalizes `--kind` and `axiom.toml` `kind` values before query evaluation and cache-key construction:

   | Primary `--kind` | Accepted Synonyms | `ArtifactKind` | Cache & Link Semantics |
   |---|---|---|---|
   | `exe` | `bin` | `Executable` | Linked standalone image (`main` or `@entry`; WASM `_start` command) |
   | `obj` | `--emit=obj` | `Object` | Single relocatable object + `.axmi` interface (no linker invocation) |
   | `lib` | `staticlib` | `StaticLib` | Native static archive (`.lib` / `.a`) of relocatable objects for C/FFI or Axiom |
   | `dll` | `cdylib`, `wasm-module`*, `wasm-reactor`* | `DynLib` | Native shared library (`.dll`+`.lib` / `.so` / `.dylib`) or WASM `_initialize` reactor |
   | `axlib` | `rlib` | `AxLib` | Axiom package archive (`.axlib`) bundling `lib.axrmeta` + per-CGU objects |

   *\*`wasm-module` and `wasm-reactor` are accepted only when `target.arch == Arch.Wasm32`; on non-WASM targets they fail with `AX_DRIVER_INVALID_ARTIFACT_KIND`.*
3. **Command & target compatibility checks (`AX_DRIVER_INVALID_ARTIFACT_KIND` vs. `AX_DRIVER_USAGE`, exit code 2):**
   - Any `--kind` or `axiom.toml` `kind` string outside `{exe, bin, obj, lib, staticlib, dll, cdylib, axlib, rlib, wasm-module, wasm-reactor}` fails immediately with `AX_DRIVER_INVALID_ARTIFACT_KIND` (`SPEC-26 AXS-WLIB-002, AXS-WLIB-050`).
   - `axiomc run` requires `ArtifactKind.Executable`; passing a recognized non-`Executable` `--kind` (`obj`, `lib`, `staticlib`, `dll`, `cdylib`, `axlib`, `rlib`, `wasm-module`, `wasm-reactor`, or `--emit=obj`) to `axiomc run` fails with `AX_DRIVER_USAGE` (`"'run' does not support '--kind <kind>'"`, exit code `2`, `SPEC-26 AXS-WLIB-002, AXS-WLIB-050`).
   - Requesting `ArtifactKind.DynLib` on a bare-metal target lacking a dynamic loader (`x86_64-none`, `aarch64-none`, `riscv64-none`), or `wasm-module`/`wasm-reactor` on a non-WASM target, fails with `AX_DRIVER_INVALID_ARTIFACT_KIND` (`data.kind`, `data.target = <triple>`). [0197 §23; tasks/0453 §194.10, §194.28; SPEC-26 AXS-WLIB-002, AXS-WLIB-050]

**AXS-ARTM-003 — Cross-Target Artifact Output Filename, Container & Companion File Matrix (`REQ-TGT-104`).**
When `-o <path>` is omitted, `axiomc` derives `<stem>` from `[package] name` in `axiom.toml` (with hyphens `-` normalized to `_` for library names where required by platform loader conventions) or the root source basename, and emits outputs in `target/<canonical-triple>/<profile>/` (`SPEC-88 AXS-XCMP-009`) according to the target matrix:

| Target Family / Triples | `exe` (`Executable`) | `obj` (`Object`) | `lib` / `staticlib` (`StaticLib`) | `dll` / `cdylib` (`DynLib`) | `axlib` (`AxLib`) |
|---|---|---|---|---|---|
| **Windows PE/COFF**<br>`x86_64-windows`, `aarch64-windows` (`E16.12`) | `<stem>.exe` (`PE32+` `EXE`, `DYNAMIC_BASE`) | `<stem>.obj` (`COFF`) | `<stem>.lib` (`CoffAr`) | `<stem>.dll` (`PE32+` `DLL`) + `<stem>.lib` import lib (+ `--emit-def <stem>.def`) | `<stem>.axlib` (`CoffAr` + `lib.axrmeta`) |
| **Linux & RISC-V ELF64**<br>`x86_64-linux`, `aarch64-linux`, `riscv64-linux` | `<stem>` (`0755`; static `ET_EXEC` or `ET_DYN` `PIE`) | `<stem>.o` (`ELF64` `ET_REL`) | `lib<stem>.a` (`GnuAr`) | `lib<stem>.so` (`ELF64` `ET_DYN`, `DT_SONAME`) | `lib<stem>.axlib` (`GnuAr` + `lib.axrmeta`) |
| **Android Bionic ELF64**<br>`aarch64-android` (`16 KiB` pages) | `<stem>` (`0755`; `ET_DYN` `PIE`, `/system/bin/linker64`) | `<stem>.o` (`ELF64` `ET_REL`) | `lib<stem>.a` (`GnuAr`) | `lib<stem>.so` (`ET_DYN`, `DT_SONAME`, `.note.android.ident`) | `lib<stem>.axlib` (`GnuAr` + `lib.axrmeta`) |
| **macOS Mach-O 64**<br>`aarch64-macos`, `x86_64-macos` (`SPEC-90`) | `<stem>` (`0755`; `MH_EXECUTE`, ad-hoc `LC_CODE_SIGNATURE`) | `<stem>.o` (`MH_OBJECT`) | `lib<stem>.a` (`BsdAr`, `__.SYMDEF SORTED`) | `lib<stem>.dylib` (`MH_DYLIB`, `LC_ID_DYLIB`, ad-hoc codesign) | `lib<stem>.axlib` (`BsdAr` + `lib.axrmeta`) |
| **WebAssembly**<br>`wasm32-wasi`, `wasm32-freestanding` | `<stem>.wasm` (`\0asm` Command: exported `_start`) | `<stem>.wasm` (relocatable `linking` v2; `.o` if `-o *.o`) | `lib<stem>.a` (`GnuAr` of relocatable `.wasm`) | `<stem>.wasm` (`\0asm` Reactor: `_initialize` + `@export` + `memory`) | `lib<stem>.axlib` (`GnuAr` + `lib.axrmeta` + `.wasm`) |
| **UEFI PE32+**<br>`x86_64-uefi`, `aarch64-uefi` (`SPEC-52`) | `<stem>.efi` (`EFI_APPLICATION = 10`, `.reloc`) | `<stem>.obj` (`COFF`) | `<stem>.lib` (`CoffAr`) | `<stem>.efi` (`EFI_BOOT_SERVICE_DRIVER = 11` / `RUNTIME = 12`) | `<stem>.axlib` (`CoffAr` + `lib.axrmeta`) |
| **Bare-Metal Freestanding**<br>`<arch>-none` (`SPEC-52`, `SPEC-55`) | `<stem>.elf` (or `<stem>.bin` with `--format bin`) | `<stem>.o` (`ELF64` `ET_REL`) | `lib<stem>.a` (`GnuAr`) | *Rejected* (`AX_DRIVER_INVALID_ARTIFACT_KIND`) | `lib<stem>.axlib` (`GnuAr` + `lib.axrmeta`) |

When `-o <dir>/<custom_name>` overrides the output path on Windows `--kind dll`, the companion import library defaults to `<dir>/<custom_stem>.lib` unless `--implib <path>` is also supplied (`SPEC-26 AXS-WLIB-002`). [0197 §23–24; 0217 §32–35, §69–71; tasks/0453 §194.10, §194.36; tasks/0563 §304.3, §304.28, §304.42; SPEC-26 AXS-WLIB-002; SPEC-80 AXS-ELFS-035; SPEC-82 AXS-ELFD-004; SPEC-84 AXS-MACHO-001, AXS-MACHO-013, AXS-MACHO-019..021; SPEC-85 AXS-ANDR-002; SPEC-86 AXS-WASM-027..029; SPEC-88 AXS-XCMP-009]

**AXS-ARTM-004 — Semantic Distinction Between `StaticLib` (`lib`/`staticlib`), `AxLib` (`axlib`), and `DynLib` (`dll`/`cdylib`).**
1. **`StaticLib` (`--kind lib` / `staticlib`, `WORLD_OPEN`):** Packages compiled machine-code `.obj`/`.o`/`.wasm` members into a platform archive (`.lib` or `.a`) consumable by both Axiom's native linkers and foreign C/C++/Rust linkers (`0097 §27`, `0197 §24`, `tasks/0369 §10`). Uninstantiated generic functions cannot be invoked by foreign C callers; `@export` items expose stable C/platform ABI entry points (`SPEC-50`), while Axiom-internal `pub` non-generic symbols remain in the archive index for Axiom multi-archive links. When `--bundle-deps` is passed with `--kind staticlib`, reachable object members of upstream `axlib` dependencies (including `std.core`/`std.alloc` if referenced) are merged into the single self-contained `.a`/`.lib` for turnkey C consumption; by default (`--bundle-deps` omitted), only the current package's `CGU` objects are archived (`SPEC-26 AXS-WLIB-010`).
2. **`AxLib` (`--kind axlib`, `WORLD_OPEN` at build time, `WORLD_CLOSED` / `WORLD_PARTIAL` when linked into final consumer):** Axiom's native multi-package distribution unit (`T686`, `SPEC-24 AXS-ART-001, AXS-ART-010..014`). Bundles `lib.axrmeta` (full typed Axiom module interface, `TypeId` DAG, trait coherence records, capability/ownership/effect summaries, `const` payloads, and serialized `Verified MIR` templates for generics and `@inline` functions) alongside per-`CGU` relocatable objects containing `.axmeta` and `.axlto` sections. Downstream Axiom packages consume `axlib` with **zero source re-parsing** and full generic monomorphization + cross-package LTO.
3. **`DynLib` (`--kind dll` / `cdylib`, `WORLD_PARTIAL`):** Links a closed internal module graph (`internal` + `pub` items optimized and dead-stripped from the `@export` root set, `SPEC-75 AXS-LTO-004..005`) behind an explicit open-world binary ABI boundary (`SPEC-56 AXS-MOD-004`, `REQ-ABI-095`, `REQ-FFI-042`). Axiom v1 intentionally does **not** stabilize an implicit cross-compiler polymorphic Axiom dynamic ABI inside `cdylib` (Axiom-ABI hot-reload/plugin components belong to Epic `E20.7`, `SPEC-56 AXS-MOD-005`). Every `DynLib` links its own required `std` slices privately with hidden visibility and **never** introduces a mandatory `libaxiom-runtime.so`/`.dll`/`.dylib` dependency (`0197 §31–32 AELF-37`, `REQ-TGT-247`). [0097 §27; 0197 §23–25, §31–32; 0217 §54; tasks/0369 §10, §14–15, §20; SPEC-24 AXS-ART-001; SPEC-56 AXS-MOD-004..005; SPEC-75 AXS-LTO-004..005]

**AXS-ARTM-005 — Position-Independence (`CodeModel`) & Relocation Policy Across Artifact Kinds (`REQ-TGT-060`, `REQ-TGT-146`).**
Relocation requirements are represented explicitly in `ObjectFile` and `LinkIR` (`tasks/0518 §151 AMACHINE-71`, `REQ-TGT-060`), and `PIC`/`GOT`/`PLT` lowering is strictly target- and artifact-kind-governed (`tasks/0521 §156 AARM-52`, `REQ-TGT-146`, `tasks/0369 §13`):
1. **Linux & RISC-V ELF64 (`SPEC-80`, `SPEC-82`, `SPEC-83`, `SPEC-87`):** `--kind dll`/`cdylib` ALWAYS compiles with `CodeModel.PositionIndependent` (`PIC`), emitting PC-relative code + `GOT`/`PLT` indirection for external/preemptible symbols. `--kind lib`/`staticlib` and `--kind axlib` default to `CodeModel.PositionIndependent` (`PIC`) so archive members can be linked seamlessly into static `ET_EXEC`, `PIE`, or `.so` consumers without recompilation (`--relocation-model=static` overrides when pure static `ET_EXEC` codegen is desired). Any absolute text relocation (`R_X86_64_64`, `R_AARCH64_ABS64`, `R_RISCV_64`) in a read-only/executable segment of a `PIE` or `.so` link fails with `AX_LINK_TEXTREL_FORBIDDEN` (`SPEC-82 AXS-ELFD-018`).
2. **Android Bionic (`SPEC-85`) & macOS Mach-O (`SPEC-84`):** Position-independent code (`PIC`) is **unconditionally mandatory** across all `exe`, `obj`, `lib`, `dll`, and `axlib` artifacts; non-PIC relocations in `__TEXT` or `PF_X` segments fail with `AX_LINK_TEXTREL_FORBIDDEN`.
3. **Windows PE32+ (`SPEC-26`):** Uses RIP-relative / PC-relative addressing within the image plus `.reloc` (`IMAGE_REL_BASED_DIR64 = 10`) base relocation blocks and `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE | HIGH_ENTROPY_VA` for ASLR rebasing in both `.exe` and `.dll`; cross-DLL data imports load via `__imp_<name>` IAT slots (`SPEC-26 AXS-WLIB-031..032`).
4. **WebAssembly (`SPEC-86`):** Separates code and linear-memory address spaces; relocatable `.wasm` objects carry `R_WASM_FUNCTION_INDEX_LEB`, `R_WASM_TABLE_INDEX_*`, `R_WASM_MEMORY_ADDR_*`, and `R_WASM_GLOBAL_INDEX_*` entries resolved statically by `compiler/link/wasm` (`SPEC-86 AXS-WASM-027..028`). [0197 §10–16, §27; 0217 §52–53; tasks/0369 §8–9, §13; tasks/0518 §151 AMACHINE-71; tasks/0521 §156 AARM-52; SPEC-26 AXS-WLIB-023; SPEC-82 AXS-ELFD-006, AXS-ELFD-018; SPEC-84 AXS-MACHO-022]

**AXS-ARTM-006 — Four-Level Binary Visibility Lattice & Hidden-by-Default `cdylib` Isolation (`T687`, `T688`).**
Axiom enforces a uniform cross-target separation between source module visibility (`pub`) and binary dynamic export (`@export`, `0197 §3, §17–18`, `0217 §24, §40–41`, `tasks/0369 §15`, `SPEC-75 AXS-LTO-004`):

| Source Declaration | PE/COFF (`.obj` / `.dll`) | ELF64 (`.o` / `.so` / `PIE`) | Mach-O 64 (`.o` / `.dylib`) | WASM (`.wasm`) |
|---|---|---|---|---|
| Module-private (`fn`, `static`) | `IMAGE_SYM_CLASS_STATIC` (omitted from `.edata`) | `STB_LOCAL` in `.symtab`; omitted from `.dynsym` | Local (`!N_EXT`); omitted from export trie | `WASM_SYM_BINDING_LOCAL`; omitted from `Export` |
| Package-public (`pub fn`, `pub static` without `@export`) | `IMAGE_SYM_CLASS_EXTERNAL` in `.obj`/`.lib`; **omitted** from `.dll` `.edata` & import `.lib` | `STB_GLOBAL` + **`STV_HIDDEN (2)`** in `.o`; resolved directly without `PLT`/`GOT`; **omitted** from `.dynsym` | `N_SECT \| N_EXT \| N_PEXT` (`private_extern`) in `MH_DYLIB` link; **omitted** from `LC_DYLD_EXPORTS_TRIE` | `WASM_SYM_VISIBILITY_HIDDEN`; **omitted** from final `Export` section |
| Explicit ABI export (`@export`, `@export("name")`, `@jni_export`, `@wasm_export`) | `IMAGE_SYM_CLASS_EXTERNAL` + `.drectve`/`ExportFlag`; emitted in `.dll` `.edata` & companion `.lib` | `STB_GLOBAL` + **`STV_DEFAULT (0)`** (or `STV_PROTECTED (3)` via `@export(protected = true)`); emitted in `.dynsym` | `N_SECT \| N_EXT` (no `N_PEXT`); serialized into `LC_DYLD_EXPORTS_TRIE` with `_` prefix | `WASM_SYM_EXPORTED`; emitted in W3C Section 7 (`Export`) & GC root set |
| Foreign dynamic import (`extern "C"` + `@link("...")`) | `__imp_<name>` IAT slot in `.idata` | `SHN_UNDEF` `STB_GLOBAL` in `.dynsym` + `GOT`/`PLT` + `DT_NEEDED` | `N_UNDF \| N_EXT` + `DYLD_CHAINED_IMPORT` + `LC_LOAD_DYLIB` | W3C Section 2 (`Import` `(module, name)`) |

Consequently, in every `--kind dll` / `cdylib` output across PE `.dll`, ELF `.so`, Mach-O `.dylib`, and WASM reactor `.wasm`, **zero non-`@export` Axiom or `std` symbols ever leak into the binary's dynamic export table**, eliminating accidental ABI coupling and symbol interposition hazards (`0217 §40–41`, `T687`, `T688`). Applying `@export` to an uninstantiated generic item fails with `AX_FFI_GENERIC_EXPORT`; exposing a non-FFI-safe Axiom type across `extern "C"` `@export` without `@repr(C)`/`@repr(transparent)` fails with `AX_FFI_BAD_TYPE` (`SPEC-50 AXS-UNS-030..034`). [0197 §3, §17–18; 0217 §24, §40–41; tasks/0369 §15; SPEC-26 AXS-WLIB-004; SPEC-50 AXS-UNS-030..034; SPEC-82 AXS-ELFD-029; SPEC-84 AXS-MACHO-024; SPEC-86 AXS-WASM-023]

**AXS-ARTM-007 — Unified `-L`, `-l`, `@link(...)` & Dependency Kind Selection Order.**
1. **Source `@link` & CLI `-l` forms:** `@link("<name>")`, `@link("<name>", kind = "static" | "dylib" | "framework", weak = false | true)`, CLI `-L <dir>` / `-L<dir>`, `-l <name>` / `-l<name>`, and exact-filename `-l:<filename>` merge deterministically: explicit CLI libraries preserve left-to-right CLI order, followed by deduplicated `@link(...)` declarations in topological module order (`SPEC-26 AXS-WLIB-003`).
2. **Search path priority (`SPEC-88 AXS-XCMP-021..022`):** (1) user `-L <dir>` directories in CLI order -> (2) target workspace build directory `target/<triple>/<profile>/deps/` (for `axlib` / local libraries) -> (3) explicit `--target-sdk <dir>` / `--sysroot <dir>` library subdirectories -> (4) Axiom's built-in hermetic OS import stub catalog (`kernel32`/`ntdll`/`ws2_32`/`bcrypt` on Windows, `libc.so.6`/`libm.so.6` on Linux, `libSystem.B.dylib` on macOS, Bionic stubs on Android, `wasi_snapshot_preview1` on WASI). Host system paths (`/usr/lib`, `C:\Windows\System32`) are **never** probed implicitly during cross-compilation or `--hermetic` builds.
3. **Per-directory candidate probe order for `-l<name>` / `@link("<name>")`:**
   - If `kind = "static"` or `--static` is active: probes `lib<name>.a` (or `<name>.lib`, `lib<name>.lib` on Windows/UEFI) only.
   - Otherwise (default dynamic-capable mode):
     - **Windows:** `<dir>/<name>.lib` -> `<dir>/lib<name>.lib` -> `<dir>/<name>.a` -> `<dir>/lib<name>.a` (where `.lib` may be either an import library or static archive, `SPEC-26 AXS-WLIB-003`).
     - **Linux / Android / RISC-V:** `<dir>/lib<name>.so` (including GNU `GROUP`/`INPUT` ASCII stubs, `SPEC-82 AXS-ELFD-032`) -> `<dir>/lib<name>.a`.
     - **macOS:** `<dir>/lib<name>.tbd` -> `<dir>/lib<name>.dylib` -> `<dir>/lib<name>.a` (or `<dir>/<name>.framework/<name>.tbd` / `<name>` when `kind = "framework"`).
     - **WASM:** `<dir>/lib<name>.a` -> `<dir>/<name>.wasm` (relocatable object).
   - Failure to locate a library in all candidate paths emits `AX_LINK_LIBRARY_NOT_FOUND` (`data.library = <name>`). [0197 §5, §26; tasks/0453 §194.20–22; SPEC-26 AXS-WLIB-003; SPEC-82 AXS-ELFD-031..032; SPEC-84 AXS-MACHO-028; SPEC-88 AXS-XCMP-021..022]

---

## 2. Reproducible Static Archive Formats (`CoffAr`, `GnuAr`, `BsdAr`) & `axlib` Layout (`AXS-ARTM-008`..`014`)

**AXS-ARTM-008 — Unified `compiler/obj/archive_matrix` Producer & Common `!<arch>\n` Envelope (`T686`, `REQ-TGT-151`, `REQ-TGT-184`).**
1. **Common 8-byte magic & 60-byte ASCII member header (`0164 §24`, `0217 §19`, `tasks/0369 §10`):**
   `compiler/obj/archive_matrix` serializes every static library (`--kind lib` / `staticlib`), import library (`.lib`), and Axiom library (`--kind axlib`) as a self-contained standard archive beginning with the 8-byte ASCII signature `"!<arch>\n"` (`0x21 0x3C 0x61 0x72 0x63 0x68 0x3E 0x0A`), followed by 2-byte-aligned members prefixed by a 60-byte ASCII header:
   ```text
   Offset  Size  Field     Format (ASCII, space-padded right; never NUL-padded)
   0       16    ar_name   Variant-specific member identifier ("/", "//", "#1/<len>", "name/", etc.)
   16      12    ar_date   Decimal modification timestamp ("0           ")
   28      6     ar_uid    Decimal user ID ("0     ")
   34      6     ar_gid    Decimal group ID ("0     ")
   40      8     ar_mode   Octal file mode (per-format canonical string; AXS-ARTM-009)
   48      10    ar_size   Decimal payload byte count (includes "#1/<len>" name bytes in BsdAr)
   58      2     ar_fmag   Header trailer "`\n" (0x60 0x0A)
   ```
   Every member payload with an odd byte length (`ar_size % 2 == 1`) is followed by a single `'\n'` (`0x0A`) pad byte so the next 60-byte header always begins at an even file offset (`offset % 2 == 0`).
2. **Thin-archive rejection & malformed container diagnostics (`T686`):**
   - GNU thin archives (`"!<thin>\n"`, storing external filesystem paths rather than self-contained object payloads) break hermeticity and cross-host reproducibility (`SPEC-88 AXS-XCMP-008`); `compiler/link/archive_resolve` explicitly detects `"!<thin>\n"` and rejects it with `AX_LINK_THIN_ARCHIVE_UNSUPPORTED` (`data.archive = <path>`).
   - Any archive lacking `"!<arch>\n"`, having `ar_fmag != "\x60\n"`, non-decimal `ar_size`, odd member header alignment, or member/index offsets exceeding file bounds fails with `AX_LINK_BAD_ARCHIVE`. [0164 §24; 0185; 0217 §19, §72 ALINK-28; tasks/0369 §10; SPEC-26 AXS-WLIB-010, AXS-WLIB-012]

**AXS-ARTM-009 — Deterministic Zeroed Archive Metadata & Per-Format `ar_mode` Harmonization (`REQ-TGT-106`, `REQ-TGT-320`).**
To guarantee bit-for-bit identical `.lib`, `.a`, and `.axlib` bytes across repeated builds, parallel `--jobs N` schedules, and Windows/Linux/macOS hosts (`0164 §33`, `0217 §44–45 ALINK-50..51`, `tasks/0453 §194.42`, `tasks/0524 §112 ABACKEND-95`):
1. **Zeroed timestamps & ownership:** `archive_matrix` unconditionally writes `ar_date = "0           "`, `ar_uid = "0     "`, and `ar_gid = "0     "` on every pseudo-member and object/metadata member, ignoring host filesystem `mtime`/`uid`/`gid`.
2. **Canonical member ordering & normalized names:** Regular object members are ordered strictly by canonical topological `ModuleId` + ascending `CGU` partition index (or ascending lexicographical `(dll_name, export_symbol)` order for import libraries), with forward-slash-free basenames `<pkg>_<mod>.cgu<k>.<ext>` independent of host directory paths.
3. **Harmonized `ar_mode` across `SPEC-26`, `SPEC-80`, `SPEC-84`, and `SPEC-86`:**
   - `ArchiveFormat.CoffAr` (`SPEC-26 AXS-WLIB-010`, Windows/UEFI): writes `ar_mode = "0       "` (`"0"` + 7 spaces) on all linker (`/`), longname (`//`), `lib.axrmeta`, `.obj`, and short-import members.
   - `ArchiveFormat.GnuAr` (`SPEC-80 AXS-ELFS-029`, `SPEC-86 AXS-WASM-027`, Linux/Android/RISC-V/WASM): writes `ar_mode = "0       "` on pseudo-members (`"/               "`, `"/SYM64/         "`, `"//              "`) and `ar_mode = "100644  "` (octal regular file `0100644`, matching `llvm-ar -D` / GNU `ar -D`) on `lib.axrmeta` and `.o`/`.wasm` members (`"0       "` emitted by Stage-1 `ElfArWriter` per `SPEC-80 AXS-ELFS-029` is accepted identically by `archive_resolve`).
   - `ArchiveFormat.BsdAr` (`SPEC-84 AXS-MACHO-019`, macOS Darwin): writes `ar_mode = "100644  "` on `"__.SYMDEF SORTED"`, `"__.SYMDEF_64"`, `lib.axrmeta`, and `.o` members. [0164 §33; 0217 §44–45 ALINK-50..51; tasks/0518 §151 AMACHINE-117; tasks/0524 §112 ABACKEND-95; SPEC-26 AXS-WLIB-010; SPEC-80 AXS-ELFS-029; SPEC-84 AXS-MACHO-019; SPEC-86 AXS-WASM-027]

**AXS-ARTM-010 — GNU / System V Archive Format (`ArchiveFormat.GnuAr`) & 64-Bit `/SYM64/` Fallback (`.a` on ELF & WASM).**
1. **Symbol directory (`"/"` vs `"/SYM64/"`):**
   - When all member header file offsets are $< 2^{32}$ (`4 GiB`), the first member has `ar_name = "/               "` and payload `[num_syms: u32be][offsets: [num_syms]u32be][strings: [num_syms]CString]`, indexing every defined external (`STB_GLOBAL` / `STB_WEAK`, including `STV_HIDDEN` for intra-static-link resolution, and WASM non-local defined symbols) symbol in member order (ties broken by ascending ASCII symbol name).
   - When any member header offset is $\ge 2^{32}$, `archive_matrix` automatically emits `ar_name = "/SYM64/         "` with 64-bit big-endian integers `[num_syms: u64be][offsets: [num_syms]u64be][strings: [num_syms]CString]` (`archive_resolve` parses both `"/"` and `"/SYM64/"`).
2. **Extended filenames (`"//"`):**
   - Short member names ($\le 15$ ASCII bytes without spaces) are stored inline as `"<name>/"` padded with spaces to 16 bytes.
   - If $\ge 1$ member name exceeds 15 bytes, `"//              "` is emitted immediately after the symbol directory, storing concatenated `"<full_name>/\n"` entries; each long-named member header sets `ar_name = "/<dec_byte_offset>"` pointing into `"//"`'s payload. [0197 §24–25; tasks/0369 §10; SPEC-80 AXS-ELFS-029; SPEC-86 AXS-WASM-027]

**AXS-ARTM-011 — Microsoft PE/COFF Archive Format (`ArchiveFormat.CoffAr`, `.lib` on Windows & UEFI).**
Per `SPEC-26 AXS-WLIB-010..011`, `archive_matrix` emits `CoffAr` archives with complete Microsoft `link.exe` / `lib.exe` and GNU `dlltool` / `lld-link` compatibility:
1. **First Linker Member (`"/               "`):** `[num_syms: u32be][member_offsets: [num_syms]u32be][strings: [num_syms]CString]` in member order for legacy `ar` / binutils tools.
2. **Second Linker Member (`"/               "`):** `[num_members: u32le][member_offsets: [num_members]u32le][num_syms: u32le][sym_member_indices: [num_syms]u16le][sorted_strings: [num_syms]CString]`, where `sym_member_indices` are 1-based indices into `member_offsets` and `sorted_strings` are strictly sorted in ascending ASCII (`strcmp`) order for $O(\log N)$ binary search.
3. **Longnames Member (`"//              "`):** NUL-terminated (`"<full_name>\0"`) string pool emitted whenever any member name exceeds 15 bytes (or contains `/`), referenced via `"/<dec_byte_offset>"` in `ar_name`.
4. **Payload members:** Regular COFF `.obj` files (`Machine = 0x8664` on `x86_64` or `0xAA64` on `aarch64`) and/or 20-byte `IMPORT_OBJECT_HEADER` (`Sig1 = 0x0000`, `Sig2 = 0xFFFF`) short-import records (`AXS-ARTM-017`). [0185; SPEC-26 AXS-WLIB-010..011]

**AXS-ARTM-012 — BSD 4.4 / Darwin Archive Format (`ArchiveFormat.BsdAr`, `.a` on macOS).**
Per `SPEC-84 AXS-MACHO-019`, Darwin static archives (`aarch64-macos` and `x86_64-macos` slices) use BSD 4.4 `ar` conventions required by Apple `ld` and `ranlib`:
1. **In-place `#1/<byte_len>` extended filenames & 8-byte `MH_OBJECT` payload alignment:**
   - Any member name $> 16$ bytes or containing spaces (including `"__.SYMDEF SORTED"` itself, `20` bytes padded) sets `ar_name = "#1/<byte_len>"` (space-padded to 16 bytes) and prepends `<byte_len>` bytes of the NUL-padded filename immediately before the member payload (`ar_size = byte_len + payload_len`).
   - For every `MH_OBJECT` member at header file offset `hdr_off`, `archive_matrix` chooses `byte_len = align_up(hdr_off + 60 + len(name) + 1, 8) - (hdr_off + 60)` (for example, at `hdr_off = 8`, `8 + 60 = 68`, so `byte_len = 20` places `"__.SYMDEF SORTED"`'s payload at offset `88`, and every embedded `MH_OBJECT` `mach_header_64` begins on an exact **8-byte** file boundary!).
2. **Sorted `ranlib` directory (`__.SYMDEF SORTED` & `__.SYMDEF_64`):**
   - The first member is `"__.SYMDEF SORTED"` (`#1/20` + `"__.SYMDEF SORTED\0\0\0\0"`): `[ranlib_byte_len: u32le][entries: [N](ran_strx: u32le, ran_off: u32le)][strtab_byte_len: u32le][strings]`, where `ran_off` is the file offset of the defining member's 60-byte `ar` header and `entries` are sorted lexicographically by Mach-O symbol name (indexing all defined `N_EXT` symbols, including `N_WEAK_DEF` and `N_PEXT | N_EXT`, while excluding `N_UNDF` imports).
   - If any member offset $\ge 2^{32}$, `archive_matrix` emits `"__.SYMDEF_64 SORTED"` using 64-bit `(ran_strx: u64le, ran_off: u64le)` entries and `u64le` table byte counts; `archive_resolve` accepts `"__.SYMDEF"`, `"__.SYMDEF SORTED"`, `"__.SYMDEF_64"`, and `"__.SYMDEF_64 SORTED"`. [0196; 0217 §19, §33; SPEC-84 AXS-MACHO-019]

**AXS-ARTM-013 — Axiom Native Library Archive (`ArtifactKind.AxLib`, `.axlib` & `lib.axrmeta` Member Contract, `T686`).**
An Axiom native library (`--kind axlib`) is a single self-contained target-native `!<arch>\n` archive (`<stem>.axlib` on Windows/UEFI using `CoffAr`; `lib<stem>.axlib` on ELF/WASM using `GnuAr` and on Darwin using `BsdAr`) with the following exact member layout:
1. **Archive symbol directory** (`/` in `GnuAr`/`CoffAr`, `__.SYMDEF SORTED` in `BsdAr`) and optional longname table (`//` in `GnuAr`/`CoffAr`), indexing only the compiled machine/WASM object members (`2..M`).
2. **Interface metadata member `lib.axrmeta` (first regular member):**
   - Contains a complete `SPEC-24 AXS-ART-002..005, AXS-ART-010..014` binary `.axmi` container (`magic = "AXMI0001"`, `format_family = 1`, 64-byte `ArtifactHeader` carrying `target_fingerprint`, `interface_fingerprint`, and BLAKE3-128 `content_hash`; any magic or `format_family` mismatch fails immediately with `AX_LINK_BAD_ARTIFACT`) whose `.axmi` payload sections store canonical `PackageName`/`PackageId` (`SemanticKey`), `AbiFingerprint` (`SPEC-24 AXS-ART-014, AXS-ART-023`), all `pub` module declarations of the package, canonical `TypeId` DAG, trait implementations/coherence summaries, interprocedural capability/ownership/effect/panic summaries, evaluated `const` payloads, and serialized `Verified MIR` templates for generic items and `@inline` functions.
   - Because `lib.axrmeta` exports zero native object symbols, standard host `ar t` / `llvm-ar t` lists it cleanly and system linkers skip it harmlessly during demand-driven symbol extraction.
3. **Compiled `CGU` object members (`<pkg>_cgu0.<obj_ext> .. <pkg>_cguK.<obj_ext>`):**
   - Hold compiled machine/WASM code and data for all non-generic items and pre-instantiated package specializations, plus embedded non-alloc `.axmeta` and `.axlto` sections (`AXS-ARTM-028`) for link-time optimization and rich demangled diagnostics. [tasks/0453 §194.28, §194.31; SPEC-24 AXS-ART-001..005, AXS-ART-010..014, AXS-ART-023]

**AXS-ARTM-014 — Cross-Package `axlib` Consumption, Diamond Dependency Coherence & `AX_LINK_AXLIB_PACKAGE_CONFLICT`.**
1. **Compile-time ingestion:** When package $P$ depends on an `axlib` library $L$, `CompilerDB` maps `lib.axrmeta` from $L$, validates its `"AXMI0001"` magic, `format_family = 1`, and BLAKE3-128 `content_hash` (`AX_LINK_BAD_ARTIFACT`), `schema_version` (`AX_LINK_ARTIFACT_SCHEMA_MISMATCH`), and `target_fingerprint` (`AX_LINK_ARTIFACT_TARGET_MISMATCH`), and populates semantic tables without reading $L$'s `.ax` source files (`SPEC-24 AXS-ART-002, AXS-ART-010`). Generic instantiations of $L$'s templates requested by $P$ are monomorphized into $P$'s own `CGU`s in `COMDAT` groups keyed by canonical `GenericInstanceId` (`tasks/0369 §12`, `SPEC-27 AXS-LNK-012`).
2. **Diamond dependency coherence (`T688`):** In a diamond dependency graph ($P \to A \to D$ and $P \to B \to D$), all resolved `axlib` inputs share a global `(PackageName -> (PackageId, InterfaceFingerprint, ArchivePath))` registry:
   - If $A$ and $B$ reference the exact same `D.axlib` (`InterfaceFingerprint` equal), `D.axlib` is loaded once and passed once to `archive_resolve`.
   - If two distinct `.axlib` files on the link line claim the same `PackageName` with differing `InterfaceFingerprint` or `AbiFingerprint` (or if an `.axlib` and a bundled `staticlib` define conflicting package metadata for $D$), compilation/linking fails deterministically with `AX_LINK_AXLIB_PACKAGE_CONFLICT` (`data.package`, `data.first_artifact`, `data.second_artifact`) before machine linking, preventing silent ODR/layout corruption. [0217 §22–23; tasks/0369 §12; tasks/0453 §194.28; SPEC-24 AXS-ART-010..014; SPEC-27 AXS-LNK-012]

---

## 3. Cross-Target Dynamic Library Matrix (`PE .dll`, `ELF .so`, `Mach-O .dylib`, `WASM Reactor`) (`AXS-ARTM-015`..`024`)

### 3.1 Windows PE32+ `.dll`, Module-Definition (`.def`) Files & Import Libraries (`T751`, `T687`)

**AXS-ARTM-015 — PE32+ `.dll` Image Contract, Deterministic Init & Base Relocations (`SPEC-26 AXS-WLIB-020..023`).**
1. **Header & ASLR relocations:** `PeImageWriter` (`compiler/link/dynlib_matrix`) emits `PE32+` (`Magic = 0x020B`) DLLs with `Characteristics |= IMAGE_FILE_EXECUTABLE_IMAGE (0x0002) | IMAGE_FILE_LARGE_ADDRESS_AWARE (0x0020) | IMAGE_FILE_DLL (0x2000)`, default `ImageBase = 0x0000_0001_8000_0000`, `DllCharacteristics = DYNAMIC_BASE (0x0040) | HIGH_ENTROPY_VA (0x0020) | NX_COMPAT (0x0100)`, zeroed `TimeDateStamp = 0`, `.reloc` (`DataDirectory[5]`) containing 4 KiB `IMAGE_BASE_RELOCATION` blocks (`IMAGE_REL_BASED_DIR64 = 10`, padded with `IMAGE_REL_BASED_ABSOLUTE = 0`), and `.pdata`/`.xdata` unwind tables (`tasks/0563 §304.14–20`).
2. **`DllMain`-free fast path vs. deterministic `_DllMainCRTStartup`:**
   - When the DLL has zero `SPEC-56` module-relative bindings (`@at(image("...") + off)`) and zero explicit user `@entry` hooks, `AddressOfEntryPoint` MAY be set to `0` (or a trivial `mov eax, 1; ret` stub) with zero OS loader-lock work (`SPEC-52 AXS-FRE-004`: all Axiom `static` items are constant-initialized in `.data`/`.rdata`, never running arbitrary user code under the Windows loader lock).
   - When `SPEC-56` module-relative bindings or an explicit `@entry fn dll_entry(hinst: *mut u8, reason: u32, reserved: *mut u8) -> i32` exist, `_DllMainCRTStartup` runs `__ax_resolve_module_bindings()` on `DLL_PROCESS_ATTACH (1)` and returns `0` (`FALSE`) immediately on missing-module failure (`ADR-0001 §5–6`, `SPEC-26 AXS-WLIB-022`, `SPEC-56 AXS-MOD-012`).
3. **`.edata` Export Directory (`DataDirectory[0]`):** Sorts named exports strictly in ascending ASCII (`strcmp`) order across `AddressOfNames` and `AddressOfNameOrdinals`, assigns dense 1-based ordinals (`OrdinalBase = min_ordinal`, defaulting to `1`), and records function/data RVAs (or forwarder ASCII string RVAs inside `[ExportDirRVA, ExportDirRVA + ExportDirSize)`) in `AddressOfFunctions` (`tasks/0563 §304.18`, `SPEC-26 AXS-WLIB-021`). [0186; 0187; tasks/0563 §304.14–20; ADR-0001 §5–6; SPEC-26 AXS-WLIB-020..023; SPEC-56 AXS-MOD-012]

**AXS-ARTM-016 — Windows `.def` Module-Definition Grammar, Consumption (`--def`) & Generation (`--emit-def`, `T687`).**
`compiler/obj/def_import` implements deterministic parsing (`--def <file.def>`) and canonical emission (`--emit-def <file.def>`) of Windows module-definition files:
1. **Supported `.def` EBNF grammar (line comments start with `;`):**
   ```text
   DefFile    = [ "LIBRARY" , [ ModuleName ] , [ "BASE" , "=" , IntLit ] ] ,
                "EXPORTS" , { ExportSpec } ;
   ExportSpec = ExtIdent , [ "=" , ( IntIdent | ForwardTarget ) ] ,
                [ "@" , OrdinalInt , [ "NONAME" ] ] , [ "DATA" ] , [ "PRIVATE" ] ;
   ForwardTarget = DllStem , "." , ( TargetIdent | "#" , OrdinalInt ) ;
   ```
2. **Semantics & merging with `@export`:**
   - Explicit `@export` / `@export("ExtName")` items in Axiom source and `ExportSpec` entries in `--def <file.def>` merge into one unified export set:
     - `ExtName = IntIdent` exports the internal Axiom/FFI symbol `IntIdent` under public DLL name `ExtName` (`AX_LINK_UNDEFINED_SYMBOL` if `IntIdent` does not exist in the linked graph).
     - `ExtName = OTHER.Bar` (or `OTHER.#42`) emits a **forwarded export**: `AddressOfFunctions[slot]` points to the NUL-terminated ASCII string `"OTHER.Bar"` stored inside `.edata`, instructing the Windows PE loader to resolve `Bar` from `OTHER.dll` at load time without code thunks.
     - `@<ordinal>` pins 1-based export ordinal `ordinal` ($1 \le \text{ordinal} \le 65535$); `NONAME` (legal **only** when `@<ordinal>` is present) omits `ExtName` from `.edata`'s `AddressOfNames` while still recording it by ordinal in the companion `.lib` (`IMPORT_ORDINAL`). Unpinned exports receive the lowest unused ordinals $\ge \text{OrdinalBase}$ in ascending `ExtName` order.
     - `DATA` marks a global variable export (`IMPORT_DATA` in the companion `.lib`, requiring `__imp_<ExtName>` indirection in callers); `PRIVATE` emits the export in `.dll` `.edata` (for `GetProcAddress`) while **excluding** it from the companion import `.lib`.
   - `--emit-def <path>` writes normalized LF-only UTF-8 `.def` text (`LIBRARY "<dll_name>"` followed by sorted `EXPORTS` entries) deterministically.
   - Syntax errors, ordinals outside `[1, 65535]`, `NONAME` without `@<ordinal>`, or conflicting `LIBRARY` names fail with `AX_LINK_INVALID_DEF_FILE`; duplicate export names or duplicate pinned ordinals fail with `AX_LINK_DUPLICATE_EXPORT`. [0186; 0187; tasks/0563 §304.18; SPEC-26 AXS-WLIB-021, AXS-WLIB-030]

**AXS-ARTM-017 — COFF Short-Import & Traditional Import `.lib` Producer/Consumer & `__imp_` Cross-Linking (`T751`, `T687`).**
1. **Producer (`compiler/obj/def_import`):** Emits a deterministic `CoffAr` import library containing one 20-byte `IMPORT_OBJECT_HEADER` (`Sig1 = 0x0000`, `Sig2 = 0xFFFF`, `Version = 0`, `Machine = 0x8664 | 0xAA64`, `TimeDateStamp = 0`, `Ordinal/Hint`, `Type = IMPORT_CODE (0) | IMPORT_DATA (1) | IMPORT_CONST (2)`, `NameType = IMPORT_ORDINAL (0) | IMPORT_NAME (1)`) followed by `"<ext_sym>\0<dll_filename>\0"` for every non-`PRIVATE` export (`SPEC-26 AXS-WLIB-030`).
2. **Consumer & `ADR-0034` §4 (`OI-07b`) `__imp_` contract:** `compiler/link` ingests **both** short-import (`Sig1=0, Sig2=0xFFFF`) `.lib` archives and traditional Microsoft/GNU `dlltool` 3-object long-import `.lib` archives (`__IMPORT_DESCRIPTOR_<dll>`, `__NULL_IMPORT_DESCRIPTOR`, `\x7f<dll>_NULL_THUNK_DATA` + `.idata$2..$7` sections). In `--kind obj` / `--emit=obj`, `extern` DLL functions and `DATA` globals reference `__imp_<name>` (`R_X86_64_GOTPCREL` / RIP-relative `[rip + __imp_<name>]` or `ARM64_IMAGE_REL_PAGE21/OFF12`), and the PE linker synthesizes 6-byte `jmp qword ptr [rip + __imp_<name>]` (`FF 25 disp32`) thunks when direct `CALL rel32` sites resolve to an import (`SPEC-26 AXS-WLIB-031..032`). [0187; ADR-0034 §4; SPEC-26 AXS-WLIB-030..032]

### 3.2 Linux, Android & RISC-V ELF64 Shared Objects (`.so`) & GNU Symbol Versioning (`T687`)

**AXS-ARTM-018 — ELF64 `ET_DYN` Shared Object Matrix Across `x86_64-linux`, `aarch64-linux`, `riscv64-linux` & `aarch64-android`.**
`compiler/link/dynlib_matrix` emits `ELFCLASS64` `ELFDATA2LSB` `e_type = ET_DYN (3)` shared libraries (`lib<stem>.so`) across `EM_X86_64 (62)`, `EM_AARCH64 (183)`, and `EM_RISCV (243)` (`0197 §1–5, §23`, `tasks/0563 §304.7–13`, `SPEC-82`, `SPEC-83`, `SPEC-85`, `SPEC-87`):
1. **Shared-object header & segments:** `e_entry = 0`, **no** `PT_INTERP`, strict W^X `PT_LOAD` segments (`PF_R`, `PF_R | PF_X`, `PF_R | PF_W`) aligned to `0x1000` (`4 KiB`) on `x86_64-linux`/`riscv64-linux`, `0x10000` (`64 KiB`, compatible with both 4 KiB and 64 KiB kernels) or `0x1000` per `TargetDesc` on `aarch64-linux`, and mandatory **`0x4000` (`16 KiB`)** on `aarch64-android` (`SPEC-85 AXS-ANDR-010..012`, alongside 152-byte `.note.android.ident`), plus Full RELRO (`PT_GNU_RELRO` + `DT_BIND_NOW` / `DF_1_NOW`) and non-executable `PT_GNU_STACK` (`PF_R | PF_W`).
2. **`DT_SONAME`, `DT_NEEDED` & `DT_RUNPATH`:**
   - `.dynamic` always sets `DT_SONAME (14)` to `"lib<stem>.so"` or explicit `--soname <name>` (`AX_LINK_INVALID_DYLIB_VERSION` if empty or containing NUL).
   - Each consumed `.so` records one `DT_NEEDED (1)` entry matching its `DT_SONAME` (never guessed from symbol names, `0197 §5`).
   - Passing `--rpath <dir>` (repeatable, joined by `:`) emits `DT_RUNPATH (29)` (never deprecated `DT_RPATH = 15`); if any `<dir>` contains `$ORIGIN` or `${ORIGIN}`, `DT_FLAGS (30)` sets `DF_ORIGIN (0x1)` and `DT_FLAGS_1 (0x6ffffffb)` sets `DF_1_ORIGIN (0x80)`. [0197 §5, §15, §23, §26; tasks/0563 §304.7–13; SPEC-82 AXS-ELFD-004, AXS-ELFD-027; SPEC-85 AXS-ANDR-010..012]

**AXS-ARTM-019 — GNU Symbol Versioning Binary Layout (`.gnu.version`, `.gnu.version_d`, `.gnu.version_r`, `T687`).**
To support both consuming versioned system libraries (`glibc` `GLIBC_2.2.5`/`GLIBC_2.34`, Bionic `LIBC`) and publishing version-stable Axiom `cdylib` shared objects (`0197 §19`, `SPEC-82 AXS-ELFD-030`):
1. **`.gnu.version` (`SHT_GNU_versym = 0x6fffffff`, `sh_entsize = 2`, `sh_link = .dynsym`, `DT_VERSYM = 0x6ffffff0`):**
   Contains exact `N = len(.dynsym)` little-endian `u16` entries: `0` (`VER_NDX_LOCAL`) for index `0` (`STN_UNDEF`) and local symbols; `1` (`VER_NDX_GLOBAL`) for unversioned global exports/imports; `v_idx` ($2 \le v\_idx < 0x8000$) for default versioned symbols (`sym@@VER`); and `v_idx | 0x8000` (`VERSYM_HIDDEN`) for non-default historical compatibility versions (`sym@VER_OLD`).
2. **`.gnu.version_d` (`SHT_GNU_verdef = 0x6ffffffd`, `sh_link = .dynstr`, `DT_VERDEF = 0x6ffffffc`, `DT_VERDEFNUM = 0x6ffffffd`):**
   Emitted whenever a `.so` defines $\ge 1$ version node:
   - Entry `0` (`vd_ndx = 1`, `vd_flags = VER_FLG_BASE = 0x1`, `vd_cnt = 1`) always records the library's `DT_SONAME` string (`vd_hash = sysv_elf_hash(soname)`).
   - Each user version node $k \ge 2$ emits a 20-byte `Elf64_Verdef { vd_version: 1u16, vd_flags: 0u16, vd_ndx: k as u16, vd_cnt: (1 + has_parent) as u16, vd_hash: sysv_elf_hash(ver_name), vd_aux: 20u32, vd_next: next_off }` followed by 8-byte `Elf64_Verdaux { vda_name: dynstr_off(ver_name), vda_next }` (plus a second `Elf64_Verdaux` naming the parent version node when version inheritance is declared).
3. **`.gnu.version_r` (`SHT_GNU_verneed = 0x6ffffffe`, `sh_link = .dynstr`, `DT_VERNEED = 0x6ffffffe`, `DT_VERNEEDNUM = 0x6fffffff`):**
   Groups imported versioned symbols by `DT_NEEDED` `vn_file` (`16`-byte `Elf64_Verneed { vn_version: 1, vn_cnt, vn_file, vn_aux: 16, vn_next }`) followed by `16`-byte `Elf64_Vernaux { vna_hash: sysv_elf_hash(ver_name), vna_flags: 0, vna_other: v_idx, vna_name, vna_next }` records assigning distinct `v_idx >= 2` slots referenced from `.gnu.version`. [0197 §19; SPEC-82 AXS-ELFD-027, AXS-ELFD-030]

**AXS-ARTM-020 — ELF Version Script (`--version-script`) & `@export` Version Metadata Contract (`T687`).**
Versioned ELF exports may be declared either via `--version-script <file.ver>` or via optional `key = value` arguments on `@export` (`SPEC-02 AXS-GRM-024`, preserving Core grammar purity per `0197 §19`):
1. **Attribute form:** `@export(name = "ax_compress", version = "AXZ_2.0", default = true)` (defaulting `default = true` -> `ax_compress@@AXZ_2.0`; `default = false` -> `ax_compress@AXZ_1.0` with `VERSYM_HIDDEN = 0x8000`, allowing two distinct internal Axiom functions `compress_v1` and `compress_v2` to export `ax_compress@AXZ_1.0` and `ax_compress@@AXZ_2.0` simultaneously in the same `.so`!).
2. **Version script grammar (`--version-script <path>`):**
   ```text
   VersionScript = { VersionNode } ;
   VersionNode   = [ VerIdent ] , "{" ,
                   [ "global" , ":" , { SymPattern , ";" } ] ,
                   [ "local"  , ":" , { ( SymPattern | "*" ) , ";" } ] ,
                   "}" , [ ParentVerIdent ] , ";" ;
   ```
   - `local: *;` matches Axiom's default `STV_HIDDEN` non-export rule (`AXS-ARTM-006`); any symbol listed under `local:` is demoted to `STB_LOCAL` / omitted from `.dynsym` even if marked `@export`.
   - Duplicate `VerIdent` nodes, cyclic or undefined `ParentVerIdent` references, multiple default (`@@`) bindings for the same `(symbol)` name, or syntax errors emit `AX_LINK_INVALID_VERSION_SCRIPT`. [0197 §19; SPEC-02 AXS-GRM-024; SPEC-82 AXS-ELFD-030]

### 3.3 macOS Mach-O 64 Dynamic Libraries (`.dylib`), Install Names, Two-Level Namespace & `.tbd` (`T687`)

**AXS-ARTM-021 — Mach-O `MH_DYLIB` Header, `LC_ID_DYLIB`, Version Triples & `LC_RPATH` (`T687`).**
`compiler/link/dynlib_matrix` emits 64-bit Darwin dynamic libraries (`lib<stem>.dylib`, `magic = MH_MAGIC_64 = 0xFEEDFACF`, `filetype = MH_DYLIB = 0x6`, `SPEC-84 AXS-MACHO-001, AXS-MACHO-013, AXS-MACHO-020..021`):
1. **Header flags:** `flags = MH_NOUNDEFS (0x1) | MH_DYLDLINK (0x4) | MH_TWOLEVEL (0x80)`, plus `MH_NO_REEXPORTED_DYLIBS (0x0010_0000)` **iff** zero `LC_REEXPORT_DYLIB` commands are present (`__PAGEZERO` and `LC_MAIN` are omitted; `__TEXT.vmaddr = 0x0`).
2. **`LC_ID_DYLIB (0x0D)` & `@rpath` / `@loader_path` / `@executable_path` install names:**
   - Every `MH_DYLIB` emits exactly one `LC_ID_DYLIB` load command (`dylib_command` padded with NULs to an 8-byte `cmdsize` multiple, `timestamp = 2` deterministic Apple static-linker constant).
   - `install_name` defaults to `"@rpath/lib<stem>.dylib"` and is overridable via `--install-name <name>`, supporting `"@rpath/..."`, `"@loader_path/..."`, `"@executable_path/..."`, and absolute framework/library paths.
3. **Packed `X.Y.Z` version triples (`current_version` & `compatibility_version`):**
   - `--current-version X[.Y[.Z]]` (default `1.0.0` -> `0x0001_0000`) and `--compatibility-version X[.Y[.Z]]` (default `1.0.0` -> `0x0001_0000`) pack into `u32` as `((X as u32) << 16) | ((Y as u32) << 8) | (Z as u32)`.
   - Any component with $X > 65535$, $Y > 255$, $Z > 255$, non-decimal syntax, `compatibility_version > current_version`, or an empty/NUL-containing `--install-name` or `--rpath` fails with `AX_LINK_INVALID_DYLIB_VERSION` (`data.flag`, `data.value`).
4. **`LC_RPATH (0x8000001C)`:** Each `--rpath <dir>` (deduplicated in CLI order) emits an 8-byte-aligned `rpath_command` (`"@executable_path/../Frameworks"`, `"@loader_path"`, etc.) in both `MH_EXECUTE` and `MH_DYLIB`. [0196; 0217 §33; tasks/0563 §304.21–24; SPEC-84 AXS-MACHO-001, AXS-MACHO-013, AXS-MACHO-020..021]

**AXS-ARTM-022 — Mach-O Two-Level Namespace, `LC_LOAD_DYLIB`, `LC_LOAD_WEAK_DYLIB`, `LC_REEXPORT_DYLIB` & `.tbd` (`T687`).**
1. **Two-level namespace binding (`MH_TWOLEVEL`):** Every imported external symbol resolved against a consumed `.dylib` or `.tbd` stub records the exact 1-based dylib ordinal (`lib_ordinal = 1..K` in load-command order; `BIND_SPECIAL_DYLIB_FLAT_LOOKUP = -2` is never emitted unless `--flat-namespace` is explicitly passed) inside `LC_DYLD_CHAINED_FIXUPS` (`DYLD_CHAINED_IMPORT`), preventing accidental cross-dylib symbol hijacking at runtime (`0217 §40`).
2. **Dependent, weak & re-exported dylib load commands:**
   - Standard dynamic dependencies emit `LC_LOAD_DYLIB (0x0C)` copying the provider's `LC_ID_DYLIB` `install_name`, `current_version`, and `compatibility_version` (`timestamp = 2`).
   - Weak dependencies (`@link("foo", weak = true)` or `-weak-l<name>`) emit `LC_LOAD_WEAK_DYLIB (0x80000018)` and set `weak_import = 1` on their `DYLD_CHAINED_IMPORT` entries so `dyld` binds missing symbols to `0x0` rather than aborting at launch (`tasks/0563 §304.24`).
   - Umbrella re-exports (`--reexport-l<name>` or `--reexport-library <path>`) emit `LC_REEXPORT_DYLIB (0x8000001F)`, clear `MH_NO_REEXPORTED_DYLIBS` in `mach_header_64.flags`, and (when re-exporting individual aliased symbols via export lists) emit `EXPORT_SYMBOL_FLAGS_REEXPORT (0x08)` entries in `LC_DYLD_EXPORTS_TRIE` (`AXS-ARTM-016` equivalent on Darwin).
3. **`.tbd` consumption & ad-hoc codesign:** `dynlib_matrix` consumes both thin/Fat `MH_DYLIB` binaries and Apple Text-Based Stubs (`.tbd` v3/v4, `SPEC-84 AXS-MACHO-028`), and signs every emitted `MH_DYLIB` at EOF with a deterministic SHA-256 ad-hoc `LC_CODE_SIGNATURE` (`execSegFlags = 0x0`, `SPEC-84 AXS-MACHO-025`). [0196; 0217 §33–34, §40; tasks/0563 §304.24–25; SPEC-84 AXS-MACHO-024..025, AXS-MACHO-028]

### 3.4 WebAssembly Command (`_start`) vs. Reactor (`_initialize`) Modules (`T687`, `T688`)

**AXS-ARTM-023 — WASM Command (`--kind exe`) vs. Reactor (`--kind dll` / `cdylib` / `wasm-module`) Contract (`REQ-TGT-245`, `REQ-TGT-246`, `REQ-TGT-247`).**
On `wasm32-wasi` and `wasm32-freestanding` (`SPEC-86 AXS-WASM-023, AXS-WASM-028..029`, `tasks/0523 §155 AWASM-56..58`, `tasks/0563 §304.26–27`):
1. **Command module (`--kind exe` / `bin`):** Represents a single-invocation process. Synthesizes exported `_start () -> ()` (initializing `$__stack_pointer`, preopened WASI capabilities on `wasm32-wasi`, calling `main`, and terminating via `proc_exit`), exports linear `"memory"` (unless `--import-memory`), omits W3C Section 8 (`Start`), and treats `_start` + any explicit `@export`/`@wasm_export` items as GC roots. If user code explicitly exports `_initialize` in `--kind exe`, linking fails with `AX_LINK_WASM_ENTRY_CONFLICT`.
2. **Reactor / library module (`--kind dll` / `cdylib` / `wasm-module` / `wasm-reactor`):** Represents a persistent, host-driven library instance whose exported functions may be called repeatedly after instantiation:
   - **Zero `main` / `_start`:** Does not require `fn main()`; if user code exports `_start` in reactor mode, linking fails with `AX_LINK_WASM_ENTRY_CONFLICT`.
   - **Synthesized single-shot `_initialize () -> ()`:** `compiler/link/wasm` synthesizes exported `"_initialize"` (`() -> ()`) guarded by a module-internal `mut i32` global `$__axiom_init_state = 0`: on the first call, it sets `$__axiom_init_state = 1`, runs `__wasm_call_ctors` / WASI descriptor discovery (on `wasm32-wasi`) and any `@entry` reactor init hook; if called a second time (`$__axiom_init_state != 0`), it traps deterministically with `unreachable` per the WASI Reactor ABI.
   - **Export & import precision (`REQ-TGT-245..247`):** Exports linear `"memory"` (unless `--import-memory`), `_initialize`, and **only** functions/globals annotated with `@export` or `@wasm_export("<name>")` (`REQ-TGT-245`). Every unresolved `extern` function maps to an explicit `(module, name)` W3C Section 2 `Import` (`REQ-TGT-246`), and mark-sweep GC strips 100% of unreferenced functions, data segments, indirect table elements, and `std` runtime helpers (`REQ-TGT-247`). [tasks/0453 §194.36; tasks/0523 §155 AWASM-56..58; tasks/0563 §304.26–27; SPEC-86 AXS-WASM-023, AXS-WASM-028..029]

### 3.5 Runtime Dynamic Loading (`DynLib`) & FFI Unwind Barrier

**AXS-ARTM-024 — Cross-Target Runtime Dynamic Loading & Mandatory `@export` No-Unwind Barrier.**
1. **Runtime `DynLib` loading (`SPEC-88 AXS-PLAT-012`):** Hosted Axiom programs load `.dll` (`LoadLibraryExW` + `GetProcAddress` + `FreeLibrary`), `.so` (`dlopen(RTLD_NOW | RTLD_LOCAL)` + `dlsym` + `dlclose`), and `.dylib` handles through `std.os.*.DynLib` (`DynLib.open` and `Drop`, capability-gated under `--safety-profile safe|sandbox` by explicit authority, `SPEC-53`); `unsafe fn symbol<T>(view(self), name: Str) -> Result<LibSymbol<T>, OsError>` returns a capability-bound `LibSymbol<T>` that cannot outlive its `DynLib` owner (`SPEC-50`, `SPEC-88 AXS-PLAT-012`).
2. **No-unwind ABI barrier (`SPEC-54 AXS-PAN-020`):** Every `@export` / `.def`-exported function in a `StaticLib` or `DynLib` enforces the mandatory foreign-ABI panic barrier: under both `--panic abort` and `--panic unwind`, an uncaught Axiom panic reaching an `@export` `extern "C"` / `extern "system"` frame boundary aborts immediately after deterministic reverse-order local `Drop` cleanup (`SPEC-54 AXS-PAN-010`) rather than unwinding across foreign C/OS/WASM frames. [0217 §54, §68; SPEC-50 AXS-UNS-030; SPEC-53; SPEC-54 AXS-PAN-010, AXS-PAN-020; SPEC-88 AXS-PLAT-012]

---

## 4. Archive Extraction, `--whole-archive`, Symbol Resolution & Embedded IR (`AXS-ARTM-025`..`030`)

**AXS-ARTM-025 — Demand-Driven Fixed-Point Archive Extraction Algorithm (`compiler/link/archive_resolve`, `T686`, `REQ-TGT-247`, `REQ-TGT-308`).**
Given ordered linker inputs $I = [i_1, \dots, i_K]$ where each $i_k$ is `Object(obj)`, `Archive(ar, whole: bool)`, or `SharedStub(sh)`:
1. **Seed phase:** Initialize live object list $M_{\text{live}} \leftarrow []$, defined symbol map $D \leftarrow \emptyset$, and FIFO unresolved queue $Q \leftarrow []$. Append every direct `Object(obj)` and every regular object member of `Archive(ar, whole = true)` (skipping `lib.axrmeta`!) in canonical order to $M_{\text{live}}$, updating $(D, Q)$ with each object's defined and undefined external symbols. Seed implicit target entry/runtime roots (`main` / `_start` / `_DllMainCRTStartup` / `_initialize`, `@export` CLI list, `.def` `EXPORTS` targets) into $Q$.
2. **Fixed-point extraction loop (`0164 §24–25`, `0217 §36–38`, `tasks/0369 §10`):**
   ```text
   loop {
       let mut extracted_any = false
       while let Some(sym) = Q.pop_front() {
           if D.contains(sym) { continue }
           if let Some((ar_idx, member_off)) = find_first_lazy_archive_provider(I, sym) {
               if !already_extracted(ar_idx, member_off) {
                   let obj = parse_and_verify_member(I[ar_idx], member_off)?  // checks TargetFingerprint
                   M_live.push(obj)
                   merge_object_symbols(obj, mut_view(D), mut_view(Q))?
                   extracted_any = true
               }
           }
       }
       if !extracted_any { break }
   }
   ```
   - Because each newly extracted member pushes its own unresolved symbols onto $Q$ and `find_first_lazy_archive_provider` re-scans all lazy archives `[i_1 .. i_K]` in deterministic CLI/dependency order, **mutually recursive static archives ($A \leftrightarrow B$, `0217 §38`) resolve deterministically in one link invocation** without requiring GNU `--start-group` / `--end-group` repetition (`--start-group` / `--end-group` are accepted as no-op compatibility flags).
   - Archive members whose defined symbols are never needed to satisfy $Q$ are **never parsed into `LinkIR` and never linked** (`REQ-TGT-247`), followed by per-section mark-sweep GC (`SPEC-27 AXS-LNK-020`, `SPEC-75 AXS-LTO-020`) to strip dead functions inside extracted members. [0164 §24–25; 0217 §36–39, §72 ALINK-28..29; tasks/0369 §10–11; tasks/0523 §155 AWASM-58; tasks/0524 §112 ABACKEND-83; SPEC-26 AXS-WLIB-012]

**AXS-ARTM-026 — Scoped `--whole-archive` / `--no-whole-archive` & Darwin `-force_load` Semantics (`T686`, `T688`).**
1. **Positional modal scoping (`--whole-archive` ... `--no-whole-archive`):**
   - `--whole-archive` enables `whole = true` for all subsequent `.lib`, `.a`, and `.axlib` inputs on the command line until `--no-whole-archive` restores default demand-driven (`whole = false`) mode.
   - Under `whole = true`, **every** regular object member of the archive (excluding pseudo-members `/`, `/SYM64/`, `//`, `__.SYMDEF*`, and `lib.axrmeta`) is unconditionally added to $M_{\text{live}}$ during the Seed phase, ensuring `@export` C-ABI wrappers (when building a `cdylib` from static archives!), `@used` sections, and `.init_array` / `.CRT$XCU` registration tables are retained.
2. **Single-archive `-force_load <path>`:** Forces `whole = true` for `<path>` alone without changing the modal state of subsequent inputs (matching Apple `ld` semantics).
3. **Validation (`AX_LINK_UNMATCHED_WHOLE_ARCHIVE`):** Reaching end-of-CLI with an unclosed `--whole-archive`, encountering `--no-whole-archive` when `whole == false`, passing `--whole-archive` with zero archive arguments before `--no-whole-archive`, or passing a non-archive file to `-force_load` fails deterministically with `AX_LINK_UNMATCHED_WHOLE_ARCHIVE`. [0217 §37; tasks/0369 §10–11]

**AXS-ARTM-027 — Cross-Format Symbol Strength, `COMDAT` / Weak Deduplication & Diamond Conflict Matrix (`REQ-TGT-308`, `T688`).**
`compiler/link` preserves exact symbol and relocation semantics across all four object formats (`tasks/0524 §112 ABACKEND-83`, `REQ-TGT-308`, `0164 §6–8, §26–27`, `0217 §11–13, §22–23, §36`, `SPEC-27 AXS-LNK-010..014`):

| Existing Binding in $D$ | Incoming Candidate | Resolution Outcome |
|---|---|---|
| `Strong` (object or extracted member) | `Strong` (object, extracted member, or `--whole-archive`) | **Error `AX_LINK_DUPLICATE_SYMBOL`** reporting demangled Axiom symbol + both `<archive>(<member>)` / `<obj>` origins and `.axmeta` source spans |
| `Strong` | `Weak` (`STB_WEAK`, `N_WEAK_DEF`, COFF `WEAK_EXTERNAL`, `WASM_SYM_BINDING_WEAK`) | Existing `Strong` definition retained (`Weak` overridden) |
| `Weak` | `Strong` | Incoming `Strong` replaces `Weak` definition |
| `Weak` | `Weak` | First canonical input retained (verified for matching symbol kind / `AbiFingerprint`) |
| `Comdat(key)` (`IMAGE_SCN_LNK_COMDAT` `SELECT_ANY`, ELF `SHT_GROUP` `GRP_COMDAT`, Mach-O weak-def coalesced, WASM `WASM_COMDAT_INFO`) | `Comdat(key)` (same canonical `GenericInstanceId` / vtable key) | First canonical group retained; duplicate group sections discarded as an atomic unit (`SPEC-27 AXS-LNK-012`) |
| `Strong` / `Weak` / `Comdat` | `ArchiveLazy` (unextracted lazy archive index entry) | Existing definition shadows archive index; **archive member is NOT extracted** (no false duplicate error unless `--whole-archive` forces extraction) |
| `Strong` / `Weak` / `Comdat` | `DynamicStub` (`.lib` import, `.so` `.dynsym`, `.dylib`/`.tbd`) | Static definition wins; dynamic import slot not emitted |
| `DynamicStub(libA)` | `DynamicStub(libB)` | First provider in CLI/dependency order selected (recorded with `libA`'s `DT_NEEDED` / Mach-O two-level `lib_ordinal` / PE `.idata` descriptor) |
| *None* (remains in $Q$ after step 2 + dynamic stub pass) | — (`!weak_undef`) | **Error `AX_LINK_UNDEFINED_SYMBOL`** with demangled symbol, referencing function + span, and candidate hint |

If two definitions or a definition and reference for external symbol `S` disagree in symbol kind (`Function` vs `Data` vs `Tls`), WASM `FuncType`, or `.axmeta` `AbiFingerprint`, linking fails with `AX_LINK_ABI_MISMATCH` (`SPEC-27 AXS-LNK-005`). [0164 §6–8, §26–27; 0217 §11–13, §22–23, §36; tasks/0369 §5–7, §12; tasks/0524 §112 ABACKEND-83; SPEC-27 AXS-LNK-005, AXS-LNK-010..014]

**AXS-ARTM-028 — Cross-Format Embedded IR & Metadata Sections (`.axmeta`, `.axmir`, `.axlto`, `SPEC-24` + `SPEC-75`).**
Extending `SPEC-24 AXS-ART-002, AXS-ART-020..021` from COFF to all supported object formats, `compiler/artifact/container` and `compiler/obj/*` embed pointer-free 64-byte-`ArtifactHeader`-wrapped metadata sections using `SPEC-24`'s per-family 8-byte ASCII `magic` and `format_family` tags (`"AXMETA01"` with `format_family = 4` for `.axmeta`, `"AXMIR001"` with `format_family = 2` for `.axmir`, and `"AXLTO001"` with `format_family = 3` for `.axlto`, carrying `target_fingerprint`, `interface_fingerprint`, and BLAKE3-128 `content_hash` in `ArtifactHeader` while storing `PackageName`/`PackageId` and `AbiFingerprint` inside `.axmeta` payload sections; any magic or `format_family` mismatch fails immediately with `AX_LINK_BAD_ARTIFACT`, `SPEC-24 AXS-ART-002, AXS-ART-021..023`) and non-allocatable container flags so host debuggers/linkers ignore them if not running Axiom LTO:

| Logical Section (`SPEC-04 AXS-EXT-071`) | Payload Summary | PE/COFF (`.obj`) | ELF64 (`.o`) | Mach-O 64 (`MH_OBJECT`) | WASM Relocatable (`.wasm`) |
|---|---|---|---|---|---|
| `Custom(".axmeta")` | `ModuleLtoSummary` (`FnLtoSummary`, `AbiFingerprint`, demangled symbol spans; `SPEC-75 AXS-LTO-002`) | `.axmeta` (`IMAGE_SCN_LNK_INFO \| IMAGE_SCN_MEM_DISCARDABLE`, `VirtualSize = 0`) | `.axmeta` (`SHT_PROGBITS`, `sh_flags = 0`, `sh_addr = 0`, `align = 8`) | `__AXIOM,__axmeta` (`S_ATTR_DEBUG = 0x02000000`) | Custom section (`id = 0`) `"axiom.axmeta"` |
| `Custom(".axmir")` | Serialized `Verified MIR` bodies for cross-package generics / CTFE / MIR diagnostics (`SPEC-24 AXS-ART-013`) | `.axmir` (`IMAGE_SCN_LNK_INFO \| IMAGE_SCN_MEM_DISCARDABLE`) | `.axmir` (`SHT_PROGBITS`, `sh_flags = 0`, `align = 8`) | `__AXIOM,__axmir` (`S_ATTR_DEBUG`) | Custom section (`id = 0`) `"axiom.axmir"` |
| `Custom(".axlto")` | Compact `Verified OptIR` bitcode for `--lto=thin` / `--lto=full` (`SPEC-75 AXS-LTO-002`) | `.axlto` (`IMAGE_SCN_LNK_INFO \| IMAGE_SCN_MEM_DISCARDABLE`) | `.axlto` (`SHT_PROGBITS`, `sh_flags = 0`, `align = 8`) | `__AXIOM,__axlto` (`S_ATTR_DEBUG`) | Custom section (`id = 0`) `"axiom.axlto"` |

Note that `.axmeta` (`7`B), `.axmir` (`6`B), and `.axlto` (`6`B) are all $\le 8$ ASCII bytes and therefore fit inline in COFF `IMAGE_SECTION_HEADER.Name[8]` and Mach-O `section_64.sectname[16]` (`__axmeta` = `8`B) with zero string-table indirection. [0164 §28; 0217 §42; SPEC-04 AXS-EXT-071; SPEC-24 AXS-ART-002, AXS-ART-020..021, AXS-ART-023; SPEC-75 AXS-LTO-002]

**AXS-ARTM-029 — Link-Time LTO Ingestion Across Archives & Mandatory Final-Image Stripping (`SPEC-24 AXS-ART-022`, `SPEC-75`).**
1. **Archive LTO ingestion:** When `--lto=thin` or `--lto=full` is active, `archive_resolve` reads `.axmeta` symbol summaries alongside native archive symbol directories, extracts required archive members to fixed point, validates every embedded `ArtifactHeader` per-family `magic` (`"AXMETA01"` / `"AXMIR001"` / `"AXLTO001"`), `format_family`, and BLAKE3-128 `content_hash` (`AX_LINK_BAD_ARTIFACT`), `schema_version` (`AX_LINK_ARTIFACT_SCHEMA_MISMATCH`), and `target_fingerprint` (`AX_LINK_ARTIFACT_TARGET_MISMATCH`), hands `.axlto`/`.axmir` payloads to `compiler/opt/lto` **before** final machine codegen (`INV-LAYER-002`, `SPEC-75 AXS-LTO-003`), and re-verifies post-LTO IR (`INV-PIPE-002`).
2. **Mandatory final-image stripping invariant:** Static archives (`.lib`, `.a`) and `.axlib` files **retain** `.axmeta`, `.axmir`, and `.axlto` inside their relocatable object members for downstream consumers, whereas **every final linked image** (`.exe`, `.dll`, ELF `ET_EXEC`/`PIE`/`.so`, Mach-O `MH_EXECUTE`/`.dylib`, linked Command/Reactor `.wasm`, `.efi`, and `--format bin`) **MUST strip 100% of `.axmeta`, `.axmir`, and `.axlto` sections** (`0` bytes mapped in memory or present on disk). [SPEC-24 AXS-ART-022; SPEC-75 AXS-LTO-002..003]

**AXS-ARTM-030 — Post-Encoding Object & Linked Image Verification Gate & Crash-Safe Atomic Output (`REQ-TGT-307`, `REQ-TGT-308`).**
Per `tasks/0524 §112 ABACKEND-82..83` (`REQ-TGT-307..308`) and `tasks/0563 §304.33–36, §304.45 AIMG-48..50`:
1. **Mandatory post-encoding verifier (`REQ-TGT-307`):** Immediately after instruction/WASM encoding (`verify_mc` / `verify_wasm`) and container serialization, every object writer, `archive_matrix` producer, and `ImageWriter` runs its structural verifier (`verify_coff_pe`, `verify_elf_image`, `verify_macho_image`, `verify_wasm`, `verify_archive`) asserting valid magic, monotonic non-overlapping section/segment bounds, W^X permissions (`AIMG-31`), valid RVA/VMA-to-file-offset mappings (`AIMG-25..26, 35..38`), sorted export tables, valid dynamic version/import indices, stripped `.axmeta`/`.axmir`/`.axlto` sections in final images, and valid Mach-O SHA-256 code-signature digests. Any internal violation aborts with `AX_ICE_INTERNAL` (`data.stage = "link_verify"`).
2. **Atomic publication (`AIMG-50`):** Every artifact (`.exe`, `.obj`/`.o`, `.lib`/`.a`, `.dll` + `.lib` + `.def`, `.so`, `.dylib`, `.axlib`, `.wasm`) is written to `<out>.tmp.<pid>` and atomically renamed to `<out>` only after verification succeeds; failed builds never leave truncated or stale output files on disk. [tasks/0524 §112 ABACKEND-82..83; tasks/0563 §304.33–36, §304.45 AIMG-25..38, 48..50; SPEC-24 AXS-ART-005]

---

## 5. CLI Surface, Diagnostics, Canonical Examples & Traceability (`AXS-ARTM-031`..`040`)

**AXS-ARTM-031 — Unified Driver & Linker CLI Flags for the Artifact & Library Matrix.**

| CLI Flag | Target Scope | Effect |
|---|---|---|
| `--kind <exe\|bin\|obj\|lib\|staticlib\|dll\|cdylib\|axlib\|wasm-module\|wasm-reactor>` | All targets | Selects normalized `ArtifactKind` (`AXS-ARTM-002`; `--emit=obj` aliases `--kind obj`) |
| `-L <dir>`, `-l <name>`, `-l:<filename>` | All targets | Appends library search path / links named or exact library (`AXS-ARTM-007`) |
| `--whole-archive`, `--no-whole-archive`, `-force_load <ar>` | All targets | Forces unconditional extraction of archive object members (`AXS-ARTM-026`) |
| `--bundle-deps` | `--kind lib\|staticlib` | Merges reachable upstream `axlib` object members into one self-contained `.a`/`.lib` (`AXS-ARTM-004`) |
| `--implib <path>`, `--def <file.def>`, `--emit-def <file.def>` | Windows / UEFI PE | Overrides companion `.lib` path; consumes or emits `.def` exports/ordinals/forwarders (`AXS-ARTM-016..017`) |
| `--soname <name>`, `--version-script <file.ver>` | ELF64 `.so` | Sets `DT_SONAME` (`AXS-ARTM-018`); emits `.gnu.version` + `.gnu.version_d` (`AXS-ARTM-019..020`) |
| `--install-name <id>`, `--current-version <X.Y.Z>`, `--compatibility-version <X.Y.Z>` | Mach-O `.dylib` | Configures `LC_ID_DYLIB` install name (`@rpath/...`) and packed version triples (`AXS-ARTM-021`) |
| `--reexport-l<name>`, `--reexport-library <path>`, `-weak-l<name>` | Mach-O `.dylib`/`exe` | Emits `LC_REEXPORT_DYLIB` or `LC_LOAD_WEAK_DYLIB` (`AXS-ARTM-022`) |
| `--rpath <dir>` | ELF64 & Mach-O | Emits `DT_RUNPATH` (`$ORIGIN` sets `DF_ORIGIN`) or `LC_RPATH` (`AXS-ARTM-018, 021`) |
| `axiomc inspect --emit=archive\|exports\|imports\|dynlib <file>` | All targets | Dumps deterministic JSON/text summary of archive members/index, exports, imports, and version/rpath metadata |

[0197 §19, §23; tasks/0563 §304.34–35; SPEC-26 AXS-WLIB-002; SPEC-82 AXS-ELFD-004, AXS-ELFD-045; SPEC-84 AXS-MACHO-021..022]

**AXS-ARTM-032 — Canonical Diagnostic Taxonomy & Task-Card Code Mapping (`spec/diagnostics.md` §3, §11).**
Per `ADR-0011` and `AXD-010..021`, all `E16.10` diagnostics use canonical `AX_<AREA>_<NAME>` identifiers across the core `DRIVER`, `FFI`, and `LINK` areas (the `T685`/`T688` card shorthand `E8900–E8919` maps 1-to-1 onto the 20 rows below):

| Card Ref | Canonical Code | Area | Sev | Task | Condition & Structured `data.*` Payload |
|---|---|---|---|---|---|
| `E8900` | `AX_DRIVER_INVALID_ARTIFACT_KIND` | `DRIVER` | E | `T750`/`T686` | Unknown `--kind` / manifest `kind` string, `wasm-module`/`wasm-reactor` on non-WASM, or `dll`/`cdylib` on `<arch>-none` (`data.kind`, `data.target`; recognized non-`exe` `--kind` passed to `axiomc run` emits `AX_DRIVER_USAGE`, `AXS-ARTM-002`) |
| `E8901` | `AX_FFI_GENERIC_EXPORT` | `FFI` | E | `T751` | `@export` / `@wasm_export` attached to uninstantiated generic `fn` or type (`SPEC-26 AXS-WLIB-004`) |
| `E8902` | `AX_FFI_BAD_TYPE` | `FFI` | E | `T501`/`T687` | Non-FFI-safe Axiom type without `@repr(C)`/`@repr(transparent)` exposed in `extern "C"` `@export` signature (`SPEC-50`) |
| `E8903` | `AX_LINK_BAD_OBJECT` | `LINK` | E | `T027`/`T686` | Corrupt/truncated COFF, ELF64, Mach-O 64, or relocatable `.wasm` object input (`data.file`) |
| `E8904` | `AX_LINK_BAD_ARCHIVE` | `LINK` | E | `T750`/`T686` | Corrupt `!<arch>\n` header, odd offset, out-of-bounds `//` or `#1/<len>` name, or corrupt `/` / `/SYM64/` / `__.SYMDEF*` index (`data.archive`) |
| `E8905` | `AX_LINK_THIN_ARCHIVE_UNSUPPORTED` | `LINK` | E | `T686` | Non-hermetic GNU thin archive (`!<thin>\n`) passed as linker input (`data.archive`) |
| `E8906` | `AX_LINK_UNMATCHED_WHOLE_ARCHIVE` | `LINK` | E | `T686` | Unclosed `--whole-archive`, stray `--no-whole-archive`, empty whole-archive group, or non-archive `-force_load` (`data.flag`) |
| `E8907` | `AX_LINK_BAD_ARTIFACT` | `LINK` | E | `T765`/`T686` | Corrupt per-family `ArtifactHeader` magic (`"AXMI0001"`/`"AXMETA01"`/`"AXMIR001"`/`"AXLTO001"`), `format_family`, bounds, or BLAKE3-128 `content_hash` in `lib.axrmeta` or `.axmeta`/`.axmir`/`.axlto` (`data.file`) |
| `E8908` | `AX_LINK_ARTIFACT_SCHEMA_MISMATCH` | `LINK` | E | `T765`/`T686` | Unsupported `schema_version` in `lib.axrmeta` or embedded `.axmeta`/`.axmir`/`.axlto` (`data.expected_version`, `data.found_version`) |
| `E8909` | `AX_LINK_ARTIFACT_TARGET_MISMATCH` | `LINK` | E | `T765`/`T686`/`T687` | `TargetFingerprint`, ISA/CPU, endianness, pointer width, or ABI mismatch in `.obj`/`.o`/`.a`/`.lib`/`.axlib`/`.so`/`.dylib`/`.tbd`/`.wasm` |
| `E8910` | `AX_LINK_AXLIB_PACKAGE_CONFLICT` | `LINK` | E | `T686`/`T688` | Diamond graph links two `.axlib` (or `.axlib` + bundled `staticlib`) artifacts for the same `package` with differing `InterfaceFingerprint` (`data.package`, `data.first_artifact`, `data.second_artifact`) |
| `E8911` | `AX_LINK_LIBRARY_NOT_FOUND` | `LINK` | E | `T750`/`T687` | `-l<name>` or `@link("<name>")` not found in `-L`, `deps/`, `--sysroot`, `.tbd`, or built-in OS stub catalogs (`data.library`) |
| `E8912` | `AX_LINK_UNDEFINED_SYMBOL` | `LINK` | E | `T027`/`T686`/`T687` | Unresolved external symbol or missing `.def` / version-script target after fixed-point extraction (`data.symbol`, `data.demangled`) |
| `E8913` | `AX_LINK_DUPLICATE_SYMBOL` | `LINK` | E | `T027`/`T686`/`T688` | Two `Strong` definitions of the same external symbol across objects, `--whole-archive` members, or diamond libraries (`data.symbol`, `data.demangled`) |
| `E8914` | `AX_LINK_DUPLICATE_EXPORT` | `LINK` | E | `T751`/`T687` | Duplicate exported symbol name or duplicate pinned PE `.def` ordinal in one image (`data.symbol`, `data.ordinal`) |
| `E8915` | `AX_LINK_ABI_MISMATCH` | `LINK` | E | `T067`/`T687` | Calling convention, symbol kind (`Function` vs `Data`/`Tls`), WASM `FuncType`, or `.axmeta` `AbiFingerprint` mismatch (`data.symbol`) |
| `E8916` | `AX_LINK_TEXTREL_FORBIDDEN` | `LINK` | E | `T658`/`T687` | Non-PIC relocation targeting a read-only/executable segment in `.so`, `PIE`, `MH_DYLIB`, or `MH_EXECUTE` (`data.section`, `data.symbol`) |
| `E8917` | `AX_LINK_INVALID_DEF_FILE` | `LINK` | E | `T687` | Invalid Windows `.def` syntax, ordinal outside `1..65535`, `NONAME` without `@ordinal`, or invalid forwarder (`data.file`, `data.line`, `data.detail`) |
| `E8918` | `AX_LINK_INVALID_VERSION_SCRIPT` | `LINK` | E | `T687` | Invalid ELF `--version-script` syntax, duplicate version node, unknown parent node, or multiple `@@` defaults (`data.version`, `data.symbol`) |
| `E8919` | `AX_LINK_INVALID_DYLIB_VERSION` / `AX_LINK_WASM_ENTRY_CONFLICT` | `LINK` | E | `T687` | Invalid Mach-O `X.Y.Z` version (`compat > current` or component overflow) / empty `--install-name`/`--soname`/`--rpath` (`AX_LINK_INVALID_DYLIB_VERSION`), or WASM `_start` vs `_initialize` mode conflict (`AX_LINK_WASM_ENTRY_CONFLICT`) |

[ADR-0011; spec/diagnostics.md AXD-010..021, §10–11]

**AXS-ARTM-033 — Canonical Positive Example 1: Axiom Native Package Library (`--kind axlib`) Exporting Generics, Capabilities & `const` Across Targets.**
```axiom
// --- greeting_pkg/lib.ax ---
// Built for Windows: axiomc build --target x86_64-windows --kind axlib greeting_pkg/lib.ax -o deps/greeting_pkg.axlib
// Built for Linux:   axiomc build --target x86_64-linux   --kind axlib greeting_pkg/lib.ax -o deps/libgreeting_pkg.axlib
// Built for macOS:   axiomc build --target aarch64-macos  --kind axlib greeting_pkg/lib.ax -o deps/libgreeting_pkg.axlib
// Archive embeds lib.axrmeta (types, capabilities, const GREETING, generic fold_slice MIR) + greeting_pkg_cgu0.{obj,o}.
module greeting_pkg

pub const GREETING: Str = "Xin chào thế giới"

pub struct Stats {
    pub count: usize
    pub total: i64
}

pub fn fold_slice<T: Copy>(items: view<[T]>, seed: i64, step: fn(i64, T) -> i64) -> Stats {
    let mut acc = seed
    let mut i: usize = 0
    while i < len(items) {
        acc = step(acc, items[i])
        i = i + 1
    }
    Stats { count: len(items), total: acc }
}

pub fn banner() -> Str {
    GREETING
}
```
```axiom
// --- app/main.ax ---
// Linked without greeting_pkg/lib.ax sources:
//   axiomc build --target x86_64-linux app/main.ax -L deps -lgreeting_pkg -o app_bin
module app

use std.io.println
use greeting_pkg.{Stats, banner, fold_slice}

fn add_i32(acc: i64, x: i32) -> i64 {
    acc + (x as i64)
}

fn main() -> i32 {
    println(banner())                                       // prints exact UTF-8: Xin chào thế giới
    let nums: [4]i32 = [10, 20, 30, 40]
    let st: Stats = fold_slice<i32>(view(nums[..]), 0, add_i32)
    if st.count == 4 && st.total == 100 { 0 } else { 1 }
}
```

**AXS-ARTM-034 — Canonical Positive Example 2: Cross-Target `cdylib` (`--kind cdylib`) with Hidden Internal Helpers, `.def`, ELF Symbol Versioning & macOS `@rpath`.**
```axiom
// --- codec/lib.ax ---
// Windows (.dll + .lib + .def):
//   axiomc build --target x86_64-windows --kind cdylib codec/lib.ax --def codec/codec.def -o codec.dll
// Linux (.so with DT_SONAME + GNU VERDEF):
//   axiomc build --target x86_64-linux --kind cdylib codec/lib.ax --soname libcodec.so.2 --version-script codec/codec.ver -o libcodec.so.2.1
// macOS (.dylib with @rpath install_name + packed X.Y.Z versions + ad-hoc LC_CODE_SIGNATURE):
//   axiomc build --target aarch64-macos --kind cdylib codec/lib.ax --install-name @rpath/libcodec.2.dylib --current-version 2.1.0 --compatibility-version 2.0.0 -o libcodec.2.dylib
module codec

@repr(C)
pub struct PacketHeader {
    pub magic: u32
    pub payload_len: u32
}

// Package-public helper WITHOUT @export:
// STV_HIDDEN on ELF, N_PEXT on Mach-O, non-dllexport on PE -> NEVER leaks into .dynsym / .edata / export trie!
pub fn checksum_step(acc: u32, byte_val: u32) -> u32 {
    (acc ^ byte_val) * 16777619u32
}

@export(name = "ax_packet_tag", version = "CODEC_2.0", default = true)
pub extern "C" fn packet_tag(hdr: *const PacketHeader) -> u32 {
    if hdr as usize == 0 {
        return 0u32
    }
    let h = unsafe { *hdr }
    checksum_step(h.magic, h.payload_len)
}
```

**AXS-ARTM-035 — Canonical Positive Example 3: WebAssembly Reactor (`--kind cdylib --target wasm32-wasi`) with Synthesized `_initialize`.**
```axiom
// Compiled with: axiomc build --target wasm32-wasi --kind cdylib filter.ax -o filter.wasm
// Emits W3C WASM Reactor: exports "memory", synthesized single-shot "_initialize", and "ax_scale_sum" ONLY;
// omits "_start" and strips unreferenced std helpers (REQ-TGT-245..247).
module filter

static mut SCALE_FACTOR: i32 = 3

// Private helper omitted from WASM Section 7 (Export)
fn clamp_positive(v: i32) -> i32 {
    if v < 0 { 0 } else { v }
}

@wasm_export("ax_scale_sum")
pub extern "C" fn scale_sum(a: i32, b: i32) -> i32 {
    let factor = unsafe { SCALE_FACTOR }
    (clamp_positive(a) + clamp_positive(b)) * factor
}
```

**AXS-ARTM-036 — Canonical Negative Example 1: Diamond Strong Symbol Collision (`AX_LINK_DUPLICATE_SYMBOL`) & Incompatible `axlib` Diamond (`AX_LINK_AXLIB_PACKAGE_CONFLICT`).**
```axiom
// --- Case A: Two static libraries forced via --whole-archive both define strong symbol "ax_crc32_init" ---
// lib_a.ax (compiled to liba.a) and lib_b.ax (compiled to libb.a):
module lib_a

@export("ax_crc32_init")
pub extern "C" fn crc32_init() -> u32 { 0xEDB8_8320u32 }

// Command:
//   axiomc build --target x86_64-linux main.ax --whole-archive liba.a libb.a --no-whole-archive -o app
// Expected: ERROR AX_LINK_DUPLICATE_SYMBOL (data.symbol = "ax_crc32_init") naming liba.a(...) and libb.a(...).

// --- Case B: Diamond axlib mismatch (app -> mid1 -> core_v1.axlib, app -> mid2 -> core_v2.axlib) ---
// Command:
//   axiomc build --target x86_64-linux app.ax deps/libmid1.axlib deps/libmid2.axlib deps/v1/libcore.axlib deps/v2/libcore.axlib
// Expected: ERROR AX_LINK_AXLIB_PACKAGE_CONFLICT (data.package = "core").
```

**AXS-ARTM-037 — Canonical Negative Example 2: Invalid Windows `.def` File (`AX_LINK_INVALID_DEF_FILE`) & Invalid ELF Version Script (`AX_LINK_INVALID_VERSION_SCRIPT`).**
```text
; --- bad_exports.def (rejected on x86_64-windows with AX_LINK_INVALID_DEF_FILE) ---
LIBRARY "codec"
EXPORTS
    ax_fast_hash NONAME          ; ERROR: NONAME requires an explicit @<ordinal> in 1..65535
    ax_overflow_ord @70000       ; ERROR: PE export ordinal 70000 exceeds u16 limit 65535
```
```text
/* --- bad_versions.ver (rejected on x86_64-linux with AX_LINK_INVALID_VERSION_SCRIPT) --- */
CODEC_2.0 {
    global:
        ax_packet_tag;
    local:
        *;
} CODEC_MISSING_PARENT;          /* ERROR: parent version node CODEC_MISSING_PARENT is undefined */
```

**AXS-ARTM-038 — Canonical Negative Example 3: CLI `--kind` Compatibility (`AX_DRIVER_USAGE` vs. `AX_DRIVER_INVALID_ARTIFACT_KIND`), Unmatched `--whole-archive` (`AX_LINK_UNMATCHED_WHOLE_ARCHIVE`), Thin Archive (`AX_LINK_THIN_ARCHIVE_UNSUPPORTED`), Invalid Mach-O Version (`AX_LINK_INVALID_DYLIB_VERSION`), and WASM Entry Conflict (`AX_LINK_WASM_ENTRY_CONFLICT`).**
```axiom
// 0a) Valid non-Executable --kind passed to `axiomc run`:
//     axiomc run --kind staticlib lib.ax
//     -> ERROR AX_DRIVER_USAGE (exit code 2: "'run' does not support '--kind staticlib'")
//
// 0b) Unknown --kind or target-incompatible artifact kind:
//     axiomc build --target x86_64-none --kind cdylib k.ax
//     -> ERROR AX_DRIVER_INVALID_ARTIFACT_KIND (exit code 2: data.kind = "dll", data.target = "x86_64-none")
//
// 1) Unclosed --whole-archive:
//    axiomc build --target x86_64-linux main.ax --whole-archive libfoo.a -o app
//    -> ERROR AX_LINK_UNMATCHED_WHOLE_ARCHIVE (missing --no-whole-archive)
//
// 2) GNU thin archive ("!<thin>\n" created by `ar rcT thin.a foo.o`):
//    axiomc build --target x86_64-linux main.ax thin.a -o app
//    -> ERROR AX_LINK_THIN_ARCHIVE_UNSUPPORTED (data.archive = "thin.a")
//
// 3) Mach-O compatibility_version > current_version:
//    axiomc build --target aarch64-macos --kind cdylib lib.ax --current-version 1.2.0 --compatibility-version 2.0.0
//    -> ERROR AX_LINK_INVALID_DYLIB_VERSION (compatibility_version 2.0.0 > current_version 1.2.0)
//
// 4) WASM reactor defining reserved "_start":
//    axiomc build --target wasm32-wasi --kind cdylib bad_reactor.ax -o bad_reactor.wasm
//    -> ERROR AX_LINK_WASM_ENTRY_CONFLICT (data.symbol = "_start", data.kind = "dll")
module bad_reactor

@wasm_export("_start")
pub extern "C" fn bogus_reactor_start() {}
```

**AXS-ARTM-039 — Architecture Layering & Module Ownership Split (`E18.7` vs. `E16.10` vs. `E16.11`, `INV-LAYER-002`).**
1. **Strict `INV-LAYER-002` compliance:** `compiler/obj/archive_matrix`, `compiler/obj/def_import`, `compiler/link/archive_resolve`, and `compiler/link/dynlib_matrix` reside in the `objmodel` and `link` architectural layers and depend **only** on `kernel`, `diag`, `source`, `artifact/container`, and `objmodel` (`SPEC-04 AXS-EXT-074`, `SPEC-75 AXS-LTO-003`). They **never** import `syntax`, `hir`, `sema`, `mir`, or `opt`. (`CompilerDB` in `compiler/driver` / `compiler/artifact/axmi` extracts `lib.axrmeta` bytes via `archive_matrix` and deserializes semantic interface tables at the frontend/driver layer.)
2. **Epic boundary split:**
   - **`E18.7` (`T750`–`T751`, `SPEC-26`):** Delivers baseline Windows x64 `CoffAr` `.lib` static archives, PE32+ `.dll` emission (`.edata`, `_DllMainCRTStartup`, `.reloc`), and short-import `.lib` generation in `compiler/obj` and `compiler/link` (`REQ-OWNER-006`).
   - **`E16.10` (`T686`–`T688`, `SPEC-89`):** Generalizes static archives (`CoffAr`, `GnuAr` + `/SYM64/`, `BsdAr` + `__.SYMDEF SORTED`), `.axlib` (`lib.axrmeta`), `--whole-archive`/`-force_load` fixed-point resolution, Windows `.def` parsing/emission + forwarders, ELF GNU symbol versioning (`VERSYM`/`VERDEF`/`VERNEED`), Mach-O `@rpath` / version triples / two-level namespace / `LC_REEXPORT_DYLIB`, and WASM `_initialize` reactors across all targets.
   - **`E16.11` (`T689`–`T692`, `SPEC-90`):** Wraps per-architecture `SPEC-89` `MH_EXECUTE`, `MH_DYLIB`, and `BsdAr` `.a` slices into Mach-O Universal 2 (`0xCAFEBABE` / `0xCAFEBABF`) multi-arch containers (`ArtifactKind.Universal`). [INV-LAYER-002; SPEC-04 AXS-EXT-070..074; SPEC-26; SPEC-75 AXS-LTO-003]

**AXS-ARTM-040 — `E16.10` Implementation, Invariant & Requirement Traceability Matrix.**

| Task | Owned Paths | Rules & Invariants Verified | Covered Requirements |
|---|---|---|---|
| `T685` | `spec/SPEC-89-artifact-library-matrix.md` (`locks`: `INDEX.md`, `diagnostics.md`, `invariants.md`) | `AXS-ARTM-001`..`040`; registers `INV-ARTM-001`..`005` & `E16.10` diagnostics | `REQ-TGT-101`, `REQ-TGT-103`, `REQ-TGT-104`, `REQ-TGT-184`, `REQ-TGT-307`, `REQ-TGT-308` |
| `T686` | `compiler/obj/archive_matrix`, `compiler/link/archive_resolve`, `tests/link/static_matrix`, `tests/selfhost/obj`, `tests/selfhost/link` | `AXS-ARTM-001`..`014`, `025`..`030`; `INV-ARTM-001`, `INV-ARTM-002` | `REQ-TOOL-001`, `REQ-TGT-101`, `REQ-TGT-151`, `REQ-TGT-184`, `REQ-TGT-247` |
| `T687` | `compiler/obj/def_import`, `compiler/link/dynlib_matrix`, `tests/link/dynlib_matrix`, `tests/selfhost/obj`, `tests/selfhost/link` | `AXS-ARTM-005`..`007`, `015`..`024`, `031`..`032`; `INV-ARTM-003`, `INV-ARTM-004` | `REQ-TGT-060`, `REQ-TGT-104`, `REQ-TGT-146`, `REQ-TGT-245`, `REQ-TGT-246`, `REQ-TGT-308` |
| `T688` | `tests/conformance/p16/e16_10_artifact_matrix` | End-to-end conformance across `AXS-ARTM-001`..`040`; `INV-ARTM-005` | `REQ-TGT-106`, `REQ-TGT-307`, `REQ-TGT-308`, `REQ-TGT-318`, `REQ-TGT-320` |

---

## Sources
`0097 §27`; `0164 §1–11, §20–35`; `0185`; `0186`; `0187`; `0196`; `0197 §1–5, §17–26`; `0217 §3–4, §11–24, §30–45, §53–57, §68–72` (`ALINK-20..56`); `tasks/0369 §1–22, §25–37` (`ALINK-20..50`); `tasks/0453 §194.10, §194.20–23, §194.28–31, §194.36, §194.42–44` (`ATARGET-20..50`); `tasks/0518 §151` (`AMACHINE-71, 112, 114, 115, 117`); `tasks/0521 §156` (`AARM-52, 57`); `tasks/0522 §159` (`ABACKEND-38`); `tasks/0523 §155` (`AWASM-56..58`); `tasks/0524 §112` (`ABACKEND-82..83, 93, 95`); `tasks/0563 §304.1–304.46` (`AIMG-20..60`); `spec/decisions/ADR-0001-fixed-address-declarations.md`; `spec/decisions/ADR-0011-diagnostic-code-taxonomy.md`; `spec/decisions/ADR-0034-oracle-independence.md`; `spec/SPEC-02-grammar.md`; `spec/SPEC-04-core-extensibility.md`; `spec/SPEC-24-artifact-format-module-interfaces.md`; `spec/SPEC-26-windows-artifact-kinds.md`; `spec/SPEC-27-separate-compilation-linker-v2.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-52-freestanding-runtime-composition.md`; `spec/SPEC-54-panic-unwinding.md`; `spec/SPEC-55-fixed-address-declarations.md`; `spec/SPEC-56-module-relative-bindings.md`; `spec/SPEC-75-lto-wpo-section-gc-pgo.md`; `spec/SPEC-80-linux-x86-64-elf-static.md`; `spec/SPEC-81-target-desc-isa-conformance.md`; `spec/SPEC-82-linux-elf-dynamic.md`; `spec/SPEC-83-aarch64-linux.md`; `spec/SPEC-84-macos-aarch64-macho.md`; `spec/SPEC-85-android-aarch64-jni.md`; `spec/SPEC-86-wasm32-backend.md`; `spec/SPEC-87-riscv64-linux.md`; `spec/SPEC-88-cross-compilation-platform-layer.md`; `spec/requirements/CATALOG.md`; `spec/requirements/OWNER.md`.
